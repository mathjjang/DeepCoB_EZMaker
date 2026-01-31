# 이지메이커 서보모터 테스트 코드
# 연결: D1 (GPIO 47)

from machine import Pin, PWM
import time

# 핀 설정 (D1 -> GPIO 47)
SERVO_PIN = 47

def test_servo():
    print(f"Starting Servo Motor Test on D1 (GPIO {SERVO_PIN})...")
    
    try:
        # 서보모터는 PWM을 사용합니다. (50Hz)
        servo = PWM(Pin(SERVO_PIN))
        servo.freq(50)
        
        print("Servo initialized. Moving 0 -> 90 -> 180 degrees...")
        
        while True:
            # 0도 (Duty cycle 약 2.5% -> 1638/65535)
            # SG90 기준: 0.5ms ~ 2.4ms (2.5% ~ 12%)
            # 정확한 값은 모터마다 다를 수 있으므로 일반적인 값 사용
            
            # 0도
            print("Angle: 0")
            servo.duty_u16(1638) 
            time.sleep(1)
            
            # 90도
            print("Angle: 90")
            servo.duty_u16(4915)
            time.sleep(1)
            
            # 180도
            print("Angle: 180")
            servo.duty_u16(8192)
            time.sleep(1)
            
            # 다시 90도
            print("Angle: 90")
            servo.duty_u16(4915)
            time.sleep(1)
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # 종료 시 PWM 해제
        try:
            servo.deinit()
        except:
            pass
        print("Servo test finished.")

if __name__ == "__main__":
    test_servo()

