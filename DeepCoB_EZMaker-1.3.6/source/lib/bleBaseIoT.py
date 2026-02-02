# bleBaseIoT.py

import bluetooth
import struct
from micropython import const
import micropython  ### CHANGED: micropython 모듈 추가
import logger  # 로깅 시스템 임포트

_IRQ_CENTRAL_CONNECT    = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE        = const(3)

_FLAG_WRITE  = const(0x0008)
_FLAG_NOTIFY = const(0x0010)

# ----------------------------
# 1) 기존 LED/CAM
# ----------------------------
_LED_CAM_UUID = bluetooth.UUID("11112222-3333-4444-5555-666677778888")

_LED_CHAR = (
    bluetooth.UUID("11112222-3333-4444-5555-666677778889"),  # Write-only
    _FLAG_WRITE,
)
_CAM_CHAR = (
    bluetooth.UUID("11112222-3333-4444-5555-66667777888A"),  # Write+Notify
    _FLAG_WRITE | _FLAG_NOTIFY,
)

# REPL 모드 전환 특성 추가
_REPL_CHAR = (
    bluetooth.UUID("11112222-3333-4444-5555-666677778893"),  # Write+Notify
    _FLAG_WRITE | _FLAG_NOTIFY,
)

# [NEW] UPGRADE CHAR - 펌웨어 업그레이드 특성 추가
_UPGRADE_CHAR = (
    bluetooth.UUID("11112222-3333-4444-5555-666677778898"),  # Write+Notify
    _FLAG_WRITE | _FLAG_NOTIFY,
)

_LED_CAM_SERVICE = (
    _LED_CAM_UUID,
    (
        _LED_CHAR,
        _CAM_CHAR,
        _REPL_CHAR,  # REPL 모드 전환 특성 추가
        _UPGRADE_CHAR,  # 펌웨어 업그레이드 특성 추가
    ),
)

# ----------------------------
# 2) SENSOR SERVICE
#    - ULTRA, DHT, [NEW] SERVO, [NEW] NEOPIXEL, [NEW] TOUCH, [NEW] LIGHT, [NEW] BUZZER, [NEW] GYRO
# ----------------------------
_SENSOR_UUID = bluetooth.UUID("11112222-3333-4444-5555-66667777888C")

_ULTRA_CHAR = (
    bluetooth.UUID("11112222-3333-4444-5555-66667777888B"),  # Write+Notify
    _FLAG_WRITE | _FLAG_NOTIFY,
)

_DHT_CHAR = (
    bluetooth.UUID("11112222-3333-4444-5555-66667777888D"),  # Write+Notify
    _FLAG_WRITE | _FLAG_NOTIFY,
)

# [NEW] SERVO CHAR
_SERVO_CHAR = (
    bluetooth.UUID("11112222-3333-4444-5555-66667777888E"),  # Write-only
    _FLAG_WRITE,
)

# [NEW] NEOPIXEL CHAR - 센서 서비스에 포함
_NEO_CHAR = (
    bluetooth.UUID("11112222-3333-4444-5555-66667777888f"),  # Write-only
    _FLAG_WRITE,
)



# [NEW] TOUCH CHAR - 센서 서비스에 포함
_TOUCH_CHAR = (
    bluetooth.UUID("11112222-3333-4444-5555-666677778890"),  # Write+Notify
    _FLAG_WRITE | _FLAG_NOTIFY,
)

# [NEW] LIGHT CHAR - 센서 서비스에 포함
_LIGHT_CHAR = (
    bluetooth.UUID("11112222-3333-4444-5555-666677778891"),  # Write+Notify
    _FLAG_WRITE | _FLAG_NOTIFY,
)

# [NEW] BUZZER CHAR - 센서 서비스에 포함
_BUZZER_CHAR = (
    bluetooth.UUID("11112222-3333-4444-5555-666677778892"),  # Write+Notify
    _FLAG_WRITE | _FLAG_NOTIFY,
)

# [NEW] GYRO CHAR - 자이로스코프 센서 추가 (기존 DeepCo 공통)
_GYRO_CHAR = (
    bluetooth.UUID("11112222-3333-4444-5555-666677778894"),  # Write+Notify
    _FLAG_WRITE | _FLAG_NOTIFY,
)

# [NEW] DUST CHAR - 먼지 센서 추가
_DUST_CHAR = (
    bluetooth.UUID("11112222-3333-4444-5555-666677778895"),  # Write+Notify
    _FLAG_WRITE | _FLAG_NOTIFY,
)

# [NEW] DCMOTOR CHAR - DC 모터 추가
_DCMOTOR_CHAR = (
    bluetooth.UUID("11112222-3333-4444-5555-666677778896"),  # Write-only
    _FLAG_WRITE,
)

# [NEW] EZ-LASER CHAR - EZMaker 전용 레이저 모듈 (별도 UUID 대역 사용)
_EZ_LASER_CHAR = (
    bluetooth.UUID("22223333-4444-5555-6666-777788889001"),  # Write+Notify
    _FLAG_WRITE | _FLAG_NOTIFY,
)

# [NEW] EZ-GYRO CHAR - EZMaker 전용 자이로센서 (ICM20948, 별도 UUID 대역)
_EZ_GYRO_CHAR = (
    bluetooth.UUID("22223333-4444-5555-6666-777788889002"),  # Write+Notify
    _FLAG_WRITE | _FLAG_NOTIFY,
)

# [NEW] EZ-PRESSURE CHAR - EZMaker 전용 기압센서 (BMP280, 별도 UUID 대역)
_EZ_PRESS_CHAR = (
    bluetooth.UUID("22223333-4444-5555-6666-777788889003"),  # Write+Notify
    _FLAG_WRITE | _FLAG_NOTIFY,
)

