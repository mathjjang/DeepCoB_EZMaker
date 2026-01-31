# 이지메이커 초음파 센서 (1핀 방식) 테스트 코드
# 연결: A0 / D7 (GPIO 2)
# GPIO 2는 부트 핀으로 보통 풀다운이 되어 있어 초음파 센서(Low Idle)와 호환성이 좋을 수 있음

from machine import Pin, time_pulse_us, disable_irq, enable_irq
import time

# 핀 설정 (A0/D7 -> GPIO 2)
ULTRASONIC_PIN = 2

def get_distance_a0():
    # 초기화: 출력 모드, Low
    pin = Pin(ULTRASONIC_PIN, Pin.OUT)
    pin.value(0)
    
    state = disable_irq()
    
    try:
        # Trig 신호
        time.sleep_us(2)
        pin.value(1)
        time.sleep_us(10)
        pin.value(0)
        
        # 입력 모드 전환 (GPIO 2는 기본 풀다운일 수 있으나 명시적으로 PULL_DOWN 설정)
        pin.init(Pin.IN, Pin.PULL_DOWN)
        
        # Echo 측정 (30ms)
        duration = time_pulse_us(pin, 1, 30000)
        
    finally:
        enable_irq(state)
    
    if duration < 0:
        if duration == -1: return -1 # Timeout
        if duration == -2: return -2 # Stuck High
        return None

    distance = duration / 58.0
    return distance

def test_ultrasonic():
    print(f"Starting 1-Pin Ultrasonic Sensor Test on A0/D7 (GPIO {ULTRASONIC_PIN})...")
    
    fail_count = 0
    
    while True:
        dist = get_distance_a0()
        
        if dist is not None and dist >= 0:
            print(f"Distance: {dist:.1f} cm")
            fail_count = 0
        else:
            if dist == -1:
                print("Error: Timeout (No Echo)")
            elif dist == -2:
                print("Error: Pin stuck High")
            
            fail_count += 1
            if fail_count > 5:
                # 리셋 시도
                p = Pin(ULTRASONIC_PIN, Pin.OUT)
                p.value(0)
                time.sleep(0.1)
                fail_count = 0
            
        time.sleep(0.5)

if __name__ == "__main__":
    test_ultrasonic()

