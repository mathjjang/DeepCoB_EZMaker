# 이지메이커 초음파 센서 (1핀 방식) 테스트 코드
# 연결: D0 (GPIO 21)
# D0는 I2C SCL이지만 일반 GPIO로 사용 가능

from machine import Pin, time_pulse_us, disable_irq, enable_irq
import time

# 핀 설정 (D0 -> GPIO 21)
ULTRASONIC_PIN = 21

def get_distance_d0():
    pin = Pin(ULTRASONIC_PIN, Pin.OUT)
    pin.value(0)
    
    state = disable_irq()
    
    try:
        # Trig
        time.sleep_us(2)
        pin.value(1)
        time.sleep_us(10)
        pin.value(0)
        
        # Input Mode
        # D0는 I2C 핀이라 내부 풀업이 있을 수 있으므로, PULL_DOWN 시도
        pin.init(Pin.IN, Pin.PULL_DOWN)
        
        # Echo
        duration = time_pulse_us(pin, 1, 30000)
        
    finally:
        enable_irq(state)
    
    if duration < 0:
        if duration == -1: return -1
        if duration == -2: return -2
        return None

    distance = duration / 58.0
    return distance

def test_ultrasonic():
    print(f"Starting 1-Pin Ultrasonic Sensor Test on D0 (GPIO {ULTRASONIC_PIN})...")
    
    fail_count = 0
    
    while True:
        dist = get_distance_d0()
        
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

