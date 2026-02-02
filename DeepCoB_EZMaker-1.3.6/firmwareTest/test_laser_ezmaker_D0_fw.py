"""
EZMaker 레이저 모듈 펌웨어 테스트 코드 (D0 포트 사용)

- DeepCo 보드 + EZMaker 쉴드 조합에서 레이저 모듈을 D0 포트에 연결했을 때,
  새로 추가한 LASER 캐릭터리스틱과 핀 설정 로직이 정상 동작하는지 확인하기 위한 스크립트입니다.

사용 방법 (펌웨어 단독 테스트 / REPL 기준):
1. 최신 bleIoT/bleBaseIoT를 mpy로 컴파일하여 보드의 /lib 에 배포합니다.
2. 이 파일을 보드 루트(또는 /firmwareTest)에 업로드합니다.
3. 보드가 정상 부팅되어 BLE IoT 모드(bleIoT)가 올라온 상태에서, REPL에 아래 순서로 입력합니다.
   >>> import test_laser_ezmaker_D0_fw
   >>> test_laser_ezmaker_D0_fw.main()
4. 동작:
   - 레이저 핀을 EZMaker D0 포트(GPIO 21)로 설정합니다.
   - 약 1초 간격으로 레이저를 3회 ON/OFF 하여 하드웨어 동작을 직접 확인합니다.

주의:
- Thonny에서 에디터 창의 "Run" 버튼으로 실행하면 soft reboot가 걸리면서 main/bleIoT가 다시 올라가므로,
  이 테스트 파일은 반드시 REPL에서 import 후 main()을 호출하는 방식으로만 실행합니다.
  
향후 웹/BLE 테스트:
- 펌웨어 동작이 확인된 뒤에는 웹페이지에서 BLE 명령으로 동일한 패턴을 검증합니다.
  예) LASER:PIN:21 → LASER:ON / LASER:OFF
"""

import time
import bleIoT  # 보드 /lib 에 설치된 bleIoT.mpy를 직접 사용

def configure_laser_pin_for_D0():
    """
    EZMaker 쉴드의 D0 포트는 ESP32 GPIO 21과 매핑되어 있으므로,
    LASER 모듈용 핀을 21번으로 설정합니다.
    """
    GPIO_D0 = 21  # DeepcoBoard v2.0 + EZMaker Shield v2.0 핀맵 기준
    ok = bleIoT.update_pin_config("laser", GPIO_D0)
    return ok, GPIO_D0


def simple_on_off_test(delay_sec: float = 1.0, repeat: int = 3):
    """
    내부적으로 레이저 핸들러를 직접 호출해서,
    레이저가 켜졌다 꺼지는지 눈으로 확인할 수 있는 간단한 테스트입니다.
    (BLE 명령이 아니라, 펌웨어 함수 직접 호출 방식)
    """
    from bleIoT import laser_handler  # type: ignore

    for i in range(repeat):
        print(f"[TEST] LASER:ON (step {i+1}/{repeat})")
        laser_handler(None, "LASER:ON")
        time.sleep(delay_sec)

        print(f"[TEST] LASER:OFF (step {i+1}/{repeat})")
        laser_handler(None, "LASER:OFF")
        time.sleep(delay_sec)


def main():
    print("[LASER TEST] Configure laser pin for EZMaker D0 (GPIO 21)")
    ok, gpio = configure_laser_pin_for_D0()
    if not ok:
        print(f"[LASER TEST] PIN CONFIG FAILED (GPIO {gpio})")
        return

    print(f"[LASER TEST] PIN CONFIG OK (GPIO {gpio})")
    print("[LASER TEST] Starting simple ON/OFF test...")
    simple_on_off_test(delay_sec=1.0, repeat=3)
    print("[LASER TEST] Done. 이제 BLE를 통해 LASER:ON / LASER:OFF 명령으로도 제어를 시도해보세요.")


if __name__ == "__main__":
    main()


