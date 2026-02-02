"""
BMP280 Barometric Pressure Sensor Library for MicroPython
==========================================================

BMP280 기압 센서 MicroPython 드라이버 라이브러리

주요 기능:
- 대기압 측정 (300~1100 hPa)
- 온도 측정 (0~65°C)
- I2C 통신
- 내부 보정 데이터 자동 로드

사용 예:
    from machine import Pin, SoftI2C
    from bmp280 import BMP280
    
    i2c = SoftI2C(scl=Pin(40), sda=Pin(41), freq=100000)
    sensor = BMP280(i2c)
    
    temp, press = sensor.read()
    print(f"Temperature: {temp:.2f} C")
    print(f"Pressure: {press/100:.2f} hPa")

연결:
- SCL (D5) -> GPIO 40
- SDA (D6) -> GPIO 41
- I2C Address: 0x76 or 0x77

참고:
- Bosch BMP280 Digital Pressure Sensor
"""

from machine import SoftI2C
import time
import ustruct

class BMP280:
    """BMP280 기압 센서 드라이버"""
    
    def __init__(self, i2c, addr=0x77):
        self.i2c = i2c
        self.addr = addr
        self.t_fine = 0
        
        # Calibration data
        self.dig_T1 = self.read_u16_le(0x88)
        self.dig_T2 = self.read_s16_le(0x8A)
        self.dig_T3 = self.read_s16_le(0x8C)
        self.dig_P1 = self.read_u16_le(0x8E)
        self.dig_P2 = self.read_s16_le(0x90)
        self.dig_P3 = self.read_s16_le(0x92)
        self.dig_P4 = self.read_s16_le(0x94)
        self.dig_P5 = self.read_s16_le(0x96)
        self.dig_P6 = self.read_s16_le(0x98)
        self.dig_P7 = self.read_s16_le(0x9A)
        self.dig_P8 = self.read_s16_le(0x9C)
        self.dig_P9 = self.read_s16_le(0x9E)
        
        # Configure
        self.write_byte(0xF4, 0x27) # Normal mode
        self.write_byte(0xF5, 0xA0) # Standby 1000ms, Filter x4

    def read_u16_le(self, reg):
        data = self.i2c.readfrom_mem(self.addr, reg, 2)
        return ustruct.unpack('<H', data)[0]

    def read_s16_le(self, reg):
        data = self.i2c.readfrom_mem(self.addr, reg, 2)
        return ustruct.unpack('<h', data)[0]

    def write_byte(self, reg, val):
        self.i2c.writeto_mem(self.addr, reg, bytes([val]))

    def read(self):
        """온도와 기압 읽기"""
        data = self.i2c.readfrom_mem(self.addr, 0xF7, 6)
        
        raw_p = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
        raw_t = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
        
        # Calculate Temperature
        var1 = (((raw_t >> 3) - (self.dig_T1 << 1)) * self.dig_T2) >> 11
        var2 = (((((raw_t >> 4) - self.dig_T1) * ((raw_t >> 4) - self.dig_T1)) >> 12) * self.dig_T3) >> 14
        self.t_fine = var1 + var2
        temp = (self.t_fine * 5 + 128) >> 8
        
        # Calculate Pressure
        var1 = (self.t_fine >> 1) - 64000
        var2 = (((var1 >> 2) * (var1 >> 2)) >> 11) * self.dig_P6
        var2 = var2 + ((var1 * self.dig_P5) << 1)
        var2 = (var2 >> 2) + (self.dig_P4 << 16)
        var1 = (((self.dig_P3 * (((var1 >> 2) * (var1 >> 2)) >> 13)) >> 3) + ((self.dig_P2 * var1) >> 1)) >> 18
        var1 = ((var1 + 32768) * self.dig_P1) >> 15
        
        if var1 == 0:
            return temp / 100.0, 0
            
        p = ((1048576 - raw_p) - (var2 >> 12)) * 3125
        if p < 0x80000000:
            p = (p << 1) // var1
        else:
            p = (p // var1) * 2
            
        var1 = (self.dig_P9 * (((p >> 3) * (p >> 3)) >> 13)) >> 12
        var2 = (((p >> 2)) * self.dig_P8) >> 13
        p = p + ((var1 + var2 + self.dig_P7) >> 4)
        
        return temp / 100.0, p / 256.0  # Temp in C, Pressure in Pa

