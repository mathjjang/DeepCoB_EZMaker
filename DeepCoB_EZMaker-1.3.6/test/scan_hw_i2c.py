# 하드웨어 I2C 스캐너
# 연결: SCL(D0) -> GPIO 21, SDA(D1) -> GPIO 47

from machine import Pin, I2C
import time

# 핀 설정
SCL_PIN = 40
SDA_PIN = 41

def scan_hw_i2c():
    print(f"Scanning Hardware I2C bus on SCL={SCL_PIN}, SDA={SDA_PIN}...")
    
    # 하드웨어 I2C는 ID(0 또는 1)를 지정해야 함
    # ESP32-S3의 I2C0 또는 I2C1 사용
    
    try:
        # ID 0번으로 시도
        print("Trying I2C(0)...")
        i2c = I2C(0, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=100000)
        devices = i2c.scan()
        
        if len(devices) > 0:
            print(f"Found {len(devices)} device(s) on I2C(0):")
            for device in devices:
                print(f"  Decimal: {device}, Hex: {hex(device)}")
            return
        else:
            print("No devices found on I2C(0).")
            
        # ID 1번으로 시도 (혹시 모르니)
        print("Trying I2C(1)...")
        try:
            i2c = I2C(1, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=100000)
            devices = i2c.scan()
            if len(devices) > 0:
                print(f"Found {len(devices)} device(s) on I2C(1):")
                for device in devices:
                    print(f"  Decimal: {device}, Hex: {hex(device)}")
            else:
                print("No devices found on I2C(1).")
        except Exception as e:
            print(f"I2C(1) Init Error: {e}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    scan_hw_i2c()

