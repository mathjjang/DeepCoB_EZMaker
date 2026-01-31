"""
EZMaker 미세먼지 센서(EZDUST, PMS7003M) 펌웨어 테스트 코드

- DeepCo 보드 + EZMaker 쉴드 조합에서 EZ 미세먼지 센서(EZDUST)를 UART로 연결했을 때,
  bleIoT 의 EZDUST 핀 설정 및 상태 값이 정상 동작하는지 확인하기 위한 스크립트입니다.

중요(핀/배선):
- EZMaker 쉴드 UART 포트 핀은 고정입니다.
  - D10(RXD) = GPIO 14  (보드 RX)
  - D11(TXD) = GPIO 42  (보드 TX)
- PMS7003M 연결(일반 규칙):
  - 센서 TX  -> 보드 RX (GPIO 14)
  - 센서 RX  -> 보드 TX (GPIO 42)
- EZDUST 명령 포맷은 "EZDUST:PIN:RX,TX" (보드 기준 RX,TX 순서) 입니다.

사용 방법 (펌웨어 단독 테스트 / REPL 기준):
1) 최신 bleIoT/bleBaseIoT/ez_dust_pms7003 드라이버를 보드에 배포합니다.
2) 이 파일을 보드 루트(또는 /firmwareTest)에 업로드합니다.
3) 보드가 정상 부팅되어 BLE IoT 모드(bleIoT)가 올라온 상태에서, REPL 에 아래 순서로 입력합니다.
   >>> import test_ezdust_ezmaker_fw
   >>> test_ezdust_ezmaker_fw.main()

주의:
- Thonny 에디터 창의 "Run" 버튼으로 실행하면 soft reboot 가 걸리면서 main/bleIoT 가 다시 올라가므로,
  이 테스트 파일은 반드시 REPL 에서 import 후 main() 을 호출하는 방식으로만 실행합니다.
- PMS 센서는 동작 안정화에 시간이 걸릴 수 있습니다(수십 초 워밍업). 초기에 -1 또는 0이 나올 수 있습니다.
"""

import time
import bleIoT  # 보드 /lib 에 설치된 bleIoT.mpy 를 직접 사용


# EZMaker 쉴드 UART 공통 핀 (보드 기준 RX,TX)
DEFAULT_EZDUST_RX_PIN = 14   # D10(RXD)
DEFAULT_EZDUST_TX_PIN = 42   # D11(TXD)


def configure_ezdust_pin_for_ezmaker(rx_pin: int = DEFAULT_EZDUST_RX_PIN,
                                     tx_pin: int = DEFAULT_EZDUST_TX_PIN):
    """
    EZMaker 쉴드의 고정 UART 핀에 맞춰 EZDUST 센서 핀을 설정합니다.

    - update_pin_config('ezdust', RX, TX) 을 호출하면,
      bleIoT 내부에서 EzDustSensor 초기화를 수행하고
      ez_dust_sensor 전역 객체를 준비합니다.
    """
    ok = bleIoT.update_pin_config("ezdust", rx_pin, tx_pin)
    return ok, rx_pin, tx_pin


def read_once_via_ezdust_sensor():
    """
    bleIoT.ez_dust_sensor (EzDustSensor 인스턴스)를 직접 사용해서
    PM10 / PM2.5 / PM1.0 값을 한 번 읽어 출력합니다.
    """
    sensor = getattr(bleIoT, "ez_dust_sensor", None)
    if sensor is None:
        print("[EZDUST TEST] ez_dust_sensor 가 None 입니다. 핀 설정 또는 센서 초기화를 확인하세요.")
        return

    try:
        status = sensor.get_status()
        pm10 = status.get("pm10")
        pm2_5 = status.get("pm2_5")
        pm1_0 = status.get("pm1_0")

        # 드라이버에서 읽기 실패 시 -1을 반환하도록 구현된 경우가 있음
        if pm10 is None or pm2_5 is None or pm1_0 is None:
            print("[EZDUST TEST] Read failed (pm values are None)")
            return

        print(
            "[EZDUST TEST] "
            f"PM10: {pm10:>4} | "
            f"PM2.5: {pm2_5:>4} | "
            f"PM1.0: {pm1_0:>4}  (μg/m³)"
        )
    except Exception as e:
        print(f"[EZDUST TEST] 센서 읽기 오류: {e}")


def send_status_via_handler(repeat: int = 3, delay_sec: float = 1.0):
    """
    EZDUST:STATUS 명령을 bleIoT.ez_dust_handler 를 통해 반복 호출합니다.

    - 이 함수는 실제 BLE 경로(EZ_DUST_CHARACTERISTIC) 로 전송되는
      문자열 포맷(EZDUST:<pm10>,<pm2_5>,<pm1_0>) 이 정상인지 확인할 때 사용합니다.
    - 값 자체는 BLE 알림으로 나가기 때문에, 웹/PC 쪽에서 통합 테스트할 때 함께 활용합니다.
    """
    try:
        from bleIoT import ez_dust_handler  # type: ignore
    except ImportError:
        print("[EZDUST TEST] ez_dust_handler 를 가져올 수 없습니다. bleIoT 버전을 확인하세요.")
        return

    for i in range(repeat):
        print(f"[EZDUST TEST] EZDUST:STATUS 요청 전송 ({i + 1}/{repeat})")
        try:
            ez_dust_handler(None, "EZDUST:STATUS")
        except Exception as e:
            print(f"[EZDUST TEST] EZDUST:STATUS 처리 중 오류: {e}")
        time.sleep(delay_sec)


def main(rx_pin: int = DEFAULT_EZDUST_RX_PIN, tx_pin: int = DEFAULT_EZDUST_TX_PIN):
    print("==============================================")
    print("=== EZMaker EZDUST 미세먼지센서 펌웨어 테스트 ===")
    print("==============================================")
    print(f"[EZDUST TEST] RX = GPIO {rx_pin}, TX = GPIO {tx_pin}")
    print("[EZDUST TEST] (센서 TX -> RX, 센서 RX -> TX 로 배선되어야 합니다.)")

    ok, used_rx, used_tx = configure_ezdust_pin_for_ezmaker(rx_pin, tx_pin)
    if not ok:
        print(f"[EZDUST TEST] PIN CONFIG FAILED (RX={used_rx}, TX={used_tx}) - 배선 또는 센서 전원을 확인하세요.")
        return

    print(f"[EZDUST TEST] PIN CONFIG OK (RX={used_rx}, TX={used_tx})")
    print("[EZDUST TEST] PM 값을 10회 정도 읽어 봅니다... (초기에는 워밍업으로 값이 불안정할 수 있습니다)")

    for i in range(10):
        print(f"[EZDUST TEST] 측정 {i + 1}/10")
        read_once_via_ezdust_sensor()
        time.sleep(1.0)

    print("[EZDUST TEST] 이제 필요한 경우 EZDUST:STATUS 명령도 함께 테스트할 수 있습니다.")
    print("[EZDUST TEST] (원하면 send_status_via_handler() 를 REPL 에서 직접 호출하세요.)")


if __name__ == "__main__":
    main()


