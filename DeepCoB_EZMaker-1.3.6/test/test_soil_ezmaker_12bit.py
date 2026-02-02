# 이지메이커 토양수분 센서 테스트 코드 - 12비트
# 연결: A4 (GPIO 19) -> 문서상 A4=19

from machine import Pin, ADC
import time

# 핀 설정 (A4 -> GPIO 19)
SOIL_PIN = 19

def test_soil_12bit():
    print(f"Starting Soil Moisture Sensor Test (12-bit) on A4 (GPIO {SOIL_PIN})...")
    
    try:
        # ADC 설정
        adc = ADC(Pin(SOIL_PIN))
        adc.atten(ADC.ATTN_11DB) # 3.3V 범위
        adc.width(ADC.WIDTH_12BIT)
        
        print("Sensor initialized. Reading...")
        
        while True:
            # 값 읽기
            val_12bit = adc.read()
            
            # 전압 변환 (참고용)
            voltage = val_12bit * 3.3 / 4095
            
            # 백분율 (0=Dry, 4095=Wet 이라고 가정 시, 혹은 반대일 수 있음)
            # 보통 토양수분센서는 물에 닿으면 저항 감소 -> 전압 변화
            # (센서 타입에 따라 값이 커질지 작아질지 다름, 일단 Raw 값 출력)
            
            print(f"Raw: {val_12bit:>4} / 4095, Voltage: {voltage:.2f}V")
            
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\nTest stopped.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_soil_12bit()

