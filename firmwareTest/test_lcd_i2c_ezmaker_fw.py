"""
EZMaker I2C LCD (16x2 / 20x4) 펌웨어 통합 테스트 코드

- DeepCo 보드 + EZMaker 쉴드 조합에서 I2C LCD(16x2 또는 20x4)를
  SCL=D5(GPIO 40), SDA=D6(GPIO 41)에 연결했을 때,
  bleIoT 에 새로 추가된 LCD 핸들러와 I2cLcd 초기화가 정상 동작하는지 확인하기 위한 스크립트입니다.

사용 방법 (펌웨어 단독 테스트 / REPL 기준):
1. 최신 bleIoT/bleBaseIoT/i2c_lcd 를 mpy 로 컴파일하여 보드의 /lib 에 배포합니다.
2. 이 파일을 보드 루트(또는 /firmwareTest)에 업로드합니다.
3. 보드가 정상 부팅되어 BLE IoT 모드(bleIoT)가 올라온 상태에서, REPL 에 아래 순서로 입력합니다.
   >>> import test_lcd_i2c_ezmaker_fw
   >>> test_lcd_i2c_ezmaker_fw.main()
4. 동작:
   - LCD 타입(16x2 또는 20x4)을 선택하여 초기화합니다.
   - 화면 클리어 / 백라이트 ON/OFF / 여러 줄 텍스트 출력 명령을
     bleIoT.lcd_handler 를 통해 전송하여 실제 LCD 동작을 확인합니다.

주의:
- Thonny 에디터 창의 "Run" 버튼으로 실행하면 soft reboot 가 걸리면서 main/bleIoT 가 다시 올라가므로,
  이 테스트 파일은 반드시 REPL 에서 import 후 main() 을 호출하는 방식으로만 실행합니다.
"""

import time
import bleIoT  # 보드 /lib 에 설치된 bleIoT.mpy 를 직접 사용


# EZMaker I2C LCD 기본 핀 (DeepCo v2.0 + EZMaker Shield v2.0 기준)
DEFAULT_SCL_PIN = 40  # D5
DEFAULT_SDA_PIN = 41  # D6

# 테스트할 LCD 타입 선택: "16X2" 또는 "20X4"
DEFAULT_LCD_TYPE = "16X2"


def lcd_cmd(cmd: str):
    """
    bleIoT.lcd_handler 를 직접 호출하는 헬퍼 함수입니다.

    예)
      lcd_cmd("LCD:CLEAR")
      lcd_cmd("LCD:BACKLIGHT:ON")
      lcd_cmd("LCD:PRINT:0,0:Hello")
    """
    try:
        from bleIoT import lcd_handler  # type: ignore
    except ImportError:
        print("[LCD TEST] lcd_handler 를 가져올 수 없습니다. bleIoT 버전을 확인하세요.")
        return

    try:
        lcd_handler(None, cmd)
    except Exception as e:
        print(f"[LCD TEST] 명령 처리 중 오류: {cmd} -> {e}")


def init_lcd(lcd_type: str = DEFAULT_LCD_TYPE):
    """
    LCD 초기화 (LCD:INIT:타입:SCL,SDA 명령 사용)

    lcd_type: "16X2" 또는 "20X4"
    """
    cmd = f"LCD:INIT:{lcd_type}:{DEFAULT_SCL_PIN},{DEFAULT_SDA_PIN}"
    print(f"[LCD TEST] 초기화 명령 전송: {cmd}")
    lcd_cmd(cmd)

    # bleIoT 전역 lcd 객체가 생성되었는지 간단히 확인
    lcd_obj = getattr(bleIoT, "lcd", None)
    if lcd_obj is None:
        print("[LCD TEST] bleIoT.lcd 가 None 입니다. I2C 연결 또는 주소를 확인하세요.")
    else:
        print(f"[LCD TEST] bleIoT.lcd 가 준비되었습니다. 타입={lcd_type}")


def simple_display_sequence():
    """
    기본적인 LCD 동작을 순서대로 테스트합니다.
    - 화면 클리어
    - 한/두 줄 텍스트 출력
    - 백라이트 깜빡임
    - 카운트다운 출력
    """
    print("[LCD TEST] 화면 클리어")
    lcd_cmd("LCD:CLEAR")
    time.sleep(0.5)

    print("[LCD TEST] 기본 메시지 출력")
    lcd_cmd("LCD:PRINT:0,0:EZMaker I2C LCD Test")
    # 두 번째 줄은 LCD 타입에 따라 다르게 사용
    if DEFAULT_LCD_TYPE == "16X2":
        lcd_cmd("LCD:PRINT:1,0:Type: 16x2")
    else:
        # 20x4 인 경우 첫 두 줄만 간단히 사용
        lcd_cmd("LCD:PRINT:1,0:Type: 20x4")
        lcd_cmd("LCD:PRINT:2,0:Line 3 Example")
        lcd_cmd("LCD:PRINT:3,0:Line 4 Example")
    time.sleep(2.0)

    print("[LCD TEST] 백라이트 깜빡임 테스트")
    for i in range(3):
        print(f"[LCD TEST] Backlight OFF ({i+1}/3)")
        lcd_cmd("LCD:BACKLIGHT:OFF")
        time.sleep(0.5)
        print(f"[LCD TEST] Backlight ON ({i+1}/3)")
        lcd_cmd("LCD:BACKLIGHT:ON")
        time.sleep(0.5)

    print("[LCD TEST] 카운트다운 출력")
    lcd_cmd("LCD:CLEAR")
    lcd_cmd("LCD:PRINT:0,0:Countdown:")
    for i in range(10, -1, -1):
        # 두 번째 줄 첫 칸에 카운트 출력
        lcd_cmd(f"LCD:PRINT:1,0:Count: {i:2d}   ")
        time.sleep(0.5)


def main():
    print("==========================================")
    print("=== EZMaker I2C LCD 펌웨어 통합 테스트 ===")
    print("==========================================")
    print(f"[LCD TEST] LCD 타입: {DEFAULT_LCD_TYPE}")
    print(f"[LCD TEST] SCL = GPIO {DEFAULT_SCL_PIN}, SDA = GPIO {DEFAULT_SDA_PIN}")
    print("")

    # 1) LCD 초기화
    init_lcd(DEFAULT_LCD_TYPE)

    # 2) 간단한 디스플레이 시퀀스 실행
    simple_display_sequence()

    print("[LCD TEST] 테스트가 완료되었습니다.")
    print("[LCD TEST] 이제 BLE 를 통해 동일한 LCD 명령(LCD:INIT/CLEAR/BACKLIGHT/PRINT)을 보내 전체 경로를 검증할 수 있습니다.")


if __name__ == "__main__":
    main()


