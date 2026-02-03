# bleIoT.py

import time
import machine
import _thread
import gc
import array
import dht
import network
from micropython import const  # const 함수 임포트 추가
from HC1SR04 import HCSR04
from neopixel import NeoPixel  # NeoPixel 라이브러리 추가
from i2c_lcd import I2cLcd  # I2C LCD 드라이버 추가
import bleBaseIoT
import buzzerModule  # 통합된 버저 모듈 사용
import ubinascii
from cameraModule import CameraModule  # CameraModule 임포트 추가
import logger  # 로깅 시스템 임포트

# EZMaker 자이로센서(ICM20948) 드라이버 임포트
from icm20948 import ICM20948

# EZMaker 기압센서(BMP280) 드라이버 임포트
from bmp280 import BMP280

# EZMaker CO2 센서(SCD40) 드라이버 임포트
from scd40 import SCD40

# 로그 레벨 설정 (기본값은 INFO)
#logger.set_level(logger.INFO)

# BLE 상태 표시 LED 핀 (GPIO 46)
PIN_BLE_STATUS_LED = const(46)
ble_status_led = None

# ADXL345 가속도계 라이브러리 임포트
from ADXL345 import ADXL345

# 글로벌 변수 및 임포트 섹션에 추가
from dust_sensor import DustSensor
from ez_dust_pms7003 import EzDustSensor

# MAX30102 심장박동 센서를 위한 임포트 추가
from max30102 import MAX30102, MAX30105_PULSE_AMP_MEDIUM

# YL-69 토양수분센서를 위한 임포트 추가
from YL69SoilMoisture import YL69SoilMoisture

# EZMaker DIY-A / DIY-B / HALL / EZLIGHT 아날로그 센서 드라이버 임포트
from diyA_sensor import DiyASensor
from diyB_sensor import DiyBSensor
from hall_sensor import HallSensor
from ez_light_sensor import EzLightSensor
from ez_volt_sensor import EzVoltSensor
from human_sensor import HumanSensor
from ez_curr_sensor import EzCurrSensor
from ez_thermal_sensor import EzThermalSensor
from ez_sound_sensor import EzSoundSensor
from ez_weight_sensor import EzWeightSensor

# DC 모터 핀 추가
PIN_DCMOTOR = None  # DC 모터 PWM 핀

# ---------------------------
# 핀 설정 (None으로 초기화)
# ---------------------------
# LED 핀
PIN_LED = None  # 초기값은 None
led_pin = None
led_pwm_value = 255  # LED의 PWM 값 (0-255), 기본값 255(최대 밝기)

# 초음파 센서 핀
PIN_ULTRASONIC_TRIGGER = None
PIN_ULTRASONIC_ECHO = None

# DHT 센서 핀
PIN_DHT = None

# 서보 모터 핀 (2개 서보모터 지원)
PIN_SERVO1 = None
PIN_SERVO2 = None
servo_pin1 = None
servo_pin2 = None
servo_pwm1 = None
servo_pwm2 = None

# TTP223 터치센서 핀
PIN_TOUCH = None

# 조도센서 핀
PIN_LIGHT_ANALOG = None
PIN_LIGHT_DIGITAL = None

# NeoPixel 핀
PIN_NEO = None

# 버저 핀
PIN_BUZZER = const(42)

# 자이로 센서 핀
PIN_GYRO_SDA = None      # ADXL345 (기존 DeepCo 공통)
PIN_GYRO_SCL = None
PIN_EZ_GYRO_SDA = None   # ICM20948 (EZMaker 전용)
PIN_EZ_GYRO_SCL = None

# EZMaker 기압센서(BMP280) 핀
PIN_EZ_PRESS_SDA = None
PIN_EZ_PRESS_SCL = None

# EZMaker CO2 센서(SCD40) 핀
PIN_EZ_CO2_SDA = None
PIN_EZ_CO2_SCL = None

# NeoPixel 설정
NUM_PIXELS_DEFAULT = const(4)  # 기본 네오픽셀 LED 개수
# 현재 사용 중인 네오픽셀 개수 (동적으로 변경 가능)
neo_num_pixels = NUM_PIXELS_DEFAULT
# 네오픽셀 밝기 전역 변수 추가
neo_brightness = 1.0  # 기본 밝기는 100% (0.0-1.0 범위)

# I2C LCD 관련 변수 (공통: 16x2 / 20x4 등)
LCD_I2C_ADDR = const(0x27)  # 기본 I2C 주소 (테스트 코드와 동일)
LCD_SDA_PIN = None          # I2C SDA 핀 (예: 41)
LCD_SCL_PIN = None          # I2C SCL 핀 (예: 40)
LCD_ROWS = 0                # LCD 줄 수 (2 또는 4 등)
LCD_COLS = 0                # LCD 열 수 (16 또는 20 등)
lcd_i2c = None              # SoftI2C 인스턴스
lcd = None                  # I2cLcd 인스턴스

# BLE 연결 상태 변수
ble_connected = False

# 센서/액추에이터 객체 초기화
ultraSensor = None
dht_pin = None
dht_sensor = None
servo_pin = None
servo_pwm = None
neo_pin = None
neo = None
touch_pin = None
light_analog_pin = None
light_digital_pin = None
gyro_i2c = None        # ADXL345용 I2C
gyro_sensor = None     # ADXL345 센서 객체
ez_gyro_i2c = None     # ICM20948용 I2C (EZMaker 전용)
ez_gyro_sensor = None  # ICM20948 센서 객체
ez_press_i2c = None    # BMP280용 I2C (EZMaker 전용)
ez_press_sensor = None # BMP280 센서 객체
ez_co2_i2c = None      # SCD40용 I2C (EZMaker 전용)
ez_co2_sensor = None   # SCD40 센서 객체

# 버저 초기화 상태 추적 변수
buzzer_initialized = False

# 글로벌 변수 섹션에 추가
dust_sensor = None          # DeepCo 공통 아날로그 먼지센서
ez_dust_sensor = None       # EZMaker 디지털 미세먼지 센서(PMS7003M)
PIN_EZDUST_RX = None        # EZDUST UART RX 핀 (센서 TX에 연결)
PIN_EZDUST_TX = None        # EZDUST UART TX 핀 (센서 RX에 연결)
dcmotor_pin = None   # DC 모터 핀
dcmotor_pwm = None   # DC 모터 PWM 제어

# 심장박동 센서 관련 변수
heart_rate_i2c = None
heart_rate_sensor = None
heart_rate_monitor = None
heart_rate_enabled = False
heart_rate_streaming = False
last_heart_rate_time = 0
heart_rate_interval = 2000  # 2초마다 측정
heart_rate_value = None

# 자이로센서 스트리밍 관련 변수 (ADXL345 공통)
gyro_streaming = False
gyro_stream_interval = 200  # 자이로 스트리밍 기본 간격(ms)
last_gyro_stream_time = 0

# EZMaker 전용 자이로(ICM20948) 스트리밍 관련 변수 (필요 시 사용)
ez_gyro_streaming = False
ez_gyro_stream_interval = 200
last_ez_gyro_stream_time = 0

# EZMaker DIY-A / DIY-B / HALL / EZLIGHT / EZVOLT / EZCURR / EZTHERMAL / EZSOUND / EZWEIGHT 센서 관련 변수
diya_sensor = None         # DiyASensor 객체
PIN_DIYA = None            # EZMaker DIY-A 센서 핀
diyb_sensor = None         # DiyBSensor 객체
PIN_DIYB = None            # EZMaker DIY-B 센서 핀
hall_sensor = None         # HallSensor 객체
PIN_HALL = None            # 자기장 센서 핀
ez_light_sensor = None     # EzLightSensor 객체
PIN_EZLIGHT = None         # EZMaker 밝기센서 핀
ez_volt_sensor = None      # EzVoltSensor 객체
PIN_EZVOLT = None          # EZMaker 전압센서 핀
ez_curr_sensor = None      # EzCurrSensor 객체 (INA219)
PIN_EZCURR_SDA = None      # EZMaker 전류센서 I2C SDA 핀
PIN_EZCURR_SCL = None      # EZMaker 전류센서 I2C SCL 핀
ez_thermal_sensor = None   # EzThermalSensor 객체 (DS18B20)
PIN_EZTHERMAL = None       # EZMaker 수중/접촉 온도센서 핀
ez_sound_sensor = None     # EzSoundSensor 객체
PIN_EZSOUND = None         # EZMaker 소리센서 핀
ez_weight_sensor = None    # EzWeightSensor 객체 (HX711)
PIN_EZWEIGHT_DOUT = None   # EZMaker 무게센서 DOUT(DT) 핀
PIN_EZWEIGHT_SCK = None    # EZMaker 무게센서 SCK(CLK) 핀

# 토양수분센서 관련 변수
soil_sensor = None  # YL69SoilMoisture 센서 객체
PIN_SOIL = None     # 토양수분센서 핀

# 빗방울센서 관련 변수
rain_sensor = None  # 빗방울센서 ADC 객체
PIN_RAIN = None     # 빗방울센서 핀

# 인체감지 센서 관련 변수
human_sensor = None  # HumanSensor 객체 (PIR)
PIN_HUMAN = None     # 인체감지 센서 디지털 핀

# 레이저 모듈 관련 변수 (EZMaker 전용)
PIN_LASER = None    # 레이저 모듈 디지털 핀
laser_pin = None    # 레이저 제어용 Pin 객체

