"""
SCD40/SCD41 CO2 Sensor Library for MicroPython
===============================================

Sensirion SCD40/SCD41 이산화탄소 센서 MicroPython 드라이버 라이브러리

주요 기능:
- CO2 농도 측정 (400~2000 ppm)
- 온도 측정 (-10~60°C)
- 습도 측정 (0~100% RH)
- I2C 통신
- CRC-8 체크섬 검증
- 주기적 측정 모드 (5초 간격)

사용 예:
    from machine import Pin, SoftI2C
    from scd40 import SCD40
    import time
    
    i2c = SoftI2C(scl=Pin(40), sda=Pin(41), freq=100000)
    sensor = SCD40(i2c)
    
    sensor.start_measurement()
    time.sleep(5)
    
    if sensor.is_data_ready():
        co2, temp, hum = sensor.read()
        print(f"CO2: {co2} ppm, Temp: {temp:.1f} C, Humidity: {hum:.1f} %")

연결:
- SCL (D5) -> GPIO 40
- SDA (D6) -> GPIO 41
- I2C Address: 0x62 (고정)

참고:
- Sensirion SCD40/SCD41 CO2 Sensor
- 첫 측정까지 약 5초 소요
"""

from machine import SoftI2C
import time

class SCD40:
    """Sensirion SCD40/SCD41 CO2 센서 드라이버"""
    
    # 명령어 정의
    CMD_START_MEASUREMENT = 0x21B1
    CMD_STOP_MEASUREMENT = 0x3F86
    CMD_READ_MEASUREMENT = 0xEC05
    CMD_DATA_READY = 0xE4B8
    CMD_SERIAL_NUMBER = 0x3682
    CMD_REINIT = 0x3646
    
    def __init__(self, i2c, addr=0x62):
        self.i2c = i2c
        self.addr = addr
        
    def _send_command(self, cmd):
        """2바이트 명령어 전송"""
        self.i2c.writeto(self.addr, bytes([cmd >> 8, cmd & 0xFF]))
        
    def _read_data(self, length):
        """데이터 읽기 (CRC 포함)"""
        return self.i2c.readfrom(self.addr, length)
    
    def _crc8(self, data):
        """CRC-8 계산 (polynomial 0x31, init 0xFF)"""
        crc = 0xFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1) ^ 0x31
                else:
                    crc <<= 1
                crc &= 0xFF
        return crc
    
    def _check_crc(self, data, crc):
        """CRC 검증"""
        return self._crc8(data) == crc
    
    def start_measurement(self):
        """주기적 측정 시작 (5초 간격)"""
        self._send_command(self.CMD_START_MEASUREMENT)
        time.sleep_ms(1)
        
    def stop_measurement(self):
        """측정 중지"""
        self._send_command(self.CMD_STOP_MEASUREMENT)
        time.sleep_ms(500)
        
    def is_data_ready(self):
        """데이터 준비 상태 확인"""
        self._send_command(self.CMD_DATA_READY)
        time.sleep_ms(1)
        data = self._read_data(3)
        ready = ((data[0] << 8) | data[1]) & 0x07FF
        return ready != 0
    
    def read(self):
        """CO2, 온도, 습도 읽기"""
        self._send_command(self.CMD_READ_MEASUREMENT)
        time.sleep_ms(1)
        
        # 9바이트 읽기: CO2(2) + CRC + Temp(2) + CRC + Humidity(2) + CRC
        data = self._read_data(9)
        
        # CRC 검증
        if not self._check_crc(data[0:2], data[2]):
            raise ValueError("CO2 CRC error")
        if not self._check_crc(data[3:5], data[5]):
            raise ValueError("Temperature CRC error")
        if not self._check_crc(data[6:8], data[8]):
            raise ValueError("Humidity CRC error")
        
        # 데이터 파싱
        co2 = (data[0] << 8) | data[1]
        
        temp_raw = (data[3] << 8) | data[4]
        temperature = -45 + 175 * (temp_raw / 65535)
        
        hum_raw = (data[6] << 8) | data[7]
        humidity = 100 * (hum_raw / 65535)
        
        return co2, temperature, humidity
    
    def get_serial_number(self):
        """센서 시리얼 번호 읽기"""
        self._send_command(self.CMD_SERIAL_NUMBER)
        time.sleep_ms(1)
        data = self._read_data(9)
        serial = (data[0] << 40) | (data[1] << 32) | (data[3] << 24) | \
                 (data[4] << 16) | (data[6] << 8) | data[7]
        return serial

