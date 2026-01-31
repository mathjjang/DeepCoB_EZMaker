# 이지메이커 수중온도센서 (DS18B20) 테스트 코드 - 라이브러리 사용
# 연결: D0(GPIO 21) - 1-Wire 프로토콜
# 온도 범위: -55°C ~ +125°C

from machine import Pin
import time
import sys

# lib 폴더의 ds18b20_sensor.py import
try:
    from lib.ds18b20_sensor import WaterTempSensor
except ImportError:
    print("Error: ds18b20_sensor.py not found in lib directory.")
    sys.exit()

# ============================================================
# 초기 설정 - 여기서 핀을 설정하세요
# ============================================================

# 연결 핀 설정 (DeepCo v2.0 + Shield v2.0 기준)
# D0=21, D1=47, D2=48, D3=38, D4=39
DATA_PIN = 21


# ============================================================
# 테스트 함수
# ============================================================

def test_water_temp_sensor():
    print("=" * 45)
    print("=== DS18B20 Water Temperature Sensor Test ===")
    print(f"Data Pin: GPIO {DATA_PIN}")
    print("=" * 45)
    
    try:
        # 센서 초기화
        sensor = WaterTempSensor(DATA_PIN)
        
        # 센서 스캔
        count = sensor.get_sensor_count()
        if count == 0:
            print("Error: No DS18B20 sensor detected.")
            print("Check wiring and power supply.")
            return
            
        print(f"Detected {count} DS18B20 sensor(s).")
        
        # 센서 ID 출력
        ids = sensor.get_sensor_ids()
        for i, sensor_id in enumerate(ids):
            print(f"  Sensor {i}: {sensor_id}")
        
        print("-" * 45)
        print("Reading temperatures...")
        print("-" * 45)
        
        while True:
            if count == 1:
                # 단일 센서
                temp = sensor.read_temp(0)
                if temp is not None:
                    print(f"Temperature: {temp:.2f} C")
                else:
                    print("Error reading temperature.")
            else:
                # 다중 센서
                temps = sensor.read_all_temps()
                for i, temp in enumerate(temps):
                    if temp is not None:
                        print(f"Sensor {i}: {temp:.2f} C")
                    else:
                        print(f"Sensor {i}: Read Error")
            
            print("-" * 45)
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\nTest stopped.")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_water_temp_sensor()
