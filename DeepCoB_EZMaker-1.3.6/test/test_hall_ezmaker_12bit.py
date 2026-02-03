# 이지메이커 자기장(Hall) 센서 테스트 코드 - 12비트 ADC 사용, 10비트/극성(N/S) 출력
# 연결: A3 (보드에 따라 GPIO 번호는 다를 수 있음)

from machine import Pin, ADC
import time

# 핀 설정 (테스트에 사용 중인 GPIO 번호)
HALL_PIN = 2

def test_hall_12bit():
    print(f"Starting Hall Sensor Test (12-bit ADC, 10-bit output) on A3 (GPIO {HALL_PIN})...")
    
    try:
        # ADC 설정
        adc = ADC(Pin(HALL_PIN))
        adc.atten(ADC.ATTN_11DB) # 3.3V 범위
        adc.width(ADC.WIDTH_12BIT)
        
        print("Sensor initialized. Reading...")
        print("Place a magnet near the sensor and observe changes.")
        
        # 기준값 설정을 위한 초기 평균 측정 (12비트 기준)
        initial_sum_12 = 0
        for _ in range(10):
            initial_sum_12 += adc.read()
            time.sleep(0.05)
        initial_val_12 = int(initial_sum_12 / 10)

        # 10비트(0~1023) 스케일로 변환한 기준값
        initial_val_10bit = int(initial_val_12 * 1023 / 4095)
        print(f"Initial Reference (10bit): {initial_val_10bit}")
        
        while True:
            # 값 읽기 (12비트: 0~4095)
            val_12bit = adc.read()

            # 10비트(0~1023) 스케일 값으로 변환
            val_10bit = int(val_12bit * 1023 / 4095)

            # 전압 변환 (3.3V 기준, 참고용)
            voltage = val_12bit * 3.3 / 4095

            # 변화량 계산 (10비트 기준)
            diff_10bit = val_10bit - initial_val_10bit

            # 자석 N/S 극 세기 (-512 ~ +512) 스케일로 변환
            # 경험적으로 변화량 ±128 근처를 최대 세기(±512)로 매핑
            MAX_DIFF_10BIT = 128
            if diff_10bit > MAX_DIFF_10BIT:
                diff_clamped = MAX_DIFF_10BIT
            elif diff_10bit < -MAX_DIFF_10BIT:
                diff_clamped = -MAX_DIFF_10BIT
            else:
                diff_clamped = diff_10bit
            strength_512 = int(diff_clamped * 512 / MAX_DIFF_10BIT)

            # N/S 극성 텍스트 (양수: N, 음수: S, 0 근처: 0)
            if strength_512 > 0:
                polarity = "N"
            elif strength_512 < 0:
                polarity = "S"
            else:
                polarity = "0"

            print(
                f"Raw10(0-1023): {val_10bit:>4}, "
                f"Voltage(3.3V): {voltage:.2f}V, "
                f"Diff10: {diff_10bit:>4}, "
                f"Strength(-512~+512): {strength_512:>4}, "
                f"Polarity(N/S): {polarity}"
            )

            # 자기장 센서는 자석의 극(N/S)에 따라 전압이 증가하거나 감소함
            # 10비트 기준으로 변화폭이 충분히 크면 자석 감지로 판단 (대략 30 이상)
            if abs(diff_10bit) > 30:
                print("  -> Magnet Detected!")
                
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\nTest stopped.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_hall_12bit()

