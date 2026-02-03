"""
EZMaker 자기장(Hall) 센서 드라이버

- 센서 스펙(사이트 기준):
    - 아날로그 값: 0~1023
    - 자석의 N극/S극 세기: -512 ~ +512
    - 자속 밀도 값: 0 ~ 512

- 보드 ADC:
    - ESP32-S3 12비트(0~4095), 3.3V 기준

이 모듈은 보드 내부 12비트 ADC 값을 읽어:
    - 10비트 Raw 값 (0~1023)
    - 기준 대비 변화량(10bit)
    - N/S 세기(-512~+512)
    - 자속 밀도(0~512)
    - 전압(3.3V 기준, 참고용)
을 계산해 반환합니다.
"""

import machine


class HallSensor:
    """
    EZMaker 자기장 센서 드라이버

    사용 예:
        sensor = HallSensor(adc_pin=2)  # 예: A0 포트
        status = sensor.get_status()
        print(status["raw"], status["strength"], status["density"])
    """

    def __init__(self, adc_pin, vref_board=3.3):
        """
        Hall 센서 초기화

        Args:
            adc_pin (int): ESP32-S3 GPIO 번호 (예: A0=2, A1=1 ...)
            vref_board (float): 보드 ADC 기준 전압 (기본 3.3V)
        """
        self.adc_pin = adc_pin
        self.vref_board = vref_board

        # ADC 객체 생성 (12비트, ATTN_11DB -> 약 0~vref_board)
        self.adc = machine.ADC(machine.Pin(adc_pin))
        # ESP32-S3 기준: 0~3.3V 측정
        try:
            self.adc.atten(machine.ADC.ATTN_11DB)
        except AttributeError:
            # 플랫폼에 따라 atten이 없을 수 있음
            pass
        try:
            self.adc.width(machine.ADC.WIDTH_12BIT)
        except AttributeError:
            # width 설정이 없는 포트도 있으므로 무시
            pass

        # 기준값(10비트 스케일)
        self.ref_10bit = None

        # 노이즈/스케일 파라미터 (테스트 코드와 동일한 값 사용)
        self.dead_zone_diff = 5      # |diff_10bit| < 5 이면 0으로 간주
        self.max_diff_10bit = 128    # ±128을 ±512로 매핑

    # ------------------------------------------------------------------
    # 기본 읽기 API
    # ------------------------------------------------------------------
    def read_raw_12bit(self):
        """
        ADC 12비트 원시값 (0~4095 추정) 반환
        """
        # ESP32-S3에서는 read()가 0~4095를 반환
        val = self.adc.read()
        # 일부 보드에서 0~65535를 반환하는 경우를 대비하여 스케일 조정
        if val > 4095:
            # 16비트 → 12비트로 선형 스케일링
            val = int(val * 4095 / 65535)
        return val

    def read_raw_10bit(self):
        """
        12비트 원시값을 10비트 스케일(0~1023)로 변환해 반환
        """
        raw_12 = self.read_raw_12bit()
        return int(raw_12 * 1023 / 4095)

    def read_voltage(self):
        """
        보드 기준 전압(0~vref_board, 보통 3.3V)으로 환산한 값 반환
        """
        raw_12 = self.read_raw_12bit()
        return (raw_12 / 4095) * self.vref_board

    # ------------------------------------------------------------------
    # 기준값 및 상태 계산
    # ------------------------------------------------------------------
    def calibrate_reference(self, samples=20, delay_ms=50):
        """
        현재 상태를 기준(reference)으로 설정

        - 자석을 멀리 둔 "자기장 없음" 상태에서 호출하는 것을 권장
        """
        import time

        total = 0
        for _ in range(samples):
            total += self.read_raw_10bit()
            time.sleep_ms(delay_ms)

        self.ref_10bit = int(total / samples)
        return self.ref_10bit

    def _ensure_reference(self):
        """
        기준값(ref_10bit)이 설정되지 않았다면 자동으로 보정
        """
        if self.ref_10bit is None:
            self.calibrate_reference(samples=20, delay_ms=50)

    def get_status(self):
        """
        센서 상태를 딕셔너리로 반환

        Returns:
            dict: {
                "raw": int,        # 10비트 Raw 값 (0~1023)
                "strength": int,   # N/S 세기(-512~+512)
                "density": int,    # 자속 밀도(0~512)
                "voltage": float,  # 전압(3.3V 기준, 참고용)
            }
        """
        self._ensure_reference()

        raw_10 = self.read_raw_10bit()
        voltage = (raw_10 / 1023) * self.vref_board

        # 기준 대비 변화량 (10비트)
        diff_10 = raw_10 - self.ref_10bit

        # 작은 노이즈 영역(데드존) 제거
        if -self.dead_zone_diff < diff_10 < self.dead_zone_diff:
            diff_for_strength = 0
        else:
            diff_for_strength = diff_10

        # ±max_diff_10bit 를 ±512로 스케일링
        if diff_for_strength > self.max_diff_10bit:
            diff_clamped = self.max_diff_10bit
        elif diff_for_strength < -self.max_diff_10bit:
            diff_clamped = -self.max_diff_10bit
        else:
            diff_clamped = diff_for_strength

        strength = int(diff_clamped * 512 / self.max_diff_10bit)
        density = abs(strength)

        return {
            "raw": raw_10,
            "strength": strength,
            "density": density,
            "voltage": voltage,
        }


if __name__ == "__main__":
    print("HallSensor 드라이버 모듈입니다.")
    print("예시:")
    print("  from hall_sensor import HallSensor")
    print("  sensor = HallSensor(adc_pin=2)  # A0 포트")
    print("  status = sensor.get_status()")
    print("  print(status['raw'], status['strength'], status['density'])")


