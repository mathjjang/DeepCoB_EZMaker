# 이지메이커 초음파 센서 (1핀 방식) 테스트 코드
# 연결: D2 (GPIO 48)

from machine import Pin, time_pulse_us
import time

# 핀 설정 (D2 -> GPIO 48)
ULTRASONIC_PIN = 48

def get_distance():
    # 1. 핀을 출력(OUT) 모드로 설정하고 초기화
    pin = Pin(ULTRASONIC_PIN, Pin.OUT)
    pin.value(0) # Low
    time.sleep_us(2)
    
    # 2. Trig 신호 전송 (10us High Pulse)
    pin.value(1) # High
    time.sleep_us(10)
    pin.value(0) # Low
    
    # 3. 핀을 입력(IN) 모드로 변경하여 Echo 수신 준비
    pin.init(Pin.IN)
    
    try:
        # 4. Echo 펄스 길이 측정 (High 상태 지속 시간)
        # timeout_us=30000 (30ms) -> 약 5m 거리까지 측정 가능
        duration = time_pulse_us(pin, 1, 30000)
        
        # 5. 거리 계산 (cm)
        # 소리의 속도: 340m/s = 0.034cm/us
        # 거리 = 시간 * 속도 / 2 (왕복)
        # distance = duration * 0.034 / 2 = duration / 58.82
        # 아두이노 코드 기준: duration / 29.0 / 2.0 = duration / 58.0
        
        if duration < 0:
            return None # 타임아웃 또는 오류
        
        distance = duration / 58.0
        return distance
        
    except OSError as e:
        # time_pulse_us 에러 처리
        return None

def test_ultrasonic():
    print(f"Starting 1-Pin Ultrasonic Sensor Test on D2 (GPIO {ULTRASONIC_PIN})...")
    
    while True:
        dist = get_distance()
        
        if dist is not None:
            print(f"Distance: {dist:.1f} cm")
        else:
            print("Out of range or Sensor Error")
            
        time.sleep(0.5)

if __name__ == "__main__":
    test_ultrasonic()