# [NEW] EZ-CO2 CHAR - EZMaker 전용 이산화탄소 센서 (SCD40, 별도 UUID 대역)
_EZ_CO2_CHAR = (
    bluetooth.UUID("22223333-4444-5555-6666-777788889004"),  # Write+Notify
    _FLAG_WRITE | _FLAG_NOTIFY,
)

# [NEW] EZMaker DIY-A CHAR - EZMaker 전용 DIY 아날로그 전압 센서
_EZ_DIYA_CHAR = (
    bluetooth.UUID("22223333-4444-5555-6666-777788889005"),  # Write+Notify
    _FLAG_WRITE | _FLAG_NOTIFY,
)

# [NEW] EZMaker DIY-B CHAR - EZMaker 전용 전류/전도도 아날로그 센서
_EZ_DIYB_CHAR = (
    bluetooth.UUID("22223333-4444-5555-6666-777788889006"),  # Write+Notify
    _FLAG_WRITE | _FLAG_NOTIFY,
)

# [NEW] EZMaker HALL CHAR - EZMaker 전용 자기장 센서
_EZ_HALL_CHAR = (
    bluetooth.UUID("22223333-4444-5555-6666-777788889007"),  # Write+Notify
    _FLAG_WRITE | _FLAG_NOTIFY,
)

# [NEW] EZ-LCD CHAR - I2C 캐릭터 LCD (16x2 / 20x4, EZMaker 전용)
_EZ_LCD_CHAR = (
    bluetooth.UUID("22223333-4444-5555-6666-777788889008"),  # Write+Notify
    _FLAG_WRITE | _FLAG_NOTIFY,
)

# [NEW] EZMaker LIGHT CHAR - EZMaker 전용 밝기센서 (별도 UUID 대역)
_EZ_LIGHT_CHAR = (
    bluetooth.UUID("22223333-4444-5555-6666-777788889009"),  # Write+Notify
    _FLAG_WRITE | _FLAG_NOTIFY,
)

# [NEW] EZMaker VOLT CHAR - EZMaker 전용 전압센서 (0~25V, 별도 UUID 대역)
_EZ_VOLT_CHAR = (
    bluetooth.UUID("22223333-4444-5555-6666-77778888900A"),  # Write+Notify
    _FLAG_WRITE | _FLAG_NOTIFY,
)

# [NEW] EZMaker CURR CHAR - EZMaker 전용 전류센서 (INA219, I2C)
_EZ_CURR_CHAR = (
    bluetooth.UUID("22223333-4444-5555-6666-77778888900B"),  # Write+Notify
    _FLAG_WRITE | _FLAG_NOTIFY,
)

# [NEW] EZMaker HUMAN PRESENCE SENSOR CHAR - EZMaker 전용 인체감지 센서 (별도 UUID 대역)
_EZ_HUMAN_CHAR = (
    bluetooth.UUID("22223333-4444-5555-6666-77778888900C"),  # Write+Notify
    _FLAG_WRITE | _FLAG_NOTIFY,
)

# [NEW] EZMaker THERMAL PROBE CHAR - EZMaker 수중/접촉 온도센서 (DS18B20, 별도 UUID 대역)
_EZ_THERMAL_CHAR = (
    bluetooth.UUID("22223333-4444-5555-6666-77778888900D"),  # Write+Notify
    _FLAG_WRITE | _FLAG_NOTIFY,
)

# [NEW] EZMaker SOUND CHAR - EZMaker 전용 소리센서 (마이크, 별도 UUID 대역)
_EZ_SOUND_CHAR = (
    bluetooth.UUID("22223333-4444-5555-6666-77778888900E"),  # Write+Notify
    _FLAG_WRITE | _FLAG_NOTIFY,
)

# [NEW] EZMaker WEIGHT CHAR - EZMaker 전용 무게센서 (HX711, 별도 UUID 대역)
_EZ_WEIGHT_CHAR = (
    bluetooth.UUID("22223333-4444-5555-6666-77778888900F"),  # Write+Notify
    _FLAG_WRITE | _FLAG_NOTIFY,
)

# [NEW] EZMaker FINE DUST CHAR - EZMaker 전용 미세먼지 센서 (PMS7003M, 별도 UUID 대역)
_EZ_DUST_CHAR = (
    bluetooth.UUID("22223333-4444-5555-6666-777788889010"),  # Write+Notify
    _FLAG_WRITE | _FLAG_NOTIFY,
)

# [NEW] HEART RATE CHAR - 심장박동 센서 추가
_HEART_RATE_CHAR = (
    bluetooth.UUID("11112222-3333-4444-5555-666677778897"),  # Write+Notify
    _FLAG_WRITE | _FLAG_NOTIFY,
)

# [NEW] SOIL MOISTURE CHAR - 토양수분센서 추가
_SOIL_CHAR = (
    bluetooth.UUID("11112222-3333-4444-5555-666677778899"),  # Write+Notify
    _FLAG_WRITE | _FLAG_NOTIFY,
)

# [NEW] RAIN SENSOR CHAR - 빗방울센서 추가
_RAIN_CHAR = (
    bluetooth.UUID("11112222-3333-4444-5555-66667777889A"),  # Write+Notify
    _FLAG_WRITE | _FLAG_NOTIFY,
)

