"""
EZMaker 인체감지 센서(HUMAN) 펌웨어 테스트 코드

- DeepCo 보드 + EZMaker 쉴드 조합에서, 인체감지 센서 모듈을
  EZMaker D포트(D0~D4) 중 하나에 연결했을 때
  bleIoT 의 HUMAN 핀 설정 및 상태 값이 정상 동작하는지 확인하기 위한 스크립트입니다.

사용 방법 (펌웨어 단독 테스트 / REPL 기준):
1. 최신 bleIoT/bleBaseIoT/human_sensor 를 mpy 로 컴파일하여 보드의 /lib 에 배포합니다.
2. 이 파일을 보드 루트(또는 /firmwareTest)에 업로드합니다.
3. 보드가 정상 부팅되어 BLE IoT 모드(bleIoT)가 올라온 상태에서, REPL 에 아래 순서로 입력합니다.
   >>> import test_human_ezmaker_fw
   >>> test_human_ezmaker_fw.main()
4. 동작:
   - HUMAN 센서 핀을 기본값으로는 EZMaker D0 포트에 대응하는 GPIO 로 설정합니다.
   - bleIoT 내부의 human_sensor(HumanSensor 인스턴스)를 통해
     0 또는 1 의 디지털 값을 여러 번 읽어 콘솔에 출력합니다.
   - 필요하면 HUMAN:STATUS 명령을 직접 호출해, BLE 경로로도 값이 전송되는지 확인할 수 있습니다.

주의:
- Thonny 에디터 창의 "Run" 버튼으로 실행하면 soft reboot 가 걸리면서 main/bleIoT 가 다시 올라가므로,
  이 테스트 파일은 반드시 REPL 에서 import 후 main() 을 호출하는 방식으로만 실행합니다.
"""

import time
import bleIoT  # 보드 /lib 에 설치된 bleIoT.mpy 를 직접 사용


# EZMaker HUMAN 센서 기본 포트 (D0) 에 대응하는 GPIO 번호
# - 현재 레이저 테스트 기준으로 D0 → GPIO 21 을 사용 중
DEFAULT_HUMAN_PIN = 21


def configure_human_pin_for_ezmaker(pin: int = DEFAULT_HUMAN_PIN):
    """
    EZMaker 쉴드의 D포트(D0~D4)에 맞춰 인체감지 센서 핀을 설정합니다.

    - update_pin_config('human', PIN) 을 호출하면,
      bleIoT 내부에서 HumanSensor 초기화를 수행하고
      human_sensor 전역 객체를 준비합니다.
    """
    ok = bleIoT.update_pin_config("human", pin)
    return ok, pin


def read_once_via_human_sensor():
    """
    bleIoT.human_sensor (HumanSensor 인스턴스)를 직접 사용해서
    현재 감지 상태(0 또는 1)를 한 번 읽어 출력합니다.
    """
    sensor = getattr(bleIoT, "human_sensor", None)
    if sensor is None:
        print("[HUMAN TEST] human_sensor 가 None 입니다. 핀 설정 또는 센서 초기화를 확인하세요.")
        return

    try:
        status = sensor.get_status()
        value = int(status.get("value", 0))

        # 0: 감지 없음, 1: 인체(움직임) 감지
        state_str = "DETECTED" if value == 1 else "NO MOTION"
        print(f"[HUMAN TEST] value={value} ({state_str})")
    except Exception as e:
        print(f"[HUMAN TEST] 센서 읽기 오류: {e}")


def send_status_via_handler(repeat: int = 3, delay_sec: float = 0.5):
    """
    HUMAN:STATUS 명령을 bleIoT.human_handler 를 통해 반복 호출합니다.

    - 이 함수는 실제 BLE 경로(EZ_HUMAN_CHARACTERISTIC) 로 전송되는
      문자열 포맷(HUMAN:0 또는 HUMAN:1) 이 정상인지 확인할 때 사용합니다.
    - 값 자체는 BLE 알림으로 나가기 때문에, 웹/PC 쪽에서 통합 테스트할 때 함께 활용합니다.
    """
    try:
        from bleIoT import human_handler  # type: ignore
    except ImportError:
        print("[HUMAN TEST] human_handler 를 가져올 수 없습니다. bleIoT 버전을 확인하세요.")
        return

    for i in range(repeat):
        print(f"[HUMAN TEST] HUMAN:STATUS 요청 전송 ({i + 1}/{repeat})")
        try:
            human_handler(None, "HUMAN:STATUS")
        except Exception as e:
            print(f"[HUMAN TEST] HUMAN:STATUS 처리 중 오류: {e}")
        time.sleep(delay_sec)


def main(pin: int = DEFAULT_HUMAN_PIN):
    print("===============================================")
    print("=== EZMaker 인체감지 센서(HUMAN) 펌웨어 테스트 ===")
    print("===============================================")
    print(f"[HUMAN TEST] EZMaker D0 포트를 인체감지 센서 입력으로 사용합니다. (PIN={pin})")

    ok, used_pin = configure_human_pin_for_ezmaker(pin)
    if not ok:
        print(f"[HUMAN TEST] PIN CONFIG FAILED (PIN={used_pin}) - 배선 또는 센서 전원을 확인하세요.")
        return

    print(f"[HUMAN TEST] PIN CONFIG OK (PIN={used_pin})")
    print("[HUMAN TEST] 인체감지 센서 값을 10회 정도 읽어 봅니다...")

    for i in range(10):
        print(f"[HUMAN TEST] 측정 {i + 1}/10")
        read_once_via_human_sensor()
        time.sleep(1.0)

    print(
        "[HUMAN TEST] 이제 필요한 경우 HUMAN:STATUS 명령도 함께 테스트할 수 있습니다."
    )
    print("[HUMAN TEST] (원하면 send_status_via_handler() 를 REPL 에서 직접 호출하세요.)")


if __name__ == "__main__":
    main()


