"""
ICM20948 9-Axis Sensor Library for MicroPython
===============================================

ICM20948 9축 모션 센서 (가속도+자이로+지자기) MicroPython 드라이버 라이브러리

주요 기능:
- 3축 가속도 측정 (±2g, ±4g, ±8g, ±16g)
- 3축 자이로 측정 (±250, ±500, ±1000, ±2000 dps)
- 3축 지자기 측정 (AK09916, 별도 구현 필요)
- 온도 측정
- Roll, Pitch 각도 계산
- Bank 전환 시스템 (Register Bank 0~3)

사용 예:
    from machine import Pin, SoftI2C
    from icm20948 import ICM20948
    
    i2c = SoftI2C(scl=Pin(40), sda=Pin(41), freq=100000)
    sensor = ICM20948(i2c)
    
    data = sensor.read_accel_gyro()
    print(f"Accel X: {data['accel']['x']:.2f} g")
    
    rpy = sensor.calculate_rpy(data['accel'])
    print(f"Roll: {rpy['roll']:.1f} deg")

연결:
- SCL (D5) -> GPIO 40
- SDA (D6) -> GPIO 41
- I2C Address: 0x68 (AD0=Low) or 0x69 (AD0=High)

참고:
- TDK InvenSense ICM20948 9-Axis Sensor
"""

from machine import SoftI2C
import time
import math

class ICM20948:
    """ICM20948 9-Axis Motion Tracking Device"""
    
    # Register Map
    REG_BANK_SEL = 0x7F
    
    # User Bank 0
    REG_WHO_AM_I = 0x00
    REG_PWR_MGMT_1 = 0x06
    REG_PWR_MGMT_2 = 0x07
    REG_INT_PIN_CFG = 0x0F
    
    REG_ACCEL_XOUT_H = 0x2D
    REG_GYRO_XOUT_H = 0x33
    REG_TEMP_OUT_H = 0x39
    
    # User Bank 2
    REG_GYRO_SMPLRT_DIV = 0x00
    REG_GYRO_CONFIG_1 = 0x01
    REG_ACCEL_SMPLRT_DIV_1 = 0x10
    REG_ACCEL_SMPLRT_DIV_2 = 0x11
    REG_ACCEL_CONFIG = 0x14
    
    # Magnetometer (AK09916) I2C Address
    MAG_I2C_ADDR = 0x0C
    
    def __init__(self, i2c, addr=0x68):
        self.i2c = i2c
        self.addr = addr
        self._bank = 0
        
        self.reset()
        time.sleep(0.1)
        self.wake()
        
        # Check connection
        who_am_i = self.read_register(self.REG_WHO_AM_I)
        if who_am_i != 0xEA:
            print(f"Warning: ICM20948 ID mismatch. Expected 0xEA, got 0x{who_am_i:02X}")
        else:
            print(f"ICM20948 found (ID: 0x{who_am_i:02X})")
            
        self.config()
        
    def select_bank(self, bank):
        if self._bank != bank:
            self.i2c.writeto_mem(self.addr, self.REG_BANK_SEL, bytes([bank << 4]))
            self._bank = bank

    def read_register(self, reg, bank=0):
        self.select_bank(bank)
        return self.i2c.readfrom_mem(self.addr, reg, 1)[0]

    def write_register(self, reg, value, bank=0):
        self.select_bank(bank)
        self.i2c.writeto_mem(self.addr, reg, bytes([value]))

    def reset(self):
        self.write_register(self.REG_PWR_MGMT_1, 0x80)
        time.sleep(0.1)
        
    def wake(self):
        self.write_register(self.REG_PWR_MGMT_1, 0x01)
        
    def config(self):
        # Configure Accelerometer (±2g)
        self.write_register(self.REG_ACCEL_CONFIG, 0x01, bank=2)
        
        # Configure Gyroscope (±250dps)
        self.write_register(self.REG_GYRO_CONFIG_1, 0x01, bank=2)
        
        # Enable bypass mode for Magnetometer access
        self.write_register(self.REG_INT_PIN_CFG, 0x02, bank=0)

    def read_accel_gyro(self):
        self.select_bank(0)
        data = self.i2c.readfrom_mem(self.addr, self.REG_ACCEL_XOUT_H, 14)
        
        ax = self._bytes_to_int(data[0], data[1])
        ay = self._bytes_to_int(data[2], data[3])
        az = self._bytes_to_int(data[4], data[5])
        
        gx = self._bytes_to_int(data[6], data[7])
        gy = self._bytes_to_int(data[8], data[9])
        gz = self._bytes_to_int(data[10], data[11])
        
        temp = self._bytes_to_int(data[12], data[13])
        
        # Convert to units
        accel_scale = 16384.0  # ±2g
        gyro_scale = 131.0     # ±250dps
        temp_c = (temp / 333.57) + 21.0
        
        return {
            'accel': {'x': ax/accel_scale, 'y': ay/accel_scale, 'z': az/accel_scale},
            'gyro': {'x': gx/gyro_scale, 'y': gy/gyro_scale, 'z': gz/gyro_scale},
            'temp': temp_c
        }

    def calculate_rpy(self, accel_data):
        """Calculate Roll and Pitch from Accelerometer data."""
        ax = accel_data['x']
        ay = accel_data['y']
        az = accel_data['z']
        
        roll = math.atan2(ay, az) * 180.0 / math.pi
        pitch = math.atan2(-ax, math.sqrt(ay*ay + az*az)) * 180.0 / math.pi
        yaw = 0.0  # Requires Magnetometer
        
        return {'roll': roll, 'pitch': pitch, 'yaw': yaw}
        
    def _bytes_to_int(self, msb, lsb):
        val = (msb << 8) | lsb
        if val >= 0x8000:
            val -= 0x10000
        return val

