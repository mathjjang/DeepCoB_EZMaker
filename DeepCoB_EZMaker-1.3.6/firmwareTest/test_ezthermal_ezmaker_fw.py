"""
EZMaker 수중/접촉 온도센서(EZTHERMAL, DS18B20) 펌웨어 테스트 코드 (EZMaker D0 포트 기본 사용)

- DeepCo 보드 + EZMaker 쉴드 조합에서 EZTHERMAL 수중/접촉 온도센서를
  EZMaker D0~D4 디지털 포트에 연결했을 때,
  bleIoT 의 EZTHERMAL 핀 설정 및 상태 값이 정상 동작하는지 확인하기 위한 스크립트입니다.

사용 방법 (펌웨어 단독 테스트 / REPL 기준):
1. 최신 bleIoT / bleBaseIoT / ez_thermal_sensor 를 mpy 로 컴파일하여 보드의 /lib 에 배포합니다.
2. 이 파일을 보드 루트(또는 /firmwareTest)에 업로드합니다.
3. 보드가 정상 부팅되어 BLE IoT 모드(bleIoT)가 올라온 상태에서, REPL 에 아래 순서로 입력합니다.
   >>> import test_ezthermal_ezmaker_fw
   >>> test_ezthermal_ezmaker_fw.main()
4. 동작:
   - EZTHERMAL 센서 핀을 EZMaker D0 포트(기본) 에 대응하는 GPIO 로 설정합니다.
   - bleIoT 내부의 ez_thermal_sensor(EzThermalSensor 인스턴스)를 통해
     현재 온도(섭씨, ℃)를 여러 번 읽어 콘솔에 출력합니다.
   - 필요하면 EZTHERMAL:STATUS 명령을 직접 호출해, BLE 경로로도 값이 전송되는지 확인할 수 있습니다.

주의:
- Thonny 에디터 창의 "Run" 버튼으로 실행하면 soft reboot 가 걸리면서 main/bleIoT 가 다시 올라가므로,
  이 테스트 파일은 반드시 REPL 에서 import 후 main() 을 호출하는 방식으로만 실행합니다.
"""

import time
import bleIoT  # 보드 /lib 에 설치된 bleIoT.mpy 를 직접 사용


# EZMaker EZTHERMAL 센서 기본 포트 (D0) 에 대응하는 GPIO 번호
# - 현재 테스트 환경에서 D0 → GPIO 21 을 사용 중
DEFAULT_EZTHERMAL_PIN = 21


def configure_ezthermal_pin_for_ezmaker(pin: int = DEFAULT_EZTHERMAL_PIN):
    """
    EZMaker 쉴드의 D0 포트 등에 맞춰 EZTHERMAL 센서 핀을 설정합니다.

    - update_pin_config('ezthermal', PIN) 을 호출하면,
      bleIoT 내부에서 EzThermalSensor 초기화를 수행하고
      ez_thermal_sensor 전역 객체를 준비합니다.
    """
    ok = bleIoT.update_pin_config("ezthermal", pin)
    return ok, pin


def read_once_via_ezthermal_sensor():
    """
    bleIoT.ez_thermal_sensor (EzThermalSensor 인스턴스)를 직접 사용해서
    현재 온도(℃)를 한 번 읽어 출력합니다.
    """
    sensor = getattr(bleIoT, "ez_thermal_sensor", None)
    if sensor is None:
        print("[EZTHERMAL TEST] ez_thermal_sensor 가 None 입니다. 핀 설정 또는 센서 초기화를 확인하세요.")
        return

    try:
        status = sensor.get_status()
        temp_c = status.get("temperature")

        if temp_c is None:
            print("[EZTHERMAL TEST] 온도 읽기 실패 (temperature 가 None 입니다.)")
            return

        print(
            "[EZTHERMAL TEST] "
            f"Temperature: {temp_c:6.2f} °C"
        )
    except Exception as e:
        print(f"[EZTHERMAL TEST] 센서 읽기 오류: {e}")


def send_status_via_handler(repeat: int = 3, delay_sec: float = 0.5):
    """
    EZTHERMAL:STATUS 명령을 bleIoT.ez_thermal_handler 를 통해 반복 호출합니다.

    - 이 함수는 실제 BLE 경로(EZ_THERMAL_CHARACTERISTIC) 로 전송되는
      문자열 포맷(EZTHERMAL:<temperatureC>) 이 정상인지 확인할 때 사용합니다.
    - 값 자체는 BLE 알림으로 나가기 때문에, 웹/PC 쪽에서 통합 테스트할 때 함께 활용합니다.
    """
    try:
        from bleIoT import ez_thermal_handler  # type: ignore
    except ImportError:
        print("[EZTHERMAL TEST] ez_thermal_handler 를 가져올 수 없습니다. bleIoT 버전을 확인하세요.")
        return

    for i in range(repeat):
        print(f"[EZTHERMAL TEST] EZTHERMAL:STATUS 요청 전송 ({i + 1}/{repeat})")
        try:
            ez_thermal_handler(None, "EZTHERMAL:STATUS")
        except Exception as e:
            print(f"[EZTHERMAL TEST] EZTHERMAL:STATUS 처리 중 오류: {e}")
        time.sleep(delay_sec)


def main(pin: int = DEFAULT_EZTHERMAL_PIN):
    print("=" * 40)
    print("=== EZMaker 수중/접촉 온도센서(EZTHERMAL) 펌웨어 테스트 ===")
    print("=" * 40)
    print(f"[EZTHERMAL TEST] EZMaker D0 포트를 수중/접촉 온도센서 입력으로 사용합니다. (PIN={pin})")

    ok, used_pin = configure_ezthermal_pin_for_ezmaker(pin)
    if not ok:
        print(f"[EZTHERMAL TEST] PIN CONFIG FAILED (PIN={used_pin}) - 배선 또는 센서 전원을 확인하세요.")
        return

    print(f"[EZTHERMAL TEST] PIN CONFIG OK (PIN={used_pin})")
    print("[EZTHERMAL TEST] EZTHERMAL 센서 값을 5회 정도 읽어 봅니다...")

    for i in range(5):
        print(f"[EZTHERMAL TEST] 측정 {i + 1}/5")
        read_once_via_ezthermal_sensor()
        time.sleep(1.0)

    print(
        "[EZTHERMAL TEST] 이제 필요한 경우 EZTHERMAL:STATUS 명령도 함께 테스트할 수 있습니다."
    )
    print("[EZTHERMAL TEST] (원하면 send_status_via_handler() 를 REPL 에서 직접 호출하세요.)")


if __name__ == "__main__":
    main()