# 핀 설정 변경 함수 추가
def update_pin_config(pin_type, pin_number, secondary_pin=None):
    """
    실행 중 핀 설정 변경 함수
    pin_type: 'led', 'touch', 'light', 'dht', 'ultra', 'servo', 'servo1', 'servo2',
              'neo', 'gyro', 'ezgyro', 'ezpress', 'ezco2', 'dcmotor', 'dust',
              'heart', 'soil', 'rain', 'human', 'laser', 'diya', 'diyb', 'hall',
              'ezlight', 'ezvolt', 'ezcurr', 'ezthermal', 'ezsound', 'ezweight'
    pin_number: 새 핀 번호
    secondary_pin: 보조 핀 번호 (초음파 센서의 에코 핀 등)
    """
    global PIN_LED, PIN_TOUCH, PIN_LIGHT_ANALOG, PIN_LIGHT_DIGITAL
    global PIN_DHT, PIN_ULTRASONIC_TRIGGER, PIN_ULTRASONIC_ECHO
    global PIN_SERVO, PIN_SERVO1, PIN_SERVO2, PIN_NEO
    global PIN_GYRO_SDA, PIN_GYRO_SCL, PIN_EZ_GYRO_SDA, PIN_EZ_GYRO_SCL, PIN_EZ_PRESS_SDA, PIN_EZ_PRESS_SCL, PIN_EZ_CO2_SDA, PIN_EZ_CO2_SCL
    global PIN_EZCURR_SDA, PIN_EZCURR_SCL, neo_num_pixels
    global PIN_DCMOTOR, PIN_SOIL, PIN_RAIN, PIN_HUMAN, PIN_LASER, PIN_DIYA, PIN_DIYB, PIN_HALL, PIN_EZLIGHT, PIN_EZVOLT, PIN_EZTHERMAL, PIN_EZSOUND  # DC 모터, 토양수분, 빗방울, 인체감지, 레이저, DIY-A/DIY-B/HALL/EZLIGHT/EZVOLT/EZTHERMAL/EZSOUND 핀 변수
    global PIN_EZWEIGHT_DOUT, PIN_EZWEIGHT_SCK  # EZWEIGHT(HX711) 핀 변수
    global led_pin, ultraSensor, dht_pin, dht_sensor, servo_pin, servo_pwm
    global servo_pin1, servo_pin2, servo_pwm1, servo_pwm2
    global neo_pin, neo, touch_pin, light_analog_pin, light_digital_pin
    global gyro_i2c, gyro_sensor, ez_gyro_i2c, ez_gyro_sensor, ez_press_i2c, ez_press_sensor, ez_co2_i2c, ez_co2_sensor
    global ez_curr_i2c, ez_curr_sensor
    global dcmotor_pin, dcmotor_pwm, dust_sensor  # DC 모터 객체 추가
    global heart_rate_i2c, heart_rate_sensor, heart_rate_monitor  # 심장박동 센서 객체 추가
    global soil_sensor, rain_sensor, human_sensor, diya_sensor, diyb_sensor, hall_sensor, ez_light_sensor, ez_volt_sensor, ez_thermal_sensor, ez_sound_sensor  # 토양수분, 빗방울, 인체감지, DIY-A/DIY-B/HALL/EZLIGHT/EZVOLT/EZTHERMAL/EZSOUND 센서 객체 추가
    global ez_weight_sensor  # EZWEIGHT(HX711) 센서 객체
    global laser_pin  # 레이저 모듈 제어 핀
    global LCD_I2C_ADDR, LCD_SDA_PIN, LCD_SCL_PIN, LCD_ROWS, LCD_COLS, lcd_i2c, lcd  # I2C LCD 관련 전역 변수
    
    pin_type = pin_type.lower()
    
    try:
        # 핀 번호 유효성 검사
        if not isinstance(pin_number, int) or pin_number < 0 or pin_number > 48:
            logger.error(f"Invalid pin number {pin_number}", "SYS")
            return False
        
        # 보조 핀 번호 유효성 검사
        if secondary_pin is not None:
            if not isinstance(secondary_pin, int) or secondary_pin < 0 or secondary_pin > 48:
                logger.error(f"Invalid secondary pin number {secondary_pin}", "SYS")
                return False
        
        # 핀 유형에 따라 변수 업데이트
        if pin_type == 'led':
            PIN_LED = pin_number
            
            # LED 핀 재설정
            if led_pin is not None:
                try:
                    led_pin.deinit()  # 기존 핀 설정 해제
                except:
                    pass
                
            # 새 PWM 핀 설정
            from machine import Pin, PWM
            led_temp_pin = Pin(pin_number, Pin.OUT)
            led_pin = PWM(led_temp_pin)
            led_pin.freq(1000)  # PWM 주파수 설정 (1kHz)
            led_pin.duty_u16(0)  # 초기 밝기 0
            
            logger.info(f"LED pin set to {pin_number} (PWM mode)", "LED")
            return True
            
        elif pin_type == 'touch':
            PIN_TOUCH = pin_number
           
            # 터치 센서 핀 재설정
            if touch_pin is not None:
                try:
                    touch_pin.deinit()  # 기존 핀 설정 해제(필요하면)
                except:
                    pass
                
            touch_pin = machine.Pin(pin_number, machine.Pin.IN)
            
            logger.info(f"Touch sensor pin set to {pin_number}", "TOUCH")
            return True
            
        elif pin_type == 'light':
            PIN_LIGHT_ANALOG = pin_number
            # 조도 센서 핀 재설정
            try:
                if light_analog_pin is not None:
                    # ADC 핀 재설정
                    light_analog_pin.deinit()  # 기존 ADC 해제
            except:
                pass  # ADC에는 deinit이 없을 수 있음
            
            light_analog_pin = machine.ADC(machine.Pin(pin_number))
            light_analog_pin.atten(machine.ADC.ATTN_11DB)
            
            # 디지털 핀은 옵션 - 제공된 경우에만 설정
            if secondary_pin is not None:
                PIN_LIGHT_DIGITAL = secondary_pin  # 디지털 핀 변수 업데이트
                if light_digital_pin is not None:
                    try:
                        light_digital_pin.deinit()  # 기존 핀 설정 해제
                    except:
                        pass
                light_digital_pin = machine.Pin(secondary_pin, machine.Pin.IN)
                logger.info(f"Light sensor pins set to analog={pin_number}, digital={secondary_pin}", "LIGHT")
            else:
                PIN_LIGHT_DIGITAL = None  # 디지털 핀 사용하지 않음을 명시
                light_digital_pin = None  # 디지털 핀 객체도 None으로 설정
                logger.info(f"Light sensor analog pin set to {pin_number} (no digital pin)", "LIGHT")
            
            return True
            
        elif pin_type == 'dht':
            PIN_DHT = pin_number
            # DHT 센서 핀 재설정
            dht_pin = machine.Pin(pin_number, machine.Pin.IN)
            dht_sensor = dht.DHT11(dht_pin)
            
            logger.info(f"DHT sensor pin set to {pin_number}", "DHT")
            return True
            
        elif pin_type == 'ultra':
            # 핀 번호 저장
            PIN_ULTRASONIC_TRIGGER = pin_number
            if secondary_pin is not None:
                PIN_ULTRASONIC_ECHO = secondary_pin
            
            # HCSR04 객체 다시 생성
            ultraSensor = HCSR04(trigger_pin=pin_number, 
                                echo_pin=secondary_pin, 
                                echo_timeout_us=10000)
            
            logger.info(f"Ultrasonic sensor trigger pin set to {pin_number}", "ULTRA")
            if secondary_pin is not None:
                logger.info(f"Ultrasonic sensor echo pin set to {secondary_pin}", "ULTRA")
            return True
            
        elif pin_type == 'servo':
            # 핀 번호 저장 (하위 호환성 유지를 위해 PIN_SERVO도 업데이트)
            PIN_SERVO = pin_number
            PIN_SERVO1 = pin_number  # 첫 번째 서보모터로 설정
            
            # 서보 모터 핀 재설정
            if servo_pwm is not None:
                try:
                    servo_pwm.deinit()  # PWM 설정 해제
                except:
                    pass
            
            if servo_pwm1 is not None:
                try:
                    servo_pwm1.deinit()  # PWM 설정 해제
                except:
                    pass
                
            servo_pin = machine.Pin(pin_number, machine.Pin.OUT)
            servo_pwm = machine.PWM(servo_pin)
            servo_pwm.freq(50)  # 서보는 보통 50Hz
            
            # 서보1도 함께 설정 (레거시 호환)
            servo_pin1 = servo_pin
            servo_pwm1 = servo_pwm
            
            logger.info(f"Servo motor pin set to {pin_number}", "SERVO")
            return True
            
        elif pin_type == 'servo1':
            # 첫 번째 서보 핀 번호 저장
            PIN_SERVO1 = pin_number
            
            # 서보 모터 핀 재설정
            if servo_pwm1 is not None:
                try:
                    servo_pwm1.deinit()  # PWM 설정 해제
                except:
                    pass
                
            servo_pin1 = machine.Pin(pin_number, machine.Pin.OUT)
            servo_pwm1 = machine.PWM(servo_pin1)
            servo_pwm1.freq(50)  # 서보는 보통 50Hz
            
            # 하위 호환성을 위해 기본 servo 변수도 설정
            servo_pin = servo_pin1
            servo_pwm = servo_pwm1
            PIN_SERVO = PIN_SERVO1
            
            logger.info(f"Servo motor 1 pin set to {pin_number}", "SERVO")
            return True
            
        elif pin_type == 'servo2':
            # 두 번째 서보 핀 번호 저장
            PIN_SERVO2 = pin_number
            
            # 서보 모터 핀 재설정
            if servo_pwm2 is not None:
                try:
                    servo_pwm2.deinit()  # PWM 설정 해제
                except:
                    pass
                
            servo_pin2 = machine.Pin(pin_number, machine.Pin.OUT)
            servo_pwm2 = machine.PWM(servo_pin2)
            servo_pwm2.freq(50)  # 서보는 보통 50Hz
            
            logger.info(f"Servo motor 2 pin set to {pin_number}", "SERVO")
            return True
            
        elif pin_type == 'neo':
            # 핀 번호 저장
            PIN_NEO = pin_number

            # secondary_pin 인자를 "픽셀 개수"로 사용 (없으면 기본값)
            try:
                if secondary_pin is not None:
                    pixel_count = int(secondary_pin)
                else:
                    pixel_count = NUM_PIXELS_DEFAULT
            except Exception:
                pixel_count = NUM_PIXELS_DEFAULT

            # 허용 범위 제한 (1~60 정도로 제한)
            if pixel_count < 1:
                pixel_count = 1
            elif pixel_count > 60:
                pixel_count = 60

            neo_num_pixels = pixel_count
            
            # NeoPixel 핀 및 LED 개수 재설정
            # 기존 NeoPixel 끄기
            if neo is not None:
                try:
                    neo.fill((0, 0, 0))
                    neo.write()
                except:
                    pass
            
            # 새 NeoPixel 객체 생성
            neo_pin = machine.Pin(pin_number, machine.Pin.OUT)
            neo = NeoPixel(neo_pin, neo_num_pixels)
            # 초기화 시 모든 LED 끄기
            neo.fill((0, 0, 0))
            neo.write()
            
            logger.info(f"NeoPixel pin set to {pin_number} with {neo_num_pixels} LEDs", "NEO")
            return True
            
        elif pin_type == 'gyro':
            # 자이로 센서(ADXL345, DeepCo 공통) 핀 설정
            PIN_GYRO_SDA = pin_number
            PIN_GYRO_SCL = secondary_pin if secondary_pin is not None else pin_number + 1
            
            # 기존 I2C 인스턴스 정리
            if gyro_i2c is not None:
                try:
                    gyro_i2c.deinit()
                except:
                    pass
                gyro_i2c = None
                gyro_sensor = None
            
            # 새 I2C 인스턴스 생성
            try:
                gyro_i2c = machine.I2C(0, scl=machine.Pin(PIN_GYRO_SCL), sda=machine.Pin(PIN_GYRO_SDA))
                
                # I2C 장치 스캔
                devices = gyro_i2c.scan()
                if devices:
                    logger.debug(f"I2C devices found: {[hex(d) for d in devices]}", "GYRO")
                    
                    # ADXL345 초기화
                    try:
                        gyro_sensor = ADXL345(gyro_i2c)
                        logger.info("ADXL345 sensor initialized successfully", "GYRO")
                    except Exception as e:
                        logger.error(f"Failed to initialize ADXL345: {e}", "GYRO")
                        gyro_sensor = None
                else:
                    logger.warning("No I2C devices found", "GYRO")
                
                logger.info(f"Gyro sensor pins set to SDA={PIN_GYRO_SDA}, SCL={PIN_GYRO_SCL}", "GYRO")
                return True if gyro_sensor is not None else False
                
            except Exception as e:
                logger.error(f"Failed to initialize I2C for gyro sensor: {e}", "GYRO")
                gyro_i2c = None
                gyro_sensor = None
                return False
            
        elif pin_type == 'ezgyro':
            # EZMaker 자이로센서(ICM20948) 핀 설정
            PIN_EZ_GYRO_SDA = pin_number
            PIN_EZ_GYRO_SCL = secondary_pin if secondary_pin is not None else pin_number + 1
            
            # 기존 I2C 인스턴스 정리
            if ez_gyro_i2c is not None:
                try:
                    ez_gyro_i2c.deinit()
                except:
                    pass
                ez_gyro_i2c = None
                ez_gyro_sensor = None
            
            # 새 SoftI2C 인스턴스 생성
            try:
                from machine import SoftI2C, Pin
                ez_gyro_i2c = SoftI2C(scl=Pin(PIN_EZ_GYRO_SCL), sda=Pin(PIN_EZ_GYRO_SDA), freq=100000)
                
                # I2C 장치 스캔
                devices = ez_gyro_i2c.scan()
                if devices:
                    logger.debug(f"[EZGYRO] I2C devices found: {[hex(d) for d in devices]}", "GYRO")

                    addr = 0x68
                    if addr not in devices and 0x69 in devices:
                        addr = 0x69
                        logger.info("[EZGYRO] Using address 0x69", "GYRO")

                    try:
                        ez_gyro_sensor = ICM20948(ez_gyro_i2c, addr)
                        logger.info("ICM20948 sensor initialized successfully (EZMaker)", "GYRO")
                    except Exception as e:
                        logger.error(f"Failed to initialize ICM20948: {e}", "GYRO")
                        ez_gyro_sensor = None
                else:
                    logger.warning("[EZGYRO] No I2C devices found", "GYRO")
                
                logger.info(f"EZ-Gyro pins set to SDA={PIN_EZ_GYRO_SDA}, SCL={PIN_EZ_GYRO_SCL}", "GYRO")
                return True if ez_gyro_sensor is not None else False
                
            except Exception as e:
                logger.error(f"Failed to initialize SoftI2C for EZ-Gyro sensor: {e}", "GYRO")
                ez_gyro_i2c = None
                ez_gyro_sensor = None
                return False
        
        elif pin_type == 'ezpress':
            # EZMaker 기압센서(BMP280) 핀 설정
            PIN_EZ_PRESS_SDA = pin_number
            PIN_EZ_PRESS_SCL = secondary_pin if secondary_pin is not None else pin_number + 1
            
            # 기존 I2C 인스턴스 정리
            if ez_press_i2c is not None:
                try:
                    ez_press_i2c.deinit()
                except:
                    pass
                ez_press_i2c = None
                ez_press_sensor = None
            
            # 새 SoftI2C 인스턴스 생성
            try:
                from machine import SoftI2C, Pin
                ez_press_i2c = SoftI2C(scl=Pin(PIN_EZ_PRESS_SCL), sda=Pin(PIN_EZ_PRESS_SDA), freq=100000)
                
                # I2C 장치 스캔
                devices = ez_press_i2c.scan()
                if devices:
                    logger.debug(f"[EZPRESS] I2C devices found: {[hex(d) for d in devices]}", "PRESS")

                    # BMP280 주소 선택 (0x76 또는 0x77)
                    addr = 0x76
                    if addr not in devices and 0x77 in devices:
                        addr = 0x77
                        logger.info("[EZPRESS] Using address 0x77", "PRESS")

                    try:
                        ez_press_sensor = BMP280(ez_press_i2c, addr)
                        logger.info("BMP280 sensor initialized successfully (EZMaker)", "PRESS")
                    except Exception as e:
                        logger.error(f"Failed to initialize BMP280: {e}", "PRESS")
                        ez_press_sensor = None
                else:
                    logger.warning("[EZPRESS] No I2C devices found", "PRESS")
                
                logger.info(f"EZ-Press pins set to SDA={PIN_EZ_PRESS_SDA}, SCL={PIN_EZ_PRESS_SCL}", "PRESS")
                return True if ez_press_sensor is not None else False
                
            except Exception as e:
                logger.error(f"Failed to initialize SoftI2C for EZ-Press sensor: {e}", "PRESS")
                ez_press_i2c = None
                ez_press_sensor = None
                return False
        
        elif pin_type == 'ezco2':
            # EZMaker CO2 센서(SCD40) 핀 설정
            PIN_EZ_CO2_SDA = pin_number
            PIN_EZ_CO2_SCL = secondary_pin if secondary_pin is not None else pin_number + 1
            
            # 기존 I2C 인스턴스 정리
            if ez_co2_i2c is not None:
                try:
                    ez_co2_i2c.deinit()
                except:
                    pass
                ez_co2_i2c = None
                ez_co2_sensor = None
            
            # 새 SoftI2C 인스턴스 생성
            try:
                from machine import SoftI2C, Pin
                ez_co2_i2c = SoftI2C(scl=Pin(PIN_EZ_CO2_SCL), sda=Pin(PIN_EZ_CO2_SDA), freq=100000)
                
                # I2C 장치 스캔
                devices = ez_co2_i2c.scan()
                if devices:
                    logger.debug(f"[EZCO2] I2C devices found: {[hex(d) for d in devices]}", "CO2")

                    addr = 0x62  # SCD40 고정 주소
                    if addr in devices:
                        try:
                            ez_co2_sensor = SCD40(ez_co2_i2c, addr)
                            ez_co2_sensor.start_measurement()
                            logger.info("SCD40 CO2 sensor initialized successfully (EZMaker)", "CO2")
                        except Exception as e:
                            logger.error(f"Failed to initialize SCD40: {e}", "CO2")
                            ez_co2_sensor = None
                    else:
                        logger.warning("[EZCO2] SCD40 device not found at 0x62", "CO2")
                else:
                    logger.warning("[EZCO2] No I2C devices found", "CO2")
                
                logger.info(f"EZ-CO2 pins set to SDA={PIN_EZ_CO2_SDA}, SCL={PIN_EZ_CO2_SCL}", "CO2")
                return True if ez_co2_sensor is not None else False
                
            except Exception as e:
                logger.error(f"Failed to initialize SoftI2C for EZ-CO2 sensor: {e}", "CO2")
                ez_co2_i2c = None
                ez_co2_sensor = None
                return False

        elif pin_type == 'ezcurr':
            # EZMaker 전류센서(INA219) 핀 설정 (I2C: SDA, SCL)
            # pin_number: SDA, secondary_pin: SCL
            PIN_EZCURR_SDA = pin_number
            PIN_EZCURR_SCL = secondary_pin if secondary_pin is not None else pin_number + 1

            # 기존 I2C 인스턴스 정리
            if 'ez_curr_i2c' in globals() and ez_curr_i2c is not None:
                try:
                    ez_curr_i2c.deinit()
                except:
                    pass
                ez_curr_i2c = None
                ez_curr_sensor = None

            # 새 SoftI2C 인스턴스 생성 및 INA219(EzCurrSensor) 초기화
            try:
                from machine import SoftI2C, Pin
                ez_curr_i2c = SoftI2C(scl=Pin(PIN_EZCURR_SCL), sda=Pin(PIN_EZCURR_SDA), freq=100000)

                # I2C 장치 스캔
                devices = ez_curr_i2c.scan()
                if devices:
                    logger.debug(f"[EZCURR] I2C devices found: {[hex(d) for d in devices]}", "CURR")

                    addr = 0x40  # INA219 기본 주소 (보드 설계에 따라 다를 수 있음)
                    if addr not in devices:
                        # 다른 주소에 있을 가능성 (0x41~0x4F)
                        alt_addr = None
                        for a in devices:
                            if 0x40 <= a <= 0x4F:
                                alt_addr = a
                                break
                        if alt_addr is not None:
                            addr = alt_addr
                            logger.info(f"[EZCURR] Using address {hex(addr)}", "CURR")
                        else:
                            logger.warning("[EZCURR] INA219 address not found on I2C bus", "CURR")

                    try:
                        ez_curr_sensor = EzCurrSensor(ez_curr_i2c, addr=addr)
                        logger.info("INA219 current sensor initialized successfully (EZMaker)", "CURR")
                    except Exception as e:
                        logger.error(f"Failed to initialize INA219 (EzCurrSensor): {e}", "CURR")
                        ez_curr_sensor = None
                else:
                    logger.warning("[EZCURR] No I2C devices found", "CURR")

                logger.info(f"EZ-Curr pins set to SDA={PIN_EZCURR_SDA}, SCL={PIN_EZCURR_SCL}", "CURR")
                return True if ez_curr_sensor is not None else False

            except Exception as e:
                logger.error(f"Failed to initialize SoftI2C for EZ-Curr sensor: {e}", "CURR")
                ez_curr_i2c = None
                ez_curr_sensor = None
                return False

        elif pin_type == 'human':
            # 인체감지 센서 핀 설정 (디지털 입력)
            PIN_HUMAN = pin_number

            # 기존 센서 객체 정리
            if human_sensor is not None:
                try:
                    # machine.Pin 은 별도 deinit 이 필요 없을 수 있음
                    human_sensor = None
                except Exception:
                    human_sensor = None

            try:
                human_sensor = HumanSensor(pin_number)
                logger.info(f"Human sensor initialized on pin {pin_number}", "HUMAN")
                return True
            except Exception as e:
                logger.error(f"Failed to initialize human sensor on pin {pin_number}: {e}", "HUMAN")
                human_sensor = None
                return False

        elif pin_type == 'lcd':
            # I2C LCD (16x2 / 20x4) 핀 설정
            # pin_number: SDA, secondary_pin: SCL
            LCD_SDA_PIN = pin_number
            LCD_SCL_PIN = secondary_pin if secondary_pin is not None else pin_number + 1

            # 기존 I2C / LCD 인스턴스 정리
            if lcd_i2c is not None:
                try:
                    lcd_i2c.deinit()
                except:
                    pass
            lcd_i2c = None
            lcd = None

            try:
                from machine import SoftI2C, Pin

                # SoftI2C 초기화
                lcd_i2c = SoftI2C(scl=Pin(LCD_SCL_PIN), sda=Pin(LCD_SDA_PIN), freq=100000)

                # I2C 장치 스캔
                devices = lcd_i2c.scan()
                if LCD_I2C_ADDR not in devices:
                    logger.warning(f"LCD not found at 0x{LCD_I2C_ADDR:02X}, devices={ [hex(d) for d in devices] }", "LCD")
                    lcd_i2c = None
                    lcd = None
                    return False

                # LCD 행/열이 설정되지 않은 경우 기본값(16x2) 사용
                if LCD_ROWS <= 0 or LCD_COLS <= 0:
                    logger.warning("LCD_ROWS/LCD_COLS not set, using default 16x2", "LCD")
                    LCD_ROWS = 2
                    LCD_COLS = 16

                # LCD 인스턴스 생성
                lcd = I2cLcd(lcd_i2c, LCD_I2C_ADDR, LCD_ROWS, LCD_COLS)
                logger.info(
                    f"LCD initialized at 0x{LCD_I2C_ADDR:02X} (cols={LCD_COLS}, rows={LCD_ROWS}), SDA={LCD_SDA_PIN}, SCL={LCD_SCL_PIN}",
                    "LCD",
                )
                return True
            except Exception as e:
                logger.error(f"Failed to initialize LCD: {e}", "LCD")
                lcd_i2c = None
                lcd = None
                return False
        
        elif pin_type == 'dcmotor':
            # DC 모터 핀 설정 (단방향 모터)
            PIN_DCMOTOR = pin_number
            
            # 기존 핀 정리
            if dcmotor_pwm is not None:
                try:
                    dcmotor_pwm.deinit()
                except:
                    pass
            
            # 새 핀 설정
            dcmotor_pin = machine.Pin(pin_number, machine.Pin.OUT)
            dcmotor_pin.value(0)  # 초기 상태는 정지
            
            # PWM 핀 설정 (속도 제어용)
            try:
                dcmotor_pwm = machine.PWM(dcmotor_pin)
                dcmotor_pwm.freq(500)  # DC 모터 제어에 적합한 주파수
                dcmotor_pwm.duty(0)    # 초기 상태는 0%
                logger.info(f"DC Motor pin set to {pin_number}", "MOTOR")
                return True
            except Exception as e:
                logger.error(f"Failed to initialize DC Motor PWM: {e}", "MOTOR")
                return False
                
        elif pin_type == 'dust':
            # 먼지 센서 핀 설정
            # 기존 센서 클래스 종료 (필요시)
            if dust_sensor is not None:
                # 클린업 코드가 필요하면 여기에 추가
                pass
                
            # 새 핀으로 센서 초기화 (led_pin, vo_pin)
            try:
                dust_sensor = DustSensor(led_pin=pin_number, vo_pin=secondary_pin)
                logger.info(f"Dust sensor initialized (LED pin: {pin_number}, ADC pin: {secondary_pin})", "DUST")
                voc = dust_sensor.calibrate(20)  # 적은 샘플로 빠른 보정
                msg = f"DUST:CALIBRATE:DONE:{voc:.3f}"
                uart.dust_notify(msg.encode())
                logger.info(f"Dust sensor calibrated: VOC={voc:.3f}V", "DUST")
                return True
            except Exception as e:
                logger.error(f"Failed to initialize dust sensor: {e}", "DUST")
                return False

        elif pin_type == 'ezdust':
            # EZMaker 미세먼지 센서(PMS7003M) UART 핀 설정
            global ez_dust_sensor, PIN_EZDUST_RX, PIN_EZDUST_TX

            PIN_EZDUST_RX = pin_number
            PIN_EZDUST_TX = secondary_pin if secondary_pin is not None else pin_number + 1

            # 기존 센서 인스턴스 정리
            ez_dust_sensor = None

            try:
                ez_dust_sensor = EzDustSensor(rx_pin=PIN_EZDUST_RX, tx_pin=PIN_EZDUST_TX)
                logger.info(
                    f"EZDUST sensor initialized on UART (RX={PIN_EZDUST_RX}, TX={PIN_EZDUST_TX})",
                    "DUST",
                )
                return True
            except Exception as e:
                logger.error(
                    f"Failed to initialize EZDUST sensor on RX={PIN_EZDUST_RX}, TX={PIN_EZDUST_TX}: {e}",
                    "DUST",
                )
                ez_dust_sensor = None
                return False
            
        elif pin_type == 'heart':
            # 심장박동 센서(MAX30102) 핀 설정
            heart_rate_sda_pin = pin_number
            heart_rate_scl_pin = secondary_pin if secondary_pin is not None else pin_number + 1
            
            # 기존 I2C 인스턴스 정리
            if heart_rate_i2c is not None:
                try:
                    heart_rate_i2c.deinit()
                except:
                    pass
                heart_rate_i2c = None
                heart_rate_sensor = None
                heart_rate_monitor = None
            
            # 새 I2C 인스턴스 생성
            try:
                from machine import SoftI2C, Pin
                from HeartRateMonitor import HeartRateMonitor
                
                heart_rate_i2c = SoftI2C(
                    sda=Pin(heart_rate_sda_pin),
                    scl=Pin(heart_rate_scl_pin),
                    freq=400000
                )
                
                # I2C 장치 스캔
                devices = heart_rate_i2c.scan()
                if devices:
                    logger.debug(f"I2C devices found: {[hex(d) for d in devices]}", "HEART")
                    
                    # MAX30102 초기화
                    try:
                        heart_rate_sensor = MAX30102(i2c=heart_rate_i2c)
                        
                        # 센서 ID 확인
                        if heart_rate_sensor.check_part_id():
                            # 센서 설정
                            heart_rate_sensor.setup_sensor()
                            heart_rate_sensor.set_sample_rate(400)  # 400 samples/s
                            heart_rate_sensor.set_fifo_average(8)   # 8개 샘플 평균
                            heart_rate_sensor.set_active_leds_amplitude(MAX30105_PULSE_AMP_MEDIUM)
                            
                            # 모니터 클래스 초기화
                            acquisition_rate = 400 // 8  # 50Hz
                            heart_rate_monitor = HeartRateMonitor(
                                sample_rate=acquisition_rate,  
                                window_size=acquisition_rate * 3  # 3초 윈도우
                            )
                            
                            logger.info("MAX30102 sensor initialized successfully", "HEART")
                            return True
                        else:
                            logger.error("I2C device ID not corresponding to MAX30102 or MAX30105", "HEART")
                            heart_rate_sensor = None
                            return False
                    except Exception as e:
                        logger.error(f"Failed to initialize MAX30102: {e}", "HEART")
                        heart_rate_sensor = None
                        return False
                else:
                    logger.warning("No I2C devices found", "HEART")
                    return False
                
            except Exception as e:
                logger.error(f"Failed to initialize I2C for heart rate sensor: {e}", "HEART")
                heart_rate_i2c = None
                heart_rate_sensor = None
                heart_rate_monitor = None
                return False
                
        elif pin_type == 'diya':
            # DIY-A 아날로그 센서 핀 설정
            PIN_DIYA = pin_number
            
            # 기존 센서 객체 정리 (필요 시)
            if diya_sensor is not None:
                # 별도 deinit 필요 없음 (ADC 재사용)
                pass
            
            # 새 DIY-A 센서 초기화
            try:
                diya_sensor = DiyASensor(adc_pin=pin_number)
                logger.info(f"DIY-A sensor initialized on pin {pin_number}", "DIYA")
                return True
            except Exception as e:
                logger.error(f"Failed to initialize DIY-A sensor: {e}", "DIYA")
                return False

        elif pin_type == 'diyb':
            # DIY-B 전류/전도도 센서 핀 설정
            PIN_DIYB = pin_number

            # 기존 센서 객체 정리 (필요 시)
            if diyb_sensor is not None:
                # 별도 deinit 필요 없음 (ADC 재사용)
                pass

            # 새 DIY-B 센서 초기화
            try:
                diyb_sensor = DiyBSensor(adc_pin=pin_number)
                logger.info(f"DIY-B sensor initialized on pin {pin_number}", "DIYB")
                return True
            except Exception as e:
                logger.error(f"Failed to initialize DIY-B sensor: {e}", "DIYB")
                return False

        elif pin_type == 'hall':
            # 자기장(Hall) 센서 핀 설정
            PIN_HALL = pin_number

            # 기존 센서 객체 정리 (필요 시)
            if hall_sensor is not None:
                # 별도 deinit 필요 없음 (ADC 재사용)
                pass

            # 새 Hall 센서 초기화
            try:
                hall_sensor = HallSensor(adc_pin=pin_number)
                logger.info(f"Hall sensor initialized on pin {pin_number}", "HALL")
                return True
            except Exception as e:
                logger.error(f"Failed to initialize Hall sensor: {e}", "HALL")
                return False
                
        elif pin_type == 'soil':
            # 토양수분센서(YL-69) 핀 설정
            PIN_SOIL = pin_number
            
            # 기존 센서 객체 정리
            if soil_sensor is not None:
                # 기존 센서 정리 (필요시)
                pass
            
            # 새 토양수분센서 초기화
            try:
                soil_sensor = YL69SoilMoisture(adc_pin=pin_number)
                logger.info(f"Soil moisture sensor initialized on pin {pin_number}", "SOIL")
                return True
            except Exception as e:
                logger.error(f"Failed to initialize soil moisture sensor: {e}", "SOIL")
                return False
                
        elif pin_type == 'rain':
            # 빗방울센서 핀 설정
            PIN_RAIN = pin_number
            
            # 기존 센서 객체 정리
            if rain_sensor is not None:
                try:
                    rain_sensor.deinit()
                except:
                    pass
            
            # 새 빗방울센서 초기화 (ADC)
            try:
                rain_sensor = machine.ADC(machine.Pin(pin_number))
                rain_sensor.atten(machine.ADC.ATTN_11DB)  # 3.3V 범위
                logger.info(f"Rain sensor initialized on pin {pin_number}", "RAIN")
                return True
            except Exception as e:
                logger.error(f"Failed to initialize rain sensor: {e}", "RAIN")
                return False
        
        elif pin_type == 'ezlight':
            # EZMaker 전용 밝기센서(EZLIGHT) 핀 설정
            PIN_EZLIGHT = pin_number

            # 기존 센서 객체 정리 (필요 시)
            if ez_light_sensor is not None:
                # 별도 deinit 필요 없음 (ADC 재사용)
                pass

            # 새 EZLIGHT 센서 초기화
            try:
                ez_light_sensor = EzLightSensor(adc_pin=pin_number)
                logger.info(f"EZ-Light sensor initialized on pin {pin_number}", "EZLIGHT")
                return True
            except Exception as e:
                logger.error(f"Failed to initialize EZ-Light sensor: {e}", "EZLIGHT")
                return False

        elif pin_type == 'ezvolt':
            # EZMaker 전용 전압센서(EZVOLT) 핀 설정
            PIN_EZVOLT = pin_number

            # 기존 센서 객체 정리 (필요 시)
            if ez_volt_sensor is not None:
                # 별도 deinit 필요 없음 (ADC 재사용)
                pass

            # 새 EZVOLT 센서 초기화
            try:
                ez_volt_sensor = EzVoltSensor(adc_pin=pin_number)
                logger.info(f"EZ-Volt sensor initialized on pin {pin_number}", "EZVOLT")
                return True
            except Exception as e:
                logger.error(f"Failed to initialize EZ-Volt sensor: {e}", "EZVOLT")
                return False

        elif pin_type == 'ezthermal':
            # EZMaker 수중/접촉 온도센서(EZTHERMAL, DS18B20) 핀 설정
            PIN_EZTHERMAL = pin_number

            # 기존 센서 객체 정리 (필요 시 별도 deinit 없음)
            if ez_thermal_sensor is not None:
                pass

            # 새 EZTHERMAL 센서 초기화
            try:
                ez_thermal_sensor = EzThermalSensor(pin_num=pin_number)
                logger.info(f"EZThermal sensor initialized on pin {pin_number}", "EZTHERMAL")
                return True
            except Exception as e:
                logger.error(f"Failed to initialize EZThermal sensor: {e}", "EZTHERMAL")
                ez_thermal_sensor = None
                return False

        elif pin_type == 'ezsound':
            # EZMaker 소리센서(EZSOUND) 핀 설정
            PIN_EZSOUND = pin_number

            # 기존 센서 객체 정리 (필요 시 별도 deinit 없음)
            if ez_sound_sensor is not None:
                pass

            # 새 EZSOUND 센서 초기화
            try:
                ez_sound_sensor = EzSoundSensor(adc_pin=pin_number)
                logger.info(f"EZ-Sound sensor initialized on pin {pin_number}", "EZSOUND")
                return True
            except Exception as e:
                logger.error(f"Failed to initialize EZ-Sound sensor: {e}", "EZSOUND")
                return False

        elif pin_type == 'ezweight':
            # EZMaker 무게센서(EZWEIGHT, HX711) 핀 설정
            # pin_number: DOUT(DT), secondary_pin: SCK(CLK)
            PIN_EZWEIGHT_DOUT = pin_number
            PIN_EZWEIGHT_SCK = secondary_pin if secondary_pin is not None else pin_number + 1

            # 기존 센서 객체 정리 (필요 시 별도 deinit 없음)
            if ez_weight_sensor is not None:
                pass

            # 새 EZWEIGHT 센서 초기화
            try:
                ez_weight_sensor = EzWeightSensor(
                    dout_pin=PIN_EZWEIGHT_DOUT,
                    sck_pin=PIN_EZWEIGHT_SCK,
                )
                logger.info(f"EZ-Weight sensor initialized on DOUT={PIN_EZWEIGHT_DOUT}, SCK={PIN_EZWEIGHT_SCK}", "EZWEIGHT")
                return True
            except Exception as e:
                logger.error(f"Failed to initialize EZ-Weight sensor: {e}", "EZWEIGHT")
                return False

        elif pin_type == 'laser':
            # EZMaker 레이저 모듈 디지털 핀 설정
            PIN_LASER = pin_number
            
            # 기존 레이저 핀 정리
            if laser_pin is not None:
                try:
                    laser_pin.deinit()
                except:
                    pass
            
            # 새 레이저 핀 설정 (디지털 출력)
            laser_pin = machine.Pin(pin_number, machine.Pin.OUT)
            laser_pin.value(0)  # 초기값: OFF
            logger.info(f"Laser module pin set to {pin_number}", "LASER")
            return True
            
        else:
            logger.error(f"Unknown pin type '{pin_type}'", "SYS")
            return False
            
    except Exception as e:
        logger.error(f"Error updating pin config: {e}", "SYS")
        return False

# ---------------------------
# MAC 주소를 사용한 디바이스 이름 생성
# ---------------------------
def get_device_name():
    try:
        # ESP32의 MAC 주소 가져오기
        mac = ubinascii.hexlify(network.WLAN().config('mac')).decode()
        # 마지막 5자리만 사용
        mac_suffix = mac[-6:].upper()
        # "DB + MAC 주소 끝 5자리" 형식으로 이름 생성
        device_name = f"DCB{mac_suffix}"
        logger.info(f"Device name: {device_name}", "BLE")
        return device_name
    except Exception as e:
        logger.error(f"Error getting MAC address: {e}", "BLE")
        # 오류 발생 시 기본 이름 사용
        return "DeepCoBoard"

# ---------------------------
# 1) LED
# ---------------------------
# LED 핀은 None으로 초기화되어 있으므로 여기서는 초기화하지 않음
blink_flag = False
blink_interval = 1000  # LED 깜빡임 간격 (밀리초 단위), 기본값 1000ms

def led_blink_thread():
    while True:
        if blink_flag and led_pin is not None:
            if hasattr(led_pin, 'duty'):  # PWM 모드인 경우
                # 현재 값이 0이면 최대 밝기로, 아니면 0으로 설정
                current = led_pin.duty()
                if current > 0:
                    led_pin.duty(0)
                else:
                    led_pin.duty(1023)  # 최대 밝기
            else:  # 디지털 모드인 경우
                led_pin.value(1 - led_pin.value())
            time.sleep(blink_interval / 1000)  # 밀리초를 초 단위로 변환
        else:
            time.sleep(0.1)

