"""
DIY-A 센서 드라이버 (전압 / 전자기 유도 실험용 아날로그 센서)

- 센서 스펙: 아날로그 0~1023, 전압값 0~5V (교육용 기준)
- 보드 ADC: ESP32-S3 12비트(0~4095), 3.3V 기준

이 모듈은 보드 내부 ADC 값을 읽어서:
    - 12비트 원시값 (0~4095)
    - 10비트 스케일 값 (0~1023)
    - 전압 (0~5V 기준으로 환산)
을 계산해 반환합니다.

BLE 연동 시에는 이 모듈을 통해 측정값을 얻어
문자열 포맷으로 변환해 보내는 것을 권장합니다.
"""

import machine


class DiyASensor:
    """
    DIY-A 아날로그 센서 드라이버

    사용 예:
        sensor = DiyASensor(adc_pin=2)  # A0 포트 (GPIO 2)
        status = sensor.get_status()
        print(status["raw_10bit"], status["voltage_5v"])
    """

    def __init__(self, adc_pin, vref_board=3.3, vref_sensor=5.0):
        """
        DIY-A 센서 초기화

        Args:
            adc_pin (int): ESP32-S3 GPIO 번호 (예: A0=2, A1=1 ...)
            vref_board (float): 보드 ADC 기준 전압 (기본 3.3V)
            vref_sensor (float): 센서 스펙 기준 전압 (기본 5.0V)
        """
        self.adc_pin = adc_pin
        self.vref_board = vref_board
        self.vref_sensor = vref_sensor

        # ADC 객체 생성 (12비트, ATTN_11DB -> 약 0~vref_board)
        self.adc = machine.ADC(machine.Pin(adc_pin))
        self.adc.atten(machine.ADC.ATTN_11DB)
        self.adc.width(machine.ADC.WIDTH_12BIT)

        # 기준값(10비트 스케일, 사용자가 원하는 기준 상태에서 설정 가능)
        self.ref_10bit = None

    # ------------------------------------------------------------------
    # 기본 읽기 API
    # ------------------------------------------------------------------
    def read_raw_12bit(self):
        """ADC 12비트 원시값 (0~4095) 반환"""
        return self.adc.read()

    def read_raw_10bit(self):
        """
        12비트 원시값을 10비트 스케일(0~1023)로 변환해 반환
        센서 스펙(0~1023)을 그대로 사용하기 쉬운 형태
        """
        raw_12 = self.read_raw_12bit()
        # 0~4095 -> 0~1023 선형 스케일링
        return int(raw_12 * 1023 / 4095)

    def read_voltage_board(self):
        """
        보드 기준 전압(0~vref_board, 보통 3.3V)으로 환산한 값 반환
        """
        raw_12 = self.read_raw_12bit()
        return (raw_12 / 4095) * self.vref_board

    def read_voltage_5v(self):
        """
        센서 스펙 기준(0~vref_sensor, 기본 5V)으로 환산한 전압 반환

        - DIY-A 설명서 기준으로 사용자가 보기 쉬운 값
        - 내부적으로는 10비트 스케일(0~1023)을 사용해 계산
        """
        raw_10 = self.read_raw_10bit()
        return (raw_10 / 1023) * self.vref_sensor

    # ------------------------------------------------------------------
    # 기준값 및 상태 API
    # ------------------------------------------------------------------
    def calibrate_reference(self, samples=20, delay_ms=50):
        """
        현재 상태를 기준(reference)으로 설정

        - 예: 자석/전류가 없는 “기본 상태”에서 호출
        - 이후 diff_10bit = 현재값 - ref_10bit 로 변화량 계산 가능
        """
        import time

        total = 0
        for _ in range(samples):
            total += self.read_raw_10bit()
            time.sleep_ms(delay_ms)

        self.ref_10bit = int(total / samples)
        return self.ref_10bit

    def get_status(self):
        """
        센서 상태를 간단한 딕셔너리로 반환

        Returns:
            dict: {
                "raw": int,        # 10비트 스케일 값 (0~1023)
                "voltage": float,  # 0~5V 기준으로 환산된 전압
            }
        """
        raw_10 = self.read_raw_10bit()
        v_5 = (raw_10 / 1023) * self.vref_sensor

        return {
            "raw": raw_10,
            "voltage": v_5,
        }


# 이 모듈은 라이브러리 용도로 설계되었으며,
# 직접 실행 시에는 간단한 안내만 출력합니다.
if __name__ == "__main__":
    print("DiyASensor 드라이버 모듈입니다.")
    print("예시:")
    print("  from diyA_sensor import DiyASensor")
    print("  sensor = DiyASensor(adc_pin=2)  # A0 포트")
    print("  status = sensor.get_status()")
    print("  print(status['raw_10bit'], status['voltage_5v'])")


