import time
from machine import UART, Pin


class EzDustSensor:
    """
    EZMaker용 PMS7003M 미세먼지 센서 드라이버

    - UART 기반 디지털 미세먼지 센서
    - 한 번의 측정으로 PM1.0 / PM2.5 / PM10 값을 모두 제공
    - 펌웨어/블록에서는 한 블록에서 세 값을 선택해서 사용할 수 있도록,
      get_status()에서 세 값을 모두 반환한다.
    """

    # PMS7003/PMS7003M 프로토콜 상수
    _FRAME_HEADER_HIGH = 0x42
    _FRAME_HEADER_LOW = 0x4D
    _FRAME_LENGTH = 32  # 전체 프레임 길이 (헤더 2바이트 포함)

    def __init__(
        self,
        rx_pin: int,
        tx_pin: int,
        uart_id: int = 1,
        baudrate: int = 9600,
        timeout_ms: int = 1000,
    ):
        """
        Args:
            rx_pin: UART RX 핀 번호 (센서의 TX에 연결)
            tx_pin: UART TX 핀 번호 (센서의 RX에 연결)
            uart_id: 사용 할 UART 채널 (기본값 1)
            baudrate: 통신 속도 (PMS7003M 기본 9600 bps)
            timeout_ms: 프레임 수신 타임아웃 (ms)
        """
        self.rx_pin = rx_pin
        self.tx_pin = tx_pin
        self.uart_id = uart_id
        self.timeout_ms = timeout_ms

        self._uart = UART(
            uart_id,
            baudrate=baudrate,
            bits=8,
            parity=None,
            stop=1,
            rx=Pin(rx_pin),
            tx=Pin(tx_pin),
        )

        # 최근 측정값 캐시
        self._pm1_0 = None
        self._pm2_5 = None
        self._pm10 = None

    def _read_frame(self) -> bytes:
        """
        PMS7003M 데이터 프레임(32 바이트)을 읽어 반환한다.
        유효한 헤더(0x42, 0x4D)와 체크섬을 검사한다.

        Returns:
            bytes: 유효한 전체 프레임 (길이 32)

        Raises:
            RuntimeError: 타임아웃 또는 체크섬 오류
        """
        start = time.ticks_ms()

        while time.ticks_diff(time.ticks_ms(), start) < self.timeout_ms:
            if self._uart.any() < 2:
                # 헤더를 기다림
                time.sleep_ms(10)
                continue

            # 헤더 탐색
            first = self._uart.read(1)
            if not first:
                continue
            if first[0] != self._FRAME_HEADER_HIGH:
                # 헤더가 아니면 다음 바이트로 이동
                continue

            second = self._uart.read(1)
            if not second or second[0] != self._FRAME_HEADER_LOW:
                # 두 번째 헤더 바이트가 일치하지 않으면 다시 탐색
                continue

            # 나머지 프레임(30바이트) 읽기
            rest = self._uart.read(self._FRAME_LENGTH - 2)
            if not rest or len(rest) != self._FRAME_LENGTH - 2:
                # 길이가 부족하면 계속 대기
                continue

            frame = bytes([self._FRAME_HEADER_HIGH, self._FRAME_HEADER_LOW]) + rest

            # 체크섬 검증
            if not self._validate_checksum(frame):
                # 잘못된 프레임이면 계속 다음 프레임 탐색
                continue

            return frame

        raise RuntimeError("PMS7003M frame timeout")

    @staticmethod
    def _validate_checksum(frame: bytes) -> bool:
        """
        PMS7003M 체크섬 검증

        - 마지막 2바이트는 체크섬 (상위 바이트, 하위 바이트)
        - 체크섬 = 앞의 모든 바이트 합의 하위 16비트
        """
        if len(frame) != EzDustSensor._FRAME_LENGTH:
            return False

        data = frame[:-2]
        checksum_bytes = frame[-2:]
        calc = sum(data) & 0xFFFF
        recv = (checksum_bytes[0] << 8) | checksum_bytes[1]
        return calc == recv

    def _parse_frame(self, frame: bytes):
        """
        PMS7003M 프레임에서 PM1.0 / PM2.5 / PM10 값을 파싱한다.

        - 데이터 포맷 (데이터시트 기준):
          Byte  0: 0x42
          Byte  1: 0x4D
          Byte  2: 데이터 길이 상위바이트
          Byte  3: 데이터 길이 하위바이트
          Byte  4~5 : PM1.0 (CF=1, 표준 입자, μg/m³)
          Byte  6~7 : PM2.5 (CF=1)
          Byte  8~9 : PM10  (CF=1)
          Byte 10~11: PM1.0 (대기 환경, μg/m³)
          Byte 12~13: PM2.5 (대기 환경)
          Byte 14~15: PM10  (대기 환경)

        여기서는 “대기 환경값(Byte 10~15)”을 사용한다.
        """
        if len(frame) != self._FRAME_LENGTH:
            raise ValueError("Invalid frame length")

        # 대기 환경 기준 PM 값들
        pm1_atm = (frame[10] << 8) | frame[11]
        pm2_5_atm = (frame[12] << 8) | frame[13]
        pm10_atm = (frame[14] << 8) | frame[15]

        self._pm1_0 = pm1_atm
        self._pm2_5 = pm2_5_atm
        self._pm10 = pm10_atm

    def read(self):
        """
        센서로부터 한 프레임을 읽고 PM 값을 업데이트한다.

        Returns:
            tuple: (pm1_0, pm2_5, pm10) [μg/m³]
        """
        frame = self._read_frame()
        self._parse_frame(frame)
        return self._pm1_0, self._pm2_5, self._pm10

    def get_status(self):
        """
        현재 미세먼지 상태를 dict로 반환한다.

        Returns:
            dict: {
                "pm1_0": PM1.0 (극초미세먼지, μg/m³),
                "pm2_5": PM2.5 (초미세먼지, μg/m³),
                "pm10":  PM10  (미세먼지, μg/m³),
            }
        """
        pm1_0, pm2_5, pm10 = self.read()
        return {
            "pm1_0": pm1_0,
            "pm2_5": pm2_5,
            "pm10": pm10,
        }


if __name__ == "__main__":
    # 간단한 단독 테스트용 예제 (펌웨어 통합 전용)
    # 실제 보드는 EZMaker 쉴드의 UART 핀에 맞게 수정해서 사용
    sensor = EzDustSensor(rx_pin=18, tx_pin=17)  # 예시 핀 번호
    while True:
        try:
            status = sensor.get_status()
            print(
                "PM1.0={pm1_0} μg/m³, PM2.5={pm2_5} μg/m³, PM10={pm10} μg/m³".format(
                    **status
                )
            )
        except Exception as e:
            print("Error reading PMS7003M:", e)
        time.sleep(1)


