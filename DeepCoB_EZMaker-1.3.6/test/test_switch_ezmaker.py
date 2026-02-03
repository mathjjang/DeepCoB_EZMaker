# 이지메이커 디지털 스위치(버튼) 테스트 코드
# 연결: D2 (GPIO 48)

from machine import Pin
import time

# 핀 설정 (D2 -> GPIO 48)
SWITCH_PIN = 48

def test_switch():
    print(f"Starting Switch Test on D2 (GPIO {SWITCH_PIN})...")
    
    try:
        # 버튼 핀 설정 (입력 모드, 풀업 저항 사용)
        # 보통 스위치는 한쪽이 GND에 연결되므로, 눌렀을 때 Low(0), 뗐을 때 High(1)가 됨.
        # 만약 스위치 모듈이 VCC를 출력하는 방식이면 Pin.PULL_DOWN 사용 필요.
        # 일반적인 메이커용 버튼 모듈은 누르면 High(1)가 되는 경우가 많음. -> PULL_DOWN이 안전
        
        # 일단 이지메이커 센서 특성을 모르므로, 두 가지 경우를 모두 고려하여 값 출력
        
        # 1. 풀다운 모드 (누르면 1이 될 것으로 예상)
        # switch = Pin(SWITCH_PIN, Pin.IN, Pin.PULL_DOWN)
        
        # 2. 입력 모드 (센서 모듈 자체에 저항이 있을 수 있음 -> 단순 IN)
        switch = Pin(SWITCH_PIN, Pin.IN)
        
        print("Switch initialized. Press the button...")
        
        last_val = -1
        
        while True:
            val = switch.value()
            
            # 상태가 변했을 때만 출력
            if val != last_val:
                if val == 1:
                    print("Button Pressed (High/1)")
                else:
                    print("Button Released (Low/0)")
                last_val = val
            
            time.sleep(0.1) # 디바운싱 겸 딜레이
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_switch()

