# 이지메이커 DC 모터 테스트 코드
# 연결: D0(GPIO 21) - 단방향, PWM 속도 제어
# 속도 범위: 0~100%

from machine import Pin, PWM
import time

# ============================================================
# 초기 설정 - 여기서 모터 핀을 설정하세요
# ============================================================

# 연결 핀 설정 (DeepCo v2.0 + Shield v2.0 기준)
# D0=21, D1=47, D2=48, D3=38, D4=39
MOTOR_PIN = 21

# PWM 주파수 (Hz) - 모터에 따라 조절
PWM_FREQ = 1000

# 전역 모터 객체 (중단 시 정리용)
_motor = None

# ============================================================
# 안전한 sleep 함수 - 인터럽트 시 모터 정지
# ============================================================

def safe_sleep(seconds):
    """sleep 중 인터럽트 발생 시 모터 정지"""
    global _motor
    ms = int(seconds * 1000)
    step = 50  # 50ms 단위로 체크
    
    try:
        while ms > 0:
            time.sleep_ms(min(step, ms))
            ms -= step
    except KeyboardInterrupt:
        # 인터럽트 발생 시 즉시 모터 정지
        if _motor:
            _motor.pwm.duty(0)
            _motor.pwm.deinit()
            # 핀을 명시적으로 LOW로 설정
            p = Pin(MOTOR_PIN, Pin.OUT)
            p.value(0)
        raise  # 다시 예외 발생

def safe_sleep_ms(ms):
    """ms 단위 safe sleep"""
    safe_sleep(ms / 1000)

# ============================================================
# 모터 제어 클래스
# ============================================================

class DCMotor:
    def __init__(self, pin, freq=1000):
        self.pin = pin
        self.pwm = PWM(Pin(pin))
        self.pwm.freq(freq)
        self.pwm.duty(0)
        self.current_speed = 0
        
    def set_speed(self, speed):
        """속도 설정 (0~100%)"""
        speed = max(0, min(100, speed))  # 0~100 범위 제한
        self.current_speed = speed
        # ESP32 PWM duty: 0~1023
        duty = int(speed * 1023 / 100)
        self.pwm.duty(duty)
        
    def stop(self):
        """모터 정지"""
        self.pwm.duty(0)
        self.current_speed = 0
        
    def get_speed(self):
        """현재 속도 반환"""
        return self.current_speed
    
    def accelerate(self, target_speed, duration_ms=1000, steps=20):
        """부드러운 가속/감속"""
        start_speed = self.current_speed
        speed_diff = target_speed - start_speed
        delay = duration_ms // steps
        
        for i in range(steps + 1):
            new_speed = start_speed + (speed_diff * i / steps)
            self.set_speed(int(new_speed))
            safe_sleep_ms(delay)
    
    def deinit(self):
        """PWM 해제 및 핀 LOW로 설정"""
        self.pwm.duty(0)
        self.pwm.deinit()
        # PWM 해제 후 핀을 명시적으로 LOW로 설정
        p = Pin(self.pin, Pin.OUT)
        p.value(0)


# ============================================================
# 테스트 함수들
# ============================================================

def test_step_speed(motor):
    """단계별 속도 테스트"""
    print("\n[Test 1] Step Speed Test")
    speeds = [0, 25, 50, 75, 100, 75, 50, 25, 0]
    
    for speed in speeds:
        print(f"  Speed: {speed}%")
        motor.set_speed(speed)
        safe_sleep(1)

def test_smooth_acceleration(motor):
    """부드러운 가속/감속 테스트"""
    print("\n[Test 2] Smooth Acceleration Test")
    
    print("  Accelerating: 0% -> 100%")
    motor.accelerate(100, duration_ms=2000)
    safe_sleep(1)
    
    print("  Decelerating: 100% -> 0%")
    motor.accelerate(0, duration_ms=2000)
    safe_sleep(1)

def test_pulse(motor, cycles=3):
    """펄스 테스트 (빠른 가속/감속)"""
    print(f"\n[Test 3] Pulse Test ({cycles} cycles)")
    
    for i in range(cycles):
        print(f"  Cycle {i+1}")
        motor.accelerate(80, duration_ms=500)
        motor.accelerate(20, duration_ms=500)
    
    motor.stop()
    safe_sleep(1)

def test_gradual_steps(motor):
    """점진적 단계 테스트"""
    print("\n[Test 4] Gradual Steps Test")
    
    # 10% 단위로 증가
    print("  Increasing...")
    for speed in range(0, 101, 10):
        print(f"    Speed: {speed}%")
        motor.set_speed(speed)
        safe_sleep(0.5)
    
    # 10% 단위로 감소
    print("  Decreasing...")
    for speed in range(100, -1, -10):
        print(f"    Speed: {speed}%")
        motor.set_speed(speed)
        safe_sleep(0.5)

def test_wave(motor, cycles=2):
    """파도 효과 (사인파 속도 변화)"""
    print(f"\n[Test 5] Wave Effect ({cycles} cycles)")
    import math
    
    for _ in range(cycles):
        for angle in range(0, 360, 10):
            # 사인파: 0~100% 범위
            speed = int((math.sin(math.radians(angle)) + 1) * 50)
            motor.set_speed(speed)
            safe_sleep_ms(50)
    
    motor.stop()


# ============================================================
# 메인 테스트 함수
# ============================================================

def test_motor():
    global _motor
    
    print("=" * 40)
    print("=== DC Motor Test ===")
    print(f"Motor Pin: GPIO {MOTOR_PIN}")
    print(f"PWM Frequency: {PWM_FREQ} Hz")
    print("=" * 40)
    
    try:
        # 모터 초기화
        _motor = DCMotor(MOTOR_PIN, PWM_FREQ)
        print("Motor initialized.")
        safe_sleep(1)
        
        while True:
            # 테스트 1: 단계별 속도
            test_step_speed(_motor)
            safe_sleep(1)
            
            # 테스트 2: 부드러운 가속/감속
            test_smooth_acceleration(_motor)
            safe_sleep(1)
            
            # 테스트 3: 펄스
            test_pulse(_motor, 3)
            safe_sleep(1)
            
            # 테스트 4: 점진적 단계
            test_gradual_steps(_motor)
            safe_sleep(1)
            
            # 테스트 5: 파도 효과
            test_wave(_motor, 2)
            safe_sleep(1)
            
            print("\n" + "-" * 40)
            print("All tests complete. Repeating...")
            print("-" * 40)
            safe_sleep(2)
            
    except KeyboardInterrupt:
        pass
    finally:
        # 어떤 상황에서도 모터 정지
        if _motor:
            try:
                _motor.pwm.duty(0)
                _motor.pwm.deinit()
            except:
                pass
            _motor = None
        # 핀을 명시적으로 LOW로 설정 (가장 확실한 방법)
        p = Pin(MOTOR_PIN, Pin.OUT)
        p.value(0)
        print("\nMotor stopped.")


if __name__ == "__main__":
    test_motor()