# 스레드는 나중에 핀이 설정된 후에 유용할 것이므로 미리 시작
_thread.start_new_thread(led_blink_thread, ())


# ---------------------------
# 레이저 모듈 핸들러 (EZMaker 전용)
# ---------------------------
def laser_handler(conn_handle, cmd_str):
    """
    레이저 모듈 명령어 처리 (EZMaker 전용):
    - LASER:ON         : 레이저 ON
    - LASER:OFF        : 레이저 OFF
    - LASER:PIN:핀번호 : 레이저 모듈이 연결된 디지털 핀 설정
    """
    global laser_pin
    
    cmd_str = cmd_str.upper()
    logger.debug(f"Received command: {cmd_str}", "LASER")
    
    if cmd_str == "LASER:ON":
        if laser_pin is None:
            logger.warning("Laser module not configured", "LASER")
            try:
                uart.laser_notify(b"LASER:ERROR:Not configured")
            except Exception:
                pass
            return
        laser_pin.value(1)
        logger.info("Laser turned ON", "LASER")
        try:
            uart.laser_notify(b"LASER:ON:OK")
        except Exception:
            pass
    
    elif cmd_str == "LASER:OFF":
        if laser_pin is None:
            logger.warning("Laser module not configured", "LASER")
            try:
                uart.laser_notify(b"LASER:ERROR:Not configured")
            except Exception:
                pass
            return
        laser_pin.value(0)
        logger.info("Laser turned OFF", "LASER")
        try:
            uart.laser_notify(b"LASER:OFF:OK")
        except Exception:
            pass
    
    elif cmd_str.startswith("LASER:PIN:"):
        try:
            pin_number = int(cmd_str.split(":")[2])
            success = update_pin_config('laser', pin_number)
            if success:
                logger.info(f"Laser pin configured to {pin_number}", "LASER")
                try:
                    uart.laser_notify(f"LASER:PIN:OK:{pin_number}".encode())
                except Exception:
                    pass
            else:
                logger.warning("Laser pin configuration failed", "LASER")
                try:
                    uart.laser_notify(b"LASER:ERROR:Pin configuration failed")
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"Error setting laser pin: {e}", "LASER")
            try:
                uart.laser_notify(b"LASER:ERROR:Invalid pin configuration")
            except Exception:
                pass
    else:
        logger.warning(f"Unknown LASER command: {cmd_str}", "LASER")
        try:
            uart.laser_notify(b"LASER:ERROR:Unknown command")
        except Exception:
            pass

def led_handler(conn_handle, cmd_str):
    """
    LED 관련 명령어 처리:
    - LED:ON: LED 켜기 (저장된 PWM 값 사용)
    - LED:OFF: LED 끄기 (PWM 0)
    - LED:BLINK:간격: LED 깜빡임 시작 (간격은 밀리초 단위)
    - LED:PIN:핀번호: LED 핀 설정 (항상 PWM 모드로 초기화)
    - LED:BRIGHTNESS:값: LED 밝기 값 설정 (0-255 사이의 PWM 값, 저장만 하고 LED는 켜지 않음)
    """
    global blink_flag, blink_interval, led_pin, led_pwm_value
    
    cmd_str = cmd_str.upper()
    logger.debug(f"Received command: {cmd_str}", "LED")
    
    if cmd_str == "LED:ON":
        # LED가 설정되지 않은 경우
        if led_pin is None:
            logger.warning("LED not configured", "LED")
            #uart.led_notify(b"LED:ERROR:Not configured")
            return
            
        # 깜빡임 중지
        blink_flag = False
        time.sleep(0.2)  # 스레드가 멈출 시간 확보
        
        # LED ON - 저장된 PWM 값 사용
        pwm_16bit = int((led_pwm_value / 255) * 65535)
        led_pin.duty_u16(pwm_16bit)
        logger.info(f"LED turned ON with PWM value: {led_pwm_value} (16bit: {pwm_16bit})", "LED")
        #uart.led_notify(b"LED:ON:OK")
        
    elif cmd_str == "LED:OFF":
        # LED가 설정되지 않은 경우
        if led_pin is None:
            logger.warning("LED not configured", "LED")
            #uart.led_notify(b"LED:ERROR:Not configured")
            return
        
        # 깜빡임 중지
        blink_flag = False
        time.sleep(0.2)  # 스레드가 멈출 시간 확보
            
        # LED OFF
        led_pin.duty_u16(0)  # 밝기 0
        logger.info("LED turned OFF", "LED")
        #uart.led_notify(b"LED:OFF:OK")
        
    elif cmd_str.startswith("LED:BRIGHTNESS:"):
        # LED 밝기 설정 명령 처리
        # LED가 설정되지 않은 경우
        if led_pin is None:
            logger.warning("LED not configured", "LED")
            #uart.led_notify(b"LED:ERROR:Not configured")
            return
            
        try:
            # 밝기 값 (0-255)
            pwm_value = int(cmd_str.split(":")[2])
            if pwm_value < 0:
                pwm_value = 0
            elif pwm_value > 255:
                pwm_value = 255
                
            # PWM 값을 저장만 하고 LED는 켜지 않음
            led_pwm_value = pwm_value
            
            logger.info(f"LED brightness value set to PWM:{pwm_value} (not applied until LED:ON)", "LED")
            #uart.led_notify(f"LED:BRIGHTNESS:OK:{pwm_value}".encode())
        except Exception as e:
            logger.error(f"Error setting LED brightness value: {e}", "LED")
            #uart.led_notify(b"LED:ERROR:Invalid brightness value")
    
    elif cmd_str.startswith("LED:BLINK:"):
        # LED가 설정되지 않은 경우
        if led_pin is None:
            logger.warning("LED not configured", "LED")
            #uart.led_notify(b"LED:ERROR:Not configured")
            return
            
        try:
            # 간격 설정 (밀리초 단위)
            interval = int(cmd_str.split(":")[2])
            if interval < 50:  # 최소 간격 제한
                interval = 50
            elif interval > 10000:  # 최대 간격 제한
                interval = 10000
                
            blink_interval = interval
            blink_flag = True
            
            logger.info(f"LED blink started with interval {blink_interval}ms", "LED")
            #uart.led_notify(f"LED:BLINK:OK:{blink_interval}".encode())
        except Exception as e:
            logger.error(f"Error setting blink interval: {e}", "LED")
            #uart.led_notify(b"LED:ERROR:Invalid blink interval")
    
    elif cmd_str.startswith("LED:PIN:"):
        # 핀 설정 명령 처리
        try:
            pin_number = int(cmd_str.split(":")[2])
            success = update_pin_config('led', pin_number)
            if success:
                #uart.led_notify(f"LED:PIN:OK:{pin_number}".encode())
                pass
            else:
                logger.warning("Pin configuration failed", "LED")
                #uart.led_notify(b"LED:ERROR:Pin configuration failed")
        except Exception as e:
            logger.error(f"Error setting LED pin: {e}", "LED")
            #uart.led_notify(b"LED:ERROR:Invalid pin configuration")
    else:
        logger.warning(f"Unknown LED command: {cmd_str}", "LED")
        #uart.led_notify(b"LED:ERROR:Unknown command")

# ---------------------------
# 2) 초음파 센서
# ---------------------------
# 초음파 센서는 None으로 초기화되어 있음

def measure_distance():
    if ultraSensor is None:
        logger.warning("Ultrasonic sensor not configured", "ULTRA")
        return 999  # 에러 상태를 900으로 표시
        
    try:
        distance = ultraSensor.distance_cm()
        # 값이 0이거나 음수인 경우 센서 측정 범위 초과로 처리
        if distance <= 0:
            logger.warning("Ultrasonic measurement out of range", "ULTRA")
            return 900  # 범위 초과/에러를 나타내는 값
        return distance
    except Exception as e:
        logger.error(f"Error measuring distance: {e}", "ULTRA")
        return 900  # 예외 발생 시 동일하게 900 반환

def ultrasonic_handler(conn_handle, cmd_str):
    """
    초음파 센서 명령어 처리:
    - ULTRA:STATUS: 현재 거리 측정하여 반환
    - ULTRA:PIN:트리거핀,에코핀: 초음파 센서 핀 설정
    """
    cmd_str = cmd_str.upper()
    logger.debug(f"Received command: {cmd_str}", "ULTRA")

    if cmd_str == "ULTRA:STATUS":
        # 초음파 센서가 설정되지 않은 경우
        if ultraSensor is None:
            logger.warning("Ultrasonic sensor not configured", "ULTRA")
            uart.ultrasonic_notify(b"ULTRA:ERROR:Sensor not configured")
            return
            
        # 거리 측정 및 전송
        try:
            distance = measure_distance()
            logger.info(f"Measured distance: {distance:.1f} cm", "ULTRA")
            distance_str = f"ULTRA:{distance:.1f}"
            uart.ultrasonic_notify(distance_str.encode())
        except Exception as e:
            logger.error(f"Error measuring distance: {e}", "ULTRA")
            uart.ultrasonic_notify(b"ULTRA:ERROR:Measurement failed")
    # ULTRA:PIN:트리거핀,에코핀
    elif cmd_str.startswith("ULTRA:PIN:"):
        try:
            # 핀 번호 파싱
            pins = cmd_str.split(":")[2].split(",")
            if len(pins) < 2:
                logger.warning("Invalid pin configuration. Need two pins.", "ULTRA")
                uart.ultrasonic_notify(b"ULTRA:ERROR:Need two pins")
                return
                
            trig_pin = int(pins[0])
            echo_pin = int(pins[1])
            
            # 핀 설정 업데이트
            success = update_pin_config('ultra', trig_pin, echo_pin)
            if success:
                logger.info(f"Ultrasonic pins set to trigger={trig_pin}, echo={echo_pin}", "ULTRA")
                uart.ultrasonic_notify(f"ULTRA:PIN:OK:{trig_pin},{echo_pin}".encode())
            else:
                logger.warning("Ultrasonic pin configuration failed", "ULTRA")
                uart.ultrasonic_notify(b"ULTRA:ERROR:Pin configuration failed")
        except Exception as e:
            logger.error(f"Error setting ultrasonic pins: {e}", "ULTRA")
            uart.ultrasonic_notify(b"ULTRA:ERROR:Invalid pin configuration")
    else:
        logger.warning(f"Unknown ULTRASONIC command: {cmd_str}", "ULTRA")
        uart.ultrasonic_notify(b"ULTRA:ERROR:Unknown command")

# ---------------------------
# 3) DHT11 센서
# ---------------------------
# DHT 센서는 None으로 초기화되어 있음

def dht_handler(conn_handle, cmd_str):
    """
    DHT 온습도 센서 명령어 처리:
    - DHT:STATUS: 현재 온도와 습도 측정하여 반환
    - DHT:PIN:핀번호: DHT 센서 핀 설정
    """
    cmd_str = cmd_str.upper()
    logger.debug(f"Received command: {cmd_str}", "DHT")
    
    if cmd_str == "DHT:STATUS":
        # 센서가 설정되지 않은 경우
        if dht_sensor is None:
            logger.warning("DHT sensor not configured", "DHT")
            uart.dht_notify(b"DHT:ERROR:Sensor not configured")
            return
            
        # 현재 온습도 측정 및 전송
        try:
            dht_sensor.measure()
            t = dht_sensor.temperature()
            h = dht_sensor.humidity()
            msg = f"DHT:T={t:.1f},H={h:.1f}"
            uart.dht_notify(msg.encode())
            logger.info(f"DHT temperature: {t:.1f}°C, humidity: {h:.1f}%", "DHT")
        except Exception as e:
            logger.error(f"Error measuring DHT: {e}", "DHT")
            uart.dht_notify(b"DHT:ERROR:Measurement failed")
    # 핀 설정 명령 처리
    elif cmd_str.startswith("DHT:PIN:"):
        try:
            pin_number = int(cmd_str.split(":")[2])
            success = update_pin_config('dht', pin_number)
            if success:
                uart.dht_notify(f"DHT:PIN:OK:{pin_number}".encode())
            else:
                uart.dht_notify(b"DHT:ERROR:Pin configuration failed")
        except Exception as e:
            logger.error(f"Error setting DHT pin: {e}", "DHT")
            uart.dht_notify(b"DHT:ERROR:Invalid pin configuration")
    else:
        logger.warning(f"Unknown DHT command: {cmd_str}", "DHT")
        if uart:
            uart.dht_notify(b"DHT:ERROR:Unknown command")

# ---------------------------
# 4) 서보모터
# ---------------------------
#  - 0..180도 사이
# ---------------------------
# 서보 모터 핀과 PWM은 None으로 초기화되어 있음

def set_servo_angle(deg):
    """
    deg: 0..180
    서보 펄스 폭 = 500us(0도) ~ 2500us(180도) 일반적인 예시
    MicroPython에서는 duty_ns, duty_u16 등을 사용 가능.
    여기서는 duty_ns를 사용해 봄.
    """
    if servo_pwm is None:
        logger.warning("Servo motor not configured", "SERVO")
        return False
        
    if deg < 0: deg = 0
    if deg > 180: deg = 180

    # 0도 = 0.5ms, 180도 = 2.5ms
    pulse_min_ns = 500_000   # 0.5ms = 500,000ns
    pulse_max_ns = 2_500_000 # 2.5ms
    # 각도 비율로 보간
    pulse_ns = pulse_min_ns + (pulse_max_ns - pulse_min_ns) * deg / 180

    servo_pwm.duty_ns(int(pulse_ns))
    return True

def set_servo_angle_by_index(index, deg):
    """
    index: 서보 인덱스 (1 또는 2)
    deg: 0..180
    특정 서보 모터의 각도를 설정합니다.
    """
    if index == 1:
        if servo_pwm1 is None:
            logger.warning("Servo motor 1 not configured", "SERVO")
            return False
            
        if deg < 0: deg = 0
        if deg > 180: deg = 180

        # 0도 = 0.5ms, 180도 = 2.5ms
        pulse_min_ns = 500_000   # 0.5ms = 500,000ns
        pulse_max_ns = 2_500_000 # 2.5ms
        # 각도 비율로 보간
        pulse_ns = pulse_min_ns + (pulse_max_ns - pulse_min_ns) * deg / 180

        servo_pwm1.duty_ns(int(pulse_ns))
        return True
    elif index == 2:
        if servo_pwm2 is None:
            logger.warning("Servo motor 2 not configured", "SERVO")
            return False
            
        if deg < 0: deg = 0
        if deg > 180: deg = 180

        # 0도 = 0.5ms, 180도 = 2.5ms
        pulse_min_ns = 500_000   # 0.5ms = 500,000ns
        pulse_max_ns = 2_500_000 # 2.5ms
        # 각도 비율로 보간
        pulse_ns = pulse_min_ns + (pulse_max_ns - pulse_min_ns) * deg / 180

        servo_pwm2.duty_ns(int(pulse_ns))
        return True
    else:
        logger.error(f"Invalid servo index: {index}", "SERVO")
        return False

def servo_handler(conn_handle, cmd_str):
    """
    서보모터 명령어 처리:
    - SERVO:PIN:핀번호: 서보 핀 설정 (기존 호환)
    - SERVO:PIN1:핀번호: 첫 번째 서보 핀 설정
    - SERVO:PIN2:핀번호: 두 번째 서보 핀 설정
    - SERVO:각도: 서보 각도 설정 (기존 호환, 첫 번째 서보 제어)
    - SERVO1:각도: 첫 번째 서보 각도 설정
    - SERVO2:각도: 두 번째 서보 각도 설정
    """
    cmd_str = cmd_str.upper()
    logger.debug(f"Received command: {cmd_str}", "SERVO")
    
    # 핀 설정 명령 처리 (기존 호환)
    if cmd_str.startswith("SERVO:PIN:"):
        try:
            pin_number = int(cmd_str.split(":")[2])
            success = update_pin_config('servo', pin_number)
            if success:
                uart.servo_notify(f"SERVO:PIN:OK:{pin_number}".encode())
            else:
                uart.servo_notify(b"SERVO:ERROR:Pin configuration failed")
            return
        except Exception as e:
            logger.error(f"Error setting servo pin: {e}", "SERVO")
            uart.servo_notify(b"SERVO:ERROR:Invalid pin configuration")
            return
    
    # 첫 번째 서보 핀 설정 명령 처리
    elif cmd_str.startswith("SERVO:PIN1:"):
        try:
            pin_number = int(cmd_str.split(":")[2])
            success = update_pin_config('servo1', pin_number)
            if success:
                uart.servo_notify(f"SERVO:PIN1:OK:{pin_number}".encode())
            else:
                uart.servo_notify(b"SERVO:ERROR:Pin configuration failed")
            return
        except Exception as e:
            logger.error(f"Error setting servo1 pin: {e}", "SERVO")
            uart.servo_notify(b"SERVO:ERROR:Invalid pin configuration")
            return
    
    # 두 번째 서보 핀 설정 명령 처리
    elif cmd_str.startswith("SERVO:PIN2:"):
        try:
            pin_number = int(cmd_str.split(":")[2])
            success = update_pin_config('servo2', pin_number)
            if success:
                uart.servo_notify(f"SERVO:PIN2:OK:{pin_number}".encode())
            else:
                uart.servo_notify(b"SERVO:ERROR:Pin configuration failed")
            return
        except Exception as e:
            logger.error(f"Error setting servo2 pin: {e}", "SERVO")
            uart.servo_notify(b"SERVO:ERROR:Invalid pin configuration")
            return
    
    # 첫 번째 서보 각도 설정 명령 처리 (SERVO1:각도)
    elif cmd_str.startswith("SERVO1:"):
        # 서보 모터가 설정되지 않은 경우
        if servo_pwm1 is None:
            logger.warning("Servo motor 1 not configured", "SERVO")
            uart.servo_notify(b"SERVO:ERROR:Motor1 not configured")
            return
            
        # 예: "SERVO1:0", "SERVO1:90", ...
        parts = cmd_str.split(":")
        if len(parts) == 2 and parts[1].isdigit():
            try:
                angle = int(parts[1])
                success = set_servo_angle_by_index(1, angle)
                if success:
                    logger.info(f"Servo1 angle set to {angle}", "SERVO")
                    uart.servo_notify(f"SERVO1:OK:{angle}".encode())
                else:
                    uart.servo_notify(b"SERVO:ERROR:Failed to set angle for servo1")
            except Exception as e:
                logger.error(f"Invalid servo1 angle: {parts[1]}", "SERVO")
                uart.servo_notify(b"SERVO:ERROR:Invalid angle for servo1")
        else:
            logger.error(f"Invalid servo1 command format: {cmd_str}", "SERVO")
            uart.servo_notify(b"SERVO:ERROR:Invalid command format for servo1")
    
    # 두 번째 서보 각도 설정 명령 처리 (SERVO2:각도)
    elif cmd_str.startswith("SERVO2:"):
        # 서보 모터가 설정되지 않은 경우
        if servo_pwm2 is None:
            logger.warning("Servo motor 2 not configured", "SERVO")
            uart.servo_notify(b"SERVO:ERROR:Motor2 not configured")
            return
            
        # 예: "SERVO2:0", "SERVO2:90", ...
        parts = cmd_str.split(":")
        if len(parts) == 2 and parts[1].isdigit():
            try:
                angle = int(parts[1])
                success = set_servo_angle_by_index(2, angle)
                if success:
                    logger.info(f"Servo2 angle set to {angle}", "SERVO")
                    uart.servo_notify(f"SERVO2:OK:{angle}".encode())
                else:
                    uart.servo_notify(b"SERVO:ERROR:Failed to set angle for servo2")
            except Exception as e:
                logger.error(f"Invalid servo2 angle: {parts[1]}", "SERVO")
                uart.servo_notify(b"SERVO:ERROR:Invalid angle for servo2")
        else:
            logger.error(f"Invalid servo2 command format: {cmd_str}", "SERVO")
            uart.servo_notify(b"SERVO:ERROR:Invalid command format for servo2")
    
    # 서보 각도 설정 명령 처리 (SERVO:각도) - 기존 호환 (첫 번째 서보)
    elif cmd_str.startswith("SERVO:"):
        # 서보 모터가 설정되지 않은 경우
        if servo_pwm is None:
            logger.warning("Servo motor not configured", "SERVO")
            uart.servo_notify(b"SERVO:ERROR:Motor not configured")
            return
            
        # 예: "SERVO:0", "SERVO:90", ...
        parts = cmd_str.split(":")
        if len(parts) == 2 and parts[1].isdigit():
            try:
                angle = int(parts[1])
                success = set_servo_angle(angle)
                if success:
                    logger.info(f"Servo angle set to {angle}", "SERVO")
                    uart.servo_notify(f"SERVO:OK:{angle}".encode())
                else:
                    uart.servo_notify(b"SERVO:ERROR:Failed to set angle")
            except Exception as e:
                logger.error(f"Invalid servo angle: {parts[1]}", "SERVO")
                uart.servo_notify(b"SERVO:ERROR:Invalid angle")
        else:
            logger.error(f"Invalid servo command format: {cmd_str}", "SERVO")
            uart.servo_notify(b"SERVO:ERROR:Invalid command format")
    else:
        logger.warning(f"Unknown SERVO command: {cmd_str}", "SERVO")
        uart.servo_notify(b"SERVO:ERROR:Unknown command")

# ---------------------------
# 5) NeoPixel LED
# ---------------------------
# NeoPixel은 None으로 초기화되어 있음

# NeoPixel 상태 변수
neo_rainbow_active = False
neo_rainbow_speed = 5  # 기본 속도 (1-10)
neo_rainbow_thread = None

# 무지개 효과 함수
def wheel(pos):
    """
    0-255 위치 값을 RGB 색상으로 변환
    """
    if pos < 0 or pos > 255:
        return (0, 0, 0)
    if pos < 85:
        return (255 - pos * 3, pos * 3, 0)
    if pos < 170:
        pos -= 85
        return (0, 255 - pos * 3, pos * 3)
    pos -= 170
    return (pos * 3, 0, 255 - pos * 3)

# 네오픽셀 색상에 밝기 적용 함수 추가
def apply_brightness(r, g, b, brightness=None):
    """
    RGB 색상에 밝기 계수를 적용합니다.
    brightness가 None이면 전역 밝기 값을 사용합니다.
    """
    if brightness is None:
        brightness = neo_brightness
        
    brightness = max(0.0, min(1.0, brightness))  # 0.0-1.0 범위로 제한
    
    r = int(r * brightness)
    g = int(g * brightness)
    b = int(b * brightness)
    
    return (r, g, b)

