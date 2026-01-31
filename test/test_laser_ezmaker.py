# 이지메이커 레이저 모듈 테스트 코드
# 연결: D3 (GPIO 38)

from machine import Pin
import time

# 핀 설정 (D3 -> GPIO 38)
LASER_PIN = 38

def test_laser():
    print(f"Starting Laser Module Test on D3 (GPIO {LASER_PIN})...")
    
    try:
        # 레이저는 출력(OUT) 장치입니다.
        laser = Pin(LASER_PIN, Pin.OUT)
        
        print("Laser blinking... (1 second interval)")
        
        while True:
            # 레이저 켜기 (High)
            print("Laser ON")
            laser.value(1)
            time.sleep(5)
            
            # 레이저 끄기 (Low)
            print("Laser OFF")
            laser.value(0)
            time.sleep(1)
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # 종료 시 끄기
        try:
            pin = Pin(LASER_PIN, Pin.OUT)
            pin.value(0)
        except:
            pass

if __name__ == "__main__":
    test_laser()