_SENSOR_SERVICE = (
    _SENSOR_UUID,
    (
        _ULTRA_CHAR,   # 초음파
        _DHT_CHAR,     # DHT
        _SERVO_CHAR,   # 서보
        _NEO_CHAR,     # NeoPixel
        _EZ_LCD_CHAR,  # LCD (I2C 캐릭터 LCD, EZMaker 전용)
        _TOUCH_CHAR,   # 터치센서
        _LIGHT_CHAR,   # 조도센서
        _BUZZER_CHAR,  # 버저
        _GYRO_CHAR,    # 자이로센서 (DeepCo 공통)
        _DUST_CHAR,    # 먼지센서
        _DCMOTOR_CHAR, # DC 모터
        _EZ_LASER_CHAR,   # 레이저 모듈 (EZMaker 전용)
        _HEART_RATE_CHAR, # 심장박동 센서
        _SOIL_CHAR,    # 토양수분센서
        _RAIN_CHAR,    # 빗방울센서
        _EZ_HUMAN_CHAR,   # EZMaker 전용 인체감지 센서
        _EZ_GYRO_CHAR, # EZMaker 전용 자이로센서 (ICM20948)
        _EZ_PRESS_CHAR, # EZMaker 전용 기압센서 (BMP280)
        _EZ_CO2_CHAR,  # EZMaker 전용 이산화탄소 센서 (SCD40)
        _EZ_DIYA_CHAR,    # EZMaker DIY-A 아날로그 센서
        _EZ_DIYB_CHAR,    # EZMaker DIY-B 전류/전도도 아날로그 센서
        _EZ_HALL_CHAR,    # EZMaker 자기장 센서
        _EZ_LIGHT_CHAR, # EZMaker 전용 밝기센서
        _EZ_VOLT_CHAR,  # EZMaker 전용 전압센서
        _EZ_CURR_CHAR,  # EZMaker 전용 전류센서 (INA219)
        _EZ_THERMAL_CHAR,  # EZMaker 수중/접촉 온도센서 (DS18B20)
        _EZ_SOUND_CHAR,  # EZMaker 소리센서 (마이크)
        _EZ_WEIGHT_CHAR,  # EZMaker 무게센서 (HX711)
        _EZ_DUST_CHAR,    # EZMaker 미세먼지 센서 (PMS7003M)
    ),
)

# 전체 GATT Services
_ALL_SERVICES = (
    _LED_CAM_SERVICE,
    _SENSOR_SERVICE,
)

def advertising_payload(name=None):
    adv_data = bytearray()
    # Flags (LE General Disc Mode + BR/EDR not supported)
    adv_data += bytearray([2, 0x01, 0x06])
    if name:
        name_b = name.encode() if isinstance(name, str) else name
        adv_data += bytearray([len(name_b)+1, 0x09]) + name_b
    return adv_data, None

### 모든 핸들러에 대한 스케줄링 함수 추가
def scheduled_handler(arg):
    # arg: (bleuart, handler_func, conn_handle, cmd)
    bleuart, handler_func, conn_handle, cmd = arg
    
    # 함수 이름으로 판단하여 다르게 처리
    if handler_func.__name__ in ['connect_handler', 'disconnect_handler']:
        # 연결/해제 핸들러는 conn_handle만 인자로 받음
        handler_func(conn_handle)
    else:
        # 다른 핸들러는 conn_handle과 cmd 두 인자를 받음
        handler_func(conn_handle, cmd)

