"""
EZMaker 전류센서(EZCURR, INA219) 펌웨어 테스트 코드

- EZMaker 보드에서 REPL로 실행하여 펌웨어 연동 상태를 확인하기 위한 스크립트입니다.
- 흐름:
    1) EZCURR I2C 핀(SDA, SCL)을 설정 (기본: SDA=41, SCL=40)
    2) ez_curr_sensor.get_status() 를 직접 호출하여 값 확인
    3) ez_curr_handler 를 통해 'EZCURR:STATUS' 명령을 시뮬레이션
"""

import time
import bleIoT

# EZMaker 기본 I2C 핀 (LCD 등과 동일 패턴 사용)
DEFAULT_EZCURR_SDA_PIN = 41
DEFAULT_EZCURR_SCL_PIN = 40


def configure_ezcurr_pin_for_ezmaker(sda_pin: int = DEFAULT_EZCURR_SDA_PIN,
                                     scl_pin: int = DEFAULT_EZCURR_SCL_PIN):
    """
    EZMaker 보드에서 EZCURR 전류센서(INA219) I2C 핀 설정 헬퍼
    """
    ok = bleIoT.update_pin_config("ezcurr", sda_pin, scl_pin)
    return ok, sda_pin, scl_pin


def read_once_via_ezcurr_sensor():
    """
    bleIoT.ez_curr_sensor 객체를 직접 사용하여 값 1회 읽기
    """
    sensor = getattr(bleIoT, "ez_curr_sensor", None)
    if sensor is None:
        print("[EZCURR TEST] ez_curr_sensor 가 None 입니다. I2C 핀 설정 또는 센서 초기화를 확인하세요.")
        return

    try:
        status = sensor.get_status()
        voltage = status.get("voltage")
        current_mA = status.get("current_mA")
        power_mW = status.get("power_mW")

        print(
            "[EZCURR TEST] "
            f"Vbus: {voltage if voltage is not None else 0.0:6.3f} V | "
            f"I: {current_mA if current_mA is not None else 0.0:7.3f} mA | "
            f"P: {power_mW if power_mW is not None else 0.0:7.1f} mW"
        )
    except Exception as e:
        print(f"[EZCURR TEST] 센서 읽기 오류: {e}")


def send_status_via_handler(repeat: int = 3, delay_sec: float = 0.5):
    """
    bleIoT.ez_curr_handler 를 직접 호출하여 'EZCURR:STATUS' 명령 시뮬레이션
    (BLE 없이 펌웨어 로직만 테스트)
    """
    try:
        from bleIoT import ez_curr_handler
    except ImportError:
        print("[EZCURR TEST] ez_curr_handler 를 가져올 수 없습니다. bleIoT 버전을 확인하세요.")
        return

    for i in range(repeat):
        print(f"[EZCURR TEST] EZCURR:STATUS 요청 전송 ({i + 1}/{repeat})")
        try:
            ez_curr_handler(None, "EZCURR:STATUS")
        except Exception as e:
            print(f"[EZCURR TEST] EZCURR:STATUS 처리 중 오류: {e}")
        time.sleep(delay_sec)


def main(sda_pin: int = DEFAULT_EZCURR_SDA_PIN, scl_pin: int = DEFAULT_EZCURR_SCL_PIN):
    print("==========================================")
    print("=== EZMaker EZCURR 전류센서 펌웨어 테스트 ===")
    print("==========================================")
    print(f"[EZCURR TEST] SDA = GPIO {sda_pin}, SCL = GPIO {scl_pin}")

    ok, used_sda, used_scl = configure_ezcurr_pin_for_ezmaker(sda_pin, scl_pin)
    if not ok:
        print(f"[EZCURR TEST] PIN CONFIG FAILED (SDA={used_sda}, SCL={used_scl}) - 배선 또는 센서 전원을 확인하세요.")
        return

    print(f"[EZCURR TEST] PIN CONFIG OK (SDA={used_sda}, SCL={used_scl})")
    print("[EZCURR TEST] 전류/전압 값을 5회 정도 읽어 봅니다...")

    for i in range(5):
        print(f"[EZCURR TEST] 측정 {i + 1}/5")
        read_once_via_ezcurr_sensor()
        time.sleep(1.0)

    print("[EZCURR TEST] 이제 필요한 경우 EZCURR:STATUS 명령도 함께 테스트할 수 있습니다.")
    print("[EZCURR TEST] (원하면 send_status_via_handler() 를 REPL 에서 직접 호출하세요.)")


if __name__ == "__main__":
    main()


