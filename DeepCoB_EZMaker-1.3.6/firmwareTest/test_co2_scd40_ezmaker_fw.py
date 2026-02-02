"""
EZMaker 이산화탄소 센서(SCD40) 펌웨어 테스트 코드 (EZMaker 쉴드 기본 핀 사용)

- DeepCo 보드 + EZMaker 쉴드 조합에서 SCD40 CO2 센서가
  I2C 로 정상 인식되고, bleIoT 의 EZCO2 핀 설정/STATUS 경로가
  제대로 동작하는지 확인하기 위한 스크립트입니다.

사용 방법 (펌웨어 단독 테스트 / REPL 기준):
1. 최신 bleIoT/bleBaseIoT/scd40 를 mpy 로 컴파일하여 보드의 /lib 에 배포합니다.
2. 이 파일을 보드 루트(또는 /firmwareTest)에 업로드합니다.
3. 보드가 정상 부팅되어 BLE IoT 모드(bleIoT)가 올라온 상태에서, REPL 에 아래 순서로 입력합니다.
   >>> import test_co2_scd40_ezmaker_fw
   >>> test_co2_scd40_ezmaker_fw.main()
4. 동작:
   - EZCO2 용 핀을 EZMaker 기본 핀(SDA=D6=GPIO 41, SCL=D5=GPIO 40) 으로 설정합니다.
   - bleIoT 내부의 ez_co2_sensor(SCD40 인스턴스)를 통해 CO2/온도/습도 값을 몇 차례 읽어서 출력합니다.
   - 필요하면 EZCO2:STATUS 명령을 직접 호출해, BLE 경로로도 값이 전송되는지 확인할 수 있습니다.

주의:
- Thonny 에디터 창의 "Run" 버튼으로 실행하면 soft reboot 가 걸리면서 main/bleIoT 가 다시 올라가므로,
  이 테스트 파일은 반드시 REPL 에서 import 후 main() 을 호출하는 방식으로만 실행합니다.
"""

import time
import bleIoT  # 보드 /lib 에 설치된 bleIoT.mpy 를 직접 사용

# EZMaker CO2 센서 기본 핀 (쉴드 실크 기준)
# - SCL: D5 -> GPIO 40
# - SDA: D6 -> GPIO 41
DEFAULT_EZCO2_SDA = 41
DEFAULT_EZCO2_SCL = 40


def configure_ezco2_pins_for_ezmaker():
    """
    EZMaker 쉴드의 기본 I2C 핀에 맞춰 EZCO2 핀을 설정합니다.

    - update_pin_config('ezco2', SDA, SCL) 을 호출하면,
      bleIoT 내부에서 SoftI2C + SCD40 초기화를 수행하고
      ez_co2_sensor 전역 객체를 준비합니다.
    """
    ok = bleIoT.update_pin_config("ezco2", DEFAULT_EZCO2_SDA, DEFAULT_EZCO2_SCL)
    return ok, DEFAULT_EZCO2_SDA, DEFAULT_EZCO2_SCL


def read_once_via_ezco2_sensor():
    """
    bleIoT.ez_co2_sensor (SCD40 인스턴스)를 직접 사용해서
    CO2/온도/습도 값을 한 번 읽어 출력합니다.
    """
    sensor = getattr(bleIoT, "ez_co2_sensor", None)
    if sensor is None:
        print("[EZCO2 TEST] ez_co2_sensor 가 None 입니다. 핀 설정 또는 센서 초기화를 확인하세요.")
        return

    try:
        # 데이터 준비 여부 확인
        if not sensor.is_data_ready():
            print("[EZCO2 TEST] 데이터가 아직 준비되지 않았습니다. 잠시 후 다시 시도하세요.")
            return

        co2, temp_c, hum = sensor.read()

        print(
            "[EZCO2 TEST] "
            f"CO2: {co2:4.0f} ppm | "
            f"Temp: {temp_c:6.2f} C | "
            f"Hum: {hum:6.2f} %RH"
        )
    except Exception as e:
        print(f"[EZCO2 TEST] 센서 읽기 오류: {e}")


def send_status_via_handler(repeat: int = 3, delay_sec: float = 5.0):
    """
    EZCO2:STATUS 명령을 bleIoT.ez_co2_handler 를 통해 반복 호출합니다.

    - 이 함수는 실제 BLE 경로(EZ_CO2_CHARACTERISTIC) 로 전송되는
      문자열 포맷(EZCO2:CO2=...,T=...,H=...) 이 정상인지 확인할 때 사용합니다.
    - 값 자체는 BLE 알림으로 나가기 때문에, 웹/PC 쪽에서 통합 테스트할 때 함께 활용합니다.
    """
    try:
        from bleIoT import ez_co2_handler  # type: ignore
    except ImportError:
        print("[EZCO2 TEST] ez_co2_handler 를 가져올 수 없습니다. bleIoT 버전을 확인하세요.")
        return

    for i in range(repeat):
        print(f"[EZCO2 TEST] EZCO2:STATUS 요청 전송 ({i + 1}/{repeat})")
        try:
            ez_co2_handler(None, "EZCO2:STATUS")
        except Exception as e:
            print(f"[EZCO2 TEST] EZCO2:STATUS 처리 중 오류: {e}")
        time.sleep(delay_sec)


def main():
    print("[EZCO2 TEST] EZMaker 이산화탄소 센서(SCD40) 펌웨어 테스트 시작")
    print(
        f"[EZCO2 TEST] EZMaker 기본 핀으로 설정: SDA={DEFAULT_EZCO2_SDA}, "
        f"SCL={DEFAULT_EZCO2_SCL}"
    )

    ok, sda, scl = configure_ezco2_pins_for_ezmaker()
    if not ok:
        print(
            f"[EZCO2 TEST] PIN CONFIG FAILED (SDA={sda}, SCL={scl}) - "
            "배선 또는 센서 전원을 확인하세요."
        )
        return

    print(f"[EZCO2 TEST] PIN CONFIG OK (SDA={sda}, SCL={scl})")
    print("[EZCO2 TEST] SCD40 측정이 준비될 때까지 약 5초 정도 대기합니다...")
    time.sleep(5.0)

    print("[EZCO2 TEST] CO2/온도/습도 값을 5회 정도 읽어 봅니다...")

    for i in range(5):
        print(f"[EZCO2 TEST] 측정 {i + 1}/5")
        read_once_via_ezco2_sensor()
        time.sleep(5.0)

    print(
        "[EZCO2 TEST] 이제 필요한 경우 EZCO2:STATUS 명령도 함께 테스트할 수 있습니다."
    )
    print("[EZCO2 TEST] (원하면 send_status_via_handler() 를 REPL 에서 직접 호출하세요.)")


if __name__ == "__main__":
    main()