class BLEUART:
    """
    - LED/CAM
    - SENSOR (ULTRA + DHT + SERVO)
    """
    def __init__(self, ble, name="MyIoTBoard", rxbuf=256):
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(self._irq_handler)

        # MTU 크기 증가 (ESP32에서 지원하는 경우)
        try:
            self._ble.config(mtu=185)  # 최대 MTU 크기로 설정
            logger.info("MTU size increased to 185 bytes", "BLE")
        except Exception as e:
            logger.warning(f"Could not increase MTU size: {e}", "BLE")

        # Services 등록
        (
            (self._led_handle, self._cam_handle, self._repl_handle, self._upgrade_handle),  # 업그레이드 핸들 추가
            (self._ultra_handle, self._dht_handle, self._servo_handle, self._neo_handle,
             self._lcd_handle,
             self._touch_handle, self._light_handle, self._buzzer_handle, self._gyro_handle,
             self._dust_handle, self._dcmotor_handle, self._laser_handle,
             self._heart_rate_handle, self._soil_handle, self._rain_handle, self._human_handle,
             self._ez_gyro_handle, self._ez_press_handle, self._ez_co2_handle,
             self._diya_handle, self._diyb_handle, self._hall_handle,
             self._ez_light_handle, self._ez_volt_handle, self._ez_curr_handle,
             self._ez_thermal_handle, self._ez_sound_handle, self._ez_weight_handle,
             self._ez_dust_handle),  # EZMaker 전용 자이로/기압/CO2/DIY/자기장/밝기/전압/전류/온도/소리/무게/미세먼지 센서 핸들 추가
        ) = self._ble.gatts_register_services(_ALL_SERVICES)

        # 🔥 BLE 특성 버퍼 크기 설정 (명령어 잘림 방지)
        try:
            # 버저 특성 버퍼 크기 증가 (긴 명령어 지원)
            self._ble.gatts_set_buffer(self._buzzer_handle, 64, True)
            logger.info("Buzzer characteristic buffer set to 64 bytes", "BLE")
            
            # 다른 주요 특성들도 버퍼 크기 증가
            #self._ble.gatts_set_buffer(self._led_handle, 64, True)
            #self._ble.gatts_set_buffer(self._cam_handle, 64, True)
            #self._ble.gatts_set_buffer(self._servo_handle, 64, True)
            self._ble.gatts_set_buffer(self._neo_handle, 64, True)
            #self._ble.gatts_set_buffer(self._dcmotor_handle, 64, True)


            self._ble.gatts_set_buffer(self._lcd_handle, 200, True)
            logger.info("LCD characteristic buffer set to 64 bytes", "BLE")
            
            # 펌웨어 업그레이드용 버퍼 크기 대폭 증가 (Base64 청크 처리용)
            self._ble.gatts_set_buffer(self._upgrade_handle, 512, True)  # 64 → 185바이트
            logger.info("Upgrade characteristic buffer increased to 185 bytes", "BLE")
        except Exception as e:
            logger.warning(f"Could not set characteristic buffer sizes: {e}", "BLE")

        self._connections = set()

        # 핸들러
        self._led_handler   = None
        self._cam_handler   = None
        self._repl_handler  = None  # REPL 핸들러 추가
        self._ultra_handler = None
        self._dht_handler   = None
        self._servo_handler = None  # [NEW] 서보
        self._neopixel_handler = None  # [NEW] NeoPixel
        self._lcd_handler = None  # [NEW] LCD (I2C 캐릭터 LCD)
        self._touch_handler = None  # [NEW] 터치센서
        self._light_handler = None  # [NEW] 조도센서
        self._buzzer_handler = None  # [NEW] 버저
        self._gyro_handler = None  # [NEW] 자이로센서 (DeepCo 공통)
        self._dust_handler = None  # [NEW] 먼지센서
        self._dcmotor_handler = None  # [NEW] DC 모터
        self._laser_handler = None  # [NEW] 레이저 모듈 (EZMaker 전용)
        self._heart_rate_handler = None  # [NEW] 심장박동 센서
        self._soil_handler = None  # [NEW] 토양수분센서
        self._rain_handler = None  # [NEW] 빗방울센서
        self._human_handler = None  # [NEW] 인체감지 센서
        self._ez_gyro_handler = None  # [NEW] EZMaker 전용 자이로센서
        self._ez_press_handler = None  # [NEW] EZMaker 전용 기압센서
        self._ez_co2_handler = None  # [NEW] EZMaker 전용 이산화탄소 센서
        self._diya_handler = None  # [NEW] EZMaker DIY-A 센서
        self._diyb_handler = None  # [NEW] EZMaker DIY-B 센서
        self._hall_handler = None  # [NEW] EZMaker 자기장 센서
        self._ez_light_handler = None  # [NEW] EZMaker 밝기센서
        self._ez_volt_handler = None  # [NEW] EZMaker 전압센서
        self._ez_curr_handler = None  # [NEW] EZMaker 전류센서 (INA219)
        self._ez_thermal_handler = None  # [NEW] EZMaker 수중/접촉 온도센서
        self._ez_sound_handler = None  # [NEW] EZMaker 소리센서
        self._ez_weight_handler = None  # [NEW] EZMaker 무게센서
        self._ez_dust_handler = None  # [NEW] EZMaker 미세먼지 센서 (PMS7003M)
        self._connect_handler = None
        self._disconnect_handler = None
        self._upgrade_handler = None  # [NEW] 펌웨어 업그레이드 핸들러

        # 광고
        self._payload, self._rspdata = advertising_payload(name)
        self._advertise()

    # -------------------------
    # Handler 등록
    # -------------------------
    def set_led_handler(self, fn):
        """fn(conn_handle, cmd_str) -> handle LED commands"""
        self._led_handler = fn

    def set_cam_handler(self, fn):
        """fn(conn_handle, cmd_str) -> handle CAM commands"""
        self._cam_handler = fn
        
    def set_repl_handler(self, fn):
        """fn(conn_handle, cmd_str) -> handle REPL mode switching commands"""
        self._repl_handler = fn

    def set_ultrasonic_handler(self, fn):
        """fn(conn_handle, cmd_str) -> handle ultrasonic commands"""
        self._ultra_handler = fn

    def set_dht_handler(self, fn):
        self._dht_handler = fn

    def set_servo_handler(self, fn):
        """
        fn(conn_handle, cmd_str) -> handle servo commands (e.g. 'SERVO 90')
        """
        self._servo_handler = fn
        
    def set_neopixel_handler(self, fn):
        """
        fn(conn_handle, cmd_str) -> handle neopixel commands
        """
        self._neopixel_handler = fn

    def set_lcd_handler(self, fn):
        """
        fn(conn_handle, cmd_str) -> handle LCD (I2C character LCD) commands
        """
        self._lcd_handler = fn

    def set_touch_handler(self, fn):
        """
        fn(conn_handle, cmd_str) -> handle touch commands
        """
        self._touch_handler = fn

    def set_light_handler(self, fn):
        """
        fn(conn_handle, cmd_str) -> handle light sensor commands
        """
        self._light_handler = fn
    
    def set_buzzer_handler(self, fn):
        """
        fn(conn_handle, cmd_str) -> handle buzzer commands
        """
        self._buzzer_handler = fn
    
    def set_gyro_handler(self, fn):
        """
        fn(conn_handle, cmd_str) -> handle gyroscope sensor commands
        """
        self._gyro_handler = fn
    
    def set_ez_gyro_handler(self, fn):
        """
        fn(conn_handle, cmd_str) -> handle EZMaker gyroscope (ICM20948) commands
        """
        self._ez_gyro_handler = fn
    
    def set_ez_press_handler(self, fn):
        """
        fn(conn_handle, cmd_str) -> handle EZMaker barometric pressure (BMP280) commands
        """
        self._ez_press_handler = fn
    
    def set_ez_co2_handler(self, fn):
        """
        fn(conn_handle, cmd_str) -> handle EZMaker CO2 sensor (SCD40) commands
        """
        self._ez_co2_handler = fn
    
    def set_dust_handler(self, fn):
        """
        fn(conn_handle, cmd_str) -> handle dust sensor commands
        """
        self._dust_handler = fn
    
    def set_dcmotor_handler(self, fn):
        """
        fn(conn_handle, cmd_str) -> handle DC motor commands
        """
        self._dcmotor_handler = fn
    
    def set_laser_handler(self, fn):
        """
        fn(conn_handle, cmd_str) -> handle laser module commands
        """
        self._laser_handler = fn
    
    def set_heart_rate_handler(self, fn):
        """
        fn(conn_handle, cmd_str) -> handle heart rate sensor commands
        """
        self._heart_rate_handler = fn
    
    def set_soil_handler(self, fn):
        """
        fn(conn_handle, cmd_str) -> handle soil moisture sensor commands
        """
        self._soil_handler = fn
    
    def set_rain_handler(self, fn):
        """
        fn(conn_handle, cmd_str) -> handle rain sensor commands
        """
        self._rain_handler = fn

    def set_human_handler(self, fn):
        """
        fn(conn_handle, cmd_str) -> handle human presence sensor commands
        """
        self._human_handler = fn
    
    def set_ez_light_handler(self, fn):
        """
        fn(conn_handle, cmd_str) -> handle EZMaker light sensor commands
        """
        self._ez_light_handler = fn
    
    def set_diya_handler(self, fn):
        """
        fn(conn_handle, cmd_str) -> handle DIY-A sensor commands
        """
        self._diya_handler = fn
    
    def set_diyb_handler(self, fn):
        """
        fn(conn_handle, cmd_str) -> handle DIY-B sensor commands
        """
        self._diyb_handler = fn
    
    def set_hall_handler(self, fn):
        """
        fn(conn_handle, cmd_str) -> handle Hall sensor commands
        """
        self._hall_handler = fn

    def set_ez_volt_handler(self, fn):
        """
        fn(conn_handle, cmd_str) -> handle EZMaker voltage sensor commands
        """
        self._ez_volt_handler = fn

    def set_ez_curr_handler(self, fn):
        """
        fn(conn_handle, cmd_str) -> handle EZMaker current sensor (INA219) commands
        """
        self._ez_curr_handler = fn
    
    def set_ez_thermal_handler(self, fn):
        """
        fn(conn_handle, cmd_str) -> handle EZMaker thermal probe (DS18B20) commands
        """
        self._ez_thermal_handler = fn

    def set_ez_sound_handler(self, fn):
        """
        fn(conn_handle, cmd_str) -> handle EZMaker sound sensor (microphone) commands
        """
        self._ez_sound_handler = fn

    def set_ez_weight_handler(self, fn):
        """
        fn(conn_handle, cmd_str) -> handle EZMaker weight sensor (HX711) commands
        """
        self._ez_weight_handler = fn

    def set_ez_dust_handler(self, fn):
        """
        fn(conn_handle, cmd_str) -> handle EZMaker fine dust sensor (PMS7003M) commands
        """
        self._ez_dust_handler = fn
    
    def set_diyb_handler(self, fn):
        """
        fn(conn_handle, cmd_str) -> handle DIY-B sensor commands
        """
        self._diyb_handler = fn
    
    def set_connect_handler(self, fn):
        """fn(conn_handle) -> 장치 연결 시 호출될 함수"""
        self._connect_handler = fn

    def set_disconnect_handler(self, fn):
        """fn(conn_handle) -> 장치 연결 해제 시 호출될 함수"""
        self._disconnect_handler = fn

    def set_upgrade_handler(self, fn):
        """fn(conn_handle, cmd_str) -> handle firmware upgrade commands"""
        self._upgrade_handler = fn
    # -------------------------
    # Notify 함수
    # -------------------------
    def cam_notify(self, data):
        for c in self._connections:
            self._ble.gatts_notify(c, self._cam_handle, data)
            
    def repl_notify(self, data):
        """REPL 모드 상태 변경 통지"""
        for c in self._connections:
            self._ble.gatts_notify(c, self._repl_handle, data)

    def upgrade_notify(self, data):
        """펌웨어 업그레이드 상태 통지"""
        for c in self._connections:
            self._ble.gatts_notify(c, self._upgrade_handle, data)

    def ultrasonic_notify(self, data):
        for c in self._connections:
            self._ble.gatts_notify(c, self._ultra_handle, data)

    def dht_notify(self, data):
        for c in self._connections:
            self._ble.gatts_notify(c, self._dht_handle, data)

    def touch_notify(self, data):
        for c in self._connections:
            self._ble.gatts_notify(c, self._touch_handle, data)

    def light_notify(self, data):
        for c in self._connections:
            self._ble.gatts_notify(c, self._light_handle, data)
            
    def buzzer_notify(self, data):
        for c in self._connections:
            self._ble.gatts_notify(c, self._buzzer_handle, data)
            
    def gyro_notify(self, data):
        """자이로스코프 센서 데이터 알림"""
        for c in self._connections:
            self._ble.gatts_notify(c, self._gyro_handle, data)

    def ez_gyro_notify(self, data):
        """EZMaker 자이로센서(ICM20948) 데이터 알림"""
        for c in self._connections:
            self._ble.gatts_notify(c, self._ez_gyro_handle, data)

    def ez_press_notify(self, data):
        """EZMaker 기압센서(BMP280) 데이터 알림"""
        for c in self._connections:
            self._ble.gatts_notify(c, self._ez_press_handle, data)

    def ez_co2_notify(self, data):
        """EZMaker CO2 센서(SCD40) 데이터 알림"""
        for c in self._connections:
            self._ble.gatts_notify(c, self._ez_co2_handle, data)

    def led_notify(self, data):
        for c in self._connections:
            self._ble.gatts_notify(c, self._led_handle, data)
    
    def neopixel_notify(self, data):
        for c in self._connections:
            self._ble.gatts_notify(c, self._neo_handle, data)

    def lcd_notify(self, data):
        """LCD (I2C 캐릭터 LCD) 상태 알림"""
        for c in self._connections:
            self._ble.gatts_notify(c, self._lcd_handle, data)
    
    def ez_light_notify(self, data):
        """EZMaker 밝기센서 데이터 알림"""
        for c in self._connections:
            self._ble.gatts_notify(c, self._ez_light_handle, data)

    def ez_volt_notify(self, data):
        """EZMaker 전압센서 데이터 알림"""
        for c in self._connections:
            self._ble.gatts_notify(c, self._ez_volt_handle, data)

    def ez_curr_notify(self, data):
        """EZMaker 전류센서(INA219) 데이터 알림"""
        for c in self._connections:
            self._ble.gatts_notify(c, self._ez_curr_handle, data)
    
    def ez_thermal_notify(self, data):
        """EZMaker 수중/접촉 온도센서(EZTHERMAL) 데이터 알림"""
        for c in self._connections:
            self._ble.gatts_notify(c, self._ez_thermal_handle, data)
    
    def ez_sound_notify(self, data):
        """EZMaker 소리센서(EZSOUND) 데이터 알림"""
        for c in self._connections:
            self._ble.gatts_notify(c, self._ez_sound_handle, data)

    def ez_weight_notify(self, data):
        """EZMaker 무게센서(EZWEIGHT, HX711) 데이터 알림"""
        for c in self._connections:
            self._ble.gatts_notify(c, self._ez_weight_handle, data)

    def ez_dust_notify(self, data):
        """EZMaker 미세먼지 센서(EZDUST, PMS7003M) 데이터 알림"""
        for c in self._connections:
            self._ble.gatts_notify(c, self._ez_dust_handle, data)
            
    def servo_notify(self, data):
        for c in self._connections:
            self._ble.gatts_notify(c, self._servo_handle, data)

    def dust_notify(self, data):
        """먼지 센서 데이터 알림"""
        for c in self._connections:
            self._ble.gatts_notify(c, self._dust_handle, data)

    def dcmotor_notify(self, data):
        """DC 모터 상태 알림"""
        for c in self._connections:
            self._ble.gatts_notify(c, self._dcmotor_handle, data)
    
    def laser_notify(self, data):
        """레이저 모듈 상태 알림 (EZMaker 전용)"""
        for c in self._connections:
            self._ble.gatts_notify(c, self._laser_handle, data)

    def heart_rate_notify(self, data):
        """심장박동 센서 데이터 알림"""
        for c in self._connections:
            self._ble.gatts_notify(c, self._heart_rate_handle, data)

    def soil_notify(self, data):
        """토양수분센서 데이터 알림"""
        for c in self._connections:
            self._ble.gatts_notify(c, self._soil_handle, data)

    def rain_notify(self, data):
        """빗방울센서 데이터 알림"""
        for c in self._connections:
            self._ble.gatts_notify(c, self._rain_handle, data)
    
    def human_notify(self, data):
        """인체감지 센서 데이터 알림"""
        for c in self._connections:
            self._ble.gatts_notify(c, self._human_handle, data)
    
    def diyb_notify(self, data):
        """DIY-B 센서 데이터 알림"""
        for c in self._connections:
            self._ble.gatts_notify(c, self._diyb_handle, data)
    
    def hall_notify(self, data):
        """자기장 센서 데이터 알림"""
        for c in self._connections:
            self._ble.gatts_notify(c, self._hall_handle, data)

    def diya_notify(self, data):
        """DIY-A 센서 데이터 알림 (EZMaker 전용)"""
        for c in self._connections:
            self._ble.gatts_notify(c, self._diya_handle, data)

    # -------------------------
    # BLE 이벤트
    # -------------------------
    def _irq_handler(self, event, data):
        # BLE IRQ 이벤트 핸들러
        global _conn_handle, _write_buf
        
        if event == _IRQ_CENTRAL_CONNECT:
            # 연결 이벤트 발생
            conn_handle, addr_type, addr = data
            _conn_handle = conn_handle
            
            # 연결 시도 기기의 MAC 주소를 가져오는 방법
            addr_str = ':'.join('%02X' % b for b in addr)
            logger.info(f"연결 시도 - Handle: {conn_handle}, MAC: {addr_str}", "BLE")

            # 연결 추가
            self._connections.add(conn_handle)
            
            # 연결 핸들러 호출
            if self._connect_handler:
                micropython.schedule(scheduled_handler, (self, self._connect_handler, conn_handle, None))

        elif event == _IRQ_CENTRAL_DISCONNECT:
            (conn_handle, _, _) = data
            if conn_handle in self._connections:
                self._connections.remove(conn_handle)
            # 연결 해제 이벤트 핸들러 호출
            if self._disconnect_handler:
                micropython.schedule(scheduled_handler, (self, self._disconnect_handler, conn_handle, None))
            self._advertise()

        elif event == _IRQ_GATTS_WRITE:
            (conn_handle, attr_handle) = data
            if conn_handle not in self._connections:
                return

            # LED
            if attr_handle == self._led_handle and self._led_handler:
                raw = self._ble.gatts_read(self._led_handle)
                cmd = raw.decode().strip().upper()
                micropython.schedule(scheduled_handler, (self, self._led_handler, conn_handle, cmd))

            # CAM
            elif attr_handle == self._cam_handle and self._cam_handler:
                raw = self._ble.gatts_read(self._cam_handle)
                cmd = raw.decode().strip().upper()
                micropython.schedule(scheduled_handler, (self, self._cam_handler, conn_handle, cmd))
                
            # REPL
            elif attr_handle == self._repl_handle and self._repl_handler:
                raw = self._ble.gatts_read(self._repl_handle)
                cmd = raw.decode().strip().upper()
                micropython.schedule(scheduled_handler, (self, self._repl_handler, conn_handle, cmd))

            # UPGRADE
            elif attr_handle == self._upgrade_handle and self._upgrade_handler:
                raw = self._ble.gatts_read(self._upgrade_handle)
                cmd = raw.decode().strip()  # 대소문자 구분 유지
                micropython.schedule(scheduled_handler, (self, self._upgrade_handler, conn_handle, cmd))

            # ULTRA
            elif attr_handle == self._ultra_handle and self._ultra_handler:
                raw = self._ble.gatts_read(self._ultra_handle)
                cmd = raw.decode().strip().upper()
                micropython.schedule(scheduled_handler, (self, self._ultra_handler, conn_handle, cmd))

            # DHT
            elif attr_handle == self._dht_handle and self._dht_handler:
                raw = self._ble.gatts_read(self._dht_handle)
                cmd = raw.decode().strip().upper()
                micropython.schedule(scheduled_handler, (self, self._dht_handler, conn_handle, cmd))

            # SERVO
            elif attr_handle == self._servo_handle and self._servo_handler:
                raw = self._ble.gatts_read(self._servo_handle)
                cmd = raw.decode().strip().upper()
                micropython.schedule(scheduled_handler, (self, self._servo_handler, conn_handle, cmd))
                
            # NEOPIXEL
            elif attr_handle == self._neo_handle and self._neopixel_handler:
                raw = self._ble.gatts_read(self._neo_handle)
                cmd = raw.decode().strip()  # 대문자 변환 안함 (RGB 값 유지)
                micropython.schedule(scheduled_handler, (self, self._neopixel_handler, conn_handle, cmd))

            # LCD (I2C 캐릭터 LCD)
            elif attr_handle == self._lcd_handle and self._lcd_handler:
                raw = self._ble.gatts_read(self._lcd_handle)
                cmd = raw.decode().strip()  # 텍스트 보존을 위해 대소문자 변환 없음
                micropython.schedule(scheduled_handler, (self, self._lcd_handler, conn_handle, cmd))

            # TOUCH
            elif attr_handle == self._touch_handle and self._touch_handler:
                raw = self._ble.gatts_read(self._touch_handle)
                cmd = raw.decode().strip()
                micropython.schedule(scheduled_handler, (self, self._touch_handler, conn_handle, cmd))

            # LIGHT
            elif attr_handle == self._light_handle and self._light_handler:
                raw = self._ble.gatts_read(self._light_handle)
                cmd = raw.decode().strip()
                micropython.schedule(scheduled_handler, (self, self._light_handler, conn_handle, cmd))
                
            # BUZZER
            elif attr_handle == self._buzzer_handle and self._buzzer_handler:
                raw = self._ble.gatts_read(self._buzzer_handle)
                cmd = raw.decode().strip()  # 대소문자 구분 유지
                micropython.schedule(scheduled_handler, (self, self._buzzer_handler, conn_handle, cmd))

            # GYRO (DeepCo 공통)
            elif attr_handle == self._gyro_handle and self._gyro_handler:
                raw = self._ble.gatts_read(self._gyro_handle)
                cmd = raw.decode().strip()
                micropython.schedule(scheduled_handler, (self, self._gyro_handler, conn_handle, cmd))
            
            # EZ-GYRO (EZMaker 전용 ICM20948)
            elif attr_handle == self._ez_gyro_handle and self._ez_gyro_handler:
                raw = self._ble.gatts_read(self._ez_gyro_handle)
                cmd = raw.decode().strip()
                micropython.schedule(scheduled_handler, (self, self._ez_gyro_handler, conn_handle, cmd))

            # EZ-PRESS (EZMaker 전용 BMP280)
            elif attr_handle == self._ez_press_handle and self._ez_press_handler:
                raw = self._ble.gatts_read(self._ez_press_handle)
                cmd = raw.decode().strip()
                micropython.schedule(scheduled_handler, (self, self._ez_press_handler, conn_handle, cmd))

            # EZ-CO2 (EZMaker 전용 SCD40)
            elif attr_handle == self._ez_co2_handle and self._ez_co2_handler:
                raw = self._ble.gatts_read(self._ez_co2_handle)
                cmd = raw.decode().strip()
                micropython.schedule(scheduled_handler, (self, self._ez_co2_handler, conn_handle, cmd))
                
            # DUST
            elif attr_handle == self._dust_handle and self._dust_handler:
                raw = self._ble.gatts_read(self._dust_handle)
                cmd = raw.decode().strip().upper()
                micropython.schedule(scheduled_handler, (self, self._dust_handler, conn_handle, cmd))

            # DCMOTOR
            elif attr_handle == self._dcmotor_handle and self._dcmotor_handler:
                raw = self._ble.gatts_read(self._dcmotor_handle)
                cmd = raw.decode().strip().upper()
                micropython.schedule(scheduled_handler, (self, self._dcmotor_handler, conn_handle, cmd))

            # LASER (EZMaker 전용)
            elif attr_handle == self._laser_handle and self._laser_handler:
                raw = self._ble.gatts_read(self._laser_handle)
                cmd = raw.decode().strip().upper()
                micropython.schedule(scheduled_handler, (self, self._laser_handler, conn_handle, cmd))

            # HEART RATE
            elif attr_handle == self._heart_rate_handle and self._heart_rate_handler:
                raw = self._ble.gatts_read(self._heart_rate_handle)
                cmd = raw.decode().strip().upper()
                micropython.schedule(scheduled_handler, (self, self._heart_rate_handler, conn_handle, cmd))

            # SOIL MOISTURE
            elif attr_handle == self._soil_handle and self._soil_handler:
                raw = self._ble.gatts_read(self._soil_handle)
                cmd = raw.decode().strip().upper()
                micropython.schedule(scheduled_handler, (self, self._soil_handler, conn_handle, cmd))

            # RAIN SENSOR
            elif attr_handle == self._rain_handle and self._rain_handler:
                raw = self._ble.gatts_read(self._rain_handle)
                cmd = raw.decode().strip().upper()
                micropython.schedule(scheduled_handler, (self, self._rain_handler, conn_handle, cmd))

            # HUMAN PRESENCE SENSOR
            elif attr_handle == self._human_handle and self._human_handler:
                raw = self._ble.gatts_read(self._human_handle)
                cmd = raw.decode().strip().upper()
                micropython.schedule(scheduled_handler, (self, self._human_handler, conn_handle, cmd))

            # DIY-A SENSOR (EZMaker 전용 아날로그 센서)
            elif attr_handle == self._diya_handle and self._diya_handler:
                raw = self._ble.gatts_read(self._diya_handle)
                cmd = raw.decode().strip().upper()
                micropython.schedule(scheduled_handler, (self, self._diya_handler, conn_handle, cmd))

            # DIY-B SENSOR (EZMaker 전용 전류/전도도 아날로그 센서)
            elif attr_handle == self._diyb_handle and self._diyb_handler:
                raw = self._ble.gatts_read(self._diyb_handle)
                cmd = raw.decode().strip().upper()
                micropython.schedule(scheduled_handler, (self, self._diyb_handler, conn_handle, cmd))

            # HALL SENSOR (EZMaker 자기장 센서)
            elif attr_handle == self._hall_handle and self._hall_handler:
                raw = self._ble.gatts_read(self._hall_handle)
                cmd = raw.decode().strip().upper()
                micropython.schedule(scheduled_handler, (self, self._hall_handler, conn_handle, cmd))

            # EZ-LIGHT SENSOR (EZMaker 밝기센서)
            elif attr_handle == self._ez_light_handle and self._ez_light_handler:
                raw = self._ble.gatts_read(self._ez_light_handle)
                cmd = raw.decode().strip().upper()
                micropython.schedule(scheduled_handler, (self, self._ez_light_handler, conn_handle, cmd))

            # EZ-VOLT SENSOR (EZMaker 전압센서)
            elif attr_handle == self._ez_volt_handle and self._ez_volt_handler:
                raw = self._ble.gatts_read(self._ez_volt_handle)
                cmd = raw.decode().strip().upper()
                micropython.schedule(scheduled_handler, (self, self._ez_volt_handler, conn_handle, cmd))

            # EZ-CURR SENSOR (EZMaker 전류센서, INA219)
            elif attr_handle == self._ez_curr_handle and self._ez_curr_handler:
                raw = self._ble.gatts_read(self._ez_curr_handle)
                cmd = raw.decode().strip().upper()
                micropython.schedule(scheduled_handler, (self, self._ez_curr_handler, conn_handle, cmd))
            
            # EZ-THERMAL SENSOR (EZMaker 수중/접촉 온도센서, DS18B20)
            elif attr_handle == self._ez_thermal_handle and self._ez_thermal_handler:
                raw = self._ble.gatts_read(self._ez_thermal_handle)
                cmd = raw.decode().strip().upper()
                micropython.schedule(scheduled_handler, (self, self._ez_thermal_handler, conn_handle, cmd))

            # EZ-SOUND SENSOR (EZMaker 소리센서, 마이크)
            elif attr_handle == self._ez_sound_handle and self._ez_sound_handler:
                raw = self._ble.gatts_read(self._ez_sound_handle)
                cmd = raw.decode().strip().upper()
                micropython.schedule(scheduled_handler, (self, self._ez_sound_handler, conn_handle, cmd))

            # EZ-WEIGHT SENSOR (EZMaker 무게센서, HX711)
            elif attr_handle == self._ez_weight_handle and self._ez_weight_handler:
                raw = self._ble.gatts_read(self._ez_weight_handle)
                cmd = raw.decode().strip().upper()
                micropython.schedule(scheduled_handler, (self, self._ez_weight_handler, conn_handle, cmd))

            # EZ-DUST SENSOR (EZMaker 미세먼지 센서, PMS7003M)
            elif attr_handle == self._ez_dust_handle and self._ez_dust_handler:
                raw = self._ble.gatts_read(self._ez_dust_handle)
                cmd = raw.decode().strip().upper()
                micropython.schedule(scheduled_handler, (self, self._ez_dust_handler, conn_handle, cmd))

    def _advertise(self, interval_us=500000):
        self._ble.gap_advertise(interval_us, adv_data=self._payload, resp_data=self._rspdata)

    def close(self):
        for c in self._connections:
            self._ble.gap_disconnect(c)
        self._connections.clear()


def start(name="iot-ble"):
    """
    BLE 통신 시작 함수
    
    Args:
        name (str): BLE 장치 이름
    
    Returns:
        BLEUART: BLE 통신 객체
    """
    #global ble  # 전역 변수로 ble 객체 저장 (다른 모듈에서 접근 가능)
    ble = bluetooth.BLE()
    
    logger.info(f"'{name}' 시작", "BLE")
    
    # BLEUART 객체 생성
    uart = BLEUART(ble, name=name)
    return uart