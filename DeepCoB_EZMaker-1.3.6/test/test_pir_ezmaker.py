# 이지메이커 인체감지센서(PIR) 테스트 코드
# 연결: D3 (GPIO 38)

from machine import Pin
import time

# 핀 설정 (D3 -> GPIO 38)
PIR_PIN = 38

def test_pir():
    print(f"Starting PIR Motion Sensor Test on D3 (GPIO {PIR_PIN})...")
    
    try:
        # PIR 센서는 감지 시 High(1)를 출력합니다. (Active High)
        # 모듈 자체에 풀다운이 있을 수 있지만, 없으면 Pin.PULL_DOWN 사용 가능
        # 일단 기본 입력 모드로 설정
        pir = Pin(PIR_PIN, Pin.IN)
        
        print("PIR Sensor initialized. Waiting for motion...")
        print("(Note: PIR sensors need 30-60s warmup time on power-up)")
        
        last_val = -1
        
        while True:
            val = pir.value()
            
            if val != last_val:
                if val == 1:
                    print("Motion Detected! (1)")
                else:
                    print("Motion Ended (0)")
                last_val = val
            
            time.sleep(0.1)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_pir()

