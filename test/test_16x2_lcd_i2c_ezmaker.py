# 이지메이커 I2C LCD (16x2) 테스트 코드 - 라이브러리 사용
# 연결: SCL=D5(GPIO 40), SDA=D6(GPIO 41)
# I2C Address: 0x27 (Detected)

from machine import Pin, SoftI2C
import time
import sys

# lib 폴더의 i2c_lcd.py import
try:
    from lib.i2c_lcd import I2cLcd
except ImportError:
    print("Error: i2c_lcd.py not found in lib directory.")
    sys.exit()

# ============================================================
# 초기 설정 - 핀과 주소를 설정하세요
# ============================================================

# I2C 핀 설정 (DeepCo v2.0 + Shield v2.0 기준)
SCL_PIN = 40
SDA_PIN = 41
I2C_ADDR = 0x27   # 스캔된 주소
LCD_COLS = 16     # 가로 글자 수
LCD_ROWS = 2      # 세로 줄 수


# ============================================================
# 테스트 함수
# ============================================================

def test_lcd():
    print("=" * 40)
    print("=== I2C LCD (16x2) Test ===")
    print(f"SCL: GPIO {SCL_PIN}, SDA: GPIO {SDA_PIN}")
    print(f"Address: 0x{I2C_ADDR:02X}")
    print("=" * 40)
    
    try:
        # I2C 초기화
        i2c = SoftI2C(scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=100000)
        
        # 연결 확인
        scan_result = i2c.scan()
        if I2C_ADDR not in scan_result:
            print(f"Error: LCD not found at 0x{I2C_ADDR:02X}")
            print(f"Found devices: {[hex(x) for x in scan_result]}")
            return
            
        # LCD 초기화
        lcd = I2cLcd(i2c, I2C_ADDR, LCD_ROWS, LCD_COLS)
        print("LCD initialized.")
        
        while True:
            # 1. 기본 텍스트 출력
            print("1. Hello World")
            lcd.clear()
            lcd.putstr("Hello, World!")
            lcd.move_to(0, 1)
            lcd.putstr("EZMaker LCD Test")
            time.sleep(2)
            
            # 2. 백라이트 점멸
            print("2. Backlight Blink")
            for _ in range(3):
                lcd.backlight_off()
                time.sleep(0.5)
                lcd.backlight_on()
                time.sleep(0.5)
                
            # 3. 카운트다운
            print("3. Countdown")
            lcd.clear()
            lcd.putstr("Countdown:")
            for i in range(10, -1, -1):
                lcd.move_to(0, 1)
                lcd.putstr(f"{i}  ")  # 공백으로 이전 글자 지움
                time.sleep(0.5)
                
            # 4. 커서 이동 및 애니메이션
            print("4. Animation")
            lcd.clear()
            message = "DeepCoB EZMaker"
            for i in range(len(message)):
                lcd.move_to(i, 0)
                lcd.putstr(message[i])
                time.sleep(0.2)
                
            time.sleep(1)
            
            print("-" * 40)
            print("Cycle complete. Repeating...")
            
    except KeyboardInterrupt:
        print("\nStopping...")
        try:
            lcd.clear()
            lcd.backlight_off()
        except:
            pass
        print("Test stopped.")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_lcd()
