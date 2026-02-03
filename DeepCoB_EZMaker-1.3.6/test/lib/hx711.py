"""
HX711 Weight Sensor Library for MicroPython
============================================

무게 센서 (HX711 + Load Cell) MicroPython 드라이버 라이브러리

주요 기능:
- 24비트 고정밀 무게 측정
- Tare (영점 조정) 기능
- Scale (보정) 기능
- Gain 설정 (128, 64, 32)
- 인터럽트 제어로 안정적인 통신

사용 예:
    from hx711 import HX711
    
    hx = HX711(dout_pin=42, pd_sck_pin=14)
    hx.tare()  # 영점 조정
    hx.set_scale(400.0)  # 스케일 설정
    weight = hx.get_units()  # 무게 읽기 (g)
    print(f"Weight: {weight:.2f} g")

연결:
- DOUT (Data) -> GPIO 42 (RXD/D10)
- SCK (Clock) -> GPIO 14 (TXD/D11)
- VCC, GND

참고:
- 아두이노 HX711 라이브러리 (bogde/HX711)를 MicroPython으로 포팅
- https://github.com/bogde/HX711
"""

import time
from machine import Pin, disable_irq, enable_irq

class HX711:
    def __init__(self, dout_pin, pd_sck_pin, gain=128):
        """
        Initialize HX711 instance.
        
        Args:
            dout_pin (int): GPIO number for DOUT (Data)
            pd_sck_pin (int): GPIO number for PD_SCK (Clock)
            gain (int): Initial gain (128, 64, or 32). Default 128.
        """
        self.p_dout = Pin(dout_pin, Pin.IN)
        self.p_pd_sck = Pin(pd_sck_pin, Pin.OUT)
        self.p_pd_sck.value(0)
        
        self.GAIN = 0
        self.OFFSET = 0
        self.SCALE = 1.0
        
        self.set_gain(gain)

    def is_ready(self):
        """
        Check if HX711 is ready for reading.
        Returns:
            bool: True if ready (DOUT is low), False otherwise.
        """
        return self.p_dout.value() == 0

    def set_gain(self, gain):
        """
        Set the gain factor; takes effect on the NEXT read.
        """
        if gain == 128:
            self.GAIN = 1
        elif gain == 64:
            self.GAIN = 3
        elif gain == 32:
            self.GAIN = 2
        
        # Unlike original C++ lib, we don't read here to apply gain immediately,
        # because reading when not ready can hang or return garbage.
        # The gain will be applied after the next valid read() call.

    def read(self):
        """
        Read 24-bit data from HX711.
        Waits for ready state (blocking).
        
        Returns:
            int: Signed 24-bit integer value
        """
        # Wait for the chip to become ready
        self.wait_ready()

        # Disable interrupts for critical timing
        irq_state = disable_irq()
        
        try:
            data = 0
            
            # Pulse the clock pin 24 times to read the data.
            # MSB First.
            # Timing is critical:
            # PD_SCK high time: min 0.2 us, max 50 us
            # PD_SCK low time: min 0.2 us
            # We use simple loop/operations which take > 1us on MicroPython,
            # so we might not need explicit sleeps if CPU isn't too fast.
            # But to be safe and match C++ 'shiftInSlow', we add delays if needed.
            
            for _ in range(24):
                self.p_pd_sck.value(1)
                # time.sleep_us(1) # Optional, usually overhead is enough
                
                # Read bit when Clock is High? No, usually read on rising edge or high level.
                # HX711: Data is shifted out on falling edge of PD_SCK and remains valid until next falling edge.
                # But C++ code reads *while* clock is High.
                # shiftInSlow: Clock HIGH -> Read -> Clock LOW
                
                # Reading bit
                bit_val = self.p_dout.value()
                data = (data << 1) | bit_val
                
                self.p_pd_sck.value(0)
                # time.sleep_us(1) 

            # Set the channel and the gain factor for the next reading using the clock pin.
            for _ in range(self.GAIN):
                self.p_pd_sck.value(1)
                # time.sleep_us(1)
                self.p_pd_sck.value(0)
                # time.sleep_us(1)
                
        finally:
            enable_irq(irq_state)

        # Replicate the most significant bit to pad out a 32-bit signed integer
        # Data is 24-bit 2's complement.
        # If bit 23 (0x800000) is 1, it's negative.
        if data & 0x800000:
            data -= 0x1000000

        return data

    def wait_ready(self, delay_ms=10):
        """
        Wait for the chip to become ready. Blocking.
        """
        while not self.is_ready():
            time.sleep_ms(delay_ms)

    def wait_ready_retry(self, retries=3, delay_ms=10):
        count = 0
        while count < retries:
            if self.is_ready():
                return True
            time.sleep_ms(delay_ms)
            count += 1
        return False
        
    def wait_ready_timeout(self, timeout_ms=1000, delay_ms=10):
        start = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start) < timeout_ms:
            if self.is_ready():
                return True
            time.sleep_ms(delay_ms)
        return False

    def read_average(self, times=10):
        sum_val = 0
        for _ in range(times):
            sum_val += self.read()
            # Slight delay to prevent WDT issues if reading takes long
            # time.sleep_ms(1) 
        return sum_val / times

    def get_value(self, times=10):
        return self.read_average(times) - self.OFFSET

    def get_units(self, times=10):
        return self.get_value(times) / self.SCALE

    def tare(self, times=15):
        sum_val = self.read_average(times)
        self.set_offset(sum_val)

    def set_scale(self, scale):
        self.SCALE = scale

    def get_scale(self):
        return self.SCALE

    def set_offset(self, offset):
        self.OFFSET = offset

    def get_offset(self):
        return self.OFFSET

    def power_down(self):
        self.p_pd_sck.value(0)
        self.p_pd_sck.value(1)

    def power_up(self):
        self.p_pd_sck.value(0)

