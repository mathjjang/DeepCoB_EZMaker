"""
EZMaker 수중/접촉 온도센서(EZTHERMAL, DS18B20 기반) 드라이버

- DS18B20 1-Wire 디지털 온도 센서를 사용하여 섭씨 온도를 측정합니다.
- 수중(방수 프로브) 및 접촉/공기 온도 측정에 공통으로 사용합니다.

사용 예시 (펌웨어 내부):
    from ez_thermal_sensor import EzThermalSensor

    sensor = EzThermalSensor(pin_num=21)  # 예: EZMaker D0 → GPIO 21
    status = sensor.get_status()
    temp_c = status.get("temperature")
"""

import machine
import onewire
import ds18x20
import time


class EzThermalSensor:
    """
    DS18B20 기반 EZMaker 수중/접촉 온도센서 드라이버
    """

    def __init__(self, pin_num: int, max_sensors: int = 1):
        """
        DS18B20 센서를 초기화합니다.

        :param pin_num: 1-Wire 데이터 라인이 연결된 GPIO 번호
        :param max_sensors: 버스에서 사용할 최대 센서 개수 (기본 1개)
        """
        self.pin_num = pin_num
        self._ow = onewire.OneWire(machine.Pin(pin_num))
        self._ds = ds18x20.DS18X20(self._ow)

        # 버스에 연결된 DS18B20 목록 검색
        roms = self._ds.scan()
        if not roms:
            raise RuntimeError("No DS18B20 sensors found on pin {}".format(pin_num))

        # 여러 개가 있을 경우, 우선 1개만 사용 (필요시 확장 가능)
        self._roms = roms[: max_sensors]

    def read_celsius(self):
        """
        섭씨 온도를 한 번 읽어 반환합니다.

        :return: temperature in Celsius (float) 또는 None (실패 시)
        """
        try:
            # 변환 명령 전송
            self._ds.convert_temp()
            # 최대 변환 시간(12bit 기준 약 750ms) 대기
            time.sleep_ms(750)

            temps = []
            for rom in self._roms:
                t = self._ds.read_temp(rom)
                temps.append(t)

            if not temps:
                return None

            # 현재는 첫 번째 센서 값만 사용
            return temps[0]
        except Exception:
            # 상위 코드에서 에러 문자열을 보낼 수 있도록 None 반환
            return None

    def get_status(self):
        """
        상태를 딕셔너리 형태로 반환합니다.

        :return: {"temperature": float 또는 None}
        """
        temp_c = self.read_celsius()
        return {"temperature": temp_c}


