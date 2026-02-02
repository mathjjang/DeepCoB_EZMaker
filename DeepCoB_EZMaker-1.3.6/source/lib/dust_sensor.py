import machine
from time import sleep
import gc

class DustSensor:
    """
    먼지 센서(예: GP2Y1010AU0F) 제어를 위한 클래스
    """
    # 상수 설정
    SAMPLING_TIME = 0.00028  # 샘플링 시간(초)
    DELTA_TIME = 0.00004     # 델타 시간(초)
    SLEEP_TIME = 0.00968     # 슬립 시간(초)
    WARMUP_SAMPLES = 30      # 예열 샘플 수
    CALIBRATION_SAMPLES = 100 # 보정 샘플 수
    
    
    def __init__(self, led_pin=39, vo_pin=19):
        """
        먼지 센서 초기화
        
        Args:
            led_pin: LED 제어 핀 번호
            vo_pin: 먼지 센서 아날로그 출력 핀 번호
        """
        # 핀 설정
        self.led_pin = machine.Pin(led_pin, machine.Pin.OUT)
        self.vo_pin = machine.ADC(vo_pin)
        
        # ESP32 여부 확인 및 ADC 설정
        self.is_esp32 = hasattr(machine, 'TouchPad')
        if self.is_esp32:
            # ESP32 ADC 설정 (12비트, 0-4095)
            self.vo_pin.atten(machine.ADC.ATTN_11DB)  # 3.3V 범위로 설정
            self.adc_max = 4095
        else:
            # ESP8266 ADC 설정 (10비트, 0-1023)
            self.adc_max = 1023
        
        # 상태 변수
        self.voc = None  # 자동 보정될 VOC 기준값
        self.max_density = 0  # 최대 먼지 밀도
        self.is_calibrated = False
        
        # LED 초기 상태: 꺼짐
        self.led_pin.value(1)

        # 초기 보정 시도 (아직 보정되지 않은 경우에만)
        #if not self.is_calibrated or self.voc is None:
        #    self.calibrate(20)  # 적은 샘플로 빠른 보정
        
    def calc_volt(self, val):
        """ADC 값을 전압으로 변환 (0-3.3V)"""
        return val * 3.3 / self.adc_max
    
    def calc_density(self, vo, k=0.5):
        """전압을 먼지 밀도로 변환 (μg/m³)"""
        # VOC가 초기화되지 않았다면 현재 값으로 설정
        if self.voc is None:
            self.voc = vo
            return 0
        
        # 전압 차이 계산
        dv = vo - self.voc
        
        # 음수 값 처리 (더 낮은 값이 측정되면 기준값 천천히 갱신)
        if dv < 0:
            # VOC 값을 약간만 조정 (급격한 변화 방지)
            self.voc = self.voc * 0.95 + vo * 0.05
            dv = 0
        
        # 밀도 계산 및 최대값 갱신
        density = dv / k * 100
        self.max_density = max(self.max_density, density)
        
        return density
    
    def calibrate(self, samples=None):
        """
        센서 보정 - 깨끗한 공기에서 기준 VOC 값 설정
        
        Args:
            samples: 보정을 위한 샘플 수 (기본값: self.CALIBRATION_SAMPLES)
        
        Returns:
            float: 보정된 VOC 기준값
        """
        if samples is None:
            samples = self.CALIBRATION_SAMPLES
            
        print("센서 예열 중...")
        # 센서 예열
        for _ in range(self.WARMUP_SAMPLES):
            self.led_pin.value(0)  # LED 켜기
            sleep(0.2)
            self.led_pin.value(1)  # LED 끄기
            sleep(0.1)
        
        print("센서 보정 중... (깨끗한 공기에서 실행하세요)")
        vals = []
        
        # 보정용 샘플 수집
        for i in range(samples):
            # 측정 사이클
            self.led_pin.value(0)  # LED 켜기
            sleep(self.SAMPLING_TIME)
            val = self.vo_pin.read()
            vals.append(val)
            sleep(self.DELTA_TIME)
            self.led_pin.value(1)  # LED 끄기
            sleep(self.SLEEP_TIME)
            
            # 진행 상황 표시
            if (i+1) % 20 == 0:
                print(f"보정 진행률: {i+1}/{samples}")
        
        # 이상치 제거 (상위 10%, 하위 10% 제거)
        vals.sort()
        valid_vals = vals[samples//10:samples-samples//10]
        
        # 보정값 계산 및 설정
        avg = sum(valid_vals) / len(valid_vals)
        self.voc = self.calc_volt(avg)
        self.is_calibrated = True
        
        print(f"보정 완료. 기준 VOC: {self.voc:.3f}V")
        return self.voc
    
    def read_raw(self):
        """
        센서에서 단일 원시 ADC 값을 읽기
        
        Returns:
            int: 원시 ADC 값
        """
        self.led_pin.value(0)  # LED 켜기
        sleep(self.SAMPLING_TIME)
        val = self.vo_pin.read()
        sleep(self.DELTA_TIME)
        self.led_pin.value(1)  # LED 끄기
        sleep(self.SLEEP_TIME)
        return val
    
    def read(self, samples=10):
        """
        먼지 농도를 측정하여 반환
        
        Args:
            samples: 평균을 위한 샘플 수
        
        Returns:
            tuple: (밀도(μg/m³), 전압(V), 원시ADC값)
        """
        # 보정되지 않았으면 보정 실행
        if not self.is_calibrated and self.voc is None:
            self.calibrate(20)  # 적은 샘플로 빠른 보정
        
        vals = []
        for _ in range(samples):
            vals.append(self.read_raw())
        
        # 평균값 계산
        avg = sum(vals) / len(vals)
        volt = self.calc_volt(avg)
        density = self.calc_density(volt)
        
        return (density, volt, avg)
    
    def get_status(self):
        """
        센서의 현재 상태를 간단히 반환
        
        Returns:
            dict: 센서 상태 정보
        """
        density, volt, raw = self.read(5)  # 적은 샘플로 빠른 측정
        
        return {
            "density": density,      # 먼지 농도 (μg/m³)
            "voltage": volt,         # 측정 전압 (V)
            "raw": raw,              # 원시 ADC 값
            "voc": self.voc,         # 보정 기준값 (V)
            "max_density": self.max_density,  # 최대 측정값
            "calibrated": self.is_calibrated  # 보정 완료 여부
        }
    
    def monitor(self, sample_size=100, duration=None, callback=None):
        """
        먼지 센서 모니터링 함수
        
        Args:
            sample_size: 평균을 위한 샘플 크기
            duration: 모니터링 지속 시간(초), None이면 무한 반복
            callback: 결과를 처리할 콜백 함수 callback(density, voltage, raw_value)
        """
        # 보정 확인
        if not self.is_calibrated and self.voc is None:
            print("센서가 보정되지 않았습니다. 보정을 시작합니다...")
            self.calibrate()
        
        print("\n먼지 측정 시작...\n")
        
        vals = []
        start_time = None
        if duration is not None:
            import time
            start_time = time.time()
        
        try:
            while True:
                # 시간 제한 확인
                if duration is not None and time.time() - start_time > duration:
                    print(f"{duration}초 모니터링 완료")
                    break
                
                # 센서 측정
                vals.append(self.read_raw())
                
                # 메모리 정리 (주기적으로)
                if len(vals) % 500 == 0:
                    gc.collect()
                
                # 샘플 사이즈에 도달하면 계산 및 출력
                if len(vals) >= sample_size:
                    # 평균값 계산
                    avg = sum(vals) / len(vals)
                    volt = self.calc_volt(avg)
                    density = self.calc_density(volt)
                    mv = volt * 1000
                    
                    # 결과 출력
                    print(
                        "{:.1f} mV / {:.2f} μg/m³ (Voc={:.3f}V) | 최대: {:.2f} μg/m³".format(
                            mv, density, self.voc, self.max_density
                        )
                    )
                    
                    # 버퍼 초기화
                    vals = []
                    
                    # 콜백 실행
                    if callback:
                        callback(density, volt, avg)
        
        except KeyboardInterrupt:
            print("\n사용자에 의해 중단됨")
        except Exception as e:
            print(f"\n오류 발생: {e}")
            raise
        finally:
            self.led_pin.value(1)  # LED 끄기
            print("먼지 센서 모니터링 종료")

# 사용 예시
if __name__ == "__main__":
    # 센서 생성
    dust = DustSensor(led_pin=39, vo_pin=19)
    
    # 보정 수행
    dust.calibrate()
    
    # 결과 출력 콜백
    def print_result(density, volt, raw):
        print(f"콜백: 먼지 농도 = {density:.2f} μg/m³")
    
    # 모니터링 실행 (50개 샘플로 더 빠른 결과 확인)
    dust.monitor(sample_size=50, callback=print_result) 