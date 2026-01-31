# 이지메이커 터치 스위치 테스트 코드
# 연결: D3 (GPIO 38)
# 주의: D3는 원래 온습도센서(DHT) 맵핑이지만, 터치 스위치 테스트를 위해 GPIO 38로 사용합니다.

from machine import Pin
import time

# 핀 설정 (D3 -> GPIO 38)
TOUCH_PIN = 21

def test_touch():
    print(f"Starting Touch Sensor Test on D3 (GPIO {TOUCH_PIN})...")
    
    try:
        # 터치 센서는 보통 Active High (터치 시 1) 입니다.
        # 별도 풀업/풀다운 없이 입력 모드로 설정합니다.
        touch = Pin(TOUCH_PIN, Pin.IN)
        
        print("Touch sensor initialized. Touch the sensor...")
        
        last_val = -1
        
        while True:
            val = touch.value()
            
            # 상태가 변했을 때만 출력
            if val != last_val:
                if val == 1:
                    print("Touched! (1)")
                else:
                    print("Released (0)")
                last_val = val
            
            time.sleep(0.1)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_touch()

