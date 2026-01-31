# 이지메이커 조도 센서 (GL5549) 테스트 코드 - 12비트 해상도
# 연결: A1 (GPIO 1)

from machine import Pin, ADC
import time

# 핀 설정 (A1 -> GPIO 1)
LIGHT_PIN = 1

def test_light_12bit():
    print(f"Starting Light Sensor Test (12-bit) on A1 (GPIO {LIGHT_PIN})...")
    
    try:
        # ADC 객체 생성
        adc = ADC(Pin(LIGHT_PIN))
        
        # ADC 감쇠 설정 (입력 전압 범위 조정)
        # ATTN_11DB: 약 0 ~ 3.3V 입력 가능
        adc.atten(ADC.ATTN_11DB)
        
        # 해상도 설정 (12비트: 0~4095)
        adc.width(ADC.WIDTH_12BIT)
        
        print("Sensor initialized (12-bit ADC).")
        print("Reading light values every 0.5 seconds (12bit + 10bit scale)...")
        print("-" * 40)
        
        while True:
            # 12비트 값 읽기 (read() 메서드 사용)
            # read_u16()은 16비트로 업스케일링된 값을 반환하므로,
            # 순수 12비트 값을 원하면 read()를 사용합니다.
            val_12bit = adc.read()

            # 12bit → 10bit(0~1023) 스케일로 변환
            val_10bit = int(val_12bit * 1023 / 4095)
            
            # 전압으로 변환 (3.3V 기준, 12bit 값 사용)
            voltage = val_12bit * 3.3 / 4095
            
            # 0-100% 비율로 변환 (12bit 기준)
            percent_12 = (val_12bit / 4095) * 100
            # 0-100% 비율로 변환 (10bit 기준)
            percent_10 = (val_10bit / 1023) * 100
            
            print(
                f"Raw12: {val_12bit:>4}/4095 "
                f"Raw10: {val_10bit:>4}/1023 "
                f"Volt(3.3V): {voltage:.2f}V "
                f"Pct12: {percent_12:.1f}% Pct10: {percent_10:.1f}%"
            )
            
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\nTest stopped.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_light_12bit()

