"""
EZMaker 전용 전압센서(EZVOLT) 드라이버

- 전압센서 스펙(교육용 EZMaker 스타일 가정):
    - 측정 입력 전압: 0~25V (DC)
    - 보드 ADC 입력: 저항 분할을 통해 0~3.3V 범위로 스케일링
    - 보드 ADC: ESP32-S3 12비트(0~4095), 3.3V 기준

이 모듈은 보드 내부 12비트 ADC 값을 읽어:
    - 10비트 Raw 값 (0~1023)
    - 보드 기준 전압(0~3.3V)
    - 센서 입력 전압(0~25V 환산 값)
을 계산해 반환합니다.
"""

import machine


class EzVoltSensor:
    """
    EZMaker 전압센서(EZVOLT) 드라이버

    사용 예:
        sensor = EzVoltSensor(adc_pin=2)  # 예: A0 포트
        status = sensor.get_status()
        print(status["raw"], status["voltage"])
    """

    def __init__(self, adc_pin, vref_board=3.3, vref_input=25.0):
        """
        EZVOLT 센서 초기화

        Args:
            adc_pin (int): ESP32-S3 GPIO 번호 (예: A0=2, A1=1 ...)
            vref_board (float): 보드 ADC 기준 전압 (기본 3.3V)
            vref_input (float): 전압센서 입력 기준 전압 (기본 25.0V)
        """
        self.adc_pin = adc_pin
        self.vref_board = vref_board
        self.vref_input = vref_input

        # ADC 객체 생성 (12비트, ATTN_11DB -> 약 0~vref_board)
        self.adc = machine.ADC(machine.Pin(adc_pin))
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

    def read_voltage_board(self):
        """
        보드 기준 전압(0~vref_board, 보통 3.3V)으로 환산한 값 반환
        """
        raw_12 = self.read_raw_12bit()
        return (raw_12 / 4095) * self.vref_board

    def read_voltage_input(self):
        """
        전압센서 입력 측(0~vref_input, 기본 25V) 기준으로 환산한 값 반환

        - EZMaker 전압센서가 0~25V 입력을 0~3.3V 범위로 스케일링한다고 가정
        - 10비트 Raw 값(0~1023)을 기준으로 선형 비례 변환
        """
        raw_10 = self.read_raw_10bit()
        return (raw_10 / 1023) * self.vref_input

    # ------------------------------------------------------------------
    # 상태 API
    # ------------------------------------------------------------------
    def get_status(self):
        """
        센서 상태를 딕셔너리로 반환

        Returns:
            dict: {
                "raw": int,        # 10비트 Raw 값 (0~1023)
                "voltage": float,  # 센서 입력 전압(0~25V 환산)
                "board_v": float,  # 보드 기준 전압(0~3.3V, 참고용)
            }
        """
        raw_10 = self.read_raw_10bit()
        board_v = self.read_voltage_board()
        input_v = (raw_10 / 1023) * self.vref_input

        return {
            "raw": raw_10,
            "voltage": input_v,
            "board_v": board_v,
        }


if __name__ == "__main__":
    print("EzVoltSensor 드라이버 모듈입니다.")
    print("예시:")
    print("  from ez_volt_sensor import EzVoltSensor")
    print("  sensor = EzVoltSensor(adc_pin=2)  # A0 포트")
    print("  status = sensor.get_status()")
    print("  print(status['raw'], status['voltage'], status['board_v'])")


