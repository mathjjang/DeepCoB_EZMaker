# 이지메이커 초음파 센서 (1핀 방식) 테스트 코드 V2
# 연결: D2 (GPIO 48)
# 개선사항: 핀 모드 전환 속도 최적화 시도 및 디버깅 정보 추가

from machine import Pin, time_pulse_us, disable_irq, enable_irq
import time

# 핀 설정 (D2 -> GPIO 48)
ULTRASONIC_PIN = 48

def get_distance_v2():
    pin = Pin(ULTRASONIC_PIN, Pin.OUT)
    
    # 인터럽트 비활성화 (정확한 타이밍을 위해)
    state = disable_irq()
    
    try:
        # 1. Trig 신호 전송
        pin.value(0)
        time.sleep_us(2)
        pin.value(1)
        time.sleep_us(10)
        pin.value(0)
        
        # 2. 핀 모드를 입력으로 즉시 변경
        pin.init(Pin.IN)
        
        # 3. Echo 측정 (타임아웃 30ms)
        # time_pulse_us는 blocking 함수이므로 여기서 대기함
        duration = time_pulse_us(pin, 1, 30000)
        
    finally:
        # 인터럽트 다시 활성화
        enable_irq(state)
    
    if duration < 0:
        if duration == -1:
            return -1 # 타임아웃 (신호 없음)
        if duration == -2:
            return -2 # 이미 High 상태임 (센서 오류 또는 너무 가까움)
        return None

    # 거리 계산 (cm)
    distance = duration / 58.0
    return distance

def test_ultrasonic():
    print(f"Starting 1-Pin Ultrasonic Sensor Test V2 on D2 (GPIO {ULTRASONIC_PIN})...")
    print("Using interrupt disable for better timing.")
    
    fail_count = 0
    
    while True:
        dist = get_distance_v2()
        
        if dist is not None and dist >= 0:
            print(f"Distance: {dist:.1f} cm")
            fail_count = 0
        else:
            if dist == -1:
                print("Error: Timeout (No Echo)")
            elif dist == -2:
                print("Error: Pin stuck High (Sensor Fault)")
            else:
                print("Error: Unknown")
            
            fail_count += 1
            
            # 연속 실패 시 핀 리셋 시도 (Low로 확실히 내리기)
            if fail_count > 5:
                print("Resetting pin...")
                p = Pin(ULTRASONIC_PIN, Pin.OUT)
                p.value(0)
                time.sleep(0.1)
                fail_count = 0
            
        time.sleep(0.5)

if __name__ == "__main__":
    test_ultrasonic()

