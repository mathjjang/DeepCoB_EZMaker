"""
EZMaker 전용 전류센서(EZCURR, INA219 기반) 드라이버

- 센서: INA219 (I2C 전류/전압/전력 센서)
- 측정:
    - 버스 전압 (Vbus, 보통 0~26V)
    - 샌트 전압 (shunt, mV 단위)
    - 전류 (mA)
    - 전력 (mW, W)

주의:
- 실제 샌트 저항 값(Rshunt)이 몇 Ω 인지에 따라 보정이 필요합니다.
- EZMaker 보드의 회로 설계에 맞춰 shunt_ohms, current_lsb 등을 조정해야 합니다.
"""

import machine
import time


class EzCurrSensor:
    """
    INA219 기반 EZMaker 전류센서 드라이버

    사용 예:
        i2c = machine.SoftI2C(scl=machine.Pin(40), sda=machine.Pin(41))
        sensor = EzCurrSensor(i2c)
        status = sensor.get_status()
        print(status["voltage"], status["current_mA"], status["power_mW"])
    """

    # INA219 레지스터 주소
    REG_CONFIG = 0x00
    REG_SHUNT_VOLTAGE = 0x01
    REG_BUS_VOLTAGE = 0x02
    REG_POWER = 0x03
    REG_CURRENT = 0x04
    REG_CALIBRATION = 0x05

    def __init__(self, i2c, addr=0x40, shunt_ohms=0.1, max_expected_amps=3.2):
        """
        EzCurrSensor 초기화

        Args:
            i2c (machine.I2C or SoftI2C): I2C 객체
            addr (int): INA219 I2C 주소 (기본 0x40)
            shunt_ohms (float): 샌트 저항 값 (Ω)
            max_expected_amps (float): 예상 최대 전류 (A)
        """
        self.i2c = i2c
        self.addr = addr
        self.shunt_ohms = shunt_ohms
        self.max_expected_amps = max_expected_amps

        # 보정 관련 값 (데이터시트 공식 기반 단순 버전)
        # current_LSB ~ max_current / 32767
        self.current_lsb = max_expected_amps / 32767.0  # A/LSB
        # 예: max_expected_amps=3.2A => current_lsb ≈ 9.76e-5 A/LSB

        # CAL = trunc(0.04096 / (current_lsb * shunt_ohms))
        self.calibration_value = int(0.04096 / (self.current_lsb * self.shunt_ohms))

        # 실제 mA 변환에 사용할 계수
        # current_LSB(A) * 1000 = mA/LSB
        self._current_LSB_mA = self.current_lsb * 1000.0

        # 전력 LSB = 20 * current_LSB (INA219 데이터시트)
        self._power_LSB_mW = 20.0 * self._current_LSB_mA  # mW/LSB

        # 센서 구성
        self._configure()

    # -------------------------------
    # 저수준 I2C 헬퍼
    # -------------------------------
    def _write_register(self, reg, value):
        """
        16비트 레지스터 쓰기 (big-endian)
        """
        data = bytearray(2)
        data[0] = (value >> 8) & 0xFF
        data[1] = value & 0xFF
        self.i2c.writeto_mem(self.addr, reg, data)

    def _read_register(self, reg):
        """
        16비트 레지스터 읽기 (big-endian)
        """
        data = self.i2c.readfrom_mem(self.addr, reg, 2)
        return (data[0] << 8) | data[1]

    # -------------------------------
    # 센서 설정
    # -------------------------------
    def _configure(self):
        """
        INA219 구성 레지스터 및 보정 레지스터 설정
        """
        # 1) 보정값 설정
        try:
            self._write_register(self.REG_CALIBRATION, self.calibration_value)
        except OSError:
            # I2C 통신 실패 시 무시 (상위에서 처리)
            return

        # 2) 구성 레지스터 설정
        # - Bus Voltage Range: 32V
        # - Gain: /8 (320mV)
        # - Bus ADC: 12bit
        # - Shunt ADC: 12bit
        # - Mode: Shunt and Bus, Continuous
        config = 0x019F  # 데이터시트 예제 설정값 사용
        try:
            self._write_register(self.REG_CONFIG, config)
        except OSError:
            return

    # -------------------------------
    # 측정 API
    # -------------------------------
    def read_bus_voltage_voltage(self):
        """
        버스 전압(V) 반환
        """
        try:
            value = self._read_register(self.REG_BUS_VOLTAGE)
        except OSError:
            return None

        # 하위 3비트는 상태 플래그, 상위 13비트가 실제 데이터
        value >>= 3
        # LSB = 4mV
        voltage = value * 0.004  # V
        return voltage

    def read_current_mA(self):
        """
        전류(mA) 반환
        """
        try:
            raw = self._read_register(self.REG_CURRENT)
        except OSError:
            return None

        # signed 값 처리
        if raw & 0x8000:
            raw -= 1 << 16

        current_mA = raw * self._current_LSB_mA
        return current_mA

    def read_power_mW(self):
        """
        전력(mW) 반환
        """
        try:
            raw = self._read_register(self.REG_POWER)
        except OSError:
            return None

        power_mW = raw * self._power_LSB_mW
        return power_mW

    def get_status(self):
        """
        전류센서 상태를 딕셔너리로 반환

        Returns:
            dict: {
                "voltage": float or None,     # 버스 전압 (V)
                "current_mA": float or None,  # 전류 (mA)
                "power_mW": float or None,    # 전력 (mW)
            }
        """
        voltage = self.read_bus_voltage_voltage()
        current_mA = self.read_current_mA()
        power_mW = self.read_power_mW()

        return {
            "voltage": voltage,
            "current_mA": current_mA,
            "power_mW": power_mW,
        }


if __name__ == "__main__":
    print("EzCurrSensor (INA219) 드라이버 모듈입니다.")
    print("보드에서 직접 사용 시 SoftI2C 생성 후 EzCurrSensor(i2c) 로 초기화하세요.")


