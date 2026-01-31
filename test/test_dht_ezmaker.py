# 이지메이커 온습도 센서 테스트 코드
# 연결: D0 (GPIO 21)

from machine import Pin
import dht
import time

# 핀 설정 (D0 -> GPIO 21)
DHT_PIN = 21

def test_dht():
    print(f"Starting DHT Sensor Test on D0 (GPIO {DHT_PIN})...")
    
    try:
        # DHT 센서 객체 생성 (DHT11로 가정, DHT22인 경우 dht.DHT22 사용)
        # EZMaker 온습도 센서는 보통 DHT11을 사용합니다.
        sensor = dht.DHT11(Pin(DHT_PIN))
        # sensor = dht.DHT22(Pin(DHT_PIN)) # 만약 DHT22라면 주석 해제 후 위 라인 주석 처리
        
        print("Sensor initialized. Reading data every 2 seconds...")
        
        while True:
            try:
                # 측정 시작
                sensor.measure()
                
                # 값 읽기
                temp = sensor.temperature()
                hum = sensor.humidity()
                
                print(f"Temperature: {temp}°C, Humidity: {hum}%")
                
            except OSError as e:
                print("Failed to read sensor. (OSError)")
            
            time.sleep(2)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_dht()