# 무지개 효과 스레드
def rainbow_thread(speed=5):
    global neo_rainbow_active, neo_rainbow_speed, neo_num_pixels  # 전역 변수 사용 선언 추가
    
    # 전달받은 speed 파라미터를 전역 변수에 설정
    neo_rainbow_speed = max(1, min(10, speed))
    
    offset = 0
    while neo_rainbow_active:
        if neo is None:  # NeoPixel이 설정되지 않은 경우 스레드 종료
            neo_rainbow_active = False
            break
            
        for i in range(neo_num_pixels):
            # 각 LED마다 다른 색상 오프셋 적용
            color = wheel((i * 256 // neo_num_pixels + offset) & 255)
            # 밝기 적용
            color = apply_brightness(*color)
            neo[i] = color
        neo.write()
        
        # 속도에 따른 지연 시간 계산 (속도 1-10)
        delay = (11 - neo_rainbow_speed) * 0.05
        time.sleep(delay)
        
        # 오프셋 증가
        offset = (offset + 1) & 255
    
    # 스레드 종료 시 모든 LED 끄기
    if neo is not None:
        neo.fill((0, 0, 0))
        neo.write()

# 무지개 효과 시작
def start_rainbow(speed=5):
    global neo_rainbow_active, neo_rainbow_speed, neo_rainbow_thread
    
    # NeoPixel이 설정되지 않은 경우
    if neo is None:
        logger.warning("NeoPixel not configured", "NEO")
        return False
    
    # 속도 범위 제한 (1-10)
    neo_rainbow_speed = max(1, min(10, speed))
    
    # 이미 실행 중이면 속도만 업데이트
    if neo_rainbow_active:
        return True
    
    # 무지개 효과 활성화 및 스레드 시작
    neo_rainbow_active = True
    neo_rainbow_thread = _thread.start_new_thread(rainbow_thread, (speed,))
    return True

# 무지개 효과 중지
def stop_rainbow():
    global neo_rainbow_active
    if not neo_rainbow_active:
        return
        
    neo_rainbow_active = False
    # 스레드가 종료될 때까지 잠시 대기
    time.sleep(0.1)

def neopixel_handler(conn_handle, cmd_str):
    """
    NeoPixel 명령어 처리:
    - NEO:PIN:핀번호[,LED개수]: NeoPixel 핀 설정
    - NEO:PX:인덱스,R,G,B: 개별 LED 색상 설정
    - NEO:ALL:R,G,B: 모든 LED 색상 설정
    - NEO:RAINBOW:속도: 무지개 효과 설정
    - NEO:OFF: 모든 LED 끄기
    - NEO:BRIGHTNESS:밝기: 네오픽셀 밝기 설정 (0-100)
    """
    global neo_brightness  # 밝기 전역 변수 추가
    
    # 원시 명령어 로깅 - 문제 디버깅을 위해 추가
    logger.debug(f"Raw command received: '{cmd_str}'", "NEO")
    
    # 명령어의 각 문자를 16진수로 출력하여 숨겨진 문자 확인
    hex_values = [f"{ord(c):02x}" for c in cmd_str]
    logger.debug(f"Command bytes: {' '.join(hex_values)}", "NEO")
    
    logger.info(f"Received command: {cmd_str}", "NEO")
    print(f"1111111111111Received command: {cmd_str}")
    
    try:
        # 명령어 파싱
        parts = cmd_str.upper().split(":")
        
        if len(parts) < 2 or parts[0] != "NEO":
            logger.error(f"Invalid NeoPixel command format: {cmd_str}", "NEO")
            uart.neopixel_notify(b"NEO:ERROR:Invalid command format")
            return
            
        cmd = parts[1]  # 두 번째 요소를 명령으로 사용 (PIN, PIXEL, SETALL, RAINBOW, OFF)
        
        # PIN 설정 명령 처리
        if cmd == "PIN" and len(parts) >= 3:
            try:
                values = parts[2].split(",")
                if not values[0].strip():
                    raise ValueError("Pin number cannot be empty")
                pin_number = int(values[0].strip())
                
                pixel_count = NUM_PIXELS_DEFAULT  # 기본값 사용
                if len(values) > 1 and values[1].strip():
                    pixel_count = int(values[1].strip())
                
                success = update_pin_config('neo', pin_number, pixel_count)
                if success:
                    uart.neopixel_notify(f"NEO:PIN:OK:{pin_number},{pixel_count}".encode())
                else:
                    uart.neopixel_notify(b"NEO:ERROR:Pin configuration failed")
            except ValueError as e:
                logger.error(f"Error parsing pin values: {e}", "NEO")
                uart.neopixel_notify(b"NEO:ERROR:Invalid number format")
            except Exception as e:
                logger.error(f"Error setting NeoPixel pin: {e}", "NEO")
                uart.neopixel_notify(b"NEO:ERROR:Invalid pin configuration")
            return  # PIN 명령 처리 후 함수 종료
            
        # 아래 명령들은 NeoPixel이 설정되어 있어야 함
        if neo is None:
            logger.warning("NeoPixel not configured", "NEO")
            uart.neopixel_notify(b"NEO:ERROR:NeoPixel not configured")
            return
        
        # 밝기 설정 명령 처리 (추가)
        if cmd == "BRIGHTNESS" and len(parts) >= 3:
            try:
                brightness_value = int(parts[2].strip())
                
                # 범위 제한 (0-255)
                if brightness_value < 0:
                    brightness_value = 0
                elif brightness_value > 255:
                    brightness_value = 255
                
                # 0-255에서 0.0-1.0 범위로 변환
                neo_brightness = brightness_value / 255.0
                
                logger.info(f"NeoPixel brightness set to {brightness_value}", "NEO")
                uart.neopixel_notify(f"NEO:BRIGHTNESS:OK:{brightness_value}".encode())
            except ValueError as e:
                logger.error(f"Error in BRIGHTNESS command: {e}", "NEO")
                uart.neopixel_notify(f"NEO:ERROR:Invalid value - {str(e)}".encode())
            except Exception as e:
                logger.error(f"Error processing NeoPixel command: {e}", "NEO")
                uart.neopixel_notify(b"NEO:ERROR:Command processing failed")
        
        # PIXEL 명령 처리
        elif cmd == "PX" and len(parts) >= 3:
            try:
                values = parts[2].split(",")
                # 디버깅 정보 기록
                logger.debug(f"PIXEL command values: {values}, length: {len(values)}", "NEO")

                # 값 유효성 검사
                if len(values) < 4:
                    raise ValueError(f"Not enough values. Expected 4, got {len(values)}")
                
                # 모든 값을 정수로 변환 시도 전에 유효성 검사
                for i, val in enumerate(values[:4]):
                    if not val.strip():
                        raise ValueError(f"Value at position {i} is empty")
                    if not val.strip().isdigit():
                        raise ValueError(f"Value '{val}' at position {i} is not a valid number")
                
                index = int(values[0].strip())
                r = int(values[1].strip())
                g = int(values[2].strip())
                b = int(values[3].strip())
                
                # 값 범위 검사
                if not (0 <= index < neo_num_pixels):
                    raise ValueError(f"Index {index} out of range (0-{neo_num_pixels-1})")
                if not (0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255):
                    raise ValueError(f"RGB values must be between 0 and 255")
                
                # 무지개 효과 중지
                if neo_rainbow_active:
                    stop_rainbow()
                
                # 색상에 밝기 적용
                color = apply_brightness(r, g, b)
                
                # LED 색상 설정
                neo[index] = color
                neo.write()
                logger.info(f"Set NeoPixel {index} to RGB({r},{g},{b}) with brightness {neo_brightness:.1f}", "NEO")
                uart.neopixel_notify(f"NEO:PIXEL:OK:{index}".encode())
            except ValueError as e:
                logger.error(f"Error in PIXEL command: {e}", "NEO")
                uart.neopixel_notify(f"NEO:ERROR:Invalid value - {str(e)}".encode())
            except Exception as e:
                logger.error(f"Error processing NeoPixel command: {e}", "NEO")
                uart.neopixel_notify(b"NEO:ERROR:Command processing failed")
            return    
        # PIXEL 명령 처리
        elif cmd == "PIXEL" and len(parts) >= 3:
            try:
                values = parts[2].split(",")
                # 디버깅 정보 기록
                logger.debug(f"PIXEL command values: {values}, length: {len(values)}", "NEO")

                # 값 유효성 검사
                if len(values) < 4:
                    raise ValueError(f"Not enough values. Expected 4, got {len(values)}")
                
                # 모든 값을 정수로 변환 시도 전에 유효성 검사
                for i, val in enumerate(values[:4]):
                    if not val.strip():
                        raise ValueError(f"Value at position {i} is empty")
                    if not val.strip().isdigit():
                        raise ValueError(f"Value '{val}' at position {i} is not a valid number")
                
                index = int(values[0].strip())
                r = int(values[1].strip())
                g = int(values[2].strip())
                b = int(values[3].strip())
                
                # 값 범위 검사
                if not (0 <= index < neo_num_pixels):
                    raise ValueError(f"Index {index} out of range (0-{neo_num_pixels-1})")
                if not (0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255):
                    raise ValueError(f"RGB values must be between 0 and 255")
                
                # 무지개 효과 중지
                if neo_rainbow_active:
                    stop_rainbow()
                
                # 색상에 밝기 적용
                color = apply_brightness(r, g, b)
                
                # LED 색상 설정
                neo[index] = color
                neo.write()
                logger.info(f"Set NeoPixel {index} to RGB({r},{g},{b}) with brightness {neo_brightness:.1f}", "NEO")
                uart.neopixel_notify(f"NEO:PIXEL:OK:{index}".encode())
            except ValueError as e:
                logger.error(f"Error in PIXEL command: {e}", "NEO")
                uart.neopixel_notify(f"NEO:ERROR:Invalid value - {str(e)}".encode())
            except Exception as e:
                logger.error(f"Error processing NeoPixel command: {e}", "NEO")
                uart.neopixel_notify(b"NEO:ERROR:Command processing failed")
                
        # SETALL 명령 처리
        elif cmd == "ALL" and len(parts) >= 3:
            try:
                values = parts[2].split(",")
                if len(values) < 3:
                    raise ValueError(f"Not enough values. Expected 3, got {len(values)}")
                
                # 모든 값을 정수로 변환 시도 전에 유효성 검사
                for i, val in enumerate(values[:3]):
                    if not val.strip():
                        raise ValueError(f"Value at position {i} is empty")
                    if not val.strip().isdigit():
                        raise ValueError(f"Value '{val}' at position {i} is not a valid number")
                
                r = int(values[0].strip())
                g = int(values[1].strip())
                b = int(values[2].strip())
                
                # 값 범위 검사
                if not (0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255):
                    raise ValueError(f"RGB values must be between 0 and 255")
                
                # 무지개 효과 중지
                if neo_rainbow_active:
                    stop_rainbow()
                
                # 색상에 밝기 적용
                color = apply_brightness(r, g, b)
                
                # 모든 LED 색상 설정
                neo.fill(color)
                neo.write()
                logger.info(f"Set all NeoPixels to RGB({r},{g},{b}) with brightness {neo_brightness:.1f}", "NEO")
                uart.neopixel_notify(b"NEO:SETALL:OK")
            except ValueError as e:
                logger.error(f"Error in SETALL command: {e}", "NEO")
                uart.neopixel_notify(f"NEO:ERROR:Invalid value - {str(e)}".encode())
            except Exception as e:
                logger.error(f"Error processing NeoPixel command: {e}", "NEO")
                uart.neopixel_notify(b"NEO:ERROR:Command processing failed")
                
        # RAINBOW 명령 처리
        elif cmd == "RAINBOW" and len(parts) >= 2:
            try:
                speed = 5  # 기본 속도
                if len(parts) > 2 and parts[2].strip():
                    if not parts[2].strip().isdigit():
                        raise ValueError(f"Speed value '{parts[2]}' is not a valid number")
                    speed = int(parts[2].strip())
                
                # 무지개 효과 시작
                success = start_rainbow(speed)
                if success:
                    logger.info(f"Started rainbow effect with speed {speed}", "NEO")
                    uart.neopixel_notify(f"NEO:RAINBOW:OK:{speed}".encode())
                else:
                    uart.neopixel_notify(b"NEO:ERROR:Failed to start rainbow effect")
            except ValueError as e:
                logger.error(f"Error in RAINBOW command: {e}", "NEO")
                uart.neopixel_notify(f"NEO:ERROR:Invalid speed value - {str(e)}".encode())
            except Exception as e:
                logger.error(f"Error processing NeoPixel command: {e}", "NEO")
                uart.neopixel_notify(b"NEO:ERROR:Command processing failed")
        
        # OFF 명령 처리
        elif cmd == "OFF":
            try:
                if neo_rainbow_active:
                    stop_rainbow()
                
                neo.fill((0, 0, 0))
                neo.write()
                logger.info("Turned off all NeoPixels", "NEO")
                uart.neopixel_notify(b"NEO:OFF:OK")
            except Exception as e:
                logger.error(f"Error turning off NeoPixels: {e}", "NEO")
                uart.neopixel_notify(b"NEO:ERROR:Failed to turn off")
            
        # 알 수 없는 명령어 처리
        else:
            logger.error(f"Unknown NeoPixel command: {cmd_str}", "NEO")
            uart.neopixel_notify(b"NEO:ERROR:Unknown command")
            
    except Exception as e:
        logger.error(f"Error processing NeoPixel command: {e}", "NEO")
        uart.neopixel_notify(b"NEO:ERROR:Command processing failed")

# ---------------------------
# 6) TTP223 터치센서
# ---------------------------
# 터치센서는 None으로 초기화되어 있음
touch_state = False  # 터치 상태 (True: 터치됨, False: 터치 안됨)

def touch_handler(conn_handle, cmd_str):
    """
    터치센서 명령어 처리:
    - TOUCH:STATUS: 현재 터치 상태 반환
    - TOUCH:PIN:핀번호: 터치 센서 핀 설정
    """
    logger.debug(f"Received command: {cmd_str}", "TOUCH")
    
    if cmd_str == "TOUCH:STATUS":
        # 터치 센서가 설정되지 않은 경우
        if touch_pin is None:
            logger.warning("Touch sensor not configured", "TOUCH")
            uart.touch_notify(b"TOUCH:ERROR:Sensor not configured")
            return
            
        # 현재 터치 핀 상태 확인
        current_touch_state = touch_pin.value() == 1
        # 현재 상태 전송
        if uart:
            status = "TOUCH:1" if current_touch_state else "TOUCH:0"
            uart.touch_notify(status.encode())
    elif cmd_str.startswith("TOUCH:PIN:"):
        # 핀 설정 명령 처리
        try:
            pin_number = int(cmd_str.split(":")[2])
            success = update_pin_config('touch', pin_number)
            if success:
                uart.touch_notify(f"TOUCH:PIN:OK:{pin_number}".encode())
            else:
                uart.touch_notify(b"TOUCH:ERROR:Pin configuration failed")
        except Exception as e:
            logger.error(f"Error setting touch pin: {e}", "TOUCH")
            uart.touch_notify(b"TOUCH:ERROR:Invalid pin configuration")
    else:
        logger.warning(f"Unknown TOUCH command: {cmd_str}", "TOUCH")
        if uart:
            uart.touch_notify(b"TOUCH:ERROR:Unknown command")

# ---------------------------
# 7) 조도센서
# ---------------------------
# 조도센서는 None으로 초기화되어 있음

def light_handler(conn_handle, cmd_str):
    """
    조도센서 명령어 처리:
    - LIGHT:STATUS: 현재 조도센서 값 측정하여 반환
    - LIGHT:PIN:아날로그핀번호[,디지털핀번호]: 핀 설정 (디지털핀은 옵션)
    """
    logger.debug(f"Received command: {cmd_str}", "LIGHT")
    
    if cmd_str == "LIGHT:STATUS":
        # 조도 센서가 설정되지 않은 경우
        if light_analog_pin is None:
            logger.warning("Light sensor not configured", "LIGHT")
            uart.light_notify(b"LIGHT:ERROR:Sensor not configured")
            return
            
        # 현재 조도값 측정 및 전송
        try:
            light_analog_value = light_analog_pin.read()
            light_digital_value = light_digital_pin.value() if light_digital_pin is not None else 0
            msg = f"LIGHT:{light_analog_value},{light_digital_value}"
            uart.light_notify(msg.encode())
            
            # 디지털 핀 상태 로그 메시지 개선
            if light_digital_pin is not None:
                logger.info(f"Light sensor: analog={light_analog_value}, digital={light_digital_value}", "LIGHT")
            else:
                logger.info(f"Light sensor: analog={light_analog_value} (no digital pin)", "LIGHT")
        except Exception as e:
            logger.error(f"Error measuring light: {e}", "LIGHT")
            uart.light_notify(b"LIGHT:ERROR:Measurement failed")
    elif cmd_str.startswith("LIGHT:PIN:"):
        # 핀 설정 명령 처리
        try:
            pins = cmd_str.split(":")[2].split(",")
            analog_pin = int(pins[0]) 
            digital_pin = int(pins[1]) if len(pins) > 1 else None
            
            # 핀 설정 업데이트 - 디지털 핀은 옵션
            success = update_pin_config('light', analog_pin, digital_pin)
            if success:
                if digital_pin is not None:
                    uart.light_notify(f"LIGHT:PIN:OK:{analog_pin},{digital_pin}".encode())
                else:
                    uart.light_notify(f"LIGHT:PIN:OK:{analog_pin}".encode())
            else:
                uart.light_notify(b"LIGHT:ERROR:Pin configuration failed")
        except Exception as e:
            logger.error(f"Error setting light sensor pins: {e}", "LIGHT")
            uart.light_notify(b"LIGHT:ERROR:Invalid pin configuration")
    elif cmd_str == "LIGHT:ON" or cmd_str == "LIGHT:OFF":
        # 조도 센서가 설정되지 않은 경우
        if light_analog_pin is None:
            logger.warning("Light sensor not configured", "LIGHT")
            uart.light_notify(b"LIGHT:ERROR:Sensor not configured")
            return
            
        # 연속 모니터링 명령 지원 중단 안내
        logger.info("Continuous light monitoring not supported", "LIGHT")
        uart.light_notify(b"LIGHT:INFO:Use STATUS command instead")
        # 현재 상태 한번 전송
        try:
            light_analog_value = light_analog_pin.read()
            light_digital_value = light_digital_pin.value() if light_digital_pin is not None else 0
            msg = f"LIGHT:A={light_analog_value},D={light_digital_value}"
            uart.light_notify(msg.encode())
        except Exception as e:
            logger.error(f"Error measuring light: {e}", "LIGHT")
    else:
        logger.warning(f"Unknown LIGHT command: {cmd_str}", "LIGHT")
        if uart:
            uart.light_notify(b"LIGHT:ERROR:Unknown command")


# ---------------------------
# I2C LCD (16x2 / 20x4)
# ---------------------------
def lcd_handler(conn_handle, cmd_str):
    """
    I2C LCD 명령어 처리:
    - LCD:INIT:16X2:SCL,SDA
    - LCD:INIT:20X4:SCL,SDA
    - LCD:CLEAR
    - LCD:BACKLIGHT:ON|OFF
    - LCD:PRINT:row,col:텍스트...
    """
    global LCD_ROWS, LCD_COLS, lcd

    logger.debug(f"Received command: {cmd_str}", "LCD")

    try:
        parts = cmd_str.split(":")
        if len(parts) < 2:
            logger.error("Invalid LCD command format", "LCD")
            uart.lcd_notify(b"LCD:ERROR:Invalid command format")
            return

        if parts[0].upper() != "LCD":
            logger.error("Invalid LCD command prefix", "LCD")
            uart.lcd_notify(b"LCD:ERROR:Invalid prefix")
            return

        subcmd = parts[1].upper()

        # 초기화: LCD:INIT:16X2:SCL,SDA  또는  LCD:INIT:20X4:SCL,SDA
        if subcmd == "INIT":
            if len(parts) < 4:
                logger.error("INIT command requires type and pins", "LCD")
                uart.lcd_notify(b"LCD:ERROR:INIT requires type and pins")
                return

            lcd_type = parts[2].upper()
            pins = parts[3].split(",")
            if len(pins) < 2:
                logger.error("INIT requires SCL and SDA pins", "LCD")
                uart.lcd_notify(b"LCD:ERROR:INIT requires SCL,SDA")
                return

            try:
                scl_pin = int(pins[0].strip())
                sda_pin = int(pins[1].strip())
            except Exception as e:
                logger.error(f"Invalid INIT pin numbers: {pins}", "LCD")
                uart.lcd_notify(b"LCD:ERROR:Invalid pin numbers")
                return

            # 타입에 따라 행/열 설정
            if lcd_type == "16X2":
                LCD_COLS = 16
                LCD_ROWS = 2
            elif lcd_type == "20X4":
                LCD_COLS = 20
                LCD_ROWS = 4
            else:
                logger.warning(f"Unknown LCD type '{lcd_type}', defaulting to 16x2", "LCD")
                LCD_COLS = 16
                LCD_ROWS = 2

            # SDA, SCL 순서로 update_pin_config 호출
            success = update_pin_config('lcd', sda_pin, scl_pin)
            if success:
                msg = f"LCD:INIT:OK:{lcd_type}:{scl_pin},{sda_pin}"
                uart.lcd_notify(msg.encode())
            else:
                uart.lcd_notify(b"LCD:ERROR:INIT failed")
            return

        # 이후 명령은 LCD가 초기화되어 있어야 함
        if lcd is None:
            logger.warning("LCD not initialized", "LCD")
            uart.lcd_notify(b"LCD:ERROR:Not initialized")
            return

        # 화면 지우기
        if subcmd == "CLEAR":
            try:
                lcd.clear()
                lcd.home()
                uart.lcd_notify(b"LCD:CLEAR:OK")
            except Exception as e:
                logger.error(f"Error clearing LCD: {e}", "LCD")
                uart.lcd_notify(b"LCD:ERROR:CLEAR failed")
            return

        # 백라이트 ON/OFF
        if subcmd == "BACKLIGHT":
            if len(parts) < 3:
                logger.error("BACKLIGHT command requires ON or OFF", "LCD")
                uart.lcd_notify(b"LCD:ERROR:BACKLIGHT requires ON/OFF")
                return

            mode = parts[2].upper()
            try:
                if mode == "ON":
                    lcd.backlight_on()
                    uart.lcd_notify(b"LCD:BACKLIGHT:OK:ON")
                elif mode == "OFF":
                    lcd.backlight_off()
                    uart.lcd_notify(b"LCD:BACKLIGHT:OK:OFF")
                else:
                    logger.error(f"Unknown BACKLIGHT mode: {mode}", "LCD")
                    uart.lcd_notify(b"LCD:ERROR:Invalid BACKLIGHT mode")
            except Exception as e:
                logger.error(f"Error setting backlight: {e}", "LCD")
                uart.lcd_notify(b"LCD:ERROR:BACKLIGHT failed")
            return

        # 텍스트 출력: LCD:PRINT:row,col:텍스트...
        if subcmd == "PRINT":
            if len(parts) < 4:
                logger.error("PRINT command requires row,col and text", "LCD")
                uart.lcd_notify(b"LCD:ERROR:PRINT requires row,col and text")
                return

            pos_str = parts[2]
            text = ":".join(parts[3:])  # 텍스트 내의 ':' 보존

            try:
                row_col = pos_str.split(",")
                if len(row_col) < 2:
                    raise ValueError("row,col required")

                row = int(row_col[0].strip())
                col = int(row_col[1].strip())
            except Exception as e:
                logger.error(f"Invalid row,col in PRINT: {pos_str}", "LCD")
                uart.lcd_notify(b"LCD:ERROR:Invalid row,col")
                return

            try:
                # I2cLcd.move_to는 내부에서 범위 클램핑 수행
                lcd.move_to(col, row)
                lcd.putstr(text)
                uart.lcd_notify(b"LCD:PRINT:OK")
            except Exception as e:
                logger.error(f"Error printing to LCD: {e}", "LCD")
                uart.lcd_notify(b"LCD:ERROR:PRINT failed")
            return

        # 알 수 없는 LCD 서브 명령
        logger.warning(f"Unknown LCD command: {cmd_str}", "LCD")
        uart.lcd_notify(b"LCD:ERROR:Unknown command")

    except Exception as e:
        logger.error(f"Error processing LCD command: {e}", "LCD")
        uart.lcd_notify(b"LCD:ERROR:Command processing failed")

# ---------------------------
# EZMaker DIY-A 센서 (아날로그 전압)
# ---------------------------
def diya_handler(conn_handle, cmd_str):
    """
    EZMaker DIY-A 센서 명령어 처리:
    - DIYA:STATUS: 현재 DIY-A 센서 값 측정하여 반환
    - DIYA:PIN:핀번호: DIY-A 센서 ADC 핀 설정
    """
    logger.debug(f"Received command: {cmd_str}", "DIYA")
    
    if cmd_str == "DIYA:STATUS":
        # DIY-A 센서가 설정되지 않은 경우
        if diya_sensor is None:
            logger.warning("DIY-A sensor not configured", "DIYA")
            uart.diya_notify(b"DIYA:ERROR:Sensor not configured")
            return
        
        # 현재 DIY-A 센서 값 측정 및 전송
        try:
            status = diya_sensor.get_status()
            raw = status["raw"]
            voltage = status["voltage"]
            
            # 결과 전송 (전압, 원시값)
            msg = f"DIYA:{voltage:.3f},{raw}"
            uart.diya_notify(msg.encode())
            
            logger.info(f"DIY-A sensor: {voltage:.3f}V, raw={raw}", "DIYA")
        except Exception as e:
            logger.error(f"Error measuring DIY-A sensor: {e}", "DIYA")
            uart.diya_notify(b"DIYA:ERROR:Measurement failed")
            
    elif cmd_str.startswith("DIYA:PIN:"):
        # 핀 설정 명령 처리
        try:
            pin_number = int(cmd_str.split(":")[2])
            success = update_pin_config('diya', pin_number)
            if success:
                uart.diya_notify(f"DIYA:PIN:OK:{pin_number}".encode())
            else:
                uart.diya_notify(b"DIYA:ERROR:Pin configuration failed")
        except Exception as e:
            logger.error(f"Error setting DIY-A sensor pin: {e}", "DIYA")
            uart.diya_notify(b"DIYA:ERROR:Invalid pin configuration")
            
    else:
        logger.warning(f"Unknown DIY-A command: {cmd_str}", "DIYA")
        uart.diya_notify(b"DIYA:ERROR:Unknown command")


# ---------------------------
# EZMaker DIY-B 센서 (전류 / 전도도)
# ---------------------------
def diyb_handler(conn_handle, cmd_str):
    """
    EZMaker DIY-B 센서 명령어 처리:
    - DIYB:STATUS: 현재 DIY-B 센서 값 측정하여 반환
    - DIYB:PIN:핀번호: DIY-B 센서 ADC 핀 설정
    """
    logger.debug(f"Received command: {cmd_str}", "DIYB")

    if cmd_str == "DIYB:STATUS":
        # DIY-B 센서가 설정되지 않은 경우
        if diyb_sensor is None:
            logger.warning("DIY-B sensor not configured", "DIYB")
            uart.diyb_notify(b"DIYB:ERROR:Sensor not configured")
            return

        # 현재 DIY-B 센서 값 측정 및 전송
        try:
            status = diyb_sensor.get_status()
            raw = status["raw"]
            voltage = status["voltage"]

            # 결과 전송 (전압, 원시값)
            msg = f"DIYB:{voltage:.3f},{raw}"
            uart.diyb_notify(msg.encode())

            logger.info(f"DIY-B sensor: {voltage:.3f}V, raw={raw}", "DIYB")
        except Exception as e:
            logger.error(f"Error measuring DIY-B sensor: {e}", "DIYB")
            uart.diyb_notify(b"DIYB:ERROR:Measurement failed")

    elif cmd_str.startswith("DIYB:PIN:"):
        # 핀 설정 명령 처리
        try:
            pin_number = int(cmd_str.split(":")[2])
            success = update_pin_config('diyb', pin_number)
            if success:
                uart.diyb_notify(f"DIYB:PIN:OK:{pin_number}".encode())
            else:
                uart.diyb_notify(b"DIYB:ERROR:Pin configuration failed")
        except Exception as e:
            logger.error(f"Error setting DIY-B sensor pin: {e}", "DIYB")
            uart.diyb_notify(b"DIYB:ERROR:Invalid pin configuration")

    else:
        logger.warning(f"Unknown DIY-B command: {cmd_str}", "DIYB")
        uart.diyb_notify(b"DIYB:ERROR:Unknown command")


# ---------------------------
# EZMaker 자기장(Hall) 센서
# ---------------------------
def hall_handler(conn_handle, cmd_str):
    """
    EZMaker Hall 센서 명령어 처리:
    - HALL:STATUS: 현재 Hall 센서 값 측정하여 반환
    - HALL:PIN:핀번호: Hall 센서 ADC 핀 설정
    """
    logger.debug(f"Received command: {cmd_str}", "HALL")

    cmd_str = cmd_str.upper()

    if cmd_str == "HALL:STATUS":
        # Hall 센서가 설정되지 않은 경우
        if hall_sensor is None:
            logger.warning("Hall sensor not configured", "HALL")
            uart.hall_notify(b"HALL:ERROR:Sensor not configured")
            return

        # 현재 Hall 센서 값 측정 및 전송
        try:
            status = hall_sensor.get_status()
            raw = status["raw"]
            strength = status["strength"]
            density = status["density"]

            # 결과 전송: Raw(0~1023), Strength(-512~+512), Density(0~512)
            msg = f"HALL:{raw},{strength},{density}"
            uart.hall_notify(msg.encode())

            logger.info(f"Hall sensor: raw={raw}, strength={strength}, density={density}", "HALL")
        except Exception as e:
            logger.error(f"Error measuring Hall sensor: {e}", "HALL")
            uart.hall_notify(b"HALL:ERROR:Measurement failed")

    elif cmd_str.startswith("HALL:PIN:"):
        # 핀 설정 명령 처리
        try:
            pin_number = int(cmd_str.split(":")[2])
            success = update_pin_config('hall', pin_number)
            if success:
                uart.hall_notify(f"HALL:PIN:OK:{pin_number}".encode())
            else:
                uart.hall_notify(b"HALL:ERROR:Pin configuration failed")
        except Exception as e:
            logger.error(f"Error setting Hall sensor pin: {e}", "HALL")
            uart.hall_notify(b"HALL:ERROR:Invalid pin configuration")

    else:
        logger.warning(f"Unknown HALL command: {cmd_str}", "HALL")
        uart.hall_notify(b"HALL:ERROR:Unknown command")


# ---------------------------
# EZMaker 밝기센서 (EZLIGHT)
# ---------------------------
def ez_light_handler(conn_handle, cmd_str):
    """
    EZMaker 밝기센서(EZLIGHT) 명령어 처리:
    - EZLIGHT:STATUS: 현재 밝기 값 측정하여 반환
    - EZLIGHT:PIN:핀번호: EZLIGHT 센서 ADC 핀 설정
    """
    logger.debug(f"Received command: {cmd_str}", "EZLIGHT")

    cmd_str = cmd_str.upper()

    if cmd_str == "EZLIGHT:STATUS":
        # EZLIGHT 센서가 설정되지 않은 경우
        if ez_light_sensor is None:
            logger.warning("EZ-Light sensor not configured", "EZLIGHT")
            uart.ez_light_notify(b"EZLIGHT:ERROR:Sensor not configured")
            return

        # 현재 EZLIGHT 센서 값 측정 및 전송
        try:
            status = ez_light_sensor.get_status()
            raw = status["raw"]          # 0~1023 (10bit)
            percent = status["percent"]  # 0~100 %

            # 결과 전송: Raw(0~1023), Percent(0~100)
            msg = f"EZLIGHT:{raw},{percent:.1f}"
            uart.ez_light_notify(msg.encode())

            logger.info(
                f"EZ-Light sensor: raw={raw}, percent={percent:.1f}%",
                "EZLIGHT",
            )
        except Exception as e:
            logger.error(f"Error measuring EZ-Light sensor: {e}", "EZLIGHT")
            uart.ez_light_notify(b"EZLIGHT:ERROR:Measurement failed")

    elif cmd_str.startswith("EZLIGHT:PIN:"):
        # 핀 설정 명령 처리
        try:
            pin_number = int(cmd_str.split(":")[2])
            success = update_pin_config('ezlight', pin_number)
            if success:
                uart.ez_light_notify(f"EZLIGHT:PIN:OK:{pin_number}".encode())
            else:
                uart.ez_light_notify(b"EZLIGHT:ERROR:Pin configuration failed")
        except Exception as e:
            logger.error(f"Error setting EZ-Light sensor pin: {e}", "EZLIGHT")
            uart.ez_light_notify(b"EZLIGHT:ERROR:Invalid pin configuration")

    else:
        logger.warning(f"Unknown EZLIGHT command: {cmd_str}", "EZLIGHT")
        uart.ez_light_notify(b"EZLIGHT:ERROR:Unknown command")


# ---------------------------
# EZMaker 전압센서 (EZVOLT)
# ---------------------------
def ez_volt_handler(conn_handle, cmd_str):
    """
    EZMaker 전압센서(EZVOLT) 명령어 처리:
    - EZVOLT:STATUS: 현재 전압 값 측정하여 반환
    - EZVOLT:PIN:핀번호: EZVOLT 센서 ADC 핀 설정
    """
    logger.debug(f"Received command: {cmd_str}", "EZVOLT")

    cmd_str = cmd_str.upper()

    if cmd_str == "EZVOLT:STATUS":
        # EZVOLT 센서가 설정되지 않은 경우
        if ez_volt_sensor is None:
            logger.warning("EZ-Volt sensor not configured", "EZVOLT")
            uart.ez_volt_notify(b"EZVOLT:ERROR:Sensor not configured")
            return

        # 현재 EZVOLT 센서 값 측정 및 전송
        try:
            status = ez_volt_sensor.get_status()
            raw = status.get("raw")          # 0~1023 (10bit)
            voltage = status.get("voltage")  # 0~25V 환산

            # 결과 전송: Raw(0~1023), Voltage(0~25V)
            msg = f"EZVOLT:{raw},{voltage:.2f}"
            uart.ez_volt_notify(msg.encode())

            logger.info(
                f"EZ-Volt sensor: raw={raw}, voltage={voltage:.2f}V",
                "EZVOLT",
            )
        except Exception as e:
            logger.error(f"Error measuring EZ-Volt sensor: {e}", "EZVOLT")
            uart.ez_volt_notify(b"EZVOLT:ERROR:Measurement failed")

    elif cmd_str.startswith("EZVOLT:PIN:"):
        # 핀 설정 명령 처리
        try:
            pin_number = int(cmd_str.split(":")[2])
            success = update_pin_config('ezvolt', pin_number)
            if success:
                uart.ez_volt_notify(f"EZVOLT:PIN:OK:{pin_number}".encode())
            else:
                uart.ez_volt_notify(b"EZVOLT:ERROR:Pin configuration failed")
        except Exception as e:
            logger.error(f"Error setting EZ-Volt sensor pin: {e}", "EZVOLT")
            uart.ez_volt_notify(b"EZVOLT:ERROR:Invalid pin configuration")

    else:
        logger.warning(f"Unknown EZVOLT command: {cmd_str}", "EZVOLT")
        uart.ez_volt_notify(b"EZVOLT:ERROR:Unknown command")


# ---------------------------
# EZMaker 소리센서 (EZSOUND)
# ---------------------------
def ez_sound_handler(conn_handle, cmd_str):
    """
    EZMaker 소리센서(EZSOUND) 명령어 처리:
    - EZSOUND:STATUS: 현재 소리 레벨 값 측정하여 반환
    - EZSOUND:PIN:핀번호: EZSOUND 센서 ADC 핀 설정
    """
    global ez_sound_sensor, PIN_EZSOUND

    logger.debug(f"Received command: {cmd_str}", "EZSOUND")

    cmd_str = cmd_str.strip().upper()

    if cmd_str == "EZSOUND:STATUS":
        # EZSOUND 센서가 설정되지 않은 경우
        if ez_sound_sensor is None:
            logger.warning("EZ-Sound sensor not configured", "EZSOUND")
            uart.ez_sound_notify(b"EZSOUND:ERROR:Sensor not configured")
            return

        # 현재 EZSOUND 센서 값 측정 및 전송
        try:
            status = ez_sound_sensor.get_status()
            raw = status.get("raw")          # 0~1023 (10bit)
            percent = status.get("percent")  # 0~100 %

            # 결과 전송: Raw(0~1023), Percent(0~100)
            msg = f"EZSOUND:{raw},{percent:.1f}"
            uart.ez_sound_notify(msg.encode())

            logger.info(
                f"EZ-Sound sensor: raw={raw}, percent={percent:.1f}%",
                "EZSOUND",
            )
        except Exception as e:
            logger.error(f"Error measuring EZ-Sound sensor: {e}", "EZSOUND")
            uart.ez_sound_notify(b"EZSOUND:ERROR:Measurement failed")

    elif cmd_str.startswith("EZSOUND:PIN:"):
        # 핀 설정 명령 처리
        try:
            pin_number = int(cmd_str.split(":")[2])
            success = update_pin_config('ezsound', pin_number)
            if success:
                PIN_EZSOUND = pin_number
                uart.ez_sound_notify(f"EZSOUND:PIN:OK:{pin_number}".encode())
            else:
                uart.ez_sound_notify(b"EZSOUND:ERROR:Pin configuration failed")
        except Exception as e:
            logger.error(f"Error setting EZ-Sound sensor pin: {e}", "EZSOUND")
            uart.ez_sound_notify(b"EZSOUND:ERROR:Invalid pin configuration")

    else:
        logger.warning(f"Unknown EZSOUND command: {cmd_str}", "EZSOUND")
        uart.ez_sound_notify(b"EZSOUND:ERROR:Unknown command")


# ---------------------------
# EZMaker 무게센서 (EZWEIGHT, HX711)
# ---------------------------
def ez_weight_handler(conn_handle, cmd_str):
    """
    EZMaker 무게센서(EZWEIGHT, HX711) 명령어 처리:
    - EZWEIGHT:STATUS: 현재 무게 값 측정하여 반환
    - EZWEIGHT:PIN:DOUT,SCK: 무게센서 DOUT/SCK 핀 설정
    """
    global ez_weight_sensor, PIN_EZWEIGHT_DOUT, PIN_EZWEIGHT_SCK

    cmd_str = cmd_str.strip().upper()
    logger.info(f"[EZWEIGHT] CMD: {cmd_str}", "EZWEIGHT")

    if cmd_str == "EZWEIGHT:STATUS":
        if ez_weight_sensor is None:
            logger.warning("EZ-Weight sensor not configured", "EZWEIGHT")
            uart.ez_weight_notify(b"EZWEIGHT:ERROR:Sensor not configured")
            return

        try:
            status = ez_weight_sensor.get_status()
            raw = status.get("raw")
            weight = status.get("weight")

            if raw is None or weight is None:
                uart.ez_weight_notify(b"EZWEIGHT:ERROR:Read failed")
                return

            # 결과 전송: Raw, Weight(g 기준)
            msg = f"EZWEIGHT:{raw},{weight:.2f}"
            uart.ez_weight_notify(msg.encode())

            logger.info(
                f"EZ-Weight sensor: raw={raw}, weight={weight:.2f}g",
                "EZWEIGHT",
            )
        except Exception as e:
            logger.error(f"Error measuring EZ-Weight sensor: {e}", "EZWEIGHT")
            uart.ez_weight_notify(b"EZWEIGHT:ERROR:Measurement failed")

    elif cmd_str.startswith("EZWEIGHT:PIN:"):
        try:
            parts = cmd_str.split(":")
            if len(parts) != 3:
                uart.ez_weight_notify(b"EZWEIGHT:ERROR:Invalid PIN command")
                return

            pins_part = parts[2]
            dt_sck = pins_part.split(",")
            if len(dt_sck) != 2:
                uart.ez_weight_notify(b"EZWEIGHT:ERROR:Invalid PIN format")
                return

            dout_pin = int(dt_sck[0])
            sck_pin = int(dt_sck[1])

            ok = update_pin_config("ezweight", dout_pin, sck_pin)
            if ok:
                PIN_EZWEIGHT_DOUT = dout_pin
                PIN_EZWEIGHT_SCK = sck_pin
                uart.ez_weight_notify(f"EZWEIGHT:PIN:OK:{dout_pin},{sck_pin}".encode())
            else:
                uart.ez_weight_notify(b"EZWEIGHT:ERROR:Pin configuration failed")
        except Exception as e:
            logger.error(f"[EZWEIGHT] PIN config error: {e}", "EZWEIGHT")
            uart.ez_weight_notify(b"EZWEIGHT:ERROR:Invalid pin configuration")

    else:
        logger.warning(f"Unknown EZWEIGHT command: {cmd_str}", "EZWEIGHT")
        uart.ez_weight_notify(b"EZWEIGHT:ERROR:Unknown command")

# ---------------------------
# EZMaker 수중/접촉 온도센서 (EZTHERMAL, DS18B20)
# ---------------------------
def ez_thermal_handler(conn_handle, cmd_str):
    """
    EZMaker 수중/접촉 온도센서(EZTHERMAL, DS18B20) 명령어 처리:
    - EZTHERMAL:STATUS: 현재 온도 값(℃) 측정하여 반환
    - EZTHERMAL:PIN:핀번호: EZTHERMAL 센서 데이터 핀 설정
    """
    global ez_thermal_sensor, PIN_EZTHERMAL

    logger.debug(f"Received command: {cmd_str}", "EZTHERMAL")
    cmd_str = cmd_str.strip().upper()

    if cmd_str == "EZTHERMAL:STATUS":
        # EZTHERMAL 센서가 설정되지 않은 경우
        if ez_thermal_sensor is None:
            logger.warning("EZTHERMAL sensor not configured", "EZTHERMAL")
            uart.ez_thermal_notify(b"EZTHERMAL:ERROR:Sensor not configured")
            return

        # 현재 EZTHERMAL 센서 값 측정 및 전송
        try:
            status = ez_thermal_sensor.get_status()
            temp_c = status.get("temperature")

            if temp_c is None:
                logger.error("EZTHERMAL measurement returned None", "EZTHERMAL")
                uart.ez_thermal_notify(b"EZTHERMAL:ERROR:Measurement failed")
                return

            # 결과 전송: Temperature(℃)
            msg = f"EZTHERMAL:{temp_c:.2f}"
            uart.ez_thermal_notify(msg.encode())

            logger.info(
                f"EZTHERMAL sensor: temperature={temp_c:.2f}C",
                "EZTHERMAL",
            )
        except Exception as e:
            logger.error(f"Error measuring EZTHERMAL sensor: {e}", "EZTHERMAL")
            uart.ez_thermal_notify(b"EZTHERMAL:ERROR:Measurement failed")

    elif cmd_str.startswith("EZTHERMAL:PIN:"):
        # 핀 설정 명령 처리
        try:
            pin_number = int(cmd_str.split(":")[2])
            success = update_pin_config('ezthermal', pin_number)
            if success:
                uart.ez_thermal_notify(f"EZTHERMAL:PIN:OK:{pin_number}".encode())
            else:
                uart.ez_thermal_notify(b"EZTHERMAL:ERROR:Pin configuration failed")
        except Exception as e:
            logger.error(f"Error setting EZTHERMAL sensor pin: {e}", "EZTHERMAL")
            uart.ez_thermal_notify(b"EZTHERMAL:ERROR:Invalid pin configuration")

    else:
        logger.warning(f"Unknown EZTHERMAL command: {cmd_str}", "EZTHERMAL")
        uart.ez_thermal_notify(b"EZTHERMAL:ERROR:Unknown command")


# ---------------------------
# EZMaker 전류센서 (EZCURR, INA219)
# ---------------------------
def ez_curr_handler(conn_handle, cmd_str):
    """
    EZMaker 전류센서(EZCURR, INA219) 명령어 처리:
    - EZCURR:STATUS: 현재 전류/전압 값 측정하여 반환
    - EZCURR:PIN:SDA,SCL: I2C 핀 설정
    """
    global ez_curr_sensor, PIN_EZCURR_SDA, PIN_EZCURR_SCL

    cmd_str = cmd_str.strip().upper()
    logger.info(f"[EZCURR] CMD: {cmd_str}", "CURR")
    print(f"[EZCURR] CMD: {cmd_str}")

    if cmd_str == "EZCURR:STATUS":
        if ez_curr_sensor is None:
            logger.warning("EZ-Curr sensor not configured", "CURR")
            uart.ez_curr_notify(b"EZCURR:ERROR:Sensor not configured")
            return

        try:
            status = ez_curr_sensor.get_status()
            voltage = status.get("voltage")
            current_mA = status.get("current_mA")
            power_mW = status.get("power_mW")

            if voltage is None or current_mA is None:
                uart.ez_curr_notify(b"EZCURR:ERROR:Read failed")
                return

            msg = f"EZCURR:{current_mA:.2f},{voltage:.2f}"
            # 필요 시 전력까지 포함 가능:
            # msg = f"EZCURR:{current_mA:.2f},{voltage:.2f},{power_mW:.1f if power_mW is not None else 0.0}"
            uart.ez_curr_notify(msg.encode())

            logger.info(
                f"EZ-Curr sensor: I={current_mA:.2f}mA, V={voltage:.2f}V, P={power_mW if power_mW is not None else 0.0:.1f}mW",
                "CURR",
            )
        except Exception as e:
            logger.error(f"[EZCURR] Measurement error: {e}", "CURR")
            uart.ez_curr_notify(b"EZCURR:ERROR:Measurement failed")

    elif cmd_str.startswith("EZCURR:PIN:"):
        try:
            parts = cmd_str.split(":")
            if len(parts) != 3:
                uart.ez_curr_notify(b"EZCURR:ERROR:Invalid PIN command")
                return

            pins_part = parts[2]
            sda_scl = pins_part.split(",")
            if len(sda_scl) != 2:
                uart.ez_curr_notify(b"EZCURR:ERROR:Invalid PIN format")
                return

            sda_pin = int(sda_scl[0])
            scl_pin = int(sda_scl[1])

            ok = update_pin_config("ezcurr", sda_pin, scl_pin)
            if ok:
                PIN_EZCURR_SDA = sda_pin
                PIN_EZCURR_SCL = scl_pin
                uart.ez_curr_notify(f"EZCURR:PIN:OK:{sda_pin},{scl_pin}".encode())
            else:
                uart.ez_curr_notify(b"EZCURR:ERROR:Pin configuration failed")
        except Exception as e:
            logger.error(f"[EZCURR] PIN config error: {e}", "CURR")
            uart.ez_curr_notify(b"EZCURR:ERROR:Invalid pin configuration")

    else:
        logger.warning(f"Unknown EZCURR command: {cmd_str}", "CURR")
        uart.ez_curr_notify(b"EZCURR:ERROR:Unknown command")


# ---------------------------
# 인체감지 센서 (HUMAN, PIR)
# ---------------------------
def human_handler(conn_handle, cmd_str):
    """
    인체감지 센서(HUMAN) 명령어 처리:
    - HUMAN:STATUS: 현재 감지 여부(0 또는 1) 반환
    - HUMAN:PIN:핀번호: 인체감지 센서 디지털 핀 설정
    """
    global human_sensor, PIN_HUMAN

    cmd_str = cmd_str.strip().upper()
    logger.info(f"[HUMAN] CMD: {cmd_str}", "HUMAN")
    print(f"[HUMAN] CMD: {cmd_str}")

    if cmd_str == "HUMAN:STATUS":
        if human_sensor is None:
            logger.warning("Human sensor not configured", "HUMAN")
            uart.human_notify(b"HUMAN:ERROR:Sensor not configured")
            return

        try:
            status = human_sensor.get_status()
            value = int(status.get("value", 0))
            # 0: 미감지, 1: 인체(움직임) 감지
            msg = f"HUMAN:{value}"
            uart.human_notify(msg.encode())

            logger.info(f"Human sensor: value={value}", "HUMAN")
        except Exception as e:
            logger.error(f"Error measuring human sensor: {e}", "HUMAN")
            uart.human_notify(b"HUMAN:ERROR:Measurement failed")

    elif cmd_str.startswith("HUMAN:PIN:"):
        try:
            pin_number = int(cmd_str.split(":")[2])
            success = update_pin_config("human", pin_number)
            if success:
                PIN_HUMAN = pin_number
                uart.human_notify(f"HUMAN:PIN:OK:{pin_number}".encode())
            else:
                uart.human_notify(b"HUMAN:ERROR:Pin configuration failed")
        except Exception as e:
            logger.error(f"Error setting human sensor pin: {e}", "HUMAN")
            uart.human_notify(b"HUMAN:ERROR:Invalid pin configuration")

    else:
        logger.warning(f"Unknown HUMAN command: {cmd_str}", "HUMAN")
        uart.human_notify(b"HUMAN:ERROR:Unknown command")


# ---------------------------
# 토양수분센서
# ---------------------------
def soil_handler(conn_handle, cmd_str):
    """
    토양수분센서 명령어 처리:
    - SOIL:STATUS: 현재 토양수분 값 측정하여 반환
    - SOIL:PIN:핀번호: 토양수분센서 핀 설정
    - SOIL:CALIBRATE:DRY: 건조 상태 보정
    - SOIL:CALIBRATE:WET: 습윤 상태 보정
    """
    logger.debug(f"Received command: {cmd_str}", "SOIL")
    
    if cmd_str == "SOIL:STATUS":
        # 토양수분센서가 설정되지 않은 경우
        if soil_sensor is None:
            logger.warning("Soil sensor not configured", "SOIL")
            uart.soil_notify(b"SOIL:ERROR:Sensor not configured")
            return
            
        # 현재 토양수분 값 측정 및 전송
        try:
            raw = soil_sensor.read_raw()
            voltage = soil_sensor.read_voltage()
            moisture = soil_sensor.read_moisture()
            
            # 결과 전송 (수분%, 전압, 원시값)
            msg = f"SOIL:{moisture:.1f},{voltage:.3f},{raw}"
            uart.soil_notify(msg.encode())
            
            logger.info(f"Soil sensor: {moisture:.1f}%, {voltage:.3f}V, raw={raw}", "SOIL")
        except Exception as e:
            logger.error(f"Error measuring soil moisture: {e}", "SOIL")
            uart.soil_notify(b"SOIL:ERROR:Measurement failed")
            
    elif cmd_str.startswith("SOIL:PIN:"):
        # 핀 설정 명령 처리
        try:
            pin_number = int(cmd_str.split(":")[2])
            success = update_pin_config('soil', pin_number)
            if success:
                uart.soil_notify(f"SOIL:PIN:OK:{pin_number}".encode())
            else:
                uart.soil_notify(b"SOIL:ERROR:Pin configuration failed")
        except Exception as e:
            logger.error(f"Error setting soil sensor pin: {e}", "SOIL")
            uart.soil_notify(b"SOIL:ERROR:Invalid pin configuration")
            
    elif cmd_str == "SOIL:CALIBRATE:DRY":
        # 건조 상태 보정
        if soil_sensor is None:
            logger.warning("Soil sensor not configured", "SOIL")
            uart.soil_notify(b"SOIL:ERROR:Sensor not configured")
            return
            
        try:
            uart.soil_notify(b"SOIL:CALIBRATE:DRY:START")
            dry_value = soil_sensor.calibrate_dry()
            msg = f"SOIL:CALIBRATE:DRY:OK:{dry_value}"
            uart.soil_notify(msg.encode())
            logger.info(f"Soil sensor dry calibration: {dry_value}", "SOIL")
        except Exception as e:
            logger.error(f"Error calibrating dry state: {e}", "SOIL")
            uart.soil_notify(b"SOIL:ERROR:Dry calibration failed")
            
    elif cmd_str == "SOIL:CALIBRATE:WET":
        # 습윤 상태 보정
        if soil_sensor is None:
            logger.warning("Soil sensor not configured", "SOIL")
            uart.soil_notify(b"SOIL:ERROR:Sensor not configured")
            return
            
        try:
            uart.soil_notify(b"SOIL:CALIBRATE:WET:START")
            wet_value = soil_sensor.calibrate_wet()
            msg = f"SOIL:CALIBRATE:WET:OK:{wet_value}"
            uart.soil_notify(msg.encode())
            logger.info(f"Soil sensor wet calibration: {wet_value}", "SOIL")
        except Exception as e:
            logger.error(f"Error calibrating wet state: {e}", "SOIL")
            uart.soil_notify(b"SOIL:ERROR:Wet calibration failed")
            
    else:
        logger.warning(f"Unknown SOIL command: {cmd_str}", "SOIL")
        uart.soil_notify(b"SOIL:ERROR:Unknown command")

# ---------------------------
# 빗방울센서
# ---------------------------
def rain_handler(conn_handle, cmd_str):
    """
    빗방울센서 명령어 처리:
    - RAIN:STATUS: 현재 빗방울 감지 상태 및 값 반환
    - RAIN:PIN:핀번호: 빗방울센서 핀 설정
    """
    logger.debug(f"Received command: {cmd_str}", "RAIN")
    
    if cmd_str == "RAIN:STATUS":
        # 빗방울센서가 설정되지 않은 경우
        if rain_sensor is None:
            logger.warning("Rain sensor not configured", "RAIN")
            uart.rain_notify(b"RAIN:ERROR:Sensor not configured")
            return
            
        # 현재 빗방울 센서 값 측정 및 전송
        try:
            raw_value = rain_sensor.read()
            voltage = (raw_value / 4095.0) * 3.3  # ADC 값을 전압으로 변환
            
            # 빗방울 감지 백분율 계산 (낮은 값 = 더 많은 빗방울)
            # 실제 측정값 기준: 건조 상태: 2400-2500, 젖은 상태: 750-800
            if raw_value > 2300:
                rain_percentage = 0.0  # 건조 상태
            elif raw_value < 900:
                rain_percentage = 100.0  # 완전 젖은 상태
            else:
                # 2300에서 900 사이의 값을 0-100%로 매핑
                rain_percentage = ((2300 - raw_value) / 1400.0) * 100.0
                rain_percentage = max(0.0, min(100.0, rain_percentage))
            
            # 결과 전송 (백분율, 전압, 원시값)
            msg = f"RAIN:{rain_percentage:.1f},{voltage:.3f},{raw_value}"
            uart.rain_notify(msg.encode())
            
            logger.info(f"Rain sensor: {rain_percentage:.1f}%, {voltage:.3f}V, raw={raw_value}", "RAIN")
        except Exception as e:
            logger.error(f"Error measuring rain sensor: {e}", "RAIN")
            uart.rain_notify(b"RAIN:ERROR:Measurement failed")
            
    elif cmd_str.startswith("RAIN:PIN:"):
        # 핀 설정 명령 처리
        try:
            pin_number = int(cmd_str.split(":")[2])
            success = update_pin_config('rain', pin_number)
            if success:
                uart.rain_notify(f"RAIN:PIN:OK:{pin_number}".encode())
            else:
                uart.rain_notify(b"RAIN:ERROR:Pin configuration failed")
        except Exception as e:
            logger.error(f"Error setting rain sensor pin: {e}", "RAIN")
            uart.rain_notify(b"RAIN:ERROR:Invalid pin configuration")
            
    else:
        logger.warning(f"Unknown RAIN command: {cmd_str}", "RAIN")
        uart.rain_notify(b"RAIN:ERROR:Unknown command")

# ---------------------------
# 8)버저
# ---------------------------
def buzzer_handler(conn_handle, cmd_str):
    """
    버저 관련 명령어 처리:
    - BUZ:INIT - 버저 초기화 및 시작 신호음 재생
    - BUZ:BEEP[:count[:frequency[:duration_ms[:interval_ms]]]] - 비동기 비프음 재생 (블로킹 방지)
    - BUZ:BEEP:ON[:frequency] - 연속 비프음 시작
    - BUZ:BEEP:OFF - 연속 비프음 중지
    - BUZ:PLAY:MELODY_NAME[:tempo] - 내장 멜로디 재생
    - BUZ:STOP - 재생 중지
    - BUZ:STATUS - 재생 상태 확인
    """
    global buzzer_initialized
    
   
    
    try:
        logger.debug(f"Received command: {cmd_str}", "BUZ")
        
        # 시작 신호음 명령 처리
        if cmd_str == "BUZ:INIT":
            # 이미 초기화되어 있는지 확인
            if not buzzer_initialized:
                logger.info("Initializing buzzer module", "BUZ")
                buzzerModule.init(pin=PIN_BUZZER)  # 항상 고정된 PIN_BUZZER(42) 사용
                buzzerModule.set_completion_callback(buzzer_completion_callback)
                # 단순화된 버전에서는 더 이상 스레드가 필요없습니다
                # buzzerModule.start_buzzer_thread()
                buzzer_initialized = True
                ###uart.buzzer_notify(b"INITIALIZED")
            else:
                logger.info("buzzer module already Initialized.", "BUZ")
                ###uart.buzzer_notify(b"ALREADY_INITIALIZED")
                return
        
        # 다른 명령들은 버저가 초기화되었는지 확인
        elif cmd_str.startswith("BUZ:BEEP") or cmd_str.startswith("BUZ:PLAY:") or cmd_str == "BUZ:STATUS" or cmd_str == "BUZ:STOP":
            # 버저가 초기화되지 않았다면 오류 반환
            if not buzzer_initialized:
                logger.error("Buzzer not initialized, send BUZ:INIT first", "BUZ")
                ###uart.buzzer_notify(b"ERROR:Not initialized")
                return
            
            # 연속 비프음 ON 명령 처리 (새로 추가)
            if cmd_str.startswith("BUZ:BEEP:ON"):
                logger.info("BUZ:BEEP:ON", cmd_str)
                parts = cmd_str.split(":")
                frequency = 2000  # 기본값
                
                if len(parts) > 3 and parts[3]:
                    try:
                        frequency = int(parts[3])
                    except Exception as e:
                        logger.error(f"Invalid frequency format: {parts[3]}", "BUZ")
                        frequency = 2000  # 기본값 사용
                
                # 연속 비프음 시작
                buzzerModule.play_continuous(frequency)
                logger.info(f"Continuous beep started at {frequency}Hz", "BUZ")
                ###uart.buzzer_notify(b"PLAYING")
                return
                
            # 비프음 명령 처리
            elif cmd_str.startswith("BUZ:BEEP"):
                logger.info("BUZ:BEEP", cmd_str)
                
                # BEEP 중복 체크 - 기본형
                if buzzer_initialized:
                    if hasattr(buzzerModule, '_buzzer') and buzzerModule._buzzer:
                        current_melody = getattr(buzzerModule._buzzer, '_current_melody_name', None)
                        if current_melody == "BEEP":
                            logger.debug("BEEP already playing, ignoring", "BUZ")
                            return

                parts = cmd_str.split(":")
                count = 1
                frequency = 2000
                duration_ms = 100
                interval_ms = 100
                
                if len(parts) > 2 and parts[2]:
                    try:
                        count = int(parts[2])
                    except:
                        count = 1
                        
                if len(parts) > 3 and parts[3]:
                    try:
                        frequency = int(parts[3])
                    except:
                        frequency = 2000
                        
                if len(parts) > 4 and parts[4]:
                    try:
                        duration_ms = int(parts[4])
                    except:
                        duration_ms = 100
                        
                if len(parts) > 5 and parts[5]:
                    try:
                        interval_ms = int(parts[5])
                    except:
                        interval_ms = 100
                    
                # 버저모듈로 비동기 비프음 재생
                buzzerModule.beep_async(count=count, frequency=frequency, 
                                      duration_ms=duration_ms, interval_ms=interval_ms)
                ###uart.buzzer_notify(b"PLAYING")
                
            # 멜로디 재생 명령 처리
            elif cmd_str.startswith("BUZ:PLAY:"):
                logger.info("BUZ:PLAY", cmd_str)
                # 🔥 PLAY 중복 체크 (기본형)
                if buzzer_initialized:
                    if hasattr(buzzerModule, '_buzzer') and buzzerModule._buzzer:
                        current_melody = getattr(buzzerModule._buzzer, '_current_melody_name', None)
                        melody_name = cmd_str.split(":")[2].upper()
                        if current_melody == melody_name:
                            logger.debug("Same melody already playing, ignoring", "BUZ")
                            return  # ✅ 빠른 종료



                parts = cmd_str.split(":")
                if len(parts) < 3 or not parts[2]:
                    logger.error("Missing melody name", "BUZ")
                    ###uart.buzzer_notify(b"ERROR:Missing melody name")
                    return
                    
                melody_name = parts[2].upper()
                tempo = 120
                
                if len(parts) > 3 and parts[3]:
                    try:
                        tempo = int(parts[3])
                    except Exception as e:
                        logger.error(f"Invalid tempo format: {parts[3]}", "BUZ")
                        tempo = 120  # 기본값 사용
                    
                # 버저모듈로 멜로디 재생 (비차단 방식)
                buzzerModule.play_melody(melody_name, tempo)
                ###uart.buzzer_notify(b"PLAYING")
                
            # 중지 명령 처리
            elif cmd_str == "BUZ:STOP":
                logger.info("BUZ:STOP", cmd_str)
                buzzerModule.stop()
                ###uart.buzzer_notify(b"STOPPED")
                
            # 상태 확인 명령 처리
            elif cmd_str == "BUZ:STATUS":
                if buzzerModule.is_active():
                    ###uart.buzzer_notify(b"PLAYING")
                    pass
                else:
                    ###uart.buzzer_notify(b"STOPPED")
                    pass
        else:
            logger.error(f"Unknown BUZZER command: {cmd_str}", "BUZ")
            ###uart.buzzer_notify(b"ERROR:Unknown command")
            
    except Exception as e:
        logger.error(f"Error processing buzzer command: {e}", "BUZ")
        ###uart.buzzer_notify(b"ERROR:Command processing failed")

def buzzer_completion_callback(status):
    """
    버저 재생 완료 시 호출되는 콜백 함수
    """
    if status == "COMPLETED":
        logger.info("Playback completed", "BUZ")
        # 재생 완료 알림 전송
        if uart and ble_connected:
            ###uart.buzzer_notify(b"COMPLETED")
            pass

# ---------------------------
# 9) 카메라
# ---------------------------
camera_enabled = False  # 초기값은 False로 설정, 초기화 성공 시 True로 변경
streaming = False
# 카메라 스트리밍 설정
stream_interval = 300  # 스트리밍 캡처 간격 (ms)
cam = None            # 카메라 모듈 객체

# 메모리 모니터링 변수
last_gc_collect = 0
gc_interval = 5000  # 5초마다 GC 수행

# ---------------------------
# 카메라 스트리밍 분리(스레드 캡처 + 메인루프 전송)
# ---------------------------
# 목표:
# - 캡처(무거움): 별도 스레드에서 수행
# - BLE 전송(notify): 메인 루프에서 "조금씩" 처리하여 다른 센서/버저 명령 지연을 줄임
CAM_CHUNK_SIZE = 160
CAM_TX_MAX_CHUNKS_PER_TICK = 1  # 3에서 1로 줄여서 BLE 버퍼 부하 감소

_cam_lock = _thread.allocate_lock()
_cam_pending_frame = None          # 최신 프레임 1개만 유지 (큐 폭주 방지)
_cam_tx_frame = None               # 현재 전송 중인 프레임
_cam_tx_offset = 0
_cam_tx_seq = 0
_cam_tx_stage = 0                  # 0=idle, 1=sent CAM:START, 2=sent SIZE, 3=sending chunks, 4=sent CAM:END
_cam_snapshot_requested = False

_cam_worker_started = False
_cam_worker_stop = False
_cam_last_capture_ms = 0

# 카메라 초기화 시도
try:
    # CameraModule 인스턴스 생성
    cam = CameraModule()
    # 기본 설정으로 카메라 초기화
    if cam.init(frame_size="QVGA", quality=85, fb_count=2):
        camera_enabled = True
        logger.info("Camera initialized successfully", "CAM")
    else:
        camera_enabled = False
        cam = None
        logger.warning("Camera initialization failed", "CAM")
except Exception as e:
    logger.error(f"Camera initialization error: {e}", "CAM")
    if cam is not None:
        try:
            cam.deinit()
        except:
            pass
    camera_enabled = False
    cam = None

    # 카메라 초기화 실패 시 자동 하드 리셋 수행
    logger.critical("Camera initialization failed! Performing automatic hard reset in 3 seconds...", "CAM")
    for i in range(3, 0, -1):
        logger.warning(f"{i}...", "CAM")
        time.sleep(1)
    logger.critical("Resetting now!", "SYS")
    import machine
    machine.reset()  # 하드 리셋 수행

def _camera_offer_frame(frame):
    """최신 프레임 1개만 유지하도록 교체."""
    global _cam_pending_frame
    if not frame:
        return
    try:
        with _cam_lock:
            _cam_pending_frame = frame
    except Exception as e:
        logger.error(f"Failed to offer camera frame: {e}", "CAM")

def _camera_request_snapshot():
    global _cam_snapshot_requested
    _cam_snapshot_requested = True

def _camera_abort_tx():
    """전송 중 프레임을 중단하고 상태 초기화."""
    global _cam_tx_frame, _cam_tx_offset, _cam_tx_seq, _cam_tx_stage, _cam_pending_frame
    try:
        # 호스트가 프레임 파서를 멈추지 않도록 END는 보내줌(가능할 때만)
        if uart and ble_connected:
            uart.cam_notify(b"CAM:END")
    except Exception:
        pass
    with _cam_lock:
        _cam_tx_frame = None
        _cam_tx_offset = 0
        _cam_tx_seq = 0
        _cam_tx_stage = 0
        _cam_pending_frame = None

def _camera_tx_pump(max_chunks=CAM_TX_MAX_CHUNKS_PER_TICK):
    """
    메인 루프에서 호출: 한 번에 청크 몇 개만 전송하고 빠르게 반환.
    프로토콜은 기존과 동일:
      CAM:START -> SIZE:<n> -> BIN{seq}:<bytes>... -> CAM:END
    """
    global _cam_tx_frame, _cam_tx_offset, _cam_tx_seq, _cam_tx_stage, _cam_pending_frame

    if not (uart and ble_connected and camera_enabled):
        return

    # 스트리밍이 꺼졌는데 전송 중이면 중단
    if not streaming and _cam_tx_stage != 0:
        _camera_abort_tx()
        return

    # 전송 중이 아니면 pending에서 가져와 시작
    if _cam_tx_stage == 0:
        with _cam_lock:
            if _cam_pending_frame is None:
                return
            _cam_tx_frame = _cam_pending_frame
            _cam_pending_frame = None
            _cam_tx_offset = 0
            _cam_tx_seq = 0
            _cam_tx_stage = 1

    # Stage 1: START
    if _cam_tx_stage == 1:
        try:
            uart.cam_notify(b"CAM:START")
            _cam_tx_stage = 2
        except Exception as e:
            logger.error(f"Failed to send CAM:START: {e}", "CAM")
            _camera_abort_tx()
            return

    # Stage 2: SIZE
    if _cam_tx_stage == 2:
        try:
            size_info = f"SIZE:{len(_cam_tx_frame)}".encode()
            uart.cam_notify(size_info)
            _cam_tx_stage = 3
        except Exception as e:
            logger.error(f"Failed to send SIZE: {e}", "CAM")
            _camera_abort_tx()
            return

    # Stage 3: chunks
    if _cam_tx_stage == 3:
        try:
            length = len(_cam_tx_frame)
            chunks_sent = 0
            while _cam_tx_offset < length and chunks_sent < max_chunks:
                end = min(_cam_tx_offset + CAM_CHUNK_SIZE, length)
                chunk = _cam_tx_frame[_cam_tx_offset:end]
                header = f"BIN{_cam_tx_seq}:".encode()
                
                # ENOMEM 방지를 위한 재시도 로직
                retry = 3
                while retry > 0:
                    try:
                        uart.cam_notify(header + chunk)
                        break # 성공 시 루프 탈출
                    except Exception as e:
                        if "ENOMEM" in str(e) or "12" in str(e):
                            retry -= 1
                            time.sleep_ms(20) # BLE 버퍼가 비워질 때까지 대기
                            if retry == 0: raise e
                        else:
                            raise e

                _cam_tx_offset = end
                _cam_tx_seq += 1
                chunks_sent += 1
                # 청크 간 아주 짧은 지연 추가
                time.sleep_ms(5)

            # NOTE:
            # - 이전 구현은 청크를 1개만 보내도 Stage를 4(END)로 바꿔버려
            #   프레임이 중간에 끊겨 전송되는 문제가 발생할 수 있습니다.
            # - 모든 청크를 전송했을 때만 END를 보내도록 상태를 전이합니다.
            if _cam_tx_offset >= length:
                _cam_tx_stage = 4
            else:
                _cam_tx_stage = 3
        except Exception as e:
            logger.error(f"Frame chunk send error: {e}", "CAM")
            _camera_abort_tx()
            return

    # Stage 4: END
    if _cam_tx_stage == 4:
        try:
            uart.cam_notify(b"CAM:END")
        except Exception:
            pass
        # 상태 초기화
        with _cam_lock:
            _cam_tx_frame = None
            _cam_tx_offset = 0
            _cam_tx_seq = 0
            _cam_tx_stage = 0

def _camera_worker():
    """카메라 캡처 전용 스레드."""
    global _cam_worker_stop, _cam_last_capture_ms, _cam_snapshot_requested
    logger.info("Camera worker thread started", "CAM")
    while not _cam_worker_stop:
        try:
            if camera_enabled and cam and ble_connected and uart:
                now = time.ticks_ms()

                # 스냅샷 요청 우선 처리
                if _cam_snapshot_requested:
                    _cam_snapshot_requested = False
                    frame = cam.capture_frame()
                    if frame:
                        _camera_offer_frame(frame)

                # 스트리밍 캡처
                if streaming:
                    if time.ticks_diff(now, _cam_last_capture_ms) >= stream_interval:
                        frame = cam.capture_frame()
                        if frame:
                            _camera_offer_frame(frame)
                        _cam_last_capture_ms = now
        except Exception as e:
            logger.error(f"Camera worker error: {e}", "CAM")
            try:
                gc.collect()
            except Exception:
                pass

        time.sleep_ms(10)
    logger.info("Camera worker thread stopped", "CAM")

def _ensure_camera_worker():
    global _cam_worker_started
    if _cam_worker_started:
        return
    _cam_worker_started = True
    try:
        _thread.start_new_thread(_camera_worker, ())
    except Exception as e:
        logger.error(f"Failed to start camera worker thread: {e}", "CAM")
        _cam_worker_started = False

def cam_handler(conn_handle, cmd_str):
    global streaming, stream_interval
    cmd_str = cmd_str.upper()
    logger.debug(f"Received command: {cmd_str}", "CAM")

    if not camera_enabled:
        logger.warning("Camera not available.", "CAM")
        return

    if cmd_str == "CAM:SNAP":
        # 스냅샷은 캡처 스레드에서 수행하고, 전송은 메인 루프가 처리
        _ensure_camera_worker()
        _camera_request_snapshot()
        return
        
    elif cmd_str.startswith("CAM:INTERVAL "):
        # 스트리밍 간격 조정 명령
        try:
            interval = int(cmd_str.split()[1])
            if 50 <= interval <= 1000:
                stream_interval = interval
                logger.info(f"Stream interval set to {stream_interval}ms", "CAM")
            else:
                logger.error("Interval must be between 50-1000ms", "CAM")
        except Exception as e:
            logger.error(f"Error setting interval: {e}", "CAM")
        
    elif cmd_str == "CAM:STREAM:ON":
        global streaming
        if streaming:
            logger.info(f"Received stream ON command, current streaming status: {streaming}", "CAM")
            return
        
        _ensure_camera_worker()
        streaming = True
        logger.info(f"Streaming enabled, new status: {streaming}", "CAM")
        gc.collect()
        print_memory_info()
    elif cmd_str == "CAM:STREAM:OFF":
        global streaming
        if streaming:
            streaming = False
            logger.info("Streaming disabled", "CAM")
            # 스트리밍 종료 시 메모리 정리
            gc.collect()
            print_memory_info()
            _camera_abort_tx()
    else:
        logger.warning(f"Unrecognized camera cmd: {cmd_str}", "CAM")


# 연결 이벤트 핸들러
def connect_handler(conn_handle):
    global ble_connected
    
    # 연결된 기기의 정보 가져오기
    try:
        import bluetooth
        if hasattr(bluetooth, 'gap_peer_addr'):
            # 연결된 기기의 MAC 주소
            try:
                peer_addr_type, peer_addr = bluetooth.gap_peer_addr(conn_handle)
                peer_addr_str = ':'.join('%02X' % b for b in peer_addr)
                logger.info(f"Connected device - Handle: {conn_handle}, MAC: {peer_addr_str}, Type: {peer_addr_type}", "BLE")
            except Exception as e:
                logger.error(f"Failed to get connected device info: {e}", "BLE")
    except Exception as e:
        logger.error(f"Error getting MAC address: {e}", "BLE")
    
    # 연결 상태 업데이트
    logger.info(f"✅ Device connection complete (handle: {conn_handle})", "BLE")
    ble_connected = True
    
    # BLE 상태 LED 켜기
    if ble_status_led:
        try:
            ble_status_led.value(1)  # LED 켜기
            logger.info("BLE status LED turned ON", "BLE")
        except Exception as e:
            logger.error(f"Error turning on BLE status LED: {e}", "BLE")
    
    # 연결 이벤트 알림 전송
    uart.cam_notify(b"BLE:CONNECTED")

# 연결 해제 이벤트 핸들러
def disconnect_handler(conn_handle):
    logger.info(f"Device disconnected (handle: {conn_handle})", "BLE")
    
    # 글로벌 변수에 연결 상태 저장
    global ble_connected, buzzer_initialized, gyro_streaming, neo_rainbow_active
    global heart_rate_streaming, heart_rate_enabled  # 심장박동 센서 스트리밍 변수 추가
    ble_connected = False
    
    # BLE 상태 LED 끄기
    if ble_status_led:
        try:
            ble_status_led.value(0)  # LED 끄기
            logger.info("BLE status LED turned OFF", "BLE")
        except Exception as e:
            logger.error(f"Error turning off BLE status LED: {e}", "BLE")
    
    # 모든 센서 모니터링 중지
    global streaming  
    streaming = False
    gyro_streaming = False
    heart_rate_streaming = False  # 심장박동 센서 스트리밍도 중지
    
    # 무지개 효과 먼저 중지 (스레드 문제 해결)
    if neo_rainbow_active:
        try:
            logger.info("Stopping rainbow effect on disconnect", "NEO")
            stop_rainbow()
            time.sleep(0.2)  # 스레드가 완전히 종료될 시간 확보
        except Exception as e:
            logger.error(f"Error stopping rainbow effect: {e}", "NEO")
    
    # 그 다음 모든 NeoPixel LED 끄기
    if neo is not None:
        try:
            neo.fill((0, 0, 0))
            neo.write()
            logger.info("All NeoPixels turned off on disconnect", "NEO")
        except Exception as e:
            logger.error(f"Error turning off NeoPixels: {e}", "NEO")
    
    # LED로 연결 상태 표시 (선택적)
    if led_pin:
        # LED 깜빡임 중지
        global blink_flag
        blink_flag = False
        led_pin.duty_u16(0)  # 연결 해제되면 LED 끄기 (PWM 모드)

    # 버저 완전 정리 (중지 및 리소스 해제)
    try:
        if buzzer_initialized:
            # 먼저 연속 모드 중지 시도
            if hasattr(buzzerModule, '_buzzer') and buzzerModule._buzzer:
                if hasattr(buzzerModule._buzzer, 'is_continuous') and buzzerModule._buzzer.is_continuous:
                    logger.info("Stopping continuous buzzer mode", "BUZ")
                    buzzerModule._buzzer.is_continuous = False
                    if buzzerModule._buzzer.pwm:
                        buzzerModule._buzzer.pwm.duty_u16(0)
            
            buzzerModule.stop()  # 재생 중지
            buzzerModule.deinit()  # 리소스 해제
            buzzer_initialized = False  # 초기화 플래그 리셋
            logger.info("Buzzer deinitialized on disconnect", "BUZ")
    except Exception as e:
        logger.warning(f"Error deinitializing buzzer: {e}", "BUZ")
        
    # DC 모터 정지
    try:
        if dcmotor_pwm:
            dcmotor_pwm.duty(0)  # 모터 정지
    except Exception as e:
        logger.warning(f"Error stopping DC motor: {e}", "MOTOR")

    # 카메라 전송 상태 정리 (중간 프레임 파서가 멈추지 않도록 END 보냄)
    try:
        _camera_abort_tx()
    except Exception:
        pass

# ---------------------------
# BLE 시작
# ---------------------------
# 디바이스 이름 설정 (DB + MAC 주소 끝 5자리)
device_name = get_device_name()

# BLE 상태 LED 초기화
try:
    ble_status_led = machine.Pin(PIN_BLE_STATUS_LED, machine.Pin.OUT)
    ble_status_led.value(0)  # 초기 상태는 꺼짐
    logger.info(f"BLE status LED initialized on pin {PIN_BLE_STATUS_LED}", "BLE")
except Exception as e:
    logger.error(f"Failed to initialize BLE status LED: {e}", "BLE")
    ble_status_led = None

uart = bleBaseIoT.start(name=device_name)  # 생성된 디바이스 이름 사용

# ---------------------------
# REPL 모드 전환 처리
# ---------------------------
def repl_handler(conn_handle, cmd_str):
    """
    REPL 모드 전환 명령어 처리:
    - REPL:ON: REPL 모드로 전환
    - REPL:OFF: IoT 모드로 전환
    - REPL:STATUS: 현재 모드 상태 확인
    """
    logger.debug(f"Received command: {cmd_str}", "REPL")
    
    if cmd_str == "REPL:STATUS":
        # 현재 모드 상태 확인
        try:
            import config
            # repl_flag 안전 접근 (기본값: False - IoT 모드)
            is_repl = getattr(config, 'repl_flag', False)
            status = "REPL:ON" if is_repl else "REPL:OFF"
            uart.repl_notify(status.encode())
            logger.info(f"Current mode: {'REPL' if is_repl else 'IoT'}", "REPL")
        except ImportError:
            # config.py가 없는 경우 IoT 모드로 가정
            uart.repl_notify(b"REPL:OFF")
            logger.info("Config not found, assuming IoT mode", "REPL")
        except Exception as e:
            logger.error(f"Config access error: {e}", "REPL")
            uart.repl_notify(b"REPL:ERROR:Config access failed")
            
    elif cmd_str == "REPL:ON":
        # REPL 모드로 전환
        try:
            # change_repl_simple의 기능을 활용하여 모드 변경
            from change_repl_simple import change_mode
            if change_mode(True):
                uart.repl_notify(b"REPL:CHANGED:ON")
                logger.info("REPL mode changed. Restarting in 3 seconds...", "REPL")
                time.sleep(0.5)  # 응답이 전송될 시간 확보
                time.sleep(3)
                machine.reset()  # 시스템 재시작
            else:
                uart.repl_notify(b"REPL:ERROR:Change failed")
        except Exception as e:
            logger.error(f"REPL mode change error: {e}", "REPL")
            uart.repl_notify(b"REPL:ERROR:Internal error")
    
    elif cmd_str == "REPL:OFF":
        # IoT 모드로 전환
        try:
            # change_repl_simple의 기능을 활용하여 모드 변경
            from change_repl_simple import change_mode
            if change_mode(False):
                uart.repl_notify(b"REPL:CHANGED:OFF")
                logger.info("IoT mode changed. Restarting in 3 seconds...", "REPL")
                time.sleep(0.5)  # 응답이 전송될 시간 확보
                time.sleep(3)
                machine.reset()  # 시스템 재시작
            else:
                uart.repl_notify(b"REPL:ERROR:Change failed")
        except Exception as e:
            logger.error(f"IoT mode change error: {e}", "REPL")
            uart.repl_notify(b"REPL:ERROR:Internal error")
    
    else:
        logger.error(f"Unknown REPL command: {cmd_str}", "REPL")
        uart.repl_notify(b"REPL:ERROR:Unknown command")

# ---------------------------
# 10) 자이로센서 (ADXL345)
# ---------------------------
def gyro_handler(conn_handle, cmd_str):
    """
    자이로센서(ADXL345) 명령어 처리:
    - GYRO:STATUS - 현재 가속도 및 기울기 값 측정
    - GYRO:PIN:SDA핀,SCL핀 - 자이로센서 I2C 핀 설정
    - GYRO:STREAM:ON - 자이로 값 연속 측정 시작
    - GYRO:STREAM:OFF - 자이로 값 연속 측정 중지
    - GYRO:INTERVAL:시간(ms) - 스트리밍 간격 설정
    """
    global gyro_streaming, gyro_stream_interval
    
    cmd_str = cmd_str.upper()
    logger.debug(f"Received command: {cmd_str}", "GYRO")
    
    if cmd_str == "GYRO:STATUS":
        # 자이로센서가 설정되지 않은 경우
        if gyro_sensor is None:
            logger.warning("Gyro sensor not configured", "GYRO")
            uart.gyro_notify(b"GYRO:ERROR:Sensor not configured")
            return
            
        # 현재 가속도 및 기울기 값 측정 및 전송
        try:
            # ADXL345에서 값 읽기
            x = gyro_sensor.xValue
            y = gyro_sensor.yValue
            z = gyro_sensor.zValue
            
            # 롤과 피치 계산
            roll, pitch = gyro_sensor.RP_calculate(x, y, z)
            
            # 결과 포맷팅 및 전송
            msg = f"GYRO:X={x},Y={y},Z={z}|ROLL={roll:.2f},PITCH={pitch:.2f}"
            uart.gyro_notify(msg.encode())
            logger.debug(f"Gyro sensor values: X={x}, Y={y}, Z={z}, ROLL={roll:.2f}, PITCH={pitch:.2f}", "GYRO")
        except Exception as e:
            logger.error(f"Error reading gyro sensor: {e}", "GYRO")
            uart.gyro_notify(b"GYRO:ERROR:Measurement failed")
            
    elif cmd_str.startswith("GYRO:PIN:"):
        try:
            # 핀 번호 파싱
            pins = cmd_str.split(":")[2].split(",")
            if len(pins) < 2:
                logger.warning("Invalid pin configuration. Need SDA and SCL pins.", "GYRO")
                uart.gyro_notify(b"GYRO:ERROR:Need two pins")
                return
                
            sda_pin = int(pins[0])
            scl_pin = int(pins[1])
            
            # 핀 설정 업데이트
            success = update_pin_config('gyro', sda_pin, scl_pin)
            if success:
                logger.info(f"Gyro sensor pins set to SDA={sda_pin}, SCL={scl_pin}", "GYRO")
                uart.gyro_notify(f"GYRO:PIN:OK:{sda_pin},{scl_pin}".encode())
            else:
                logger.warning("Pin configuration failed", "GYRO")
                uart.gyro_notify(b"GYRO:ERROR:Pin configuration failed")
        except Exception as e:
            logger.error(f"Error setting gyro pins: {e}", "GYRO")
            uart.gyro_notify(b"GYRO:ERROR:Invalid pin configuration")
    
    elif cmd_str == "GYRO:STREAM:ON":
        # 자이로센서가 설정되지 않은 경우
        if gyro_sensor is None:
            logger.warning("Gyro sensor not configured", "GYRO")
            uart.gyro_notify(b"GYRO:ERROR:Sensor not configured")
            return
        
        # 🔥 중복 ON 명령 방지 (리소스 절약)
        if gyro_streaming:
            logger.debug("Gyro streaming already active, ignoring duplicate ON command", "GYRO")
            #uart.gyro_notify(b"GYRO:STREAM:ALREADY_ON")
            return
            
        # 스트리밍 시작
        gyro_streaming = True
        logger.info(f"Gyro streaming enabled with interval {gyro_stream_interval}ms", "GYRO")
        uart.gyro_notify(b"GYRO:STREAM:OK")
        
    elif cmd_str == "GYRO:STREAM:OFF":
        if gyro_streaming:
            # 스트리밍 중지
            gyro_streaming = False
            logger.info("Gyro streaming disabled", "GYRO")
            uart.gyro_notify(b"GYRO:STREAM:STOPPED")
        
    elif cmd_str.startswith("GYRO:INTERVAL:"):
        try:
            interval = int(cmd_str.split(":")[2])
            if interval < 100:  # 최소 간격 100ms
                interval = 100
            elif interval > 5000:  # 최대 간격 5초
                interval = 5000
                
            gyro_stream_interval = interval
            logger.info(f"Gyro stream interval set to {gyro_stream_interval}ms", "GYRO")
            uart.gyro_notify(f"GYRO:INTERVAL:OK:{gyro_stream_interval}".encode())
        except Exception as e:
            logger.error(f"Error setting gyro stream interval: {e}", "GYRO")
            uart.gyro_notify(b"GYRO:ERROR:Invalid interval value")
            
    else:
        logger.warning(f"Unknown GYRO command: {cmd_str}", "GYRO")
        uart.gyro_notify(b"GYRO:ERROR:Unknown command")

# ---------------------------
# 10-1) EZMaker 자이로센서 (ICM20948)
# ---------------------------
def ez_gyro_handler(conn_handle, cmd_str):
    """
    EZMaker 자이로센서(ICM20948) 명령어 처리:
    - EZGYRO:STATUS - 현재 가속도 및 기울기 값 측정
    - EZGYRO:PIN:SDA핀,SCL핀 - 자이로센서 I2C 핀 설정
    """
    global ez_gyro_i2c, ez_gyro_sensor
    
    cmd_str = cmd_str.upper()
    logger.debug(f"Received command: {cmd_str}", "GYRO")
    
    if cmd_str == "EZGYRO:STATUS":
        if ez_gyro_sensor is None:
            logger.warning("EZ-Gyro sensor not configured", "GYRO")
            uart.ez_gyro_notify(b"EZGYRO:ERROR:Sensor not configured")
            return
        
        try:
            data = ez_gyro_sensor.read_accel_gyro()
            rpy = ez_gyro_sensor.calculate_rpy(data['accel'])

            ax = data['accel']['x']
            ay = data['accel']['y']
            az = data['accel']['z']

            gx = data['gyro']['x']
            gy = data['gyro']['y']
            gz = data['gyro']['z']

            roll  = rpy['roll']
            pitch = rpy['pitch']
            temp  = data['temp']

            # 단일 라인 키=값 포맷 (Accel + Gyro + Roll/Pitch + Temp)
            msg = (
                "EZGYRO:AX={:.2f},AY={:.2f},AZ={:.2f},"
                "GX={:.2f},GY={:.2f},GZ={:.2f},"
                "ROLL={:.2f},PITCH={:.2f},TEMP={:.2f}"
            ).format(ax, ay, az, gx, gy, gz, roll, pitch, temp)

            uart.ez_gyro_notify(msg.encode())
            logger.debug(
                f"EZ-Gyro values: AX={ax}, AY={ay}, AZ={az}, "
                f"GX={gx}, GY={gy}, GZ={gz}, ROLL={roll:.2f}, PITCH={pitch:.2f}, TEMP={temp:.2f}",
                "GYRO",
            )
        except Exception as e:
            logger.error(f"Error reading EZ-Gyro sensor: {e}", "GYRO")
            uart.ez_gyro_notify(b"EZGYRO:ERROR:Measurement failed")
    
    elif cmd_str.startswith("EZGYRO:PIN:"):
        try:
            pins = cmd_str.split(":")[2].split(",")
            if len(pins) < 2:
                logger.warning("Invalid EZ-Gyro pin configuration. Need SDA and SCL pins.", "GYRO")
                uart.ez_gyro_notify(b"EZGYRO:ERROR:Need two pins")
                return

            sda_pin = int(pins[0])
            scl_pin = int(pins[1])

            success = update_pin_config('ezgyro', sda_pin, scl_pin)
            if success:
                logger.info(f"EZ-Gyro pins set to SDA={sda_pin}, SCL={scl_pin}", "GYRO")
                uart.ez_gyro_notify(f"EZGYRO:PIN:OK:{sda_pin},{scl_pin}".encode())
            else:
                logger.warning("EZ-Gyro pin configuration failed", "GYRO")
                uart.ez_gyro_notify(b"EZGYRO:ERROR:Pin configuration failed")
        except Exception as e:
            logger.error(f"Error setting EZ-Gyro pins: {e}", "GYRO")
            uart.ez_gyro_notify(b"EZGYRO:ERROR:Invalid pin configuration")
    else:
        logger.warning(f"Unknown EZGYRO command: {cmd_str}", "GYRO")
        uart.ez_gyro_notify(b"EZGYRO:ERROR:Unknown command")

# ---------------------------
# 10-2) EZMaker 기압센서 (BMP280)
# ---------------------------
def ez_press_handler(conn_handle, cmd_str):
    """
    EZMaker 기압센서(BMP280) 명령어 처리:
    - EZPRESS:STATUS - 현재 온도 및 기압 값 측정
    - EZPRESS:PIN:SDA핀,SCL핀 - 기압센서 I2C 핀 설정
    """
    global ez_press_i2c, ez_press_sensor
    
    cmd_str = cmd_str.upper()
    logger.debug(f"Received command: {cmd_str}", "PRESS")
    
    if cmd_str == "EZPRESS:STATUS":
        if ez_press_sensor is None:
            logger.warning("EZ-Press sensor not configured", "PRESS")
            uart.ez_press_notify(b"EZPRESS:ERROR:Sensor not configured")
            return
        
        try:
            temp_c, press_pa = ez_press_sensor.read()

            # 단일 라인 키=값 포맷 (Temperature + Pressure in Pa)
            msg = "EZPRESS:T={:.2f},P={:.2f}".format(temp_c, press_pa)

            uart.ez_press_notify(msg.encode())
            logger.debug(
                f"EZ-Press values: T={temp_c:.2f}C, P={press_pa:.2f}Pa",
                "PRESS",
            )
        except Exception as e:
            logger.error(f"Error reading EZ-Press sensor: {e}", "PRESS")
            uart.ez_press_notify(b"EZPRESS:ERROR:Measurement failed")
    
    elif cmd_str.startswith("EZPRESS:PIN:"):
        try:
            pins = cmd_str.split(":")[2].split(",")
            if len(pins) < 2:
                logger.warning("Invalid EZ-Press pin configuration. Need SDA and SCL pins.", "PRESS")
                uart.ez_press_notify(b"EZPRESS:ERROR:Need two pins")
                return

            sda_pin = int(pins[0])
            scl_pin = int(pins[1])

            success = update_pin_config('ezpress', sda_pin, scl_pin)
            if success:
                logger.info(f"EZ-Press pins set to SDA={sda_pin}, SCL={scl_pin}", "PRESS")
                uart.ez_press_notify(f"EZPRESS:PIN:OK:{sda_pin},{scl_pin}".encode())
            else:
                logger.warning("EZ-Press pin configuration failed", "PRESS")
                uart.ez_press_notify(b"EZPRESS:ERROR:Pin configuration failed")
        except Exception as e:
            logger.error(f"Error setting EZ-Press pins: {e}", "PRESS")
            uart.ez_press_notify(b"EZPRESS:ERROR:Invalid pin configuration")
    else:
        logger.warning(f"Unknown EZPRESS command: {cmd_str}", "PRESS")
        uart.ez_press_notify(b"EZPRESS:ERROR:Unknown command")

# ---------------------------
# 10-3) EZMaker CO2 센서 (SCD40)
# ---------------------------
def ez_co2_handler(conn_handle, cmd_str):
    """
    EZMaker CO2 센서(SCD40) 명령어 처리:
    - EZCO2:STATUS - 현재 CO2/온도/습도 값 측정
    - EZCO2:PIN:SDA핀,SCL핀 - CO2 센서 I2C 핀 설정
    """
    global ez_co2_i2c, ez_co2_sensor
    
    cmd_str = cmd_str.upper()
    logger.debug(f"Received command: {cmd_str}", "CO2")
    
    if cmd_str == "EZCO2:STATUS":
        if ez_co2_sensor is None:
            logger.warning("EZ-CO2 sensor not configured", "CO2")
            uart.ez_co2_notify(b"EZCO2:ERROR:Sensor not configured")
            return
        
        try:
            # 데이터 준비 여부 확인 (SCD40은 약 5초마다 갱신)
            if not ez_co2_sensor.is_data_ready():
                logger.info("EZ-CO2 data not ready yet", "CO2")
                uart.ez_co2_notify(b"EZCO2:WAIT")
                return

            co2, temp_c, hum = ez_co2_sensor.read()

            # 단일 라인 키=값 포맷 (CO2 ppm, Temp, Humidity)
            msg = "EZCO2:CO2={:.0f},T={:.2f},H={:.2f}".format(co2, temp_c, hum)

            uart.ez_co2_notify(msg.encode())
            logger.debug(
                f"EZ-CO2 values: CO2={co2:.0f}ppm, T={temp_c:.2f}C, H={hum:.2f}%RH",
                "CO2",
            )
        except Exception as e:
            logger.error(f"Error reading EZ-CO2 sensor: {e}", "CO2")
            uart.ez_co2_notify(b"EZCO2:ERROR:Measurement failed")
    
    elif cmd_str.startswith("EZCO2:PIN:"):
        try:
            pins = cmd_str.split(":")[2].split(",")
            if len(pins) < 2:
                logger.warning("Invalid EZ-CO2 pin configuration. Need SDA and SCL pins.", "CO2")
                uart.ez_co2_notify(b"EZCO2:ERROR:Need two pins")
                return

            sda_pin = int(pins[0])
            scl_pin = int(pins[1])

            success = update_pin_config('ezco2', sda_pin, scl_pin)
            if success:
                logger.info(f"EZ-CO2 pins set to SDA={sda_pin}, SCL={scl_pin}", "CO2")
                uart.ez_co2_notify(f"EZCO2:PIN:OK:{sda_pin},{scl_pin}".encode())
            else:
                logger.warning("EZ-CO2 pin configuration failed", "CO2")
                uart.ez_co2_notify(b"EZCO2:ERROR:Pin configuration failed")
        except Exception as e:
            logger.error(f"Error setting EZ-CO2 pins: {e}", "CO2")
            uart.ez_co2_notify(b"EZCO2:ERROR:Invalid pin configuration")
    else:
        logger.warning(f"Unknown EZCO2 command: {cmd_str}", "CO2")
        uart.ez_co2_notify(b"EZCO2:ERROR:Unknown command")

# ---------------------------
# 11) 먼지 센서
# ---------------------------
def dust_handler(conn_handle, cmd_str):
    """
    먼지 센서 명령어 처리:
    - DUST:STATUS: 현재 먼지 센서 값 측정하여 반환
    - DUST:CALIBRATE: 센서 보정 수행
    - DUST:PIN:LED핀번호,ADC핀번호: 핀 설정
    """
    logger.debug(f"Received command: {cmd_str}", "DUST")
    cmd_str = (cmd_str or "").strip().upper()
    
    if cmd_str == "DUST:STATUS":
        # 먼지 센서가 설정되지 않은 경우
        if dust_sensor is None:
            logger.warning("Dust sensor not configured", "DUST")
            uart.dust_notify(b"DUST:ERROR:Sensor not configured")
            return
            
        # 현재 먼지 농도 측정 및 전송
        try:
            status = dust_sensor.get_status()
            density = status["density"]
            voltage = status["voltage"]
            raw = status["raw"]
            
            # 결과 전송 (밀도, 전압, 원시값 포함)
            msg = f"DUST:{density:.2f},{voltage:.3f},{raw:.0f}"
            uart.dust_notify(msg.encode())
            
            logger.info(f"Dust sensor: {density:.2f} μg/m³, {voltage:.3f}V, raw={raw:.0f}", "DUST")
        except Exception as e:
            logger.error(f"Error measuring dust: {e}", "DUST")
            uart.dust_notify(b"DUST:ERROR:Measurement failed")
            
    elif cmd_str == "DUST:CALIBRATE":
        # 먼지 센서가 설정되지 않은 경우
        if dust_sensor is None:
            logger.warning("Dust sensor not configured", "DUST")
            uart.dust_notify(b"DUST:ERROR:Sensor not configured")
            return
            
        # 센서 보정 실행
        try:
            uart.dust_notify(b"DUST:CALIBRATE:START")
            voc = dust_sensor.calibrate(samples=50)  # 적은 샘플로 빠른 보정
            msg = f"DUST:CALIBRATE:DONE:{voc:.3f}"
            uart.dust_notify(msg.encode())
            logger.info(f"Dust sensor calibrated: VOC={voc:.3f}V", "DUST")
        except Exception as e:
            logger.error(f"Error calibrating dust sensor: {e}", "DUST")
            uart.dust_notify(b"DUST:ERROR:Calibration failed")
            
    elif cmd_str.startswith("DUST:PIN:"):
        # 핀 설정 명령 처리
        try:
            pins = cmd_str.split(":")[2].split(",")
            if len(pins) != 2:
                raise ValueError("두 개의 핀 번호가 필요합니다 (LED,ADC)")
                
            led_pin = int(pins[0]) 
            vo_pin = int(pins[1])
            
            # update_pin_config 함수를 사용하여 핀 설정
            success = update_pin_config('dust', led_pin, vo_pin)
            if success:
                uart.dust_notify(f"DUST:PIN:OK:{led_pin},{vo_pin}".encode())
            else:
                uart.dust_notify(b"DUST:ERROR:Pin configuration failed")
        except Exception as e:
            logger.error(f"Error setting dust sensor pins: {e}", "DUST")
            uart.dust_notify(b"DUST:ERROR:Invalid pin configuration")
            
    elif cmd_str == "DUST:ON" or cmd_str == "DUST:OFF":
        # 먼지 센서가 설정되지 않은 경우
        if dust_sensor is None:
            logger.warning("Dust sensor not configured", "DUST")
            uart.dust_notify(b"DUST:ERROR:Sensor not configured")
            return
            
        # 연속 모니터링 안내
        logger.info("Continuous dust monitoring not supported", "DUST")
        uart.dust_notify(b"DUST:INFO:Use STATUS command instead")
        
        # 현재 상태 한번 전송
        try:
            status = dust_sensor.get_status()
            msg = f"DUST:DENSITY={status['density']:.2f},VOC={status['voc']:.3f}"
            uart.dust_notify(msg.encode())
        except Exception as e:
            logger.error(f"Error measuring dust: {e}", "DUST")
            
    else:
        logger.warning(f"Unknown DUST command: {cmd_str}", "DUST")
        if uart:
            uart.dust_notify(b"DUST:ERROR:Unknown command")


# ---------------------------
# 12) EZMaker 미세먼지 센서 (PMS7003M)
# ---------------------------
def ez_dust_handler(conn_handle, cmd_str):
    """
    EZMaker 미세먼지 센서(PMS7003M) 명령어 처리:
    - EZDUST:STATUS : 현재 PM10/PM2.5/PM1.0 값을 모두 측정하여 반환
    - EZDUST:PIN:RX,TX : UART 핀 설정 (센서 TX/RX 연결)

    STATUS 응답 포맷:
      EZDUST:PM10,PM2.5,PM1.0
      (모두 μg/m³, 정수 또는 소수)
    """
    logger.debug(f"Received command: {cmd_str}", "EZDUST")
    cmd_str = (cmd_str or "").strip().upper()

    if cmd_str == "EZDUST:STATUS":
        global ez_dust_sensor

        if ez_dust_sensor is None:
            logger.warning("EZDUST sensor not configured", "EZDUST")
            uart.ez_dust_notify(b"EZDUST:ERROR:Sensor not configured")
            return

        try:
            status = ez_dust_sensor.get_status()
            pm10 = status.get("pm10", 0)
            pm2_5 = status.get("pm2_5", 0)
            pm1_0 = status.get("pm1_0", 0)

            # 한 번에 세 값을 모두 전송 (블록/JS에서 선택 사용)
            msg = f"EZDUST:{pm10},{pm2_5},{pm1_0}"
            uart.ez_dust_notify(msg.encode())

            logger.info(
                f"EZDUST sensor: PM10={pm10} μg/m³, PM2.5={pm2_5} μg/m³, PM1.0={pm1_0} μg/m³",
                "EZDUST",
            )
        except Exception as e:
            logger.error(f"Error measuring EZDUST sensor: {e}", "EZDUST")
            uart.ez_dust_notify(b"EZDUST:ERROR:Measurement failed")

    elif cmd_str.startswith("EZDUST:PIN:"):
        # UART 핀 설정 명령 처리
        try:
            pins = cmd_str.split(":")[2].split(",")
            if len(pins) != 2:
                raise ValueError("두 개의 핀 번호가 필요합니다 (RX,TX)")

            rx_pin = int(pins[0])
            tx_pin = int(pins[1])

            success = update_pin_config("ezdust", rx_pin, tx_pin)
            if success:
                uart.ez_dust_notify(f"EZDUST:PIN:OK:{rx_pin},{tx_pin}".encode())
            else:
                uart.ez_dust_notify(b"EZDUST:ERROR:Pin configuration failed")
        except Exception as e:
            logger.error(f"Error setting EZDUST pins: {e}", "EZDUST")
            uart.ez_dust_notify(b"EZDUST:ERROR:Invalid pin configuration")

    else:
        logger.warning(f"Unknown EZDUST command: {cmd_str}", "EZDUST")
        uart.ez_dust_notify(b"EZDUST:ERROR:Unknown command")

# ---------------------------
# 12) DC 모터
# ---------------------------

def dcmotor_handler(conn_handle, cmd_str):
    """
    DC 모터 명령어 처리 (단방향):
    - MOTOR:PIN:핀번호 - DC 모터 핀 설정 (PWM 속도 제어)
    - MOTOR:SPEED:속도 - 모터 구동 (속도: 0-100)
    - MOTOR:STOP - 모터 정지
    """
    global dcmotor_pin, dcmotor_pwm
    
    logger.debug(f"Received command: {cmd_str}", "MOTOR")
    
    # 핀 설정 명령 처리
    if cmd_str.startswith("MOTOR:PIN:"):
        try:
            # 핀 번호 파싱
            pin = int(cmd_str.split(":")[2])
            
            # 핀 설정 업데이트
            success = update_pin_config('dcmotor', pin)
            if success:
                uart.dcmotor_notify(f"MOTOR:PIN:OK:{pin}".encode())
            else:
                uart.dcmotor_notify(b"MOTOR:ERROR:Pin configuration failed")
        except Exception as e:
            logger.error(f"Error setting DC motor pin: {e}", "MOTOR")
            uart.dcmotor_notify(b"MOTOR:ERROR:Invalid pin configuration")
    
    # 모터 구동 명령 처리 (SPEED)
    elif cmd_str.startswith("MOTOR:SPEED:"):
        # DC 모터가 설정되지 않은 경우
        if dcmotor_pwm is None:
            logger.warning("DC motor not configured", "MOTOR")
            uart.dcmotor_notify(b"MOTOR:ERROR:Motor not configured")
            return
            
        try:
            # 속도 파싱 (0-100)
            speed = int(cmd_str.split(":")[2])
            if speed < 0:
                speed = 0
            elif speed > 100:
                speed = 100
                
            # PWM으로 속도 설정 (0-1023 스케일로 변환)
            duty = int(speed * 10.23)  # 0-100을 0-1023으로 변환
            dcmotor_pwm.duty(duty)
            
            logger.info(f"DC motor running at {speed}% speed", "MOTOR")
            uart.dcmotor_notify(f"MOTOR:SPEED:OK:{speed}".encode())
        except Exception as e:
            logger.error(f"Error setting DC motor speed: {e}", "MOTOR")
            uart.dcmotor_notify(b"MOTOR:ERROR:Speed setting failed")
    
    elif cmd_str == "MOTOR:STOP":
        # DC 모터가 설정되지 않은 경우
        if dcmotor_pwm is None:
            logger.warning("DC motor not configured", "MOTOR")
            uart.dcmotor_notify(b"MOTOR:ERROR:Motor not configured")
            return
            
        try:
            # 모터 정지 (PWM 0)
            dcmotor_pwm.duty(0)
            
            logger.info("DC motor stopped", "MOTOR")
            uart.dcmotor_notify(b"MOTOR:STOP:OK")
        except Exception as e:
            logger.error(f"Error stopping DC motor: {e}", "MOTOR")
            uart.dcmotor_notify(b"MOTOR:ERROR:Stop failed")
    
    # 역방향 명령 처리 - 지원하지 않음
    elif cmd_str.startswith("MOTOR:REV:"):
        logger.warning("Reverse direction not supported for this motor", "MOTOR")
        uart.dcmotor_notify(b"MOTOR:ERROR:Reverse direction not supported")
            
    else:
        logger.warning(f"Unknown DC motor command: {cmd_str}", "MOTOR")
        uart.dcmotor_notify(b"MOTOR:ERROR:Unknown command")

# ---------------------------
# 13) 심장박동 센서
# ---------------------------
def heart_rate_handler(conn_handle, cmd_str):
    """
    심장박동 센서 명령어 처리:
    - HEART:STATUS - 현재 심장 박동수 측정
    - HEART:PIN:SDA핀,SCL핀 - 심장박동 센서 I2C 핀 설정
    - HEART:STREAM:ON - 심장 박동수 연속 측정 시작
    - HEART:STREAM:OFF - 심장 박동수 연속 측정 중지
    """
    global heart_rate_sensor, heart_rate_monitor, heart_rate_streaming, heart_rate_enabled
    
    logger.debug(f"Received command: {cmd_str}", "HEART")
    
    if cmd_str == "HEART:STATUS":
        # 심장박동 센서가 설정되지 않은 경우
        if heart_rate_sensor is None or heart_rate_monitor is None:
            logger.warning("Heart rate sensor not configured", "HEART")
            uart.heart_rate_notify(b"HEART:ERROR:Sensor not configured")
            return
            
        # 현재 심장 박동수 측정 및 전송
        try:
            bpm = measure_heart_rate()
            if bpm is not None:
                msg = f"HEART:{bpm:.0f}"
                uart.heart_rate_notify(msg.encode())
                logger.info(f"Heart rate: {bpm:.0f} BPM", "HEART")
            else:
                logger.warning("Not enough data to calculate heart rate", "HEART")
                uart.heart_rate_notify(b"HEART:ERROR:Not enough data")
        except Exception as e:
            logger.error(f"Error measuring heart rate: {e}", "HEART")
            uart.heart_rate_notify(b"HEART:ERROR:Measurement failed")
            
    elif cmd_str.startswith("HEART:PIN:"):
        try:
            # 핀 번호 파싱
            pins = cmd_str.split(":")[2].split(",")
            if len(pins) < 2:
                logger.warning("Invalid pin configuration. Need SDA and SCL pins.", "HEART")
                uart.heart_rate_notify(b"HEART:ERROR:Need two pins")
                return
                
            sda_pin = int(pins[0])
            scl_pin = int(pins[1])
            
            # 핀 설정 업데이트
            success = update_pin_config('heart', sda_pin, scl_pin)
            if success:
                heart_rate_enabled = True
                logger.info(f"Heart rate sensor pins set to SDA={sda_pin}, SCL={scl_pin}", "HEART")
                uart.heart_rate_notify(f"HEART:PIN:OK:{sda_pin},{scl_pin}".encode())
            else:
                logger.warning("Pin configuration failed", "HEART")
                uart.heart_rate_notify(b"HEART:ERROR:Pin configuration failed")
        except Exception as e:
            logger.error(f"Error setting heart rate pins: {e}", "HEART")
            uart.heart_rate_notify(b"HEART:ERROR:Invalid pin configuration")
            
    elif cmd_str == "HEART:STREAM:ON":
        # 이미 스트리밍 중인 경우 중복 처리 방지
        if heart_rate_streaming:
            logger.debug("Heart rate streaming already active, ignoring duplicate ON command", "HEART")
            return
            
        # 심장박동 센서가 설정되지 않은 경우
        if heart_rate_sensor is None or heart_rate_monitor is None:
            logger.warning("Heart rate sensor not configured", "HEART")
            uart.heart_rate_notify(b"HEART:ERROR:Sensor not configured")
            return
            
        # 연속 측정 시작
        heart_rate_streaming = True
        logger.info("Heart rate streaming enabled", "HEART")
        uart.heart_rate_notify(b"HEART:STREAM:OK")
            
    elif cmd_str == "HEART:STREAM:OFF":
        # 실제로 스트리밍 중일 때만 처리
        if heart_rate_streaming:
            heart_rate_streaming = False
            logger.info("Heart rate streaming disabled", "HEART")
            uart.heart_rate_notify(b"HEART:STREAM:STOPPED")
            
    else:
        logger.warning(f"Unknown HEART command: {cmd_str}", "HEART")
        uart.heart_rate_notify(b"HEART:ERROR:Unknown command")

def measure_heart_rate():
    """심장 박동수 측정"""
    global heart_rate_sensor, heart_rate_monitor
    
    if heart_rate_sensor is None or heart_rate_monitor is None:
        return None
        
    # 최대 3초간 데이터 수집
    data_collection_time = 3000  # 3초
    start_time = time.ticks_ms()
    
    while time.ticks_diff(time.ticks_ms(), start_time) < data_collection_time:
        # 새 판독값이 있는지 확인
        heart_rate_sensor.check()
        
        # 저장소에 샘플이 있는지 확인
        if heart_rate_sensor.available():
            # IR 판독값 가져오기
            red_reading = heart_rate_sensor.pop_red_from_storage()
            ir_reading = heart_rate_sensor.pop_ir_from_storage()
            
            # 심장 박동 모니터에 IR 판독값 추가
            heart_rate_monitor.add_sample(ir_reading)
            
        # 짧은 시간 대기
        time.sleep_ms(10)
    
    # 심장 박동수 계산
    bpm = heart_rate_monitor.calculate_heart_rate()
    return bpm

# ---------------------------
# 펌웨어 업그레이드 핸들러
# ---------------------------
def upgrade_handler(conn_handle, cmd_str):
    """
    펌웨어 업그레이드 명령어 처리:
    - UPGRADE:START - 업그레이드 모드 시작
    - UPGRADE:FILE_START:filename:size - 파일 수신 시작
    - UPGRADE:FILE_DATA:base64_data - 파일 데이터 청크 수신
    - UPGRADE:FILE_END:filename - 파일 수신 완료
    - UPGRADE:COMMIT - 업그레이드 커밋 (파일 교체)
    - UPGRADE:ABORT - 업그레이드 중단
    - UPGRADE:ROLLBACK - 기존 버전 롤백
    """
    logger.debug(f"Received upgrade command: {cmd_str}", "UPGRADE")
    
    try:
        # firmwareUpgrader 모듈 import
        from firmwareUpgrader import handle_upgrade_command
        
        # 업그레이드 명령 처리
        logger.info(f"Processing upgrade command: {cmd_str}", "UPGRADE")
        success = handle_upgrade_command(cmd_str)
        
        if not success:
            logger.warning(f"Upgrade command failed: {cmd_str}", "UPGRADE")
            uart.upgrade_notify(b"UPGRADE_ERROR:Command_Failed")
        else:
            logger.debug(f"Upgrade command processed successfully: {cmd_str}", "UPGRADE")
            
    except ImportError as ie:
        logger.error(f"firmwareUpgrader module not found: {ie}", "UPGRADE")
        uart.upgrade_notify(b"UPGRADE_ERROR:Module_Not_Found")
    except Exception as e:
        logger.error(f"Upgrade command error: {e}", "UPGRADE")
        uart.upgrade_notify(f"UPGRADE_ERROR:Exception:{e}".encode())

# ---------------------------
# BLE 핸들러 등록
# ---------------------------
uart.set_led_handler(led_handler)
uart.set_cam_handler(cam_handler)
uart.set_ultrasonic_handler(ultrasonic_handler)
uart.set_dht_handler(dht_handler)  # 이름 변경됨
uart.set_servo_handler(servo_handler)
uart.set_neopixel_handler(neopixel_handler)  # NeoPixel 핸들러 등록
uart.set_touch_handler(touch_handler)  # 터치센서 핸들러 등록
uart.set_light_handler(light_handler)  # 조도센서 핸들러 등록
uart.set_lcd_handler(lcd_handler)      # I2C LCD 핸들러 등록
uart.set_buzzer_handler(buzzer_handler)  # 버저 핸들러 등록
uart.set_gyro_handler(gyro_handler)        # 자이로센서 핸들러 등록 (ADXL345, 공통)
uart.set_ez_gyro_handler(ez_gyro_handler)  # EZMaker 자이로센서(ICM20948) 핸들러 등록
uart.set_ez_press_handler(ez_press_handler)  # EZMaker 기압센서(BMP280) 핸들러 등록
uart.set_ez_co2_handler(ez_co2_handler)  # EZMaker CO2 센서(SCD40) 핸들러 등록
uart.set_dust_handler(dust_handler)  # 먼지 센서 핸들러 등록
uart.set_dcmotor_handler(dcmotor_handler)  # DC 모터 핸들러 등록
uart.set_laser_handler(laser_handler)  # 레이저 모듈 핸들러 등록 (EZMaker 전용)
uart.set_heart_rate_handler(heart_rate_handler)  # 심장박동 센서 핸들러 등록
uart.set_diya_handler(diya_handler)   # DIY-A 센서 핸들러 등록
uart.set_diyb_handler(diyb_handler)   # DIY-B 센서 핸들러 등록
uart.set_hall_handler(hall_handler)      # 자기장(Hall) 센서 핸들러 등록
uart.set_ez_light_handler(ez_light_handler)  # EZMaker 밝기센서(EZLIGHT) 핸들러 등록
uart.set_ez_weight_handler(ez_weight_handler)  # EZMaker 무게센서(EZWEIGHT) 핸들러 등록
uart.set_ez_sound_handler(ez_sound_handler)  # EZMaker 소리센서(EZSOUND) 핸들러 등록
uart.set_ez_dust_handler(ez_dust_handler)  # EZMaker 미세먼지 센서(EZDUST, PMS7003M) 핸들러 등록
uart.set_ez_volt_handler(ez_volt_handler)    # EZMaker 전압센서(EZVOLT) 핸들러 등록
uart.set_ez_curr_handler(ez_curr_handler)    # EZMaker 전류센서(EZCURR, INA219) 핸들러 등록
uart.set_ez_thermal_handler(ez_thermal_handler)  # EZMaker 수중/접촉 온도센서(EZTHERMAL, DS18B20) 핸들러 등록
uart.set_human_handler(human_handler)        # 인체감지 센서(HUMAN) 핸들러 등록
uart.set_soil_handler(soil_handler)  # 토양수분센서 핸들러 등록
uart.set_rain_handler(rain_handler)  # 빗방울센서 핸들러 등록
uart.set_connect_handler(connect_handler)  # 연결 핸들러 등록
uart.set_disconnect_handler(disconnect_handler)  # 연결 해제 핸들러 등록
uart.set_repl_handler(repl_handler)  # REPL 모드 전환 핸들러 등록
uart.set_upgrade_handler(upgrade_handler)  # 펌웨어 업그레이드 핸들러 등록

# 메모리 사용량 출력 함수
def print_memory_info():
    gc.collect()
    mem_free = gc.mem_free()
    mem_alloc = gc.mem_alloc()
    total = mem_free + mem_alloc
    logger.info(f"Memory - Free: {mem_free/1024:.1f} KB, Used: {mem_alloc/1024:.1f} KB, Total: {total/1024:.1f} KB ({mem_alloc*100/total:.1f}%)", "SYS")

# 초기 메모리 상태 출력
print_memory_info()
logger.info(f"Device running as: {device_name}", "SYS")
logger.info("All pins initialized to None - Configure pins before using sensors/actuators", "SYS")

# 이 코드 삭제 - BLE_STATUS_LED 핀의 상태를 덮어쓰는 문제 발생
# from machine import Pin
# pin_46 = Pin(46, Pin.OUT)
# pin_46.off()

# ---------------------------
# 리소스 정리 함수 (앱 종료 시 호출)
# ---------------------------
def cleanup_resources():
    """
    모든 리소스를 정리합니다 (앱 종료 시 호출)
    """
    global buzzer_initialized
    
    logger.info("Cleaning up resources...", "SYS")
    
    # BLE 상태 LED 끄기
    if ble_status_led:
        ble_status_led.value(0)
    
    # 버저 리소스 정리
    try:
        if buzzer_initialized:
            buzzerModule.stop()
            buzzerModule.deinit()
            buzzer_initialized = False
    except Exception as e:
        logger.warning(f"Error cleaning up buzzer resources: {e}", "BUZ")
    
    # 카메라 리소스 정리
    try:
        if cam:
            cam.deinit()
    except Exception as e:
        logger.warning(f"Error cleaning up camera resources: {e}", "CAM")
    
    # DC 모터 정지 및 리소스 정리
    try:
        if dcmotor_pwm:
            dcmotor_pwm.duty(0)  # 모터 정지
            dcmotor_pwm.deinit()  # PWM 리소스 해제
    except Exception as e:
        logger.warning(f"Error cleaning up DC motor resources: {e}", "MOTOR")
    
    # BLE 리소스 정리
    try:
        uart.close()
    except Exception as e:
        logger.warning(f"Error closing UART: {e}", "BLE")

# 필요시 메인 루프에서 Ctrl+C 처리 추가 가능
try:
    # ---------------------------
    # 17) 메인 루프
    # ---------------------------
    while True:
        # 주기적인 가비지 컬렉션
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_gc_collect) >= gc_interval:
            gc.collect()
            last_gc_collect = current_time
        
        # 카메라 처리:
        # - 캡처는 스레드가 수행
        # - 전송은 메인 루프에서 조금씩 처리
        if camera_enabled and uart and ble_connected:
            if streaming:
                _ensure_camera_worker()
            _camera_tx_pump()
        
        # 심장박동 센서 처리
        if heart_rate_streaming and heart_rate_enabled and heart_rate_sensor and heart_rate_monitor and uart and ble_connected:
            current_time = time.ticks_ms()
            if time.ticks_diff(current_time, last_heart_rate_time) >= heart_rate_interval:
                try:
                    # 심장박동 측정
                    bpm = measure_heart_rate()
                    if bpm is not None:
                        msg = f"HEART:{bpm:.0f}"
                        uart.heart_rate_notify(msg.encode())
                        logger.info(f"Heart rate: {bpm:.0f} BPM", "HEART")
                    
                    last_heart_rate_time = time.ticks_ms()
                except Exception as e:
                    logger.error(f"Error during heart rate streaming: {e}", "HEART")
                    time.sleep_ms(100)  # 오류 발생 시 짧은 대기
                    
        # 자이로 센서 스트리밍 처리
        if gyro_streaming and gyro_sensor and uart and ble_connected:
            current_time = time.ticks_ms()
            if time.ticks_diff(current_time, last_gyro_stream_time) >= gyro_stream_interval:
                try:
                    # 자이로 센서 데이터 읽기
                    x = gyro_sensor.xValue
                    y = gyro_sensor.yValue
                    z = gyro_sensor.zValue
                    
                    # 롤과 피치 계산
                    roll, pitch = gyro_sensor.RP_calculate(x, y, z)
                    
                    # 결과 전송
                    msg = f"GYRO:X={x},Y={y},Z={z}|ROLL={roll:.2f},PITCH={pitch:.2f}"
                    uart.gyro_notify(msg.encode())
                    logger.debug(f"Streamed gyro values: X={x}, Y={y}, Z={z}, ROLL={roll:.2f}, PITCH={pitch:.2f}", "GYRO")
                    
                    last_gyro_stream_time = current_time
                except Exception as e:
                    logger.error(f"Error during gyro streaming: {e}", "GYRO")
                    time.sleep_ms(100)  # 오류 발생 시 짧은 대기
                    
        time.sleep_ms(10)  # 짧은 딜레이로 CPU 점유율 감소
except KeyboardInterrupt:
    logger.info("Program terminated by user", "SYS")
    cleanup_resources()
except Exception as e:
    logger.critical(f"Unexpected error: {e}", "SYS")
    cleanup_resources()




