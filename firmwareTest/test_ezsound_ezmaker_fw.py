"""
EZMaker 소리센서(EZSOUND) 펌웨어 테스트 코드 (EZMaker A0 포트 기본 사용)

- DeepCo 보드 + EZMaker 쉴드 조합에서 EZ 소리센서(EZSOUND)를
  EZMaker A0~A4 포트에 연결했을 때,
  bleIoT 의 EZSOUND 핀 설정 및 상태 값이 정상 동작하는지 확인하기 위한 스크립트입니다.

사용 방법 (펌웨어 단독 테스트 / REPL 기준):
1. 최신 bleIoT/bleBaseIoT/ez_sound_sensor 를 mpy 로 컴파일하여 보드의 /lib 에 배포합니다.
2. 이 파일을 보드 루트(또는 /firmwareTest)에 업로드합니다.
3. 보드가 정상 부팅되어 BLE IoT 모드(bleIoT)가 올라온 상태에서, REPL 에 아래 순서로 입력합니다.
   >>> import test_ezsound_ezmaker_fw
   >>> test_ezsound_ezmaker_fw.main()
4. 동작:
   - EZSOUND 센서 핀을 EZMaker A0 포트(기본) 에 대응하는 GPIO 로 설정합니다.
   - bleIoT 내부의 ez_sound_sensor(EzSoundSensor 인스턴스)를 통해
     10비트 Raw 값(0~1023)과 소리 레벨 비율(0~100%)을 여러 번 읽어 콘솔에 출력합니다.
   - 필요하면 EZSOUND:STATUS 명령을 직접 호출해, BLE 경로로도 값이 전송되는지 확인할 수 있습니다.

주의:
- Thonny 에디터 창의 "Run" 버튼으로 실행하면 soft reboot 가 걸리면서 main/bleIoT 가 다시 올라가므로,
  이 테스트 파일은 반드시 REPL 에서 import 후 main() 을 호출하는 방식으로만 실행합니다.
"""

import time
import bleIoT  # 보드 /lib 에 설치된 bleIoT.mpy 를 직접 사용


# EZMaker EZSOUND 센서 기본 포트 (A0) 에 대응하는 GPIO 번호
# - 현재 테스트 환경에서 A0 → GPIO 2 를 사용 중
DEFAULT_EZSOUND_ADC_PIN = 2


def configure_ezsound_pin_for_ezmaker(adc_pin: int = DEFAULT_EZSOUND_ADC_PIN):
    """
    EZMaker 쉴드의 A0 포트 등에 맞춰 EZSOUND 센서 핀을 설정합니다.

    - update_pin_config('ezsound', ADC_PIN) 을 호출하면,
      bleIoT 내부에서 EzSoundSensor 초기화를 수행하고
      ez_sound_sensor 전역 객체를 준비합니다.
    """
    ok = bleIoT.update_pin_config("ezsound", adc_pin)
    return ok, adc_pin


def read_once_via_ezsound_sensor():
    """
    bleIoT.ez_sound_sensor (EzSoundSensor 인스턴스)를 직접 사용해서
    10비트 Raw 값 / 소리 레벨 비율 / 전압(참고용) 을 한 번 읽어 출력합니다.
    """
    sensor = getattr(bleIoT, "ez_sound_sensor", None)
    if sensor is None:
        print("[EZSOUND TEST] ez_sound_sensor 가 None 입니다. 핀 설정 또는 센서 초기화를 확인하세요.")
        return

    try:
        status = sensor.get_status()
        raw = status.get("raw")
        percent = status.get("percent")
        voltage = status.get("voltage")

        print(
            "[EZSOUND TEST] "
            f"Raw(0-1023): {raw:4d} | "
            f"Level(0~100%): {percent:5.1f} | "
            f"Voltage(3.3V 참고용): {voltage:4.2f} V"
        )
    except Exception as e:
        print(f"[EZSOUND TEST] 센서 읽기 오류: {e}")


def send_status_via_handler(repeat: int = 3, delay_sec: float = 0.5):
    """
    EZSOUND:STATUS 명령을 bleIoT.ez_sound_handler 를 통해 반복 호출합니다.

    - 이 함수는 실제 BLE 경로(EZ_SOUND_CHARACTERISTIC) 로 전송되는
      문자열 포맷(EZSOUND:<raw>,<percent>) 이 정상인지 확인할 때 사용합니다.
    - 값 자체는 BLE 알림으로 나가기 때문에, 웹/PC 쪽에서 통합 테스트할 때 함께 활용합니다.
    """
    try:
        from bleIoT import ez_sound_handler  # type: ignore
    except ImportError:
        print("[EZSOUND TEST] ez_sound_handler 를 가져올 수 없습니다. bleIoT 버전을 확인하세요.")
        return

    for i in range(repeat):
        print(f"[EZSOUND TEST] EZSOUND:STATUS 요청 전송 ({i + 1}/{repeat})")
        try:
            ez_sound_handler(None, "EZSOUND:STATUS")
        except Exception as e:
            print(f"[EZSOUND TEST] EZSOUND:STATUS 처리 중 오류: {e}")
        time.sleep(delay_sec)


def main(adc_pin: int = DEFAULT_EZSOUND_ADC_PIN):
    print("=" * 40)
    print("=== EZMaker 소리센서(EZSOUND) 펌웨어 테스트 ===")
    print("=" * 40)
    print(f"[EZSOUND TEST] EZMaker A0 포트를 EZSOUND 센서 입력으로 사용합니다. (ADC_PIN={adc_pin})")

    ok, used_pin = configure_ezsound_pin_for_ezmaker(adc_pin)
    if not ok:
        print(f"[EZSOUND TEST] PIN CONFIG FAILED (ADC_PIN={used_pin}) - 배선 또는 센서 전원을 확인하세요.")
        return

    print(f"[EZSOUND TEST] PIN CONFIG OK (ADC_PIN={used_pin})")
    print("[EZSOUND TEST] EZSOUND 센서 값을 5회 정도 읽어 봅니다...")

    for i in range(5):
        print(f"[EZSOUND TEST] 측정 {i + 1}/5")
        read_once_via_ezsound_sensor()
        time.sleep(1.0)

    print(
        "[EZSOUND TEST] 이제 필요한 경우 EZSOUND:STATUS 명령도 함께 테스트할 수 있습니다."
    )
    print("[EZSOUND TEST] (원하면 send_status_via_handler() 를 REPL 에서 직접 호출하세요.)")


if __name__ == "__main__":
    main()


