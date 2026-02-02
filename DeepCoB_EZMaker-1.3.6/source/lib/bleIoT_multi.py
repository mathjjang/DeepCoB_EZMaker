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
import bleBaseIoT
import buzzerModule  # 통합된 버저 모듈 사용
import ubinascii
from cameraModule import CameraModule  # CameraModule 임포트 추가
import logger  # 로깅 시스템 임포트

# 로그 레벨 설정 (기본값은 INFO)
#logger.set_level(logger.INFO)

# BLE 상태 표시 LED 핀 (GPIO 46)
PIN_BLE_STATUS_LED = const(46)
ble_status_led = None

# ADXL345 가속도계 라이브러리 임포트
from ADXL345 import ADXL345

# 글로벌 변수 및 임포트 섹션에 추가
from dust_sensor import DustSensor

# MAX30102 심장박동 센서를 위한 임포트 추가
from max30102 import MAX30102, MAX30105_PULSE_AMP_MEDIUM

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

# 서보 모터 배열 - 최대 4개까지 지원 (인덱스 0-3)
MAX_SERVOS = 4
PIN_SERVOS = [None] * MAX_SERVOS  # 서보 모터 핀 배열
servo_pins = [None] * MAX_SERVOS  # 서보 모터 Pin 객체 배열
servo_pwms = [None] * MAX_SERVOS  # 서보 모터 PWM 객체 배열

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
PIN_GYRO_SDA = None
PIN_GYRO_SCL = None

# NeoPixel 설정
NUM_PIXELS = const(4)  # 4개의 NeoPixel LED
# 네오픽셀 밝기 전역 변수 추가
neo_brightness = 1.0  # 기본 밝기는 100% (0.0-1.0 범위)

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
gyro_i2c = None
gyro_sensor = None

# 버저 초기화 상태 추적 변수
buzzer_initialized = False

# 글로벌 변수 섹션에 추가
dust_sensor = None
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

# 자이로센서 스트리밍 관련 변수
gyro_streaming = False
gyro_stream_interval = 200  # 500자이로 스트리밍 기본 간격(ms)
last_gyro_stream_time = 0

# 핀 설정 변경 함수 추가
def update_pin_config(pin_type, pin_number, secondary_pin=None):
    """
    실행 중 핀 설정 변경 함수
    pin_type: 'led', 'touch', 'light', 'dht', 'ultra', 'servo', 'servo:인덱스', 'neo', 'gyro', 'dcmotor', 'dust', 'heart'
    pin_number: 새 핀 번호
    secondary_pin: 보조 핀 번호 (초음파 센서의 에코 핀 등)
    """
    global PIN_LED, PIN_TOUCH, PIN_LIGHT_ANALOG, PIN_LIGHT_DIGITAL
    global PIN_DHT, PIN_ULTRASONIC_TRIGGER, PIN_ULTRASONIC_ECHO
    global PIN_NEO, PIN_GYRO_SDA, PIN_GYRO_SCL, NUM_PIXELS
    global PIN_DCMOTOR  # DC 모터 핀 변수 추가
    global led_pin, ultraSensor, dht_pin, dht_sensor
    global neo_pin, neo, touch_pin, light_analog_pin, light_digital_pin
    global gyro_i2c, gyro_sensor, dcmotor_pin, dcmotor_pwm, dust_sensor  # DC 모터 객체 추가
    global heart_rate_i2c, heart_rate_sensor, heart_rate_monitor  # 심장박동 센서 객체 추가
    # 서보 모터 배열 전역 변수
    global PIN_SERVOS, servo_pins, servo_pwms
    
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
            # 'servo'는 'servo:0'와 동일하게 처리 (첫 번째 서보모터)
            return update_pin_config('servo:0', pin_number)
            
        elif pin_type.startswith('servo:'):
            # 인덱스 파싱 (예: servo:0, servo:1)
            try:
                index = int(pin_type.split(':')[1])
                if index < 0 or index >= MAX_SERVOS:
                    logger.error(f"Invalid servo index {index}, using 0", "SERVO")
                    index = 0
            except:
                logger.error(f"Invalid servo index format, using 0", "SERVO")
                index = 0
            
            # 핀 번호 저장
            PIN_SERVOS[index] = pin_number
            
            # 서보 모터 핀 재설정
            if servo_pwms[index] is not None:
                try:
                    servo_pwms[index].deinit()  # PWM 설정 해제
                except:
                    pass
                
            # 새 핀 설정
            servo_pins[index] = machine.Pin(pin_number, machine.Pin.OUT)
            servo_pwms[index] = machine.PWM(servo_pins[index])
            servo_pwms[index].freq(50)  # 서보는 보통 50Hz
            
            logger.info(f"Servo motor {index} pin set to {pin_number}", "SERVO")
            return True
            
        elif pin_type == 'neo':
            # 핀 번호 저장
            PIN_NEO = pin_number
            
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
            neo = NeoPixel(neo_pin, NUM_PIXELS)
            # 초기화 시 모든 LED 끄기
            neo.fill((0, 0, 0))
            neo.write()
            
            logger.info(f"NeoPixel pin set to {pin_number} with {NUM_PIXELS} LEDs", "NEO")
            return True
            
        elif pin_type == 'gyro':
            # 자이로 센서(ADXL345) 핀 설정
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

