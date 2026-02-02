# 이지메이커 DIY-B 전류 / 전도도 센서 테스트 코드 - 10비트
# 연결 예시: A1 (GPIO 1)  -> 문서상 A1 = 1
#
#   * DIY-B 센서는 두 전극 사이를 흐르는 전류의 크기에 따라
#     출력 전압이 0~5V 범위에서 변하는 아날로그 센서입니다.
#   * 보드 내부 ADC는 12비트(0~4095) 해상도로 동작하며,
#     이 값을 코드에서 10비트(0~1023) 스케일로 변환해서 사용합니다.
#     출력 전압은 사용자가 보기 쉽도록 0~5V 기준으로 환산해 표시합니다.
#
# 사용 방법:
#  1. DIY-B 센서를 EZMaker 쉴드의 A1 포트에 연결합니다. (필요시 다른 A포트로 변경 가능)
#  2. 이 파일을 보드에 업로드한 뒤,
#     REPL에서 다음을 실행합니다.
#       >>> import test_diyb_ezmaker_10bit
#       >>> test_diyb_ezmaker_10bit.test_diyb_10bit()
#  3. 악어집게 두 개를 전류가 흐르는 회로의 두 지점에 직렬로 연결한 뒤
#     (예: 전지-부하 사이), 흐르는 전류가 달라질 때 Raw / 전압값이
#     어떻게 변하는지 관찰합니다.

from machine import Pin, ADC
import time

# 핀 설정 (A1 -> GPIO 1)
DIY_B_PIN = 1


def test_diyb_10bit():
    print(f"Starting DIY-B Current/Conductivity Sensor Test (10-bit) on A1 (GPIO {DIY_B_PIN})...")

    try:
        # ADC 설정
        adc = ADC(Pin(DIY_B_PIN))
        # ATTN_11DB: 약 0 ~ 3.3V 입력 가능
        adc.atten(ADC.ATTN_11DB)
        # 12비트 해상도 (0 ~ 4095)
        # 이후 코드에서 10비트(0~1023) 스케일로 변환하여 사용합니다.
        adc.width(ADC.WIDTH_12BIT)

        print("Sensor initialized.")
        print("먼저 회로를 고정한 상태에서 '기본 상태' 전류가 흐르도록 세팅해 주세요.")
        print("기본 상태에서의 기준값(reference)을 측정합니다... (약 2초)")

        # 기준값(reference) 측정 (내부 12비트 값을 10비트 스케일로 변환해서 사용)
        ref_sum = 0
        ref_count = 20
        for _ in range(ref_count):
            raw_12bit = adc.read()
            val_10bit = int(raw_12bit * 1023 / 4095)
            ref_sum += val_10bit
            time.sleep(0.1)
        ref_val = int(ref_sum / ref_count)

        print(f"Reference Value (raw): {ref_val}")
        print("-" * 60)
        print("이제 부하 저항을 바꾸거나, 전압원을 바꾸는 등으로")
        print("회로에 흐르는 전류를 바꾸면서 값을 관찰해 보세요.")
        print("Raw / Voltage(0~5V 환산) / Diff(전류 변화량에 비례)를 출력합니다.")
        print("-" * 60)

        # 감지 임계값 (기준값 대비 변화량)
        # 10비트(0~1023) 기준으로 약 40 정도 이상의 변화가 있으면
        # '전류가 꽤 달라졌다'고 보기로 합니다. (필요 시 조정)
        threshold = 40

        while True:
            # 내부 12비트 Raw 값(0 ~ 4095)을 읽어서 10비트 스케일(0 ~ 1023)로 변환
            raw_12bit = adc.read()
            val_10bit = int(raw_12bit * 1023 / 4095)

            # 센서 스펙(0~5V)을 기준으로 해석하기 위해 0~5V로 환산해서 표시
            #   - raw  = 0    ->  0.00V
            #   - raw  = 1023 ->  5.00V (이론상)
            voltage_5v = val_10bit * 5.0 / 1023

            # 기준값 대비 차이 (전류 변화량에 비례하는 값)
            diff = val_10bit - ref_val

            print(f"Raw: {val_10bit:>4} / 1023, Voltage(0~5V): {voltage_5v:.2f}V, Diff: {diff:>4}")

            # 전류/전도도 변화 감지 여부
            if abs(diff) > threshold:
                print("  -> Current / Conductivity Changed Noticeably")

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nTest stopped.")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_diyb_10bit()


