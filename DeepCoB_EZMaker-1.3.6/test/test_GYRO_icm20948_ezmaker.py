# 이지메이커 자이로센서 (ICM20948) 테스트 코드 - 라이브러리 사용
# 연결: SCL=D5(GPIO 40), SDA=D6(GPIO 41)
# I2C Address: 0x68 (AD0=Low) or 0x69 (AD0=High)

from machine import Pin, SoftI2C
import time
import sys

# lib 폴더의 icm20948.py import
try:
    from lib.icm20948 import ICM20948
except ImportError:
    print("Error: icm20948.py not found in lib directory.")
    sys.exit()

# 핀 설정
SCL_PIN = 40
SDA_PIN = 41
I2C_ADDR = 0x68  # 기본 주소 (0x69일 수도 있음)

def test_icm20948():
    print(f"Starting ICM20948 Test on SCL={SCL_PIN}, SDA={SDA_PIN}...")
    
    try:
        i2c = SoftI2C(scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=100000)
        
        # Scan I2C
        scan_result = i2c.scan()
        print(f"I2C Scan: {[hex(x) for x in scan_result]}")
        
        if I2C_ADDR not in scan_result:
            print(f"Error: ICM20948 not found at 0x{I2C_ADDR:02X}")
            if 0x69 in scan_result:
                print("Found device at 0x69. Trying that address...")
                I2C_ADDR = 0x69
            else:
                return
        
        # Initialize sensor
        sensor = ICM20948(i2c, I2C_ADDR)
        print("Sensor initialized.")
        print("-" * 40)
        
        while True:
            data = sensor.read_accel_gyro()
            rpy = sensor.calculate_rpy(data['accel'])
            
            print(f"Accel (g): X={data['accel']['x']:>6.2f}, Y={data['accel']['y']:>6.2f}, Z={data['accel']['z']:>6.2f}")
            print(f"Gyro (dps): X={data['gyro']['x']:>7.2f}, Y={data['gyro']['y']:>7.2f}, Z={data['gyro']['z']:>7.2f}")
            print(f"Roll: {rpy['roll']:>6.1f}°, Pitch: {rpy['pitch']:>6.1f}°")
            print(f"Temp: {data['temp']:.1f} C")
            print("-" * 40)
            
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\nTest stopped.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_icm20948()