def set_servo_angle(deg):
    """
    deg: 0..180
    서보 펄스 폭 = 500us(0도) ~ 2500us(180도) 일반적인 예시
    MicroPython에서는 duty_ns, duty_u16 등을 사용 가능.
    여기서는 duty_ns를 사용해 봄.
    
    간편한 사용을 위한 함수 - 첫 번째 서보(인덱스 0)의 각도를 설정
    """
    # 배열 기반 구현 사용
    return set_servo_angle_by_index(0, deg)

def set_servo_angle_by_index(index, deg):
    """
    index: 서보 인덱스 (0부터 MAX_SERVOS-1)
    deg: 0..180
    특정 서보 모터의 각도를 설정합니다.
    """
    # 인덱스 범위 확인
    if index < 0 or index >= MAX_SERVOS:
        logger.error(f"Invalid servo index: {index}", "SERVO")
        return False
        
    # 서보 PWM 객체 확인
    if servo_pwms[index] is None:
        logger.warning(f"Servo motor {index} not configured", "SERVO")
        return False
        
    # 각도 범위 제한
    if deg < 0: deg = 0
    if deg > 180: deg = 180
    
    # 0도 = 0.5ms, 180도 = 2.5ms
    pulse_min_ns = 500_000   # 0.5ms = 500,000ns
    pulse_max_ns = 2_500_000 # 2.5ms
    # 각도 비율로 보간
    pulse_ns = pulse_min_ns + (pulse_max_ns - pulse_min_ns) * deg / 180
    
    # PWM 설정
    servo_pwms[index].duty_ns(int(pulse_ns))
    return True

