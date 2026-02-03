"""
인체감지 센서 (PIR, Human Presence Sensor) 드라이버

- 인체(움직임)를 감지하면 디지털 출력이 변화하는 센서 모듈용 간단 드라이버입니다.
- EZMaker 쉴드의 D포트에 연결된 인체감지 센서를 대상으로 합니다.

특징:
- 출력: 디지털 0 / 1
  - 1: 인체(움직임) 감지
  - 0: 감지 없음
"""

import machine


class HumanSensor:
    """
    단순 디지털 인체감지 센서 드라이버

    사용 예:
        sensor = HumanSensor(pin_num=21)
        detected = sensor.is_detected()  # 0 또는 1
        status = sensor.get_status()     # {"value": 0 또는 1}
    """

    def __init__(self, pin_num, active_high=True):
        """
        Args:
            pin_num (int): 디지털 입력으로 사용할 GPIO 번호
            active_high (bool): True 이면 HIGH(1)을 감지 상태로 간주, False 이면 LOW(0)을 감지로 간주
        """
        self.pin_num = pin_num
        self.active_high = active_high

        # 대부분의 PIR 모듈은 push-pull 출력이므로 별도 풀업/풀다운 없이 IN 만 설정
        self.pin = machine.Pin(pin_num, machine.Pin.IN)

    def read_raw(self):
        """
        원시 핀 값 반환 (0 또는 1)
        """
        try:
            return 1 if self.pin.value() else 0
        except Exception:
            return 0

    def is_detected(self):
        """
        인체(움직임) 감지 여부 반환 (0 또는 1)
        """
        raw = self.read_raw()
        if self.active_high:
            return 1 if raw == 1 else 0
        else:
            return 1 if raw == 0 else 0

    def get_status(self):
        """
        상태 딕셔너리 반환

        Returns:
            dict: {"value": 0 또는 1}
        """
        return {"value": int(self.is_detected())}


if __name__ == "__main__":
    print("HumanSensor (PIR 인체감지 센서) 드라이버 모듈입니다.")
    print("보드에서 직접 사용 시:")
    print("    from human_sensor import HumanSensor")
    print("    s = HumanSensor(pin_num=21)")
    print("    print(s.get_status())")


