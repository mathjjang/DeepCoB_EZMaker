# 이지메이커 전압 센서 테스트 코드 - 12비트 ADC + 0~25V 환산 출력
# 연결 예: A0 (GPIO 2)  -> 필요하면 A1~A4 등 다른 아날로그 포트로 변경
#
# - 보드 내부 ADC는 12비트(0~4095) 해상도로 동작합니다.
# - 전압 센서 모듈은 내부 저항 분할 회로를 통해 **0~25V 입력을 0~3.3V 정도로 스케일링**해서
#   ESP32 ADC에 인가합니다.
# - 이 스크립트는:
#     1) 12비트 Raw 값(0~4095)
#     2) 10비트 스케일 값(0~1023)
#     3) 보드 기준 전압(0~3.3V)
#     4) 센서 입력 전압(0~25V 환산 값)
#   을 함께 출력합니다.
#
# 사용 방법:
#  1. 전압 센서를 EZMaker 쉴드의 A0 포트(또는 원하는 A포트)에 연결합니다.
#  2. 이 파일을 보드에 업로드한 뒤, REPL에서 다음을 실행합니다.
#       >>> import test_voltage_ezmaker_12bit
#       >>> test_voltage_ezmaker_12bit.test_voltage_12bit()
#  3. 측정 대상 회로의 + / - 단자를 전압 센서의 터미널에 연결하여
#     Raw 값과 0~25V 환산 전압이 어떻게 변하는지 확인합니다.

from machine import Pin, ADC
import time

# 기본 핀 설정 (A0 -> GPIO 2)
VOLT_SENSOR_PIN = 2


def test_voltage_12bit(adc_pin: int = VOLT_SENSOR_PIN):
    print(
        f"Starting Voltage Sensor Test (12-bit) on EZMaker A포트 (GPIO {adc_pin})..."
    )

    try:
        # ADC 객체 생성
        adc = ADC(Pin(adc_pin))

        # ADC 감쇠 설정 (입력 전압 범위 조정)
        # ATTN_11DB: 약 0 ~ 3.3V 입력 가능
        adc.atten(ADC.ATTN_11DB)

        # 해상도 설정 (12비트: 0~4095)
        adc.width(ADC.WIDTH_12BIT)

        print("Voltage sensor initialized (12-bit ADC).")
        print("0.5초 간격으로 12bit/10bit Raw 값과 0~3.3V / 0~25V 전압을 출력합니다.")
        print("-" * 60)

        while True:
            # 12비트 값 읽기
            val_12bit = adc.read()  # 0 ~ 4095

            # 12bit → 10bit(0~1023) 스케일로 변환
            val_10bit = int(val_12bit * 1023 / 4095)

            # 보드 기준 전압 (0~3.3V, 내부 ADC 기준)
            voltage_3v3 = val_12bit * 3.3 / 4095

            # 전압 센서 스펙 기준 입력 전압 (0~25V)로 환산
            #  - 센서가 0~25V를 0~3.3V로 스케일링한다고 가정
            #  - Raw10 = 0   -> 약 0.00V
            #  - Raw10 = 1023 -> 약 25.00V (이론값)
            voltage_25v = val_10bit * 25.0 / 1023

            print(
                f"Raw12: {val_12bit:4d}/4095  "
                f"Raw10: {val_10bit:4d}/1023  "
                f"ADC(0~3.3V): {voltage_3v3:5.2f}V  "
                f"Input(0~25V): {voltage_25v:6.2f}V"
            )

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nTest stopped.")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_voltage_12bit()


