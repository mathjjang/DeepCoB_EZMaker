# 이지메이커 미세먼지 센서 (PMS5003/PMS7003) 테스트 코드 - 라이브러리 사용
# 연결: RXD=D10(GPIO 14), TXD=D11(GPIO 42)
# 측정: PM1.0, PM2.5, PM10 (μg/m³)

import time
import sys

# lib 폴더의 pms_sensor.py import
try:
    from lib import pms_sensor
except ImportError:
    print("Error: pms_sensor.py not found in lib directory.")
    sys.exit()

# ============================================================
# 초기 설정 - 여기서 핀을 설정하세요
# ============================================================

# UART 핀 설정 (DeepCo v2.0 + Shield v2.0 기준)
# RXD(D10)=14, TXD(D11)=42
UART_NUM = 1       # UART 번호 (ESP32: 1 또는 2)
RX_PIN = 14        # 센서 TX -> 보드 RX
TX_PIN = 42        # 센서 RX -> 보드 TX (사용 안함)
BAUD_RATE = 9600   # PMS 센서 기본 속도

def get_air_quality(pm25):
    """PM2.5 기준 공기질 등급"""
    if pm25 <= 15:
        return "좋음 (Good)"
    elif pm25 <= 35:
        return "보통 (Moderate)"
    elif pm25 <= 75:
        return "나쁨 (Unhealthy)"
    else:
        return "매우나쁨 (Very Unhealthy)"


# ============================================================
# 테스트 함수
# ============================================================

def test_dust_sensor():
    print("=" * 45)
    print("=== Dust Sensor (PMS5003/PMS7003) Test ===")
    print(f"UART{UART_NUM}: RX=GPIO {RX_PIN}, TX=GPIO {TX_PIN}")
    print(f"Baud Rate: {BAUD_RATE}")
    print("=" * 45)
    
    try:
        # 센서 초기화
        sensor = pms_sensor.PMSSensor(UART_NUM, RX_PIN, TX_PIN, BAUD_RATE)
        print("Sensor initialized.")
        print("Waiting for data (sensor needs ~30s warm-up)...")
        print("-" * 45)
        
        read_count = 0
        error_count = 0
        
        while True:
            data = sensor.read()
            
            if data:
                read_count += 1
                quality = get_air_quality(data['pm2_5'])
                
                print(f"\n[Reading #{read_count}]")
                print(f"  PM1.0:  {data['pm1_0']:>4} μg/m³")
                print(f"  PM2.5:  {data['pm2_5']:>4} μg/m³  -> {quality}")
                print(f"  PM10:   {data['pm10']:>4} μg/m³")
                print(f"  Particles (per 0.1L):")
                print(f"    >0.3μm: {data['particles']['>0.3μm']}")
                print(f"    >2.5μm: {data['particles']['>2.5μm']}")
                print("-" * 45)
                error_count = 0
            else:
                error_count += 1
                if error_count > 5:
                    print("Waiting for sensor data...")
                    error_count = 0
                    
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nTest stopped.")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_dust_sensor()

