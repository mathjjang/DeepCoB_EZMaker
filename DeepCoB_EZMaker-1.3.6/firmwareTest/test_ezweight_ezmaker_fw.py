"""
EZMaker 무게센서(EZWEIGHT, HX711) 펌웨어 테스트 코드

- DeepCo 보드 + EZMaker 쉴드 조합에서 EZ 무게센서(EZWEIGHT)를 연결했을 때,
  bleIoT 의 EZWEIGHT 핀 설정 및 상태 값이 정상 동작하는지 확인하기 위한 스크립트입니다.

중요(핀/배선):
- EZMaker 쉴드 UART 포트 핀은 고정입니다.
  - D11(TXD) = GPIO 42
  - D10(RXD) = GPIO 14
- 본 프로젝트에서 무게센서(HX711)는 아래처럼 사용합니다.
  - DOUT(DT) = GPIO 42
  - SCK(CLK) = GPIO 14

사용 방법 (펌웨어 단독 테스트 / REPL 기준):
1) 최신 bleIoT/bleBaseIoT/ez_weight_sensor 및 hx711 모듈을 보드에 배포합니다.
2) 이 파일을 보드 루트(또는 /firmwareTest)에 업로드합니다.
3) 보드가 정상 부팅되어 BLE IoT 모드(bleIoT)가 올라온 상태에서, REPL 에 아래 순서로 입력합니다.
   >>> import test_ezweight_ezmaker_fw
   >>> test_ezweight_ezmaker_fw.main()

주의:
- Thonny 에디터 창의 "Run" 버튼으로 실행하면 soft reboot 가 걸리면서 main/bleIoT 가 다시 올라가므로,
  이 테스트 파일은 반드시 REPL 에서 import 후 main() 을 호출하는 방식으로만 실행합니다.
"""

import time
import bleIoT  # 보드 /lib 에 설치된 bleIoT.mpy 를 직접 사용


# EZMaker 무게센서(HX711) 기본 핀 (쉴드 고정)
DEFAULT_EZWEIGHT_DOUT_PIN = 42  # D11(TXD)
DEFAULT_EZWEIGHT_SCK_PIN = 14   # D10(RXD)


def configure_ezweight_pin_for_ezmaker(dout_pin: int = DEFAULT_EZWEIGHT_DOUT_PIN,
                                       sck_pin: int = DEFAULT_EZWEIGHT_SCK_PIN):
    """
    EZMaker 쉴드의 고정 핀에 맞춰 EZWEIGHT 센서 핀을 설정합니다.

    - update_pin_config('ezweight', DOUT, SCK) 을 호출하면,
      bleIoT 내부에서 EzWeightSensor 초기화를 수행하고
      ez_weight_sensor 전역 객체를 준비합니다.
    """
    ok = bleIoT.update_pin_config("ezweight", dout_pin, sck_pin)
    return ok, dout_pin, sck_pin


def read_once_via_ezweight_sensor():
    """
    bleIoT.ez_weight_sensor (EzWeightSensor 인스턴스)를 직접 사용해서
    Raw 값 / 무게 값을 한 번 읽어 출력합니다.
    """
    sensor = getattr(bleIoT, "ez_weight_sensor", None)
    if sensor is None:
        print("[EZWEIGHT TEST] ez_weight_sensor 가 None 입니다. 핀 설정 또는 센서 초기화를 확인하세요.")
        return

    try:
        status = sensor.get_status()
        raw = status.get("raw")
        weight = status.get("weight")

        if raw is None or weight is None:
            print("[EZWEIGHT TEST] Read failed (raw/weight is None)")
            return

        print(
            "[EZWEIGHT TEST] "
            f"Raw: {raw} | "
            f"Weight(g): {weight:8.2f}"
        )
    except Exception as e:
        print(f"[EZWEIGHT TEST] 센서 읽기 오류: {e}")


def send_status_via_handler(repeat: int = 3, delay_sec: float = 0.5):
    """
    EZWEIGHT:STATUS 명령을 bleIoT.ez_weight_handler 를 통해 반복 호출합니다.

    - 이 함수는 실제 BLE 경로(EZ_WEIGHT_CHARACTERISTIC) 로 전송되는
      문자열 포맷(EZWEIGHT:<raw>,<weight>) 이 정상인지 확인할 때 사용합니다.
    - 값 자체는 BLE 알림으로 나가기 때문에, 웹/PC 쪽에서 통합 테스트할 때 함께 활용합니다.
    """
    try:
        from bleIoT import ez_weight_handler  # type: ignore
    except ImportError:
        print("[EZWEIGHT TEST] ez_weight_handler 를 가져올 수 없습니다. bleIoT 버전을 확인하세요.")
        return

    for i in range(repeat):
        print(f"[EZWEIGHT TEST] EZWEIGHT:STATUS 요청 전송 ({i + 1}/{repeat})")
        try:
            ez_weight_handler(None, "EZWEIGHT:STATUS")
        except Exception as e:
            print(f"[EZWEIGHT TEST] EZWEIGHT:STATUS 처리 중 오류: {e}")
        time.sleep(delay_sec)


def main(dout_pin: int = DEFAULT_EZWEIGHT_DOUT_PIN, sck_pin: int = DEFAULT_EZWEIGHT_SCK_PIN):
    print("==========================================")
    print("=== EZMaker EZWEIGHT 무게센서 펌웨어 테스트 ===")
    print("==========================================")
    print(f"[EZWEIGHT TEST] DOUT(DT) = GPIO {dout_pin}, SCK(CLK) = GPIO {sck_pin}")

    ok, used_dout, used_sck = configure_ezweight_pin_for_ezmaker(dout_pin, sck_pin)
    if not ok:
        print(f"[EZWEIGHT TEST] PIN CONFIG FAILED (DOUT={used_dout}, SCK={used_sck}) - 배선 또는 센서 전원을 확인하세요.")
        return

    print(f"[EZWEIGHT TEST] PIN CONFIG OK (DOUT={used_dout}, SCK={used_sck})")
    print("[EZWEIGHT TEST] 무게 값을 5회 정도 읽어 봅니다...")

    for i in range(5):
        print(f"[EZWEIGHT TEST] 측정 {i + 1}/5")
        read_once_via_ezweight_sensor()
        time.sleep(1.0)

    print("[EZWEIGHT TEST] 이제 필요한 경우 EZWEIGHT:STATUS 명령도 함께 테스트할 수 있습니다.")
    print("[EZWEIGHT TEST] (원하면 send_status_via_handler() 를 REPL 에서 직접 호출하세요.)")


if __name__ == "__main__":
    main()


