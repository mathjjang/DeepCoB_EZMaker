# REPL over BLE UART

import bluetooth
import io
import os
import micropython
import machine
import ble_nus
import config
import sys
import ubinascii

_MP_STREAM_POLL = micropython.const(3)
_MP_STREAM_POLL_RD = micropython.const(0x0001)

# TODO: Remove this when STM32 gets machine.Timer.
if hasattr(machine, "Timer"):
    _timer = machine.Timer(-1)
else:
    _timer = None

# Global reference to the UART instance
_current_uart = None

# Batch writes into 50ms intervals.
def schedule_in(handler, delay_ms):
    def _wrap(_arg):
        handler()

    if _timer:
        _timer.init(mode=machine.Timer.ONE_SHOT, period=delay_ms, callback=_wrap)
    else:
        micropython.schedule(_wrap, None)


# Simple buffering stream to support the dupterm requirements.
class BLEUARTStream(io.IOBase):
    def __init__(self, uart):
        self._uart = uart
        self._tx_buf = bytearray()
        self._uart.irq(self._on_rx)

    def _on_rx(self):
        # Needed for ESP32.
        if hasattr(os, "dupterm_notify"):
            os.dupterm_notify(None)

    def read(self, sz=None):
        return self._uart.read(sz)

    def readinto(self, buf):
        avail = self._uart.read(len(buf))
        if not avail:
            return None
        for i in range(len(avail)):
            buf[i] = avail[i]
        return len(avail)

    def ioctl(self, op, arg):
        if op == _MP_STREAM_POLL:
            if self._uart.any():
                return _MP_STREAM_POLL_RD
        return 0

    def _flush(self):
        data = self._tx_buf[0:200]
        self._tx_buf = self._tx_buf[200:]
        self._uart.write(data)
        if self._tx_buf:
            schedule_in(self._flush, 30)

    def write(self, buf):
        empty = not self._tx_buf
        self._tx_buf += buf
        if empty:
            schedule_in(self._flush, 30)

def handle_repl_command(conn_handle, cmd):
    """
    Handle REPL mode control commands:
    - REPL:ON - Turn on REPL mode
    - REPL:OFF - Turn off REPL mode
    - REPL:STATUS - Get current REPL mode status
    """
    global _current_uart
    
    try:
        cmd_str = cmd.decode('utf-8').strip()
        print(f"Received REPL command: {cmd_str}")
        
        if cmd_str == "REPL:ON":
            # Change mode to REPL mode (True)
            try:
                # Import here to avoid circular imports
                import change_repl_simple
                change_repl_simple.change_mode(True)
                # Reload config to get the updated state
                if 'config' in sys.modules:
                    del sys.modules['config']
                import config
                mode_changed = getattr(config, 'repl_flag', False)
                response = f"REPL:ON_OK:{mode_changed}"
            except Exception as e:
                response = f"REPL:ERROR:{str(e)}"
                
        elif cmd_str == "REPL:OFF":
            # Change mode to IoT mode (False)
            try:
                # Import here to avoid circular imports
                import change_repl_simple
                change_repl_simple.change_mode(False)
                # Reload config to get the updated state
                if 'config' in sys.modules:
                    del sys.modules['config']
                import config
                mode_changed = not getattr(config, 'repl_flag', True)
                response = f"REPL:OFF_OK:{mode_changed}"
            except Exception as e:
                response = f"REPL:ERROR:{str(e)}"
                
        elif cmd_str == "REPL:STATUS":
            # Report current REPL mode
            try:
                # Reload config to get current state
                if 'config' in sys.modules:
                    del sys.modules['config']
                import config
                
                if hasattr(config, 'repl_flag'):
                    status = "ON" if config.repl_flag else "OFF"
                    response = f"REPL:STATUS:{status}"
                else:
                    response = "REPL:STATUS:UNKNOWN"
            except Exception as e:
                response = f"REPL:ERROR:{str(e)}"
                
        else:
            response = "REPL:UNKNOWN_COMMAND"
        
        print(f"REPL response: {response}")
            
        # Send response through the UART's repl_notify method
        if _current_uart and hasattr(_current_uart, 'repl_notify'):
            _current_uart.repl_notify(response.encode('utf-8'))
        else:
            print("Cannot send REPL response: UART not available or repl_notify not supported")
        
    except Exception as e:
        print(f"REPL command error: {e}")
        # Try to send error response if possible
        if _current_uart and hasattr(_current_uart, 'repl_notify'):
            _current_uart.repl_notify(f"REPL:ERROR:{str(e)}".encode('utf-8'))

def get_device_name():
    # Use unique ID from MCU without initializing network
    unique_id = ubinascii.hexlify(machine.unique_id()).decode()
    id_suffix = unique_id[-6:].upper()
    return f"DeepCoB{id_suffix}"

def start():
    """
    Start the REPL over BLE UART service
    
    Args:
        name: The name to advertise for the BLE device
        
    Returns:
        The UART instance that can be used to communicate
    """
    global _current_uart
    
    ble = bluetooth.BLE()
    uart = ble_nus.BLEUART(ble, name=get_device_name())
    _current_uart = uart  # Store global reference
    
    # Register REPL command handler if supported
    if hasattr(uart, 'repl_irq'):
        print("Registering REPL command handler")
        uart.repl_irq(handle_repl_command)
    else:
        print("REPL command handling not supported by the UART implementation")
    
    stream = BLEUARTStream(uart)
    os.dupterm(stream)
    #return uart  # Return uart for external access if needed