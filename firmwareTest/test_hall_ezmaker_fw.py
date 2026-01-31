"""
EZMaker 자기장(Hall) 센서 펌웨어 테스트 코드 (EZMaker A0 포트 사용)

- DeepCo 보드 + EZMaker 쉴드 조합에서 Hall 자기장 센서를
  EZMaker A0 포트(기본 ADC 포트)에 연결했을 때,
  bleIoT 의 HALL 핀 설정 및 상태 값이 정상 동작하는지 확인하기 위한 스크립트입니다.

사용 방법 (펌웨어 단독 테스트 / REPL 기준):
1. 최신 bleIoT/bleBaseIoT/hall_sensor 를 mpy 로 컴파일하여 보드의 /lib 에 배포합니다.
2. 이 파일을 보드 루트(또는 /firmwareTest)에 업로드합니다.
3. 보드가 정상 부팅되어 BLE IoT 모드(bleIoT)가 올라온 상태에서, REPL 에 아래 순서로 입력합니다.
   >>> import test_hall_ezmaker_fw
   >>> test_hall_ezmaker_fw.main()
4. 동작:
   - Hall 센서 핀을 EZMaker A0 포트에 대응하는 GPIO 로 설정합니다.
   - bleIoT 내부의 hall_sensor(HallSensor 인스턴스)를 통해
     아날로그 값(0~1023), N/S 세기(-512~+512), 자속 밀도(0~512)를 여러 번 읽어 콘솔에 출력합니다.
   - 필요하면 HALL:STATUS 명령을 직접 호출해, BLE 경로로도 값이 전송되는지 확인할 수 있습니다.

주의:
- Thonny 에디터 창의 "Run" 버튼으로 실행하면 soft reboot 가 걸리면서 main/bleIoT 가 다시 올라가므로,
  이 테스트 파일은 반드시 REPL 에서 import 후 main() 을 호출하는 방식으로만 실행합니다.
"""

import time
import bleIoT  # 보드 /lib 에 설치된 bleIoT.mpy 를 직접 사용


# EZMaker 자기장 센서 기본 포트 (A0) 에 대응하는 GPIO 번호
# - 현재 테스트 환경에서 A0 → GPIO 2 를 사용 중
DEFAULT_HALL_ADC_PIN = 2


def configure_hall_pin_for_ezmaker():
    """
    EZMaker 쉴드의 A0 포트에 맞춰 Hall 센서 핀을 설정합니다.

    - update_pin_config('hall', ADC_PIN) 을 호출하면,
      bleIoT 내부에서 HallSensor 초기화를 수행하고
      hall_sensor 전역 객체를 준비합니다.
    """
    ok = bleIoT.update_pin_config("hall", DEFAULT_HALL_ADC_PIN)
    return ok, DEFAULT_HALL_ADC_PIN


def read_once_via_hall_sensor():
    """
    bleIoT.hall_sensor (HallSensor 인스턴스)를 직접 사용해서
    아날로그 값 / N/S 세기 / 자속 밀도 값을 한 번 읽어 출력합니다.
    """
    sensor = getattr(bleIoT, "hall_sensor", None)
    if sensor is None:
        print("[HALL TEST] hall_sensor 가 None 입니다. 핀 설정 또는 센서 초기화를 확인하세요.")
        return

    try:
        status = sensor.get_status()
        raw = status.get("raw")
        strength = status.get("strength")
        density = status.get("density")
        voltage = status.get("voltage")

        print(
            "[HALL TEST] "
            f"Raw(0-1023): {raw:4d} | "
            f"Strength(-512~+512): {strength:5d} | "
            f"Density(0~512): {density:3d} | "
            f"Voltage(3.3V): {voltage:4.2f} V"
        )
    except Exception as e:
        print(f"[HALL TEST] 센서 읽기 오류: {e}")


def send_status_via_handler(repeat: int = 3, delay_sec: float = 0.5):
    """
    HALL:STATUS 명령을 bleIoT.hall_handler 를 통해 반복 호출합니다.

    - 이 함수는 실제 BLE 경로(HALL_CHARACTERISTIC) 로 전송되는
      문자열 포맷(HALL:<raw>,<strength>,<density>) 이 정상인지 확인할 때 사용합니다.
    - 값 자체는 BLE 알림으로 나가기 때문에, 웹/PC 쪽에서 통합 테스트할 때 함께 활용합니다.
    """
    try:
        from bleIoT import hall_handler  # type: ignore
    except ImportError:
        print("[HALL TEST] hall_handler 를 가져올 수 없습니다. bleIoT 버전을 확인하세요.")
        return

    for i in range(repeat):
        print(f"[HALL TEST] HALL:STATUS 요청 전송 ({i + 1}/{repeat})")
        try:
            hall_handler(None, "HALL:STATUS")
        except Exception as e:
            print(f"[HALL TEST] HALL:STATUS 처리 중 오류: {e}")
        time.sleep(delay_sec)


def main():
    print("[HALL TEST] EZMaker 자기장(Hall) 센서 펌웨어 테스트 시작")
    print(f"[HALL TEST] EZMaker A0 포트를 Hall 센서 입력으로 사용합니다. (ADC_PIN={DEFAULT_HALL_ADC_PIN})")

    ok, adc_pin = configure_hall_pin_for_ezmaker()
    if not ok:
        print(f"[HALL TEST] PIN CONFIG FAILED (ADC_PIN={adc_pin}) - 배선 또는 센서 전원을 확인하세요.")
        return

    print(f"[HALL TEST] PIN CONFIG OK (ADC_PIN={adc_pin})")
    print("[HALL TEST] Hall 센서 값을 5회 정도 읽어 봅니다...")

    for i in range(5):
        print(f"[HALL TEST] 측정 {i + 1}/5")
        read_once_via_hall_sensor()
        time.sleep(1.0)

    print(
        "[HALL TEST] 이제 필요한 경우 HALL:STATUS 명령도 함께 테스트할 수 있습니다."
    )
    print("[HALL TEST] (원하면 send_status_via_handler() 를 REPL 에서 직접 호출하세요.)")


if __name__ == "__main__":
    main()



