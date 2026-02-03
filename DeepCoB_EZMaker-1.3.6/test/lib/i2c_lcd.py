"""
I2C LCD Library for MicroPython
================================

I2C 방식 캐릭터 LCD (16x2, 20x4 등) MicroPython 드라이버 라이브러리

주요 기능:
- I2C 통신을 통한 LCD 제어
- 텍스트 출력, 커서 이동
- 백라이트 제어
- 화면 클리어, 홈 등 기본 기능

지원 LCD:
- 16x2 (16열 x 2행)
- 20x4 (20열 x 4행)
- HD44780 호환 LCD + PCF8574 I2C 확장 모듈

사용 예:
    from machine import Pin, SoftI2C
    from i2c_lcd import I2cLcd
    
    i2c = SoftI2C(scl=Pin(40), sda=Pin(41), freq=100000)
    lcd = I2cLcd(i2c, 0x27, num_lines=2, num_columns=16)
    lcd.putstr("Hello, World!")
    lcd.move_to(0, 1)
    lcd.putstr("Line 2")

연결:
- SCL (D5) -> GPIO 40
- SDA (D6) -> GPIO 41
- I2C Address: 0x27 (또는 0x3F)
"""

from machine import SoftI2C
import time

class I2cLcd:
    """I2C LCD 1602/2004 드라이버"""
    
    # 명령어
    LCD_CLEARDISPLAY = 0x01
    LCD_RETURNHOME = 0x02
    LCD_ENTRYMODESET = 0x04
    LCD_DISPLAYCONTROL = 0x08
    LCD_CURSORSHIFT = 0x10
    LCD_FUNCTIONSET = 0x20
    LCD_SETCGRAMADDR = 0x40
    LCD_SETDDRAMADDR = 0x80

    # 플래그
    LCD_ENTRYRIGHT = 0x00
    LCD_ENTRYLEFT = 0x02
    LCD_ENTRYSHIFTINCREMENT = 0x01
    LCD_ENTRYSHIFTDECREMENT = 0x00
    LCD_DISPLAYON = 0x04
    LCD_DISPLAYOFF = 0x00
    LCD_CURSORON = 0x02
    LCD_CURSOROFF = 0x00
    LCD_BLINKON = 0x01
    LCD_BLINKOFF = 0x00
    LCD_DISPLAYMOVE = 0x08
    LCD_CURSORMOVE = 0x00
    LCD_MOVERIGHT = 0x04
    LCD_MOVELEFT = 0x00
    LCD_8BITMODE = 0x10
    LCD_4BITMODE = 0x00
    LCD_2LINE = 0x08
    LCD_1LINE = 0x00
    LCD_5x10DOTS = 0x04
    LCD_5x8DOTS = 0x00
    LCD_BACKLIGHT = 0x08
    LCD_NOBACKLIGHT = 0x00

    def __init__(self, i2c, i2c_addr, num_lines, num_columns):
        self.i2c = i2c
        self.i2c_addr = i2c_addr
        self.num_lines = num_lines
        if self.num_lines > 1:
            self.displayfunction = self.LCD_4BITMODE | self.LCD_2LINE | self.LCD_5x8DOTS
        else:
            self.displayfunction = self.LCD_4BITMODE | self.LCD_1LINE | self.LCD_5x8DOTS
        if self.num_lines == 1:
            self.num_lines = 0
        self.num_columns = num_columns
        self.backlight_val = self.LCD_BACKLIGHT
        
        time.sleep_ms(20)
        self.expanderWrite(0)
        time.sleep_ms(20)
        
        self.write4bits(0x03 << 4)
        time.sleep_ms(5)
        self.write4bits(0x03 << 4)
        time.sleep_ms(5)
        self.write4bits(0x03 << 4)
        time.sleep_ms(5)
        self.write4bits(0x02 << 4)

        self.command(self.LCD_FUNCTIONSET | self.displayfunction)
        self.displaycontrol = self.LCD_DISPLAYON | self.LCD_CURSOROFF | self.LCD_BLINKOFF
        self.display()
        self.clear()
        self.mode = self.LCD_ENTRYLEFT | self.LCD_ENTRYSHIFTDECREMENT
        self.command(self.LCD_ENTRYMODESET | self.mode)
        self.home()

    def expanderWrite(self, _data):
        # 값을 0-255 범위로 제한
        val = (_data | self.backlight_val) & 0xFF
        self.i2c.writeto(self.i2c_addr, bytes([val]))

    def write4bits(self, value):
        self.expanderWrite(value)
        self.pulseEnable(value)

    def pulseEnable(self, _data):
        self.expanderWrite(_data | 0x04) # En high
        time.sleep_us(1)
        self.expanderWrite(_data & ~0x04) # En low
        time.sleep_us(50)

    def command(self, value):
        self.write4bits((value & 0xF0))
        self.write4bits((value << 4) & 0xF0)

    def write(self, value):
        self.write4bits((value & 0xF0) | 0x01) # Rs high
        self.write4bits((value << 4) | 0x01)   # Rs high

    def putstr(self, string):
        for char in string:
            self.write(ord(char))

    def clear(self):
        self.command(self.LCD_CLEARDISPLAY)
        time.sleep_ms(2)

    def home(self):
        self.command(self.LCD_RETURNHOME)
        time.sleep_ms(2)

    def display(self):
        self.displaycontrol |= self.LCD_DISPLAYON
        self.command(self.LCD_DISPLAYCONTROL | self.displaycontrol)

    def no_display(self):
        self.displaycontrol &= ~self.LCD_DISPLAYON
        self.command(self.LCD_DISPLAYCONTROL | self.displaycontrol)

    def backlight_on(self):
        self.backlight_val = self.LCD_BACKLIGHT
        self.expanderWrite(0)

    def backlight_off(self):
        self.backlight_val = self.LCD_NOBACKLIGHT
        self.expanderWrite(0)

    def move_to(self, col, row):
        col = max(0, min(col, self.num_columns - 1))
        row = max(0, min(row, self.num_lines - 1))
        offsets = [0x00, 0x40, 0x14, 0x54]
        self.command(self.LCD_SETDDRAMADDR | (col + offsets[row]))

