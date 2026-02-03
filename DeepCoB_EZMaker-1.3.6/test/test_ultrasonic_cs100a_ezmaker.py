# 이지메이커 초음파 센서 (CS100A, 1핀 방식) 테스트 코드 - 라이브러리 사용
# 연결: D2 (GPIO 48)
# 측정 범위: 2cm ~ 400cm

from machine import Pin
import time
import sys

# lib 폴더의 ultrasonic_1pin.py import
try:
    from lib.ultrasonic_1pin import Ultrasonic1Pin
except ImportError:
    print("Error: ultrasonic_1pin.py not found in lib directory.")
    sys.exit()

# ============================================================
# 초기 설정 - 여기서 핀을 설정하세요
# ============================================================

# 연결 핀 설정 (DeepCo v2.0 + Shield v2.0 기준)
# D0=21, D1=47, D2=48, D3=38, D4=39
ULTRASONIC_PIN = 48  # D2 (CS100A 연결 핀)

# ============================================================
# 테스트 함수
# ============================================================

def test_ultrasonic():
    print("=" * 50)
    print("=== CS100A Ultrasonic Sensor Test (1-Pin) ===")
    print(f"Pin: D2 (GPIO {ULTRASONIC_PIN})")
    print("=" * 50)
    
    try:
        # 센서 초기화
        sensor = Ultrasonic1Pin(pin=ULTRASONIC_PIN)
        print("Sensor initialized.")
        print("Measuring distance...")
        print("-" * 50)
        
        error_count = 0
        success_count = 0
        
        while True:
            # 단일 측정
            distance = sensor.get_distance()
            
            if distance is not None:
                success_count += 1
                error_count = 0
                
                # 거리에 따른 상태 표시
                if distance < 10:
                    status = "Very Close"
                elif distance < 50:
                    status = "Close"
                elif distance < 100:
                    status = "Medium"
                elif distance < 200:
                    status = "Far"
                else:
                    status = "Very Far"
                
                print(f"Distance: {distance:>6.1f} cm  [{status}]")
                
            else:
                error_count += 1
                print(f"Error: Out of range or sensor fault (Error count: {error_count})")
                
                # 연속 5회 실패 시 센서 리셋 시도
                if error_count >= 5:
                    print("Resetting sensor...")
                    sensor.reset()
                    time.sleep(0.5)
                    error_count = 0
            
            # 측정 간격 (최소 60ms 권장)
            time.sleep(0.1)  # 100ms
            
    except KeyboardInterrupt:
        print("\n" + "-" * 50)
        print(f"Test stopped. Success: {success_count} measurements")
    except Exception as e:
        print(f"Error: {e}")


def test_ultrasonic_average():
    """평균값 측정 모드"""
    print("=" * 50)
    print("=== CS100A Ultrasonic Sensor Test (Average) ===")
    print(f"Pin: D2 (GPIO {ULTRASONIC_PIN})")
    print("=" * 50)
    
    try:
        sensor = Ultrasonic1Pin(pin=ULTRASONIC_PIN)
        print("Sensor initialized.")
        print("Measuring distance (3-sample average)...")
        print("-" * 50)
        
        while True:
            # 3회 측정 평균
            distance = sensor.get_distance_average(samples=3)
            
            if distance is not None:
                print(f"Average Distance: {distance:>6.1f} cm")
            else:
                print("Error: Measurement failed")
            
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\nTest stopped.")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    # 기본 테스트 모드
    test_ultrasonic()
    
    # 평균값 모드를 테스트하려면 아래 주석 해제
    # test_ultrasonic_average()

