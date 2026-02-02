"""
EZMaker 자이로센서(ICM20948) 펌웨어 테스트 코드 (EZMaker 쉴드 기본 핀 사용)

- DeepCo 보드 + EZMaker 쉴드 조합에서 ICM20948 자이로센서가
  I2C 로 정상 인식되고, bleIoT 의 EZGYRO 핀 설정/STATUS 경로가
  제대로 동작하는지 확인하기 위한 스크립트입니다.

사용 방법 (펌웨어 단독 테스트 / REPL 기준):
1. 최신 bleIoT/bleBaseIoT/icm20948 를 mpy 로 컴파일하여 보드의 /lib 에 배포합니다.
2. 이 파일을 보드 루트(또는 /firmwareTest)에 업로드합니다.
3. 보드가 정상 부팅되어 BLE IoT 모드(bleIoT)가 올라온 상태에서, REPL 에 아래 순서로 입력합니다.
   >>> import test_ezgyro_icm20948_ezmaker_fw
   >>> test_ezgyro_icm20948_ezmaker_fw.main()
4. 동작:
   - EZGYRO 용 핀을 EZMaker 기본 핀(SDA=D6=GPIO 41, SCL=D5=GPIO 40) 으로 설정합니다.
   - bleIoT 내부의 ez_gyro_sensor(ICM20948 인스턴스)를 통해 가속도/자이로/롤/피치/온도 값을 몇 차례 읽어서 출력합니다.
   - 필요하면 EZGYRO:STATUS 명령을 직접 호출해, BLE 경로로도 값이 전송되는지 확인할 수 있습니다.

주의:
- Thonny 에디터 창의 "Run" 버튼으로 실행하면 soft reboot 가 걸리면서 main/bleIoT 가 다시 올라가므로,
  이 테스트 파일은 반드시 REPL 에서 import 후 main() 을 호출하는 방식으로만 실행합니다.
"""

import time
import bleIoT  # 보드 /lib 에 설치된 bleIoT.mpy 를 직접 사용

# EZMaker 자이로센서 기본 핀 (쉴드 실크 기준)
# - SCL: D5 -> GPIO 40
# - SDA: D6 -> GPIO 41
DEFAULT_EZGYRO_SDA = 41
DEFAULT_EZGYRO_SCL = 40


def configure_ezgyro_pins_for_ezmaker():
    """
    EZMaker 쉴드의 기본 I2C 핀에 맞춰 EZGYRO 핀을 설정합니다.

    - update_pin_config('ezgyro', SDA, SCL) 을 호출하면,
      bleIoT 내부에서 SoftI2C + ICM20948 초기화를 수행하고
      ez_gyro_sensor 전역 객체를 준비합니다.
    """
    ok = bleIoT.update_pin_config("ezgyro", DEFAULT_EZGYRO_SDA, DEFAULT_EZGYRO_SCL)
    return ok, DEFAULT_EZGYRO_SDA, DEFAULT_EZGYRO_SCL


def read_once_via_ezgyro_sensor():
    """
    bleIoT.ez_gyro_sensor (ICM20948 인스턴스)를 직접 사용해서
    가속도/자이로/ROLL/PITCH/온도 값을 한 번 읽어 출력합니다.
    """
    sensor = getattr(bleIoT, "ez_gyro_sensor", None)
    if sensor is None:
        print("[EZGYRO TEST] ez_gyro_sensor 가 None 입니다. 핀 설정 또는 센서 초기화를 확인하세요.")
        return

    try:
        data = sensor.read_accel_gyro()
        rpy = sensor.calculate_rpy(data["accel"])

        ax = data["accel"]["x"]
        ay = data["accel"]["y"]
        az = data["accel"]["z"]

        gx = data["gyro"]["x"]
        gy = data["gyro"]["y"]
        gz = data["gyro"]["z"]

        roll = rpy["roll"]
        pitch = rpy["pitch"]
        temp = data["temp"]

        print(
            "[EZGYRO TEST] "
            f"Accel(g): X={ax:6.2f}, Y={ay:6.2f}, Z={az:6.2f} | "
            f"Gyro(dps): X={gx:7.2f}, Y={gy:7.2f}, Z={gz:7.2f}"
        )
        print(
            "[EZGYRO TEST] "
            f"Roll={roll:6.1f}°, Pitch={pitch:6.1f}°, Temp={temp:5.1f}°C"
        )
    except Exception as e:
        print(f"[EZGYRO TEST] 센서 읽기 오류: {e}")


def send_status_via_handler(repeat: int = 3, delay_sec: float = 0.5):
    """
    EZGYRO:STATUS 명령을 bleIoT.ez_gyro_handler 를 통해 반복 호출합니다.

    - 이 함수는 실제 BLE 경로(EZ_GYRO_CHARACTERISTIC)로 전송되는
      문자열 포맷(EZGYRO:AX=...,AY=...,...) 이 정상인지 확인할 때 사용합니다.
    - 값 자체는 BLE 알림으로 나가기 때문에, 웹/PC 쪽에서 통합 테스트할 때 함께 활용합니다.
    """
    try:
        from bleIoT import ez_gyro_handler  # type: ignore
    except ImportError:
        print("[EZGYRO TEST] ez_gyro_handler 를 가져올 수 없습니다. bleIoT 버전을 확인하세요.")
        return

    for i in range(repeat):
        print(f"[EZGYRO TEST] EZGYRO:STATUS 요청 전송 ({i + 1}/{repeat})")
        try:
            ez_gyro_handler(None, "EZGYRO:STATUS")
        except Exception as e:
            print(f"[EZGYRO TEST] EZGYRO:STATUS 처리 중 오류: {e}")
        time.sleep(delay_sec)


def main():
    print("[EZGYRO TEST] EZMaker 자이로센서(ICM20948) 펌웨어 테스트 시작")
    print(
        f"[EZGYRO TEST] EZMaker 기본 핀으로 설정: SDA={DEFAULT_EZGYRO_SDA}, "
        f"SCL={DEFAULT_EZGYRO_SCL}"
    )

    ok, sda, scl = configure_ezgyro_pins_for_ezmaker()
    if not ok:
        print(
            f"[EZGYRO TEST] PIN CONFIG FAILED (SDA={sda}, SCL={scl}) - "
            "배선 또는 센서 전원을 확인하세요."
        )
        return

    print(f"[EZGYRO TEST] PIN CONFIG OK (SDA={sda}, SCL={scl})")
    print("[EZGYRO TEST] ICM20948 값을 5회 정도 읽어 봅니다...")

    for i in range(5):
        print(f"[EZGYRO TEST] 측정 {i + 1}/5")
        read_once_via_ezgyro_sensor()
        time.sleep(0.5)

    print(
        "[EZGYRO TEST] 이제 필요한 경우 EZGYRO:STATUS 명령도 함께 테스트할 수 있습니다."
    )
    print("[EZGYRO TEST] (원하면 send_status_via_handler() 를 REPL 에서 직접 호출하세요.)")


if __name__ == "__main__":
    main()


