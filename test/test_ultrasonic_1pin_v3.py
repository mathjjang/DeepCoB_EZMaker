# 이지메이커 초음파 센서 (1핀 방식) 테스트 코드 V3
# 연결: D2 (GPIO 48)
# 개선사항: 입력 모드 전환 시 PULL_DOWN 저항 사용하여 플로팅 방지

from machine import Pin, time_pulse_us, disable_irq, enable_irq
import time

# 핀 설정 (D2 -> GPIO 48)
ULTRASONIC_PIN = 48

def get_distance_v3():
    # 초기화: 출력 모드, Low
    pin = Pin(ULTRASONIC_PIN, Pin.OUT)
    pin.value(0)
    
    # 인터럽트 비활성화
    state = disable_irq()
    
    try:
        # 1. Trig 신호 전송
        # Low 2us
        time.sleep_us(2)
        # High 10us
        pin.value(1)
        time.sleep_us(10)
        pin.value(0)
        
        # 2. 핀 모드를 입력으로 변경 (풀다운 저항 사용)
        # 이렇게 하면 센서가 Echo를 보내기 전까지(대기 상태) 핀을 0으로 유지하려고 시도함
        pin.init(Pin.IN, Pin.PULL_DOWN)
        
        # 3. Echo 측정 (타임아웃 30ms)
        duration = time_pulse_us(pin, 1, 30000)
        
    finally:
        enable_irq(state)
    
    if duration < 0:
        if duration == -1:
            return -1 # 타임아웃
        if duration == -2:
            return -2 # Stuck High
        return None

    # 거리 계산 (cm)
    distance = duration / 58.0
    return distance

def test_ultrasonic():
    print(f"Starting 1-Pin Ultrasonic Sensor Test V3 on D2 (GPIO {ULTRASONIC_PIN})...")
    print("Using PULL_DOWN resistor to prevent Stuck High.")
    
    fail_count = 0
    
    while True:
        dist = get_distance_v3()
        
        if dist is not None and dist >= 0:
            print(f"Distance: {dist:.1f} cm")
            fail_count = 0
        else:
            if dist == -1:
                print("Error: Timeout (No Echo)")
            elif dist == -2:
                print("Error: Pin stuck High (Sensor Fault or PULL_DOWN failed)")
            else:
                print("Error: Unknown")
                
            fail_count += 1
            
            # 연속 실패 시 리셋 시도
            if fail_count > 5:
                print("Resetting pin hard...")
                p = Pin(ULTRASONIC_PIN, Pin.OUT)
                p.value(0)
                time.sleep(0.1)
                fail_count = 0
            
        time.sleep(0.5)

if __name__ == "__main__":
    test_ultrasonic()

