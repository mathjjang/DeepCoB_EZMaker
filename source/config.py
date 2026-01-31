"""
ESP32-S3 BLE 모드 설정 파일

이 파일은 BLE 통신 모드를 결정하는 설정값을 포함합니다.
- repl_flag = True: REPL 모드로 실행 (ble_repl_cus.py 사용)
- repl_flag = False: IoT 모드로 실행 (bleIoT.py 사용)
- EZMaker Sensor 적용
"""

# BLE 모드 설정
repl_flag = False  # True: REPL 모드, False: IoT 센서 모드

DEBUG = 10
INFO = 20
WARNING = 30
ERROR = 40
CRITICAL = 50

current_level = INFO

firmware_source = "1.3.6"