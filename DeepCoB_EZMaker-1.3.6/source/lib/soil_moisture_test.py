# soil_moisture_test.py
# 토양수분센서 테스트 코드

import machine
import time

class SoilMoistureSensor:
    """
    토양수분센서 클래스
    
    토양수분센서는 일반적으로 아날로그 출력을 제공합니다:
    - 수분이 많을 때: 낮은 전압 (0V에 가까움)
    - 수분이 적을 때: 높은 전압 (3.3V에 가까움)
    """
    
    def __init__(self, adc_pin, dry_value=4095, wet_value=1500):
        """
        토양수분센서 초기화
        
        Args:
            adc_pin (int): ADC 핀 번호 (ESP32-S3의 경우 1-20 중 선택)
            dry_value (int): 건조한 상태의 ADC 값 (기본값: 4095, 보정 필요)
            wet_value (int): 젖은 상태의 ADC 값 (기본값: 1500, 보정 필요)
        """
        self.adc_pin = adc_pin
        self.dry_value = dry_value
        self.wet_value = wet_value
        
        # ADC 객체 생성
        self.adc = machine.ADC(machine.Pin(adc_pin))
        self.adc.atten(machine.ADC.ATTN_11DB)  # 3.3V 측정 범위
        
        print(f"토양수분센서 초기화 완료 - ADC 핀: {adc_pin}")
        print(f"건조값: {dry_value}, 습윤값: {wet_value}")
    
    def read_raw(self):
        """
        원시 ADC 값 읽기
        
        Returns:
            int: ADC 원시 값 (0-4095)
        """
        return self.adc.read()
    
    def read_voltage(self):
        """
        전압 값 읽기
        
        Returns:
            float: 전압 (V)
        """
        raw_value = self.read_raw()
        # ESP32 ADC는 12비트 (0-4095), 참조 전압 3.3V
        voltage = (raw_value / 4095) * 3.3
        return voltage
    
    def read_moisture_percentage(self):
        """
        수분 백분율 읽기
        
        Returns:
            float: 수분 백분율 (0-100%)
        """
        raw_value = self.read_raw()
        
        # 값 범위 제한
        if raw_value >= self.dry_value:
            return 0.0  # 완전 건조
        elif raw_value <= self.wet_value:
            return 100.0  # 완전 습윤
        
        # 선형 보간으로 백분율 계산
        moisture_percent = ((self.dry_value - raw_value) / (self.dry_value - self.wet_value)) * 100
        return max(0.0, min(100.0, moisture_percent))
    
    def calibrate_dry(self):
        """
        건조 상태 보정
        현재 센서값을 건조 상태로 설정
        """
        self.dry_value = self.read_raw()
        print(f"건조값이 {self.dry_value}로 설정되었습니다")
        return self.dry_value
    
    def calibrate_wet(self):
        """
        습윤 상태 보정
        현재 센서값을 습윤 상태로 설정
        """
        self.wet_value = self.read_raw()
        print(f"습윤값이 {self.wet_value}로 설정되었습니다")
        return self.wet_value
    
    def get_status(self):
        """
        센서 상태 정보 반환
        
        Returns:
            dict: 센서 상태 정보
        """
        raw = self.read_raw()
        voltage = self.read_voltage()
        moisture = self.read_moisture_percentage()
        
        return {
            'raw': raw,
            'voltage': voltage,
            'moisture_percent': moisture,
            'dry_value': self.dry_value,
            'wet_value': self.wet_value
        }

