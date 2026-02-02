"""
PMS Sensor Library for MicroPython
===================================

미세먼지 센서 (PMS5003/PMS7003) MicroPython 드라이버 라이브러리

주요 기능:
- PM1.0, PM2.5, PM10 농도 측정 (μg/m³)
- 입자 개수 측정 (0.3μm ~ 10μm)
- UART 통신 (9600 baud)
- 체크섬 검증

사용 예:
    from pms_sensor import PMSSensor
    
    sensor = PMSSensor(uart_num=1, rx_pin=14, tx_pin=42)
    data = sensor.read()
    if data:
        print(f"PM2.5: {data['pm2_5']} μg/m³")

연결:
- RXD (D10) -> GPIO 14
- TXD (D11) -> GPIO 42
- VCC, GND
"""

from machine import UART, Pin
import time

class PMSSensor:
    """PMS5003/PMS7003 미세먼지 센서 드라이버"""
    
    # 데이터 프레임 상수
    FRAME_LENGTH = 32
    START_BYTE1 = 0x42
    START_BYTE2 = 0x4D
    
    def __init__(self, uart_num, rx_pin, tx_pin, baudrate=9600):
        # ESP32 표준: 생성자에서 키워드 인자로 설정
        self.uart = UART(uart_num, baudrate=baudrate, tx=Pin(tx_pin), rx=Pin(rx_pin))
        self.buffer = bytearray(self.FRAME_LENGTH)
        
    def _read_frame(self, timeout_ms=2000):
        """32바이트 데이터 프레임 읽기"""
        start_time = time.ticks_ms()
        
        # 시작 바이트 찾기
        while True:
            if time.ticks_diff(time.ticks_ms(), start_time) > timeout_ms:
                return None
                
            if self.uart.any():
                byte = self.uart.read(1)
                if byte and byte[0] == self.START_BYTE1:
                    if self.uart.any():
                        byte2 = self.uart.read(1)
                        if byte2 and byte2[0] == self.START_BYTE2:
                            break
            time.sleep_ms(10)
        
        # 나머지 30바이트 읽기
        self.buffer[0] = self.START_BYTE1
        self.buffer[1] = self.START_BYTE2
        
        remaining = self.FRAME_LENGTH - 2
        idx = 2
        
        while remaining > 0:
            if time.ticks_diff(time.ticks_ms(), start_time) > timeout_ms:
                return None
                
            if self.uart.any():
                chunk = self.uart.read(min(remaining, self.uart.any()))
                if chunk:
                    for b in chunk:
                        self.buffer[idx] = b
                        idx += 1
                        remaining -= 1
            time.sleep_ms(5)
        
        return self.buffer
    
    def _verify_checksum(self, data):
        """체크섬 검증"""
        if len(data) < self.FRAME_LENGTH:
            return False
        
        # 체크섬: 앞 30바이트의 합
        calc_sum = sum(data[:30])
        recv_sum = (data[30] << 8) | data[31]
        
        return calc_sum == recv_sum
    
    def read(self):
        """미세먼지 데이터 읽기"""
        frame = self._read_frame()
        
        if frame is None:
            return None
            
        if not self._verify_checksum(frame):
            return None
        
        # 데이터 파싱 (Standard Particle - 일반 환경)
        # CF=1 표준 입자 (인덱스 4-9)
        pm1_0_cf = (frame[4] << 8) | frame[5]
        pm2_5_cf = (frame[6] << 8) | frame[7]
        pm10_cf = (frame[8] << 8) | frame[9]
        
        # 대기 환경 값 (인덱스 10-15)
        pm1_0 = (frame[10] << 8) | frame[11]
        pm2_5 = (frame[12] << 8) | frame[13]
        pm10 = (frame[14] << 8) | frame[15]
        
        # 입자 개수 (0.1L당)
        particles_03 = (frame[16] << 8) | frame[17]  # >0.3μm
        particles_05 = (frame[18] << 8) | frame[19]  # >0.5μm
        particles_10 = (frame[20] << 8) | frame[21]  # >1.0μm
        particles_25 = (frame[22] << 8) | frame[23]  # >2.5μm
        particles_50 = (frame[24] << 8) | frame[25]  # >5.0μm
        particles_100 = (frame[26] << 8) | frame[27] # >10μm
        
        return {
            'pm1_0': pm1_0,
            'pm2_5': pm2_5,
            'pm10': pm10,
            'pm1_0_cf': pm1_0_cf,
            'pm2_5_cf': pm2_5_cf,
            'pm10_cf': pm10_cf,
            'particles': {
                '>0.3μm': particles_03,
                '>0.5μm': particles_05,
                '>1.0μm': particles_10,
                '>2.5μm': particles_25,
                '>5.0μm': particles_50,
                '>10μm': particles_100
            }
        }

