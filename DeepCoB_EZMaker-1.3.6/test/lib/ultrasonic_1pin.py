"""
CS100A/Generic 1-Pin Ultrasonic Sensor Library for MicroPython
===============================================================

1핀 방식 초음파 센서를 **HC-SR04 스타일**로 제어하는 MicroPython 드라이버입니다.

HC-SR04 2핀 드라이버(`trigger`, `echo`)를 참고하여,
하나의 핀을 Trig → Echo 순서로 재사용하도록 구성했습니다.

주요 기능:
- 1핀으로 Trig/Echo 통합 제어
- 거리 측정 (2cm ~ 400cm)
- time_pulse_us 기반 HC-SR04 스타일 타이밍

사용 예:
    from lib.ultrasonic_1pin import Ultrasonic1Pin
    
    sensor = Ultrasonic1Pin(pin=48)
    d = sensor.distance_cm()
    print(d, "cm")

연결:
- DATA (D2) -> GPIO 48 (또는 다른 GPIO)
- VCC, GND
"""

import machine
import time
from machine import Pin


class Ultrasonic1Pin:
    """
    HC-SR04 스타일 1핀 초음파 센서 드라이버

    - Trig: 출력 모드에서 10us HIGH 펄스 전송
    - Echo: 같은 핀을 입력 모드로 바꾼 뒤 HIGH 펄스 길이 측정
    """

    def __init__(self, pin, echo_timeout_us=500 * 2 * 30):
        """
        Args:
            pin (int): GPIO 핀 번호 (Trig/Echo 겸용)
            echo_timeout_us (int): Echo 타임아웃 (마이크로초)
        """
        self.pin_num = pin
        self.echo_timeout_us = echo_timeout_us

        # 초기 상태: 출력 LOW로 안정화
        self._as_output()
        self.pin.value(0)
        time.sleep_ms(50)

    # 내부 유틸
    def _as_output(self):
        self.pin = Pin(self.pin_num, mode=Pin.OUT, pull=None)

    def _as_input(self):
        # HC-SR04 레퍼런스는 풀 저항 없이 사용
        self.pin = Pin(self.pin_num, mode=Pin.IN, pull=None)

    def _send_pulse_and_wait(self):
        """
        Trig 펄스를 보내고, Echo 펄스를 기다려 시간을 반환.

        Returns:
            int: 펄스 시간(us)

        Raises:
            OSError('Out of range'): 타임아웃 등으로 Echo를 못 읽을 때
        """
        # Trig: 출력 모드
        self._as_output()
        self.pin.value(0)
        time.sleep_us(5)   # 안정화
        self.pin.value(1)
        time.sleep_us(10)  # 10us HIGH
        self.pin.value(0)

        # Echo: 입력 모드
        self._as_input()

        # 일반 HC-SR04는 Idle=LOW, Echo=HIGH 펄스.
        # 일부 모듈은 반대로 Idle=HIGH, Echo=LOW 펄스를 줄 수 있으므로
        # HIGH 펄스를 먼저 시도하고, 타임아웃이면 LOW 펄스도 한 번 시도한다.
        try:
            pulse_time = machine.time_pulse_us(self.pin, 1, self.echo_timeout_us)
            return pulse_time
        except OSError as ex:
            # 110 = ETIMEDOUT (MicroPython)
            if ex.args and ex.args[0] == 110:
                # HIGH 펄스 타임아웃 → LOW 펄스도 시도
                try:
                    pulse_time = machine.time_pulse_us(self.pin, 0, self.echo_timeout_us)
                    return pulse_time
                except OSError as ex2:
                    if ex2.args and ex2.args[0] == 110:
                        # 둘 다 타임아웃
                        raise OSError("Out of range")
                    raise
            # 다른 에러는 그대로 전달
            raise

    def distance_mm(self):
        """
        거리(mm) 반환 (HC-SR04 레퍼런스와 동일 공식)
        """
        pulse_time = self._send_pulse_and_wait()
        # (pulse_time / 2) / 2.91 → 정수 연산 최적화 버전
        mm = pulse_time * 100 // 582
        return mm

    def distance_cm(self):
        """
        거리(cm) 반환 (부동소수점)
        """
        pulse_time = self._send_pulse_and_wait()
        # (pulse_time / 2) / 29.1
        cms = (pulse_time / 2) / 29.1
        return cms

    # 기존 테스트 코드 호환용 메서드들
    def get_distance(self):
        """
        기존 테스트 코드 호환용: 거리(cm) 또는 None
        """
        try:
            d = self.distance_cm()
            # 일반적인 범위 필터 (2cm~400cm)
            if d < 2 or d > 400:
                return None
            return d
        except OSError:
            return None

    def get_distance_average(self, samples=3):
        """
        여러 번 측정하여 평균값 반환 (cm)
        """
        vals = []
        for _ in range(samples):
            d = self.get_distance()
            if d is not None:
                vals.append(d)
            time.sleep_ms(60)
        if not vals:
            return None
        return sum(vals) / len(vals)

    def reset(self):
        """
        센서 리셋: 핀을 출력 LOW로 잠시 유지
        """
        self._as_output()
        self.pin.value(0)
        time.sleep_ms(100)
