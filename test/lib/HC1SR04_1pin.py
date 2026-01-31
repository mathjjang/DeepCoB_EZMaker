import machine, time
from machine import Pin

__version__ = '0.2.0'
__author__ = 'Roberto Sánchez (modified for 1-pin by DeepCoB project)'
__license__ = "Apache License 2.0. https://www.apache.org/licenses/LICENSE-2.0"


class HCSR04:
    """
    1핀 방식 HC-SR04 스타일 초음파 센서 드라이버.

    원래 드라이버는 Trig/Echo 2핀을 사용하지만,
    이 버전은 하나의 GPIO 핀을 Trig → Echo 순서로 재사용합니다.

    동작 방식:
      1. 같은 핀을 OUTPUT 으로 두고, 10us HIGH Trig 펄스를 보냄
      2. 같은 핀을 INPUT 으로 바꾸고, Echo HIGH 펄스 길이를 측정
    """

    # echo_timeout_us is based in chip range limit (400cm)
    def __init__(self, data_pin, echo_timeout_us=500 * 2 * 30):
        """
        data_pin: Trig/Echo 겸용 GPIO 핀 번호
        echo_timeout_us: Timeout in microseconds to listen to echo pin.
                         By default is based on sensor limit range (4m)
        """
        self.echo_timeout_us = echo_timeout_us
        self.pin_num = data_pin

        # 초기에는 출력 LOW로 안정화
        self.pin = Pin(self.pin_num, mode=Pin.OUT, pull=None)
        self.pin.value(0)
        time.sleep_ms(50)

    def _as_output(self):
        self.pin = Pin(self.pin_num, mode=Pin.OUT, pull=None)

    def _as_input(self):
        self.pin = Pin(self.pin_num, mode=Pin.IN, pull=None)

    def _send_pulse_and_wait(self):
        """
        Send the pulse on the 1-pin line and listen for echo on the same pin.
        We use `machine.time_pulse_us()` to get microseconds until the echo is received.
        """
        # Trig: 출력 모드에서 안정화 후 10us HIGH 펄스
        self._as_output()
        self.pin.value(0)  # Stabilize the sensor
        time.sleep_us(5)
        self.pin.value(1)
        time.sleep_us(10)  # 10us pulse
        self.pin.value(0)

        # Echo: 같은 핀을 입력 모드로 전환
        self._as_input()

        try:
            pulse_time = machine.time_pulse_us(self.pin, 1, self.echo_timeout_us)
            return pulse_time
        except OSError as ex:
            if ex.args and ex.args[0] == 110:  # 110 = ETIMEDOUT
                raise OSError('Out of range')
            raise ex

    def distance_mm(self):
        """
        Get the distance in millimeters without floating point operations.
        """
        pulse_time = self._send_pulse_and_wait()

        # To calculate the distance we get the pulse_time and divide it by 2 
        # (the pulse walk the distance twice) and by 29.1 because
        # the sound speed on air (343.2 m/s), that is equivalent to
        # 0.34320 mm/us that is 1mm each 2.91us
        # pulse_time // 2 // 2.91 -> pulse_time // 5.82 -> pulse_time * 100 // 582 
        mm = pulse_time * 100 // 582
        return mm

    def distance_cm(self):
        """
        Get the distance in centimeters with floating point operations.
        It returns a float.
        """
        pulse_time = self._send_pulse_and_wait()

        # To calculate the distance we get the pulse_time and divide it by 2 
        # (the pulse walk the distance twice) and by 29.1 because
        # the sound speed on air (343.2 m/s), that is equivalent to
        # 0.034320 cm/us that is 1cm each 29.1us
        cms = (pulse_time / 2) / 29.1
        return cms