"""
EZMaker 전용 무게센서(EZWEIGHT, HX711 기반) 드라이버

- 센서: HX711 로드셀 앰프
- 측정:
    - Raw 값: HX711 24비트 ADC 출력 (보정 전 카운트 값)
    - 무게(Weight): 스케일 인자(scale)를 적용한 값 (기본 단위 g 로 가정)

주의:
- 실제 사용 시에는 `scale` 값과 영점(tare)을 반드시 보정해야 합니다.
- 이 드라이버는 보드에 이미 업로드된 `hx711` 모듈을 사용합니다.
"""

import time

try:
    import hx711  # 보드 /lib 에 존재하는 HX711 모듈을 사용
except ImportError:
    hx711 = None  # 런타임에서 ImportError 를 처리하도록 둠


class EzWeightSensor:
    """
    HX711 기반 EZMaker 무게센서 드라이버

    사용 예:
        sensor = EzWeightSensor(dout_pin=42, sck_pin=14, scale=400.0)
        status = sensor.get_status()
        print(status["raw"], status["weight"])
    """

    def __init__(self, dout_pin: int, sck_pin: int, scale: float = 400.0, ready_timeout_ms: int = 2000):
        """
        EzWeightSensor 초기화

        Args:
            dout_pin (int): HX711 DOUT(DT) 핀 번호
            sck_pin (int): HX711 SCK(CLK) 핀 번호
            scale (float): 스케일 인자 (Raw → g 변환 계수, 보정 필요)
            ready_timeout_ms (int): 센서 준비 대기 타임아웃(ms)
        """
        if hx711 is None:
            raise ImportError("hx711 module not found. Please upload hx711.py/.mpy to /lib.")

        self.dout_pin = dout_pin
        self.sck_pin = sck_pin
        self.scale = scale

        # HX711 인스턴스 생성
        self._hx = hx711.HX711(self.dout_pin, self.sck_pin)

        # 센서 준비 대기 (가능한 경우)
        try:
            if hasattr(self._hx, "wait_ready_timeout"):
                self._hx.wait_ready_timeout(timeout_ms=ready_timeout_ms)
        except Exception:
            # 준비 대기 실패는 치명적이지 않으므로 무시
            pass

        # 영점(Tare) 보정 시도
        try:
            if hasattr(self._hx, "tare"):
                self._hx.tare()
        except Exception:
            # tare 실패 시에도 이후 read()/get_units() 가 동작할 수 있으므로 무시
            pass

        # 스케일 인자 설정 시도
        try:
            if hasattr(self._hx, "set_scale"):
                self._hx.set_scale(self.scale)
        except Exception:
            # set_scale 이 없거나 실패해도 get_units 가 raw 기반으로 동작할 수 있으므로 무시
            pass

    # -------------------------------
    # 측정 API
    # -------------------------------
    def read_raw(self):
        """
        HX711 Raw 값 반환 (보정 전 카운트 값)
        """
        try:
            if hasattr(self._hx, "read"):
                return self._hx.read()
        except Exception:
            return None
        return None

    def read_weight(self, times: int = 1):
        """
        스케일/영점을 적용한 무게 값 반환

        Args:
            times (int): 내부 평균 횟수 (hx711.get_units(times) 에 전달)
        """
        try:
            if hasattr(self._hx, "get_units"):
                return self._hx.get_units(times)
        except Exception:
            return None
        return None

    def get_status(self):
        """
        무게센서 상태를 딕셔너리로 반환

        Returns:
            dict: {
                "raw":     int or None,   # HX711 Raw 카운트 값
                "weight":  float or None, # 스케일/영점 적용 무게 값 (단위 g 로 가정)
            }
        """
        raw = self.read_raw()

        # 너무 빠른 연속 읽기를 피하기 위해 약간의 지연을 둘 수 있음
        time.sleep_ms(10)

        weight = self.read_weight(times=1)

        return {
            "raw": raw,
            "weight": weight,
        }


if __name__ == "__main__":
    print("EzWeightSensor (HX711) 드라이버 모듈입니다.")
    print("보드에서 직접 사용 시 EzWeightSensor(dout_pin, sck_pin, scale) 로 초기화하세요.")


