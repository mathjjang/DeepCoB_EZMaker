# MQ2GasSensor.py
# MQ-2 가연성 가스센서 라이브러리

import machine
import time
import math

class MQ2GasSensor:
    """
    MQ-2 가연성 가스센서 클래스
    
    감지 가능한 가스: LPG, 프로판, 메탄, 알코올, 연기, 수소 등
    """
    
    # MQ-2 기본 설정값
    RL_VALUE = 5.0          # 로드 저항 (kΩ)
    RO_CLEAN_AIR = 9.83     # 깨끗한 공기에서의 센서 저항 (kΩ)
    
    # 가스별 곡선 상수 (Rs/Ro = a * ppm^b)
    GAS_LPG = {"a": 2.3, "b": -0.24}
    GAS_METHANE = {"a": 5.5, "b": -0.35}
    GAS_SMOKE = {"a": 3.6, "b": -0.30}
    GAS_HYDROGEN = {"a": 1.8, "b": -0.21}
    GAS_ALCOHOL = {"a": 0.75, "b": -0.42}
    
    # 경보 임계값 (ppm)
    ALARM_THRESHOLD = 300   # 일반적인 경보 수준
    
    def __init__(self, adc_pin, ro_value=None):
        """
        MQ-2 센서 초기화
        
        Args:
            adc_pin (int): ADC 핀 번호
            ro_value (float): 깨끗한 공기에서의 센서 저항값 (None이면 기본값)
        """
        self.adc_pin = adc_pin
        self.ro_value = ro_value or self.RO_CLEAN_AIR
        
        # ADC 초기화
        self.adc = machine.ADC(machine.Pin(adc_pin))
        self.adc.atten(machine.ADC.ATTN_11DB)
        self.adc.width(machine.ADC.WIDTH_12BIT)
        
        # 상태 변수
        self.last_reading = None
        self.readings_count = 0
        self.warmed_up = False
        self.warmup_start = time.time()
        
        print(f"MQ-2 센서 초기화 완료 (핀: {adc_pin})")
        print("⏰ 센서 예열 중... (20초 권장)")
    
    def read_raw(self):
        """원시 ADC 값 읽기"""
        return self.adc.read()
    
    def read_voltage(self):
        """전압 읽기"""
        return (self.read_raw() / 4095) * 3.3
    
    def read_resistance(self):
        """
        센서 저항값 계산 (Rs)
        
        Returns:
            float: 센서 저항값 (kΩ)
        """
        voltage = self.read_voltage()
        
        # 전압이 너무 낮으면 최대 저항으로 처리
        if voltage <= 0.1:
            return float('inf')
        
        # Rs 계산: Rs = (Vc - Vout) * RL / Vout
        # Vc = 3.3V (공급전압)
        rs = ((3.3 - voltage) * self.RL_VALUE) / voltage
        return rs
    
    def read_ratio(self):
        """
        Rs/Ro 비율 계산
        
        Returns:
            float: Rs/Ro 비율
        """
        rs = self.read_resistance()
        if rs == float('inf'):
            return float('inf')
        
        ratio = rs / self.ro_value
        self.last_reading = ratio
        self.readings_count += 1
        
        return ratio
    
    def read_ppm(self, gas_type="LPG", samples=1):
        """
        가스 농도 측정 (ppm)
        
        Args:
            gas_type (str): 가스 종류 ("LPG", "METHANE", "SMOKE", "HYDROGEN", "ALCOHOL")
            samples (int): 평균용 샘플 수
            
        Returns:
            float: 가스 농도 (ppm)
        """
        # 여러 샘플 평균
        if samples > 1:
            total_ratio = 0
            for _ in range(samples):
                total_ratio += self.read_ratio()
                time.sleep_ms(100)
            avg_ratio = total_ratio / samples
        else:
            avg_ratio = self.read_ratio()
        
        # 가스별 상수 선택
        gas_constants = {
            "LPG": self.GAS_LPG,
            "METHANE": self.GAS_METHANE,
            "SMOKE": self.GAS_SMOKE,
            "HYDROGEN": self.GAS_HYDROGEN,
            "ALCOHOL": self.GAS_ALCOHOL
        }
        
        if gas_type.upper() not in gas_constants:
            gas_type = "LPG"  # 기본값
        
        constants = gas_constants[gas_type.upper()]
        
        # ppm 계산: ppm = (Rs/Ro / a) ^ (1/b)
        if avg_ratio == float('inf') or avg_ratio <= 0:
            return 0.0
        
        try:
            ppm = math.pow(avg_ratio / constants["a"], 1.0 / constants["b"])
            return max(0.0, ppm)
        except:
            return 0.0
    
    def get_status(self, gas_type="LPG"):
        """
        센서 상태 반환
        
        Args:
            gas_type (str): 측정할 가스 종류
            
        Returns:
            dict: 센서 상태
        """
        raw = self.read_raw()
        voltage = self.read_voltage()
        resistance = self.read_resistance()
        ratio = self.read_ratio()
        ppm = self.read_ppm(gas_type)
        
        # 예열 상태 확인
        elapsed = time.time() - self.warmup_start
        self.warmed_up = elapsed >= 20  # 20초 후 예열 완료
        
        # 위험도 판정
        if ppm >= self.ALARM_THRESHOLD:
            danger_level = "위험"
        elif ppm >= self.ALARM_THRESHOLD * 0.5:
            danger_level = "주의"
        elif ppm >= self.ALARM_THRESHOLD * 0.2:
            danger_level = "약간검출"
        else:
            danger_level = "안전"
        
        return {
            "gas_type": gas_type,
            "ppm": round(ppm, 1),
            "voltage": round(voltage, 3),
            "resistance": round(resistance, 2) if resistance != float('inf') else "inf",
            "ratio": round(ratio, 3) if ratio != float('inf') else "inf",
            "raw": raw,
            "danger_level": danger_level,
            "warmed_up": self.warmed_up,
            "warmup_time": round(elapsed, 1),
            "pin": self.adc_pin,
            "readings_count": self.readings_count
        }
    
    def calibrate_ro(self, samples=50):
        """
        깨끗한 공기에서 Ro 값 보정
        
        Args:
            samples (int): 보정용 샘플 수
            
        Returns:
            float: 보정된 Ro 값
        """
        print("Ro 보정 중... (깨끗한 공기에서 실행하세요)")
        
        total_rs = 0
        valid_samples = 0
        
        for i in range(samples):
            rs = self.read_resistance()
            if rs != float('inf'):
                total_rs += rs
                valid_samples += 1
            
            if (i + 1) % 10 == 0:
                print(f"진행률: {i+1}/{samples}")
            
            time.sleep(0.2)
        
        if valid_samples > 0:
            self.ro_value = total_rs / valid_samples
            print(f"Ro 보정 완료: {self.ro_value:.2f} kΩ")
        else:
            print("보정 실패: 유효한 샘플이 없습니다")
        
        return self.ro_value
    
    def is_gas_detected(self, threshold_ppm=100, gas_type="LPG"):
        """
        가스 검출 여부 확인
        
        Args:
            threshold_ppm (float): 검출 임계값 (ppm)
            gas_type (str): 가스 종류
            
        Returns:
            bool: 가스 검출되면 True
        """
        ppm = self.read_ppm(gas_type)
        return ppm >= threshold_ppm
    
    def is_dangerous(self, gas_type="LPG"):
        """
        위험 수준 확인
        
        Returns:
            bool: 위험 수준이면 True
        """
        ppm = self.read_ppm(gas_type)
        return ppm >= self.ALARM_THRESHOLD
    
    def wait_for_warmup(self):
        """센서 예열 완료까지 대기"""
        if self.warmed_up:
            return
        
        elapsed = time.time() - self.warmup_start
        remaining = max(0, 20 - elapsed)
        
        if remaining > 0:
            print(f"센서 예열 대기 중... {remaining:.1f}초 남음")
            time.sleep(remaining)
            self.warmed_up = True
            print("✅ 센서 예열 완료!")

