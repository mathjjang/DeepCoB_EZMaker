"""
EZMaker 터치 센서(TTP223) 펌웨어 테스트 코드 (D0 포트 사용)

- DeepCo 보드 + EZMaker 쉴드 조합에서 터치 센서(TTP223)를
  EZMaker D0 포트(GPIO 21)에 연결했을 때,
  bleIoT 의 TOUCH 핀 설정 및 실제 입력 값이 정상 동작하는지 확인하기 위한 스크립트입니다.

사용 방법 (펌웨어 단독 테스트 / REPL 기준):
1. 최신 bleIoT/bleBaseIoT 를 mpy 로 컴파일하여 보드의 /lib 에 배포합니다.
2. 이 파일을 보드 루트(또는 /firmwareTest)에 업로드합니다.
3. 보드가 정상 부팅되어 BLE IoT 모드(bleIoT)가 올라온 상태에서, REPL 에 아래 순서로 입력합니다.
   >>> import test_touch_ttp223_ezmaker_fw
   >>> test_touch_ttp223_ezmaker_fw.main()
4. 동작:
   - 터치 센서 핀을 EZMaker D0 포트(GPIO 21)로 설정합니다.
   - 일정 시간 동안 주기적으로 핀 값을 읽어, 터치 여부(0/1)를 콘솔에 출력합니다.
   - 손가락으로 센서를 눌렀을 때 값이 변하는지 직접 확인할 수 있습니다.

주의:
- Thonny 에디터 창의 "Run" 버튼으로 실행하면 soft reboot 가 걸리면서 main/bleIoT 가 다시 올라가므로,
  이 테스트 파일은 반드시 REPL 에서 import 후 main() 을 호출하는 방식으로만 실행합니다.
"""

import time
import bleIoT  # 보드 /lib 에 설치된 bleIoT.mpy를 직접 사용


def configure_touch_pin_for_D0():
    """
    EZMaker 쉴드의 D0 포트는 ESP32 GPIO 21과 매핑되어 있으므로,
    터치 센서용 핀을 21번으로 설정합니다.
    """
    GPIO_D0 = 21  # DeepcoBoard v2.0 + EZMaker Shield v2.0 핀맵 기준 (레이저와 동일)
    ok = bleIoT.update_pin_config("touch", GPIO_D0)
    return ok, GPIO_D0


def read_touch_loop(duration_sec: float = 10.0, interval_sec: float = 0.5):
    """
    일정 시간 동안 주기적으로 터치 핀 값을 읽어 출력합니다.

    - duration_sec: 총 테스트 시간 (초)
    - interval_sec: 측정 간격 (초)
    """
    # bleIoT 모듈의 전역 touch_pin 을 직접 사용
    touch_pin = getattr(bleIoT, "touch_pin", None)
    if touch_pin is None:
        print("[TOUCH TEST] touch_pin 이 None 입니다. PIN 설정이 제대로 되었는지 확인하세요.")
        return

    print("[TOUCH TEST] 터치 센서를 손가락으로 눌렀다 떼면서 값 변화를 확인하세요.")

    end_time = time.time() + duration_sec
    count = 0

    while time.time() < end_time:
        try:
            raw = touch_pin.value()
            touched = (raw == 1)
            count += 1
            print(f"[TOUCH TEST] #{count:02d}  raw={raw}  ->  {'TOUCHED' if touched else 'NOT TOUCHED'}")
        except Exception as e:
            print(f"[TOUCH TEST] 읽기 오류: {e}")
            break

        time.sleep(interval_sec)


def main():
    print("[TOUCH TEST] EZMaker 터치 센서(TTP223) 펌웨어 테스트 시작")
    print("[TOUCH TEST] EZMaker D0 (GPIO 21) 를 터치 센서 입력으로 사용합니다.")

    ok, gpio = configure_touch_pin_for_D0()
    if not ok:
        print(f"[TOUCH TEST] PIN CONFIG FAILED (GPIO {gpio}) - 배선 또는 센서 전원을 확인하세요.")
        return

    print(f"[TOUCH TEST] PIN CONFIG OK (GPIO {gpio})")
    print("[TOUCH TEST] 10초 동안 0.5초 간격으로 터치 상태를 읽어옵니다...")

    read_touch_loop(duration_sec=10.0, interval_sec=0.5)

    print("[TOUCH TEST] Done. 이제 웹 테스트 페이지(test_touch.html)에서도 동일한 동작을 확인해 보세요.")


if __name__ == "__main__":
    main()


