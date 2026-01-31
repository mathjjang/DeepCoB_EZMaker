# YL69SoilMoisture.py
# YL-69 토양수분센서 간단 라이브러리 (조도센서 + 먼지센서 스타일)

import machine
import time

class YL69SoilMoisture:
    """
    YL-69 토양수분센서 클래스
    
    조도센서처럼 간단하면서 먼지센서처럼 기능적인 라이브러리
    """
    
    # YL-69 기본 보정값 (경험적 값)
    DEFAULT_DRY = 1750  #3800
    DEFAULT_WET = 500   #1200
    
    def __init__(self, adc_pin, dry_value=None, wet_value=None):
        """
        센서 초기화
        
        Args:
            adc_pin (int): ADC 핀 번호
            dry_value (int): 건조값 (None이면 기본값)
            wet_value (int): 습윤값 (None이면 기본값)
        """
        self.adc_pin = adc_pin
        self.dry_value = dry_value or self.DEFAULT_DRY
        self.wet_value = wet_value or self.DEFAULT_WET
        
        # ADC 초기화 (조도센서 방식)
        self.adc = machine.ADC(machine.Pin(adc_pin))
        self.adc.atten(machine.ADC.ATTN_11DB)
        self.adc.width(machine.ADC.WIDTH_12BIT)
        
        # 상태 변수 (먼지센서 방식)
        self.last_reading = None
        self.readings_count = 0
        
    def read_raw(self):
        """원시 ADC 값 읽기"""
        return self.adc.read()
    
    def read_voltage(self):
        """전압 읽기"""
        return (self.read_raw() / 4095) * 3.3
    
    def read_moisture(self, samples=1):
        """
        수분 백분율 읽기
        
        Args:
            samples (int): 평균용 샘플 수
            
        Returns:
            float: 수분 백분율 (0-100%)
        """
        # 여러 샘플 평균 (먼지센서 방식)
        if samples > 1:
            total = 0
            for _ in range(samples):
                total += self.read_raw()
                time.sleep_ms(50)
            raw = total / samples
        else:
            raw = self.read_raw()
        
        # YL-69 특성: 높은 값 = 건조, 낮은 값 = 습윤
        if raw >= self.dry_value:
            moisture = 0.0
        elif raw <= self.wet_value:
            moisture = 100.0
        else:
            moisture = ((self.dry_value - raw) / (self.dry_value - self.wet_value)) * 100
            moisture = max(0.0, min(100.0, moisture))
        
        # 상태 업데이트
        self.last_reading = moisture
        self.readings_count += 1
        
        return round(moisture, 1)
    

    
    def calibrate_dry(self, samples=5):
        """건조 상태 보정"""
        print("건조 상태 보정 중...")
        total = 0
        for i in range(samples):
            reading = self.read_raw()
            total += reading
            print(f"  샘플 {i+1}/{samples}: {reading}")
            time.sleep(0.5)
        
        self.dry_value = int(total / samples)
        print(f"건조값: {self.dry_value}")
        return self.dry_value
    
    def calibrate_wet(self, samples=5):
        """습윤 상태 보정"""
        print("습윤 상태 보정 중...")
        total = 0
        for i in range(samples):
            reading = self.read_raw()
            total += reading
            print(f"  샘플 {i+1}/{samples}: {reading}")
            time.sleep(0.5)
        
        self.wet_value = int(total / samples)
        print(f"습윤값: {self.wet_value}")
        return self.wet_value
    




if __name__ == "__main__":
    import time
    
    print("YL-69 토양수분센서 데이터 출력")
    print("Raw\tVoltage\tMoisture")
    print("-" * 30)
    
    sensor = YL69SoilMoisture(2)
    
    while True:
        try:
            raw = sensor.read_raw()
            voltage = sensor.read_voltage()
            moisture = sensor.read_moisture()
            
            print(f"{raw:4d}\t{voltage:.3f}V\t{moisture:5.1f}%")
            time.sleep(1)
            
        except KeyboardInterrupt:
            print("\n프로그램 종료")
            break
        except Exception as e:
            print(f"오류: {e}")
            time.sleep(1) 