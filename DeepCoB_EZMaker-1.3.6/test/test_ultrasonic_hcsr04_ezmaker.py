# 이지메이커 초음파 센서 (HC-SR04/CS100A, 2핀 방식) 테스트 코드
# 사용 드라이버: source/lib/HC1SR04.py
# 연결: TRIG=GPIO 40, ECHO=GPIO 41
#
# DeepCo v2.0 + Shield v2.0 기준
#  - TRIG  : GPIO 40 (예: D5)
#  - ECHO  : GPIO 41 (예: D6)
#  - 전원  : +5V 또는 +3.3V (모듈/보드 사양에 맞게)
#  - GND   : 공통 GND

import time
import sys

try:
    from HC1SR04 import HCSR04
except ImportError:
    print("Error: HC1SR04.py not found in source/lib directory.")
    sys.exit()


# ============================================================
# 핀 설정
# ============================================================

TRIG_PIN = 40  # GPIO 40
ECHO_PIN = 41  # GPIO 41


# ============================================================
# 테스트 함수
# ============================================================

def test_ultrasonic_2pin():
    print("=" * 60)
    print("=== HC-SR04 / CS100A Ultrasonic Sensor Test (2-Pin) ===")
    print(f"TRIG: GPIO {TRIG_PIN}, ECHO: GPIO {ECHO_PIN}")
    print("=" * 60)

    try:
        sensor = HCSR04(trigger_pin=TRIG_PIN, echo_pin=ECHO_PIN)
        print("Sensor initialized.")
        print("Measuring distance...")
        print("-" * 60)

        success = 0
        fail = 0

        while True:
            try:
                dist = sensor.distance_cm()
                print(f"Distance: {dist:7.2f} cm")
                success += 1
                fail = 0
            except OSError as e:
                print(f"Error: {e}")
                fail += 1

            # CS100A 데이터시트 기준 최대 ECHO 폭 ~33ms → 주기 50ms 이상 권장
            time.sleep(0.1)  # 100ms 간격

    except KeyboardInterrupt:
        print("\nTest stopped.")
        print(f"Total successful measurements: {success}")
    except Exception as e:
        print(f"Fatal error: {e}")


if __name__ == "__main__":
    test_ultrasonic_2pin()


