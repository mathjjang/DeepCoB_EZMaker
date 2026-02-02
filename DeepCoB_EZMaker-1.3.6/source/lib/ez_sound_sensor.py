"""
EZMaker 전용 소리센서(EZSOUND) 드라이버

- EZSOUND 스펙(교육용 기준, EZMaker 스타일 가정):
    - 아날로그 값: 0~1023 (10비트 스케일)
    - 보드 ADC: ESP32-S3 12비트(0~4095), 3.3V 기준

이 모듈은 보드 내부 12비트 ADC 값을 읽어:
    - 10비트 Raw 값 (0~1023)
    - 전압(3.3V 기준)
    - 상대적인 소리 레벨 비율(0~100%)
을 계산해 반환합니다.
"""

import machine


class EzSoundSensor:
    """
    EZMaker 소리센서(EZSOUND) 드라이버

    사용 예:
        sensor = EzSoundSensor(adc_pin=2)  # 예: A0 포트
        status = sensor.get_status()
        print(status["raw"], status["percent"], status["voltage"])
    """

    def __init__(self, adc_pin, vref_board=3.3):
        """
        EZSOUND 센서 초기화

        Args:
            adc_pin (int): ESP32-S3 GPIO 번호 (예: A0=2, A1=1 ...)
            vref_board (float): 보드 ADC 기준 전압 (기본 3.3V)
        """
        self.adc_pin = adc_pin
        self.vref_board = vref_board

        # ADC 객체 생성 (12비트, ATTN_11DB -> 약 0~vref_board)
        self.adc = machine.ADC(machine.Pin(adc_pin))
        try:
            self.adc.atten(machine.ADC.ATTN_11DB)
        except AttributeError:
            # 플랫폼에 따라 atten 이 없을 수 있음
            pass
        try:
            self.adc.width(machine.ADC.WIDTH_12BIT)
        except AttributeError:
            # width 설정이 없는 포트도 있으므로 무시
            pass

    # ------------------------------------------------------------------
    # 기본 읽기 API
    # ------------------------------------------------------------------
    def read_raw_12bit(self):
        """
        ADC 12비트 원시값 (0~4095 추정) 반환
        """
        val = self.adc.read()
        # 일부 보드에서 0~65535를 반환하는 경우를 대비하여 스케일 조정
        if val > 4095:
            val = int(val * 4095 / 65535)
        return val

    def read_raw_10bit(self):
        """
        12비트 원시값을 10비트 스케일(0~1023)로 변환해 반환
        (EZMaker 사이트 스펙에 맞춘 출력용)
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
    # 상태 API
    # ------------------------------------------------------------------
    def get_status(self):
        """
        센서 상태를 딕셔너리로 반환

        Returns:
            dict: {
                "raw": int,        # 10비트 Raw 값 (0~1023)
                "percent": float,  # 상대적인 소리 레벨 비율 (0~100)
                "voltage": float,  # 전압(3.3V 기준, 참고용)
            }
        """
        raw_10 = self.read_raw_10bit()
        voltage = (raw_10 / 1023) * self.vref_board
        percent = (raw_10 / 1023) * 100.0

        return {
            "raw": raw_10,
            "percent": percent,
            "voltage": voltage,
        }


if __name__ == "__main__":
    print("EzSoundSensor 드라이버 모듈입니다.")
    print("예시:")
    print("  from ez_sound_sensor import EzSoundSensor")
    print("  sensor = EzSoundSensor(adc_pin=2)  # A0 포트")
    print("  status = sensor.get_status()")
    print("  print(status['raw'], status['percent'], status['voltage'])")



