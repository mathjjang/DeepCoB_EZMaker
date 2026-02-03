# 이지메이커 자기장(Hall) 센서 테스트 코드
# 연결: A3 (GPIO 3)

from machine import Pin, ADC
import time

# 핀 설정 (A3 -> GPIO 3)
HALL_PIN = 2

def test_hall():
    print(f"Starting Hall Sensor Test on A3 (GPIO {HALL_PIN})...")
    
    try:
        # ADC 설정
        adc = ADC(Pin(HALL_PIN))
        adc.atten(ADC.ATTN_11DB) # 3.3V 범위
        
        print("Sensor initialized. Reading...")
        print("Place a magnet near the sensor and observe changes.")
        
        # 기준값 설정을 위한 초기 평균 측정 (u16 기준)
        initial_sum_u16 = 0
        for _ in range(10):
            initial_sum_u16 += adc.read_u16()
            time.sleep(0.05)
        initial_val_u16 = int(initial_sum_u16 / 10)

        # 10비트(0~1023) 스케일로 변환한 기준값
        initial_val_10bit = int(initial_val_u16 * 1023 / 65535)
        print(f"Initial Reference (10bit): {initial_val_10bit}")
        
        while True:
            # 값 읽기 (u16: 0~65535)
            val_u16 = adc.read_u16()

            # 10비트(0~1023) 스케일 값으로 변환
            val_10bit = int(val_u16 * 1023 / 65535)

            # 전압 변환 (3.3V 기준, 참고용)
            voltage = val_u16 * 3.3 / 65535

        # 변화량 계산 (10비트 기준)
        diff_10bit = val_10bit - initial_val_10bit

        # 작은 노이즈 영역(데드존) 제거: |diff_10bit|가 너무 작으면 0으로 취급
        DEAD_ZONE_DIFF = 5
        if -DEAD_ZONE_DIFF < diff_10bit < DEAD_ZONE_DIFF:
            diff_for_strength = 0
        else:
            diff_for_strength = diff_10bit

        # 자석 N/S 극 세기 (-512 ~ +512) 스케일로 변환
        # - diff_for_strength가 기준값에서의 의미있는 변화량(10bit)
        # - 이를 경험적으로 최대 ±128 근처까지를 ±512로 매핑하도록 설정
        MAX_DIFF_10BIT = 128
        if diff_for_strength > MAX_DIFF_10BIT:
            diff_clamped = MAX_DIFF_10BIT
        elif diff_for_strength < -MAX_DIFF_10BIT:
            diff_clamped = -MAX_DIFF_10BIT
        else:
            diff_clamped = diff_for_strength
        strength_512 = int(diff_clamped * 512 / MAX_DIFF_10BIT)

            print(
                f"Raw10(0-1023): {val_10bit}, "
                f"Voltage(3.3V): {voltage:.2f}V, "
                f"Diff10: {diff_10bit}, "
                f"Strength(-512~+512): {strength_512}"
            )

            # 자기장 센서는 자석의 극(N/S)에 따라 전압이 증가하거나 감소함
            # 10비트 기준으로 변화폭이 충분히 크면 자석 감지로 판단 (대략 30 이상)
            if abs(diff_10bit) > 30:
                print("  -> Magnet Detected!")
                
            time.sleep(0.5)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_hall()