def test_soil_moisture_sensor(pin=1, duration=30):
    """
    토양수분센서 테스트 함수
    
    Args:
        pin (int): ADC 핀 번호
        duration (int): 테스트 지속 시간 (초)
    """
    print("=== 토양수분센서 테스트 시작 ===")
    print(f"ADC 핀: {pin}")
    print(f"테스트 시간: {duration}초")
    print()
    
    try:
        # 센서 초기화
        sensor = SoilMoistureSensor(adc_pin=pin)
        
        print("초기 센서 값:")
        status = sensor.get_status()
        print(f"  원시값: {status['raw']}")
        print(f"  전압: {status['voltage']:.2f}V")
        print(f"  수분율: {status['moisture_percent']:.1f}%")
        print()
        
        print("보정 안내:")
        print("1. 센서를 완전히 건조한 상태에 두고 'calibrate_dry()' 호출")
        print("2. 센서를 물에 담그고 'calibrate_wet()' 호출")
        print()
        
        print("연속 측정 시작 (Ctrl+C로 중지):")
        print("시간\t원시값\t전압\t수분율\t상태")
        print("-" * 50)
        
        start_time = time.time()
        while True:
            current_time = time.time() - start_time
            
            # 지속 시간 체크
            if current_time >= duration:
                print(f"\n{duration}초 테스트 완료!")
                break
            
            # 센서 읽기
            status = sensor.get_status()
            raw = status['raw']
            voltage = status['voltage']
            moisture = status['moisture_percent']
            
            # 상태 판단
            if moisture >= 70:
                status_text = "매우습함"
            elif moisture >= 40:
                status_text = "적당함"
            elif moisture >= 20:
                status_text = "건조함"
            else:
                status_text = "매우건조"
            
            # 결과 출력
            print(f"{current_time:5.1f}s\t{raw:4d}\t{voltage:4.2f}V\t{moisture:5.1f}%\t{status_text}")
            
            time.sleep(1)  # 1초 간격
            
    except KeyboardInterrupt:
        print("\n사용자에 의해 테스트가 중단되었습니다.")
    except Exception as e:
        print(f"오류 발생: {e}")
    
    print("=== 토양수분센서 테스트 종료 ===")

def calibration_helper(pin=1):
    """
    센서 보정 도우미 함수
    
    Args:
        pin (int): ADC 핀 번호
    """
    print("=== 토양수분센서 보정 ===")
    
    try:
        sensor = SoilMoistureSensor(adc_pin=pin)
        
        print("\n1단계: 건조 상태 보정")
        input("센서를 완전히 건조한 상태에 두고 Enter를 누르세요...")
        dry_value = sensor.calibrate_dry()
        
        print("\n2단계: 습윤 상태 보정")
        input("센서를 물에 담그거나 젖은 흙에 넣고 Enter를 누르세요...")
        wet_value = sensor.calibrate_wet()
        
        print(f"\n보정 완료!")
        print(f"건조값: {dry_value}")
        print(f"습윤값: {wet_value}")
        print(f"\n이 값들을 코드에서 기본값으로 사용하세요:")
        print(f"sensor = SoilMoistureSensor(adc_pin={pin}, dry_value={dry_value}, wet_value={wet_value})")
        
        # 보정 후 테스트
        print("\n보정 후 테스트:")
        for i in range(5):
            status = sensor.get_status()
            print(f"  {i+1}회: 원시값={status['raw']}, 수분율={status['moisture_percent']:.1f}%")
            time.sleep(1)
            
    except Exception as e:
        print(f"보정 중 오류 발생: {e}")

# 메인 실행 부분
if __name__ == "__main__":
    # 사용 예시:
    # 1. 기본 테스트 (핀 1번 사용, 30초 동안)
    # test_soil_moisture_sensor(pin=1, duration=30)
    
    # 2. 센서 보정
    # calibration_helper(pin=1)
    
    # 3. 간단한 한번 읽기
    # sensor = SoilMoistureSensor(adc_pin=1)
    # status = sensor.get_status()
    # print(f"수분율: {status['moisture_percent']:.1f}%")
    
    print("토양수분센서 테스트 모듈이 로드되었습니다.")
    print("\n사용 방법:")
    print("1. test_soil_moisture_sensor(pin=1, duration=30)  # 기본 테스트")
    print("2. calibration_helper(pin=1)                     # 센서 보정")
    print("3. sensor = SoilMoistureSensor(adc_pin=1)        # 센서 객체 생성") 