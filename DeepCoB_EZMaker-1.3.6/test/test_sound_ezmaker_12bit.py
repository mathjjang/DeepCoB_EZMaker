# 문서 기준: A0=2, A1=1, A2=3, A3=20, A4=19

from machine import Pin, ADC
import time

# 핀 설정 (A2 -> GPIO 3)
SOUND_PIN = 3

def test_sound_12bit():
    print(f"Starting Sound Sensor Test (12-bit) on A2 (GPIO {SOUND_PIN})...")
    
    try:
        # ADC 설정
        adc = ADC(Pin(SOUND_PIN))
        adc.atten(ADC.ATTN_11DB) # 3.3V 범위
        adc.width(ADC.WIDTH_12BIT) # 12비트 설정
        
        print("Sensor initialized. Clap your hands or make noise!")
        
        # 기준값 (조용한 상태) 잡기
        print("Calibrating silence level (2 seconds)...")
        silence_sum = 0
        calib_count = 20
        for _ in range(calib_count):
            silence_sum += adc.read()
            time.sleep(0.1)
        silence_val = int(silence_sum / calib_count)
        print(f"Silence Reference: {silence_val}")
        
        while True:
            # 소리 센서는 순식간에 변하므로 빠르게 여러 번 읽어서 최대값을 찾아야 함
            peak_val = 0
            min_val = 4095
            
            # 100ms 동안 샘플링하여 피크(Peak) 감지
            start_time = time.ticks_ms()
            while time.ticks_diff(time.ticks_ms(), start_time) < 100:
                val = adc.read()
                if val > peak_val:
                    peak_val = val
                if val < min_val:
                    min_val = val
            
            # 변화폭 (Amplitude)
            amplitude = peak_val - min_val
            
            # 기준값 대비 변화가 크면 소리 감지
            # 12비트 기준 임계값 (기존 16비트의 2000 => 12비트 약 125)
            threshold = 150
            
            status = "Quiet"
            if amplitude > threshold:
                status = "LOUD!"
            
            print(f"Ref: {silence_val}, Peak: {peak_val}, Amp: {amplitude} -> {status}")
            
            # 딜레이 없음 (연속 샘플링을 위해)
            
    except KeyboardInterrupt:
        print("\nTest stopped.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_sound_12bit()

