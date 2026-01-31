# 이지메이커 네오픽셀 LED 테스트 코드
# 지원: 1구, 7구(일자형), 12구(링형)
# 연결: D0(GPIO 21) - 변경 가능

from machine import Pin
import neopixel
import time

# ============================================================
# 초기 설정 - 여기서 네오픽셀 종류와 핀을 설정하세요
# ============================================================

# 네오픽셀 종류 선택 (1, 7, 12 중 선택)
NUM_LEDS = 1  # 1: 1구, 7: 7구(일자형), 12: 12구(링형)

# 연결 핀 설정 (DeepCo v2.0 + Shield v2.0 기준)
# D0=21, D1=47, D2=48, D3=38, D4=39
DATA_PIN = 21

# 밝기 설정 (0~255, 너무 밝으면 눈이 부심)
BRIGHTNESS = 50

# ============================================================
# 색상 정의
# ============================================================
def adjust_brightness(color, brightness=BRIGHTNESS):
    """밝기 조절"""
    r, g, b = color
    factor = brightness / 255
    return (int(r * factor), int(g * factor), int(b * factor))

# 기본 색상 (RGB)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
ORANGE = (255, 165, 0)
OFF = (0, 0, 0)

# ============================================================
# 네오픽셀 효과 함수들
# ============================================================

def clear(np):
    """모든 LED 끄기"""
    for i in range(len(np)):
        np[i] = OFF
    np.write()

def fill(np, color):
    """모든 LED를 같은 색으로"""
    color = adjust_brightness(color)
    for i in range(len(np)):
        np[i] = color
    np.write()

def set_pixel(np, index, color):
    """특정 LED 색상 설정"""
    if 0 <= index < len(np):
        np[index] = adjust_brightness(color)
        np.write()

def color_wipe(np, color, delay=100):
    """순차적으로 색상 채우기"""
    color = adjust_brightness(color)
    for i in range(len(np)):
        np[i] = color
        np.write()
        time.sleep_ms(delay)

def rainbow_cycle(np, wait=20, cycles=1):
    """무지개 효과 (전체 LED에 무지개 분포)"""
    def wheel(pos):
        """0~255 값을 RGB 색상으로 변환"""
        if pos < 85:
            return (pos * 3, 255 - pos * 3, 0)
        elif pos < 170:
            pos -= 85
            return (255 - pos * 3, 0, pos * 3)
        else:
            pos -= 170
            return (0, pos * 3, 255 - pos * 3)
    
    for _ in range(cycles):
        for j in range(256):
            for i in range(len(np)):
                pixel_index = (i * 256 // len(np)) + j
                np[i] = adjust_brightness(wheel(pixel_index & 255))
            np.write()
            time.sleep_ms(wait)

def chase(np, color, delay=100, cycles=3):
    """추적 효과 (하나씩 이동)"""
    color = adjust_brightness(color)
    for _ in range(cycles):
        for i in range(len(np)):
            clear(np)
            np[i] = color
            np.write()
            time.sleep_ms(delay)

def theater_chase(np, color, delay=100, cycles=10):
    """극장 조명 효과"""
    color = adjust_brightness(color)
    for _ in range(cycles):
        for q in range(3):
            for i in range(0, len(np), 3):
                if i + q < len(np):
                    np[i + q] = color
            np.write()
            time.sleep_ms(delay)
            for i in range(0, len(np), 3):
                if i + q < len(np):
                    np[i + q] = OFF
            np.write()

def breathing(np, color, cycles=3, steps=50):
    """숨쉬기 효과 (밝기 페이드)"""
    r, g, b = color
    for _ in range(cycles):
        # 밝아지기
        for step in range(steps):
            factor = step / steps * (BRIGHTNESS / 255)
            c = (int(r * factor), int(g * factor), int(b * factor))
            fill_raw(np, c)
            time.sleep_ms(20)
        # 어두워지기
        for step in range(steps, 0, -1):
            factor = step / steps * (BRIGHTNESS / 255)
            c = (int(r * factor), int(g * factor), int(b * factor))
            fill_raw(np, c)
            time.sleep_ms(20)

def fill_raw(np, color):
    """밝기 조절 없이 채우기 (내부용)"""
    for i in range(len(np)):
        np[i] = color
    np.write()

def running_lights(np, color, delay=50, cycles=5):
    """달리는 불빛 효과"""
    r, g, b = color
    for _ in range(cycles):
        for pos in range(len(np) * 2):
            for i in range(len(np)):
                # 사인파로 밝기 계산
                import math
                level = ((math.sin(i + pos) * 127 + 128) / 255) * (BRIGHTNESS / 255)
                np[i] = (int(r * level), int(g * level), int(b * level))
            np.write()
            time.sleep_ms(delay)

# ============================================================
# 메인 테스트 함수
# ============================================================

def test_neopixel():
    print(f"=== NeoPixel Test ===")
    print(f"LED Count: {NUM_LEDS}")
    print(f"Data Pin: GPIO {DATA_PIN}")
    print(f"Brightness: {BRIGHTNESS}/255")
    print("=" * 30)
    
    try:
        # 네오픽셀 초기화
        np = neopixel.NeoPixel(Pin(DATA_PIN), NUM_LEDS)
        print("NeoPixel initialized.")
        
        # 초기화 - 모든 LED 끄기
        clear(np)
        time.sleep_ms(500)
        
        while True:
            # 1. 단색 테스트
            print("1. Color Test: RED")
            fill(np, RED)
            time.sleep(1)
            
            print("   Color Test: GREEN")
            fill(np, GREEN)
            time.sleep(1)
            
            print("   Color Test: BLUE")
            fill(np, BLUE)
            time.sleep(1)
            
            print("   Color Test: WHITE")
            fill(np, WHITE)
            time.sleep(1)
            
            clear(np)
            time.sleep_ms(500)
            
            # 2. 순차 점등
            print("2. Color Wipe")
            color_wipe(np, RED, 100)
            color_wipe(np, GREEN, 100)
            color_wipe(np, BLUE, 100)
            clear(np)
            time.sleep_ms(500)
            
            # 3. 추적 효과
            print("3. Chase Effect")
            chase(np, CYAN, 80, 2)
            clear(np)
            time.sleep_ms(500)
            
            # 4. 극장 조명
            print("4. Theater Chase")
            theater_chase(np, MAGENTA, 80, 10)
            clear(np)
            time.sleep_ms(500)
            
            # 5. 무지개 효과
            print("5. Rainbow Cycle")
            rainbow_cycle(np, 10, 1)
            clear(np)
            time.sleep_ms(500)
            
            # 6. 숨쉬기 효과
            print("6. Breathing Effect")
            breathing(np, BLUE, 2, 30)
            clear(np)
            time.sleep_ms(500)
            
            print("-" * 30)
            print("Cycle complete. Repeating...")
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping...")
        clear(np)
        print("All LEDs off. Test stopped.")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_neopixel()

