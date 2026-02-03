# 이지메이커 무게센서 (HX711) 테스트 코드 - 라이브러리 사용
# 연결: DOUT(DT), SCK(CLK)
# 쉴드 연결: RXD(D10)=GPIO 14, TXD(D11)=GPIO 42

import time
import sys
from machine import Pin
# lib 폴더의 hx711.py import
try:
    from lib import hx711
except ImportError:
    print("Error: hx711.py not found in lib directory.")
    sys.exit()

# 핀 설정
DOUT_PIN = 42  #14  # RXD
SCK_PIN = 14  #42   # TXD

def test_hx711_lib():
    print("=" * 40)
    print("=== HX711 Weight Sensor Test (Library) ===")
    print(f"DOUT (DT): GPIO {DOUT_PIN}")
    print(f"SCK (CLK): GPIO {SCK_PIN}")
    print("=" * 40)
    
    try:
        # 1. 초기화
        hx = hx711.HX711(DOUT_PIN, SCK_PIN)
        
        # 2. 연결 확인 (Ready 체크 with Timeout)
        print("Checking sensor connection...")
        if hx.wait_ready_timeout(timeout_ms=2000):
            print("Sensor is READY.")
        else:
            print("Error: Sensor NOT Ready (Timeout).")
            print("Check wiring or pins.")
            return

        # Raw 값 확인 (디버깅용)
        print("Reading initial Raw values...")
        for _ in range(5):
            raw = hx.read()
            print(f"Raw: {raw}")
            time.sleep(0.1)

        # 3. 영점 조정 (Tare)
        print("Taring... (Please remove weight)")
        time.sleep(1)
        hx.tare()
        print(f"Tare complete. Offset: {hx.get_offset()}")
        
        # 4. 스케일 설정
        # 사용자가 직접 보정해야 함.
        # 예: 100g을 올렸는데 Raw 값이 40000 증가했다면 Scale = 40000 / 100 = 400
        # 현재는 임의의 값 사용
        hx.set_scale(400.0) 
        
        print("Ready. Place weight.")
        print("-" * 40)
        
        while True:
            # 무게 및 Raw 값 동시 출력
            raw = hx.read()
            weight = hx.get_units(1) # 1회 읽기로 빠른 반응 확인
            
            # get_units는 내부적으로 read_average -> read를 호출하므로
            # raw와 weight가 정확히 같은 시점의 값은 아니지만 비슷함.
            # 정확한 비교를 위해서는:
            # val = hx.read()
            # weight = (val - hx.get_offset()) / hx.get_scale()
            
            print(f"Weight: {weight:>8.2f} g  (Raw: {raw})")
            
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\nTest stopped.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("Cleaning up...")
        if 'hx' in locals():
            hx.power_down()
            hx.p_pd_sck.value(0) # Ensure SCK is low
            hx.p_dout.init(Pin.IN) # Reset DOUT to input
        
        # 부저가 연결되었을 수 있는 핀(D10/D11)이나 시스템 핀 정리
        # (GPIO 14, 42는 무게 센서에 사용 중이므로 value(0)이면 안전)
        try:
            # 시스템 부저 핀 (만약 있다면, 예: 42번)
            Pin(42, Pin.OUT).value(0)
            #print('aa')
        except:
            pass

if __name__ == "__main__":
    test_hx711_lib()
