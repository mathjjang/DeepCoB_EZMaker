# 이지메이커 이산화탄소 센서 (SCD40/SCD41) 테스트 코드 - 라이브러리 사용
# 연결: SCL=D5(GPIO 40), SDA=D6(GPIO 41)
# I2C Address: 0x62

from machine import Pin, SoftI2C
import time
import sys

# lib 폴더의 scd40.py import
try:
    from lib.scd40 import SCD40
except ImportError:
    print("Error: scd40.py not found in lib directory.")
    sys.exit()

# 핀 설정
SCL_PIN = 40
SDA_PIN = 41
I2C_ADDR = 0x62

def test_co2_sensor():
    print(f"Starting SCD40 CO2 Sensor Test on SCL={SCL_PIN}, SDA={SDA_PIN}...")
    
    try:
        i2c = SoftI2C(scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=100000)
        
        # 연결 확인
        if I2C_ADDR not in i2c.scan():
            print(f"Error: SCD40 not found at 0x{I2C_ADDR:02X}")
            return
            
        sensor = SCD40(i2c, I2C_ADDR)
        print("SCD40 detected.")
        
        # 시리얼 번호 읽기 (선택)
        try:
            serial = sensor.get_serial_number()
            print(f"Serial Number: 0x{serial:012X}")
        except:
            pass
        
        # 측정 시작
        sensor.start_measurement()
        print("Measurement started. Waiting for data (~5 seconds)...")
        print("-" * 40)
        
        time.sleep(5)
        
        read_count = 0
        
        while True:
            if sensor.is_data_ready():
                co2, temp, hum = sensor.read()
                read_count += 1
                
                # CO2 레벨 판정
                if co2 < 600:
                    quality = "Excellent"
                elif co2 < 1000:
                    quality = "Good"
                elif co2 < 1500:
                    quality = "Fair"
                else:
                    quality = "Poor"
                
                print(f"[Reading #{read_count}]")
                print(f"  CO2:         {co2:>4} ppm  ({quality})")
                print(f"  Temperature: {temp:>5.1f} C")
                print(f"  Humidity:    {hum:>5.1f} %RH")
                print("-" * 40)
            else:
                print("Waiting for data...")
                
            time.sleep(5)  # SCD40은 5초 간격으로 측정
            
    except KeyboardInterrupt:
        print("\nStopping...")
        try:
            sensor.stop_measurement()
        except:
            pass
        print("Test stopped.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_co2_sensor()