def test_all_gases(adc_pin=1):
    """모든 가스 종류 테스트"""
    print("=== MQ-2 모든 가스 테스트 ===")
    
    sensor = MQ2GasSensor(adc_pin)
    
    # 예열 대기
    sensor.wait_for_warmup()
    
    gases = ["LPG", "METHANE", "SMOKE", "HYDROGEN", "ALCOHOL"]
    
    print(f"\n현재 센서 읽기:")
    for gas in gases:
        status = sensor.get_status(gas)
        print(f"  {gas:8s}: {status['ppm']:6.1f} ppm ({status['danger_level']})")

def monitor_gas(adc_pin=1, gas_type="LPG", duration=60, interval=2):
    """가스 모니터링"""
    sensor = MQ2GasSensor(adc_pin)
    
    print(f"🔥 MQ-2 {gas_type} 모니터링 시작 ({duration}초)")
    print("시간\t농도(ppm)\t위험도\t\t전압\t저항(kΩ)")
    print("-" * 60)
    
    start_time = time.time()
    count = 0
    
    try:
        while True:
            elapsed = time.time() - start_time
            if elapsed >= duration:
                break
            
            status = sensor.get_status(gas_type)
            count += 1
            
            resistance_str = f"{status['resistance']:.1f}" if status['resistance'] != "inf" else "inf"
            
            print(f"{count:3d}\t{status['ppm']:8.1f}\t{status['danger_level']:10s}\t{status['voltage']:.2f}V\t{resistance_str}")
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n모니터링 중지됨")
    
    print(f"\n모니터링 완료 ({count}회 측정)")

if __name__ == "__main__":
    print("MQ-2 가연성 가스센서 라이브러리")
    print("\n감지 가능한 가스:")
    print("- LPG (액화석유가스)")
    print("- 메탄 (Methane)")
    print("- 연기 (Smoke)")
    print("- 수소 (Hydrogen)")
    print("- 알코올 (Alcohol)")
    
    print("\n주의사항:")
    print("- 센서 예열 20초 필요")
    print("- 깨끗한 공기에서 보정 권장")
    print("- 300ppm 이상 시 위험 수준")
    
    # 사용 예시
    print("\n=== 사용 예시 ===")
    import time
    
    try:
        sensor = MQ2GasSensor(adc_pin=1)
        
        # 짧은 예열 (테스트용)
        print("5초 예열 후 측정...")
        time.sleep(5)
        
        # 상태 확인
        status = sensor.get_status("LPG")
        print(f"LPG: {status['ppm']:.1f} ppm ({status['danger_level']})")
        
        status = sensor.get_status("SMOKE")
        print(f"연기: {status['ppm']:.1f} ppm ({status['danger_level']})")
        
    except Exception as e:
        print(f"센서 테스트 실패: {e}")
        print("하드웨어 연결을 확인하세요.") 