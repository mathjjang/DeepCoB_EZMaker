# I2C 스캐너 (기압 센서 등 I2C 장치 검색용)
# 연결: SCL(D0) -> GPIO 21, SDA(D1) -> GPIO 47

from machine import Pin, SoftI2C
import time

# 핀 설정 (DeepCo v2.0 + Shield 기준)
SCL_PIN = 40
SDA_PIN = 41

def scan_i2c():
    print(f"Scanning I2C bus on SCL={SCL_PIN}, SDA={SDA_PIN}...")
    
    try:
        # SoftI2C 사용 (ESP32-S3는 Hardware I2C도 가능하지만 SoftI2C가 호환성이 좋음)
        i2c = SoftI2C(scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=100000)
        
        devices = i2c.scan()
        
        if len(devices) == 0:
            print("No I2C devices found.")
        else:
            print(f"Found {len(devices)} device(s):")
            for device in devices:
                print(f"  Decimal: {device}, Hex: {hex(device)}")
                
                # 알려진 센서 주소 힌트
                if device == 0x77 or device == 0x76:
                    print("    -> Possible BMP180 / BMP280 / BME280 Pressure Sensor")
                elif device == 0x68:
                    print("    -> Possible MPU6050 / DS3231")
                elif device == 0x27 or device == 0x3F:
                    print("    -> Possible I2C LCD")
                elif device == 0x57 or device == 0x53:
                    print("    -> Possible MAX30102 / ADXL345")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    scan_i2c()

