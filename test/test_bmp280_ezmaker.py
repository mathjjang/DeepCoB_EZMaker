# 이지메이커 기압센서 (BMP280) 테스트 코드 - 라이브러리 사용
# 연결: SCL=D5(GPIO 40), SDA=D6(GPIO 41)
# I2C Address: 0x77 (Detected)

from machine import Pin, SoftI2C
import time
import sys

# lib 폴더의 bmp280.py import
try:
    from bmp280 import BMP280
except ImportError:
    print("Error: bmp280.py not found in lib directory.")
    sys.exit()

# 핀 설정
SCL_PIN = 40
SDA_PIN = 41
I2C_ADDR = 0x77

def test_bmp280():
    print(f"Starting BMP280 Test on SCL={SCL_PIN}, SDA={SDA_PIN}...")
    
    try:
        i2c = SoftI2C(scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=100000)
        
        # Check connection
        if I2C_ADDR not in i2c.scan():
            print(f"Error: BMP280 not found at 0x{I2C_ADDR:02X}")
            return
            
        sensor = BMP280(i2c, I2C_ADDR)
        print("BMP280 initialized.")
        
        while True:
            temp, press = sensor.read()
            hpa = press / 100.0 # Convert Pa to hPa
            
            print(f"Temperature: {temp:.2f} C")
            print(f"Pressure: {press:.2f} Pa ({hpa:.2f} hPa)")
            print("-" * 20)
            
            time.sleep(1)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_bmp280()
