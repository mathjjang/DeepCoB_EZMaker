# 이지메이커 DIY-A 전자기 유도 센서 테스트 코드 - 10비트
# 연결: A0 (GPIO 2)  -> 문서상 A0 = 2
#
#  * 보드 내부 ADC는 12비트(0~4095) 해상도로 동작합니다.
#  * 이 값(0~4095)을 코드에서 10비트(0~1023) 스케일로 변환해 사용하고,
#    출력 전압은 사용자가 보기 쉽도록 **0~5V 기준으로 환산**해서 보여줍니다.
#
# 사용 방법:
#  1. DIY-A 센서를 EZMaker 쉴드의 A0 포트에 연결합니다.
#  2. 이 파일을 보드에 업로드한 뒤,
#     REPL에서 다음을 실행합니다.
#       >>> import test_diya_ezmaker_10bit
#       >>> test_diya_ezmaker_10bit.test_diya_10bit()
#  3. 코일 근처에서 자석을 앞뒤로 움직이거나,
#     교류(AC) 전류가 흐르는 전선에 가까이 가져가면서
#     Raw 값과 Diff 값의 변화를 관찰합니다.

from machine import Pin, ADC
import time

# 핀 설정 (A0 -> GPIO 2)
DIY_A_PIN = 2


def test_diya_10bit():
    print(f"Starting DIY-A Electromagnetic Induction Sensor Test (10-bit) on A0 (GPIO {DIY_A_PIN})...")

    try:
        # ADC 설정
        adc = ADC(Pin(DIY_A_PIN))
        # ATTN_11DB: 약 0 ~ 3.3V 입력 가능
        adc.atten(ADC.ATTN_11DB)
        # 12비트 해상도 (0 ~ 4095)
        # 이후 코드에서 10비트(0~1023) 스케일로 변환하여 사용합니다.
        adc.width(ADC.WIDTH_12BIT)

        print("Sensor initialized.")
        print("먼저 센서를 고정해 둔 상태에서 값이 안정될 때까지 기다려 주세요.")
        print("기준값(reference)을 측정합니다... (약 2초)")

        # 기준값(reference) 측정 (내부 12비트 값을 10비트 스케일로 변환해서 사용)
        ref_sum = 0
        ref_count = 20
        for _ in range(ref_count):
            raw_12bit = adc.read()
            val_10bit = int(raw_12bit * 1023 / 4095)
            ref_sum += val_10bit
            time.sleep(0.1)
        ref_val = int(ref_sum / ref_count)

        print(f"Reference Value: {ref_val}")
        print("-" * 50)
        print("이제 코일 근처에서 자석을 앞뒤로 움직이거나,")
        print("AC 전류가 흐르는 전선을 가까이 가져가 보세요.")
        print("Raw / Voltage(0~5V 환산) / Diff 값을 보면서 변화를 확인합니다.")
        print("-" * 50)

        # 감지 임계값 (기준값 대비 변화량)
        # 10비트(0~1023) 기준으로 약 40 정도 이상의 변화가 있으면
        # "자기장 변화가 눈에 띄게 발생"했다고 보기로 합니다. (필요 시 조정)
        threshold = 40

        while True:
            # 내부 12비트 Raw 값(0 ~ 4095)을 읽어서 10비트 스케일(0 ~ 1023)로 변환
            raw_12bit = adc.read()
            val_10bit = int(raw_12bit * 1023 / 4095)

            # 내부 ADC 기준 전압은 3.3V이지만,
            # 센서 스펙(0~5V)을 기준으로 해석하기 위해 0~5V로 환산해서 표시합니다.
            #   - raw  = 0   ->  0.00V
            #   - raw  = 1023 ->  5.00V (이론상)
            voltage_5v = val_10bit * 5.0 / 1023

            # 기준값 대비 차이
            diff = val_10bit - ref_val

            print(f"Raw: {val_10bit:>4} / 1023, Voltage(0~5V): {voltage_5v:.2f}V, Diff: {diff:>4}")

            # 전자기 유도(자기장 변화) 감지 여부
            if abs(diff) > threshold:
                print("  -> Induction Detected! (자기장 변화 감지)")

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nTest stopped.")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_diya_10bit()


