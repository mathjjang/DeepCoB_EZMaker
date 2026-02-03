from machine import Pin, I2C
import time
from ADXL345 import ADXL345  # 사용자 업로드 드라이버 사용

# I2C 초기화 (핀 번호는 실제 연결에 따라 조정)
i2c = I2C(0, scl=Pin(47), sda=Pin(21))  # ESP32의 I2C 기본 핀 예시

# ADXL345 인스턴스 생성
accel = ADXL345(i2c)

# 메인 루프
try:
    print("ADXL345 센서 측정 시작...")
    while True:
        x = accel.xValue
        y = accel.yValue
        z = accel.zValue
        roll, pitch = accel.RP_calculate(x, y, z)

        print("X: {:5d}, Y: {:5d}, Z: {:5d} | Roll: {:6.2f}°, Pitch: {:6.2f}°".format(
            x, y, z, roll, pitch
        ))

        time.sleep(0.5)

except KeyboardInterrupt:
    print("측정 중단됨.")