def servo_handler(conn_handle, cmd_str):
    """
    서보모터 명령어 처리:
    - SERVO:PIN:핀번호: 서보 핀 설정 (인덱스 0)
    - SERVO:PIN:인덱스:핀번호: 특정 인덱스의 서보 핀 설정
    - SERVO:각도: 서보 각도 설정 (인덱스 0)
    - SERVO:인덱스:각도: 특정 인덱스의 서보 각도 설정
    """
    cmd_str = cmd_str.upper()
    logger.debug(f"Received command: {cmd_str}", "SERVO")
    
    # 핀 설정 명령 처리
    if cmd_str.startswith("SERVO:PIN:"):
        parts = cmd_str.split(":")
        # 인덱스 기반 핀 설정 명령 (SERVO:PIN:인덱스:핀번호)
        if len(parts) >= 4 and parts[2].isdigit():
            try:
                index = int(parts[2])
                pin_number = int(parts[3])
                
                # 인덱스 범위 확인
                if index < 0 or index >= MAX_SERVOS:
                    logger.error(f"Invalid servo index: {index}", "SERVO")
                    uart.servo_notify(b"SERVO:ERROR:Invalid index")
                    return
                
                # 핀 설정 업데이트 (servo:인덱스 형식 사용)
                success = update_pin_config(f"servo:{index}", pin_number)
                if success:
                    uart.servo_notify(f"SERVO:PIN:{index}:{pin_number}:OK".encode())
                else:
                    uart.servo_notify(b"SERVO:ERROR:Pin configuration failed")
                return
            except Exception as e:
                logger.error(f"Error setting servo pin with index: {e}", "SERVO")
                uart.servo_notify(b"SERVO:ERROR:Invalid pin configuration")
                return
        
        # 인덱스 없는 핀 설정 (SERVO:PIN:핀번호) - 인덱스 0으로 처리
        try:
            pin_number = int(parts[2])
            success = update_pin_config('servo:0', pin_number)
            if success:
                uart.servo_notify(f"SERVO:PIN:OK:{pin_number}".encode())
            else:
                uart.servo_notify(b"SERVO:ERROR:Pin configuration failed")
            return
        except Exception as e:
            logger.error(f"Error setting servo pin: {e}", "SERVO")
            uart.servo_notify(b"SERVO:ERROR:Invalid pin configuration")
            return
    
    # 인덱스 기반 서보 각도 설정 명령 처리 (SERVO:인덱스:각도)
    elif cmd_str.startswith("SERVO:") and len(cmd_str.split(":")) >= 3:
        parts = cmd_str.split(":")
        # 인덱스와 각도가 모두 숫자인지 확인
        if len(parts) >= 3 and parts[1].isdigit() and parts[2].isdigit():
            try:
                index = int(parts[1])
                angle = int(parts[2])
                
                # 인덱스 범위 확인
                if index < 0 or index >= MAX_SERVOS:
                    logger.error(f"Invalid servo index: {index}", "SERVO")
                    uart.servo_notify(b"SERVO:ERROR:Invalid index")
                    return
                
                # 각도 설정
                success = set_servo_angle_by_index(index, angle)
                if success:
                    logger.info(f"Servo[{index}] angle set to {angle}", "SERVO")
                    uart.servo_notify(f"SERVO:{index}:{angle}:OK".encode())
                else:
                    uart.servo_notify(f"SERVO:ERROR:Failed to set angle for servo {index}".encode())
                return
            except Exception as e:
                logger.error(f"Error setting servo angle with index: {e}", "SERVO")
                uart.servo_notify(b"SERVO:ERROR:Invalid angle command")
                return
    
    # 서보 각도 설정 명령 처리 (SERVO:각도) - 기본 인덱스 0
    elif cmd_str.startswith("SERVO:"):
        # 예: "SERVO:90"
        parts = cmd_str.split(":")
        if len(parts) == 2 and parts[1].isdigit():
            try:
                angle = int(parts[1])
                success = set_servo_angle(angle)
                if success:
                    logger.info(f"Servo[0] angle set to {angle}", "SERVO")
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
    global neo_rainbow_active, neo_rainbow_speed  # 전역 변수 사용 선언 추가
    
    # 전달받은 speed 파라미터를 전역 변수에 설정
    neo_rainbow_speed = max(1, min(10, speed))
    
    offset = 0
    while neo_rainbow_active:
        if neo is None:  # NeoPixel이 설정되지 않은 경우 스레드 종료
            neo_rainbow_active = False
            break
            
        for i in range(NUM_PIXELS):
            # 각 LED마다 다른 색상 오프셋 적용
            color = wheel((i * 256 // NUM_PIXELS + offset) & 255)
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
                
                pixel_count = NUM_PIXELS  # 기본값 사용
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
                if not (0 <= index < NUM_PIXELS):
                    raise ValueError(f"Index {index} out of range (0-{NUM_PIXELS-1})")
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
                if not (0 <= index < NUM_PIXELS):
                    raise ValueError(f"Index {index} out of range (0-{NUM_PIXELS-1})")
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
# 8)버저
# ---------------------------
def buzzer_handler(conn_handle, cmd_str):
    """
    버저 명령어 처리:
    - BUZ:INIT - 버저 초기화 및 시작 신호음 재생
    - BUZ:BEEP[:count[:frequency[:duration_ms[:interval_ms]]]] - 비프음 재생
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
                parts = cmd_str.split(":")
                count = 1
                frequency = 2000
                duration_ms = 100
                interval_ms = 100
                
                if len(parts) > 2 and parts[2]:
                    try:
                        count = int(parts[2])
                    except Exception as e:
                        logger.error(f"Invalid count format: {parts[2]}", "BUZ")
                        count = 1  # 기본값 사용
                        
                if len(parts) > 3 and parts[3]:
                    try:
                        frequency = int(parts[3])
                    except Exception as e:
                        logger.error(f"Invalid frequency format: {parts[3]}", "BUZ")
                        frequency = 2000  # 기본값 사용
                        
                if len(parts) > 4 and parts[4]:
                    try:
                        duration_ms = int(parts[4])
                    except Exception as e:
                        logger.error(f"Invalid duration format: {parts[4]}", "BUZ")
                        duration_ms = 100  # 기본값 사용
                        
                if len(parts) > 5 and parts[5]:
                    try:
                        interval_ms = int(parts[5])
                    except Exception as e:
                        logger.error(f"Invalid interval format: {parts[5]}", "BUZ")
                        interval_ms = 100  # 기본값 사용
                    
                # 버저모듈로 비프음 재생 (비차단 방식)
                buzzerModule.beep(count=count, frequency=frequency, 
                               duration_ms=duration_ms, interval_ms=interval_ms)
                ###uart.buzzer_notify(b"PLAYING")
                
            # 멜로디 재생 명령 처리
            elif cmd_str.startswith("BUZ:PLAY:"):
                parts = cmd_str.split(":")
                if len(parts) < 3 or not parts[2]:
                    logger.error("Missing melody name", "BUZ")
                    ###uart.buzzer_notify(b"ERROR:Missing melody name")
                    return
                    
                melody_name = parts[2]
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
# 카메라 성능 최적화를 위한 변수 추가
last_frame_time = 0
stream_interval = 300  # 초기 스트리밍 간격 (ms)
cam = None            # 카메라 모듈 객체

# 메모리 모니터링 변수
last_gc_collect = 0
gc_interval = 5000  # 5초마다 GC 수행

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

# 프레임 전송 함수
def send_frame(frame):
    logger.debug(f"Sending frame: {len(frame)} bytes", "CAM")
    if not frame:
        return False
    
    try:
        # JPEG 마커 검증 - CameraModule의 validate_jpeg 사용
        #if not cam.validate_jpeg(frame):
        #    logger.warning("Invalid JPEG format", "CAM")
        #    uart.cam_notify(b"CAM:ERROR")
        #    return False
        
        # 프레임 시작 마커 전송
        uart.cam_notify(b"CAM:START")
        time.sleep_ms(5)
        
        # 프레임 크기 정보 전송
        size_info = f"SIZE:{len(frame)}".encode()
        uart.cam_notify(size_info)
        time.sleep_ms(5)
        
        # 바이너리 데이터를 청크 단위로 전송
        offset = 0
        chunk_size = 160  #200  # 160BLE MTU 크기에 맞게 조정
        length = len(frame)
        
        seq_num = 0
        while offset < length:
            end = min(offset + chunk_size, length)
            chunk = frame[offset:end]
            
            # 간소화된 헤더: BIN숫자:
            header = f"BIN{seq_num}:".encode()
            uart.cam_notify(header + chunk)
            #print('seq_num',seq_num)
            logger.debug(f"Frame chunk: seq_num={seq_num}", "CAM")
            offset = end
            seq_num += 1
            
            time.sleep_ms(5)  # 적은 딜레이
            
            # 주기적으로 메모리 확인 및 정리
            #if seq_num % 10 == 0:  # 10개 청크마다
            #    gc.collect()
        
        # 프레임 종료 마커 전송
        #time.sleep_ms(10)
        uart.cam_notify(b"CAM:END")
        
        return True
    except Exception as e:
        logger.error(f"Frame send error: {e}", "CAM")
        return False

def cam_handler(conn_handle, cmd_str):
    global streaming, stream_interval
    cmd_str = cmd_str.upper()
    logger.debug(f"Received command: {cmd_str}", "CAM")

    if not camera_enabled:
        logger.warning("Camera not available.", "CAM")
        return

    if cmd_str == "CAM:SNAP":
        # 메모리 부족 방지를 위한 GC 실행
        gc.collect()
        
        # CameraModule의 capture_frame 메서드 사용
        _ = cam.capture_frame()
        frame = cam.capture_frame()
        
        if frame is None:
            logger.error("Failed to capture frame", "CAM")
            # 오류 알림을 클라이언트에 전송
            uart.cam_notify(b"CAM:ERROR")
            return
        
        # 프레임 전송
        if send_frame(frame):
            logger.debug(f"Sent snapshot: {len(frame)} bytes", "CAM")
        else:
            logger.error("Failed to send snapshot", "CAM")
        
        # 메모리 해제를 위한 가비지 컬렉션
        frame = None
        gc.collect()
        # 메모리 사용량 출력
        print_memory_info()
        
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
        logger.info(f"Received stream ON command, current streaming status: {streaming}", "CAM")
        
        streaming = True
        logger.info(f"Streaming enabled, new status: {streaming}", "CAM")
        gc.collect()
        print_memory_info()
    elif cmd_str == "CAM:STREAM:OFF":
        streaming = False
        logger.info("Streaming disabled", "CAM")
        # 스트리밍 종료 시 메모리 정리
        gc.collect()
        print_memory_info()
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
        led_pin.duty_u16(0)  # 연결 해제되면 LED 끄기 (PWM 모드)

    # 버저 중지 (재생 중지만 수행, 리소스는 유지)
    try:
        if buzzer_initialized:
            buzzerModule.stop()
    except Exception as e:
        logger.warning(f"Error stopping buzzer: {e}", "BUZ")
        
    # DC 모터 정지
    try:
        if dcmotor_pwm:
            dcmotor_pwm.duty(0)  # 모터 정지
    except Exception as e:
        logger.warning(f"Error stopping DC motor: {e}", "MOTOR")

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
            is_repl = config.repl_flag
            status = "REPL:ON" if is_repl else "REPL:OFF"
            uart.repl_notify(status.encode())
            logger.info(f"Current mode: {'REPL' if is_repl else 'IoT'}", "REPL")
        except:
            uart.repl_notify(b"REPL:ERROR:Config not found")
            
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
            
        # 스트리밍 시작
        gyro_streaming = True
        logger.info(f"Gyro streaming enabled with interval {gyro_stream_interval}ms", "GYRO")
        uart.gyro_notify(b"GYRO:STREAM:OK")
        
    elif cmd_str == "GYRO:STREAM:OFF":
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
        # 연속 측정 중지
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
uart.set_buzzer_handler(buzzer_handler)  # 버저 핸들러 등록
uart.set_gyro_handler(gyro_handler)  # 자이로센서 핸들러 등록
uart.set_dust_handler(dust_handler)  # 먼지 센서 핸들러 등록
uart.set_dcmotor_handler(dcmotor_handler)  # DC 모터 핸들러 등록
uart.set_heart_rate_handler(heart_rate_handler)  # 심장박동 센서 핸들러 등록
uart.set_connect_handler(connect_handler)  # 연결 핸들러 등록
uart.set_disconnect_handler(disconnect_handler)  # 연결 해제 핸들러 등록
uart.set_repl_handler(repl_handler)  # REPL 모드 전환 핸들러 등록

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
        
        # 카메라 스트리밍 처리
        #print(f"Streaming: {streaming}, Camera enabled: {camera_enabled}, UART: {uart}, BLE connected: {ble_connected}")
        if streaming and camera_enabled and uart and ble_connected:  #
            current_time = time.ticks_ms()
            if time.ticks_diff(current_time, last_frame_time) >= stream_interval:
                try:
                    # 메모리 부족 방지를 위한 GC 실행
                    gc.collect()
                    
                    # CameraModule의 capture_frame 메서드 사용
                    frame = cam.capture_frame()
                    
                    if frame:
                        if send_frame(frame):
                            logger.debug(f"Streamed frame: {len(frame)} bytes", "CAM")
                        frame = None  # 메모리 해제를 위해
                        
                    gc.collect()
                    last_frame_time = time.ticks_ms()
                except Exception as e:
                    logger.error(f"Error during streaming: {e}", "CAM")
                    # 오류 발생 시 메모리 정리
                    gc.collect()
                    time.sleep_ms(100)  # 오류 발생 시 짧은 대기
        
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




