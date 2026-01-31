# 이지메이커 초음파 센서 (HC-SR04, 1핀 변형) 테스트 코드
# 연결: D2 (GPIO 48) 기준 예제
#
# 주의: 실제 보드/쉴드에서 HC-SR04의 Trig/Echo가 어떻게 1핀으로 합쳐지는지
#       하드웨어 회로에 따라 동작 여부가 달라질 수 있습니다.

from machine import Pin
import time
import sys

# lib 폴더의 HC1SR04_1pin.py import
try:
    from lib.HC1SR04_1pin import HCSR04
except ImportError:
    print("Error: HC1SR04_1pin.py not found in lib directory.")
    sys.exit()

# ============================================================
# 핀 설정
# ============================================================

# DeepCo v2.0 + Shield v2.0 기준
# D0=21, D1=47, D2=48, D3=38, D4=39
ULTRASONIC_PIN = 48  # 예: D2


# ============================================================
# 테스트 함수
# ============================================================

def test_ultrasonic_hcsr04_1pin():
    print("=" * 60)
    print("=== HC-SR04 Ultrasonic Sensor Test (1-Pin Variant) ===")
    print(f"Pin: GPIO {ULTRASONIC_PIN}")
    print("=" * 60)

    try:
        sensor = HCSR04(data_pin=ULTRASONIC_PIN)
        print("Sensor initialized.")
        print("Measuring distance...")
        print("-" * 60)

        success = 0
        fail = 0

        while True:
            try:
                dist = sensor.distance_cm()
                print(f"Distance: {dist:6.2f} cm")
                success += 1
                fail = 0
            except OSError as e:
                print(f"Error: {e}")
                fail += 1

                # 연속 실패 시 센서 라인 LOW로 리셋 시도
                if fail >= 5:
                    print("Resetting line (force LOW)...")
                    p = Pin(ULTRASONIC_PIN, Pin.OUT)
                    p.value(0)
                    time.sleep_ms(100)
                    fail = 0

            # HC-SR04는 최소 약 60ms 간격 권장
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nTest stopped.")
    except Exception as e:
        print(f"Fatal error: {e}")


if __name__ == "__main__":
    test_ultrasonic_hcsr04_1pin()


