# EZMaker 센서 통합 프로젝트

## 1. 프로젝트 개요
DeepCo 보드(완제품)에 EZMaker 시리즈의 다양한 외부 센서를 연결하고 활용하기 위한 MicroPython 펌웨어 개발 프로젝트입니다.

## 2. 하드웨어 구성
*   **메인 보드**: DeepCo Board v2.0 (ESP32-S3 기반)
*   **확장 쉴드**: EZMAKER Shield v2.0
*   **센서**: EZMaker 시리즈 (다양한 외부 센서)
*   **핀 맵핑 (DeepcoBoard v2.0 Pinmap for EZMAKER Sheild2.xlsx 기준)**

### 전체 핀 맵핑 (DeepcoBoard v2.0 + EZMAKER Shield v2.0 기준)

> **주의**: EZMaker 쉴드 v2.0 핀맵을 기준으로 합니다. (D5/D6가 I2C로 변경됨)
> (엑셀 파일: `DeepcoBoard v2.0 Pinmap for EZMAKER Sheild2.xlsx`)

| Shield Port | ESP32 GPIO | Type | 비고 (연결 권장 센서) |
| :--- | :--- | :--- | :--- |
| **D0** | **21** | Digital | 일반 GPIO (I2C용이나 일반 용도 사용 가능) |
| **D1** | **47** | Digital | 일반 GPIO |
| **D2** | **48** | Digital | **터치센서**, 버튼 등 (Servo 1) |
| **D3** | **38** | Digital | **터치센서**, 버튼 등 (Servo 2) |
| **D4** | **39** | Digital | DC 모터 등 |
| **SCL (D5)** | **40** | **I2C** | **I2C SCL (풀업 내장)** - 기압센서, LCD 등 |
| **SDA (D6)** | **41** | **I2C** | **I2C SDA (풀업 내장)** - 기압센서, LCD 등 |
| **A0 / D7** | **2** | Analog/Dig | **조도, 소리, 자기장 등** |
| **A1 / D8** | **1** | Analog/Dig | **조도, 소리, 자기장 등** (주의: TX0) |
| **A2 / D9** | **3** | Analog/Dig | **조도, 소리, 자기장 등** |
| **RXD (D10)**| **14** | UART | UART RX (미세먼지 등) |
| **TXD (D11)**| **42** | UART | UART TX (미세먼지 등) |
| **A3 / D12** | **20** | Analog/Dig | **조도, 소리, 자기장 등** |
| **A4 / D13** | **19** | Analog/Dig | **조도, 소리, 자기장 등** |
| **System** | **46** | Output | BLE Status LED |

## 3. 개발 프로세스
1.  **단위 테스트 (Unit Testing)**:
    *   새로운 센서에 대한 독립적인 MicroPython 테스트 코드 작성.
    *   `source/` 폴더 외부에 테스트 파일 생성 (예: `DeepCoB_EZMaker/test/`).
    *   실제 하드웨어에서 동작 검증.
2.  **통합 (Integration)**:
    *   검증된 코드를 `source/lib/` 라이브러리로 변환.
    *   `source/lib/bleIoT.py` 및 `bleBaseIoT.py`에 통합.
    *   BLE 명령어를 통한 제어 기능 추가.

## 4. 진행 상황
- [x] 프로젝트 문서 생성 (EZMaker프로젝트.md)
- [x] 핀 맵핑 정보 업데이트 (v2.0 + Shield v2.0 기준)
- [x] 센서 목록 및 테스트 계획 수립

## 5. 센서 및 액츄에이터 상세 목록 (제공 정보 및 테스트 현황)

| 구분 | 이름 | 칩셋 (Chipset) | 연결 방식 | 테스트 파일 (Test File) | 비고 (라이브러리/범위) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **센서** | **DIY-A** | - | Analog | - | Raw 값 측정 |
| **센서** | **DIY-B** | - | Analog | - | Raw 값 측정 |
| **센서** | **밝기센서** | GL5549 | Analog | `test/test_light_ezmaker.py` | Raw 값 측정 |
| **센서** | **소리센서** | - | Analog | `test/test_sound_ezmaker.py` | Raw 값 측정 |
| **센서** | **가스센서** | MQ2 | Analog | - | 300~10,000 ppm (가연성 가스) |
| **센서** | **전압센서** | - | Analog | - | 0~16V |
| **센서** | **자기장센서** | SLSS49E-3 | Analog | `test/test_hall_ezmaker.py` | Raw 값 측정 |
| **센서** | **초음파** | CS100A | Digital | `test/test_ultrasonic_1pin.py` | 5~200cm (1-pin 제어) |
| **센서** | **스위치** | - | Digital | `test/test_switch_ezmaker.py` | |
| **센서** | **터치스위치** | - | Digital | `test/test_touch_ezmaker.py` | |
| **센서** | **온도/습도** | DHT11 | Digital | `test/test_dht_ezmaker.py` | Temp(0~50℃), Hum(20~90%) |
| **센서** | **인체감지** | BS312 | Digital | `test/test_pir_ezmaker.py` | 적외선 인체감지 |
| **센서** | **수중/접촉온도** | DS18B20 | Digital (1-Wire) | `test/test_watertemp_ds18b20_ezmaker.py` | -55~125℃ (DallasTemperature) |
| **센서** | **미세먼지** | PMS7003M | UART | `test/test_dust_pms_ezmaker.py` | PMS Library |
| **센서** | **무게센서** | HX711 | UART/Digital | `test/test_weight_uart_ezmaker.py` | HX711 Arduino Library |
| **센서** | **이산화탄소** | SCD40 | I2C | `test/test_co2_scd40_ezmaker.py` | 0~40,000 ppm (Sensirion SCD4x) |
| **센서** | **자이로** | ICM20948 | I2C | `test/test_GYRO_mpu6050_ezmaker.py` | **주의**: 테스트 코드는 MPU6050용임 |
| **센서** | **전류센서** | INA219 | I2C | - | 0~2000 mAh (Adafruit INA219) |
| **센서** | **기압센서** | BMP280 | I2C | `test/test_bmp280_ezmaker.py` | 300~1100 hPa (Adafruit BMP280) |
| **센서** | **고온센서** | MAX31850 | I2C(표기) | - | -270~1372℃ (MAX31850 OneWire) |
| **액츄에이터** | **피에조부저** | - | Digital | - | 딥코 보드 내장과 동일 |
| **액츄에이터** | **레이저** | - | Digital | `test/test_laser_ezmaker.py` | On/Off 제어 |
| **액츄에이터** | **네오픽셀LED** | WS2812 | Digital | `test/test_neopixel_ezmaker.py` | RGB 컬러 (Adafruit NeoPixel) |
| **액츄에이터** | **서보모터** | - | Digital | `test/test_servo_ezmaker.py` | |
| **액츄에이터** | **네오픽셀RING** | WS2812 | Digital | - | 12칩 원형 (Adafruit NeoPixel) |
| **액츄에이터** | **DC모터** | - | Digital | `test/test_motor_ezmaker.py` | PWM 속도 제어 |
| **액츄에이터** | **네오픽셀BAR** | WS2812 | Digital | - | 7칩 바형 (Adafruit NeoPixel) |
| **액츄에이터** | **LCD(16*2)** | - | I2C | `test/test_16x2_lcd_i2c_ezmaker.py` | LiquidCrystal I2C |
| **액츄에이터** | **LCD(20*4)** | - | I2C | `test/test_20x4_lcd_i2c_ezmaker.py` | LiquidCrystal I2C |

## 6. 펌웨어 / MicroPython 측 과업

### 6.1 EZMaker 센서 분류 및 우선순위 확정
- [ ] `EZMAKER 센서 리스트 및 칩셋 정리-251203.xlsx` 기준으로  
      **신규(EZMaker 전용) 센서/액츄에이터**와  
      **기존 듀폰 센서와 기능이 겹치는 센서/액츄에이터**를 분류
- [ ] 1차 대상(우선 구현할 센서/액츄에이터) 리스트 확정

### 6.2 신규 EZMaker 센서/액츄에이터 펌웨어 지원
- [ ] 센서/액츄에이터별 **단위 테스트 코드 작성/정리**  
      (위 표의 `Test File` 기준, `test/` 폴더: 예 `test_xxx_ezmaker.py`)
- [ ] 센서/액츄에이터별 **MicroPython 드라이버/라이브러리** 구현  
      (`source/lib/xxx.py` 형태로 정리)
- [ ] `source/lib/bleIoT.py`, `source/lib/bleBaseIoT.py`에  
      신규 센서/액츄에이터용 **BLE 명령어·프로토콜**(서비스/캐릭터리스틱/명령 문자열) 정의 및 통합
- [ ] `compile_mpy.ps1`를 이용해 `.mpy` 빌드 후, 딥코보드에 배포 및 실측 테스트

### 6.3 기존 센서와의 중복 정리 (후순위)
- [ ] 기존 듀폰 스타일 센서와 EZMaker 센서가 **동일/유사 칩셋·기능**일 경우,  
      공용 드라이버/명령 구조로 **통합 가능한지 검토**
- [ ] 블록/웹 서비스에서의 **센서 이름·아이콘·설명**을 통일하는 방안 정의  
      (예: 동일 기능 센서는 학생 입장에서 하나의 센서처럼 보이도록 정리)

## 7. 웹서비스 / 블록코딩 측 과업

### 7.1 BLE 라이브러리 구조 정리 (`IoTmode/test/integratedBleLib_Camera.js`)
- [ ] 현재 정의된 **서비스/캐릭터리스틱 UUID**  
      (`IOT_SERVICE`, `SENSOR_SERVICE`, `REPL_SERVICE` 및 `ULTRA`, `DHT`, `NEOPIXEL`, `DCMOTOR` 등)와  
      센서/액츄에이터 매핑 관계를 문서화
- [ ] 신규 EZMaker 센서/액츄에이터에 필요한  
      **BLE 특성/명령 패턴** 설계 및 JS API 확장  
      (예: `UltrasonicSensor`, `DHTSensor`, `TouchSensor` 스타일의 클래스/모듈 추가 또는 보완)

### 7.2 블록 사양 정리 (`IoTmode/test/DeepcoIoT_block_v1.6.xlsx` 기반)
- [ ] 신규 EZMaker 센서/액츄에이터용 **블록 UI 설계**  
      (블록 이름, 카테고리, 파라미터, 기본값, 설명/도움말 텍스트)
- [ ] 각 블록이 호출해야 할 **JS 함수명 / BLE 명령 문자열 포맷** 명시  
      (예: `ULTRA:READ`, `DHT:STATUS`, `NEO:COLOR:R,G,B` 등 실제 사용 규격 정리)
- [ ] 기존 블록과의 **이름/동작 중복 여부**를 점검하고,  
      1차 단계에서는 **기존 블록 유지 + 신규 블록 추가** 전략으로 정리

### 7.3 통합 테스트 플로우 정리
- [ ] “**블록 → JS → BLE → MicroPython → 센서/액츄에이터 → 응답 값 → BLE → JS → 블록**”  
      전체 데이터 흐름에 대한 체크리스트 작성
- [ ] 대표 신규 센서/액츄에이터 몇 개를 선정해 **엔드투엔드 테스트 시나리오** 문서화  
      (예: “EZMaker 초음파로 10cm 이내 감지 시, 블록으로 부저/네오픽셀 제어” 등)
- [ ] 실제 웹서비스 환경에서 **학생 관점 시나리오 테스트** 수행  
      (장치 연결, 블록 실행, 값 확인, 오류 발생 시 메시지/가이드 확인 등)
      
## 8. 기존 DeepCo 보드 센서/액츄에이터 vs EZMaker 센서 비교

기존 DeepCo 보드(듀폰 케이블 센서 + 블록코딩)에서 이미 BLE IoT 서비스로 제공되던 센서/액츄에이터와,  
EZMaker 쉴드 + EZMaker(4핀) 센서들을 한눈에 비교하기 위한 정리입니다.  
여기서 **“기존 DeepCo 보드 IoT 서비스”** 여부는 `bleBaseIoT.py`, `bleIoT.py` 기준입니다.

### 8.1 센서 비교

| 구분 | 기능/이름                 | 칩셋/모듈 (예시)          | 기존 DeepCo 보드 IoT 서비스 (BLE) | EZMaker 센서 라인 | 관계 (중복/신규)        | 비고 |
| :--- | :----------------------- | :------------------------ | :--------------------------------: | :---------------: | :---------------------- | :--- |
| 센서 | 밝기센서(조도)           | GL5549                    | O (`LIGHT` 특성)                   | O                 | 중복(DeepCo+EZMaker)   | 듀폰 조도센서 ↔ EZMaker 4핀 조도센서, BLE는 LIGHT 특성 공통 사용 |
| 센서 | 초음파 거리센서          | HCSR04 / CS100A           | O (`ULTRA` 특성)                   | O                 | 중복(DeepCo+EZMaker)   | 기능은 동일(거리 측정), DeepCo는 HCSR04 2핀, EZMaker는 CS100A 1핀 등 하드웨어만 다름 |
| 센서 | 터치스위치               | TTP223 등                 | O (`TOUCH` 특성)                   | O                 | 중복(DeepCo+EZMaker)   | 듀폰 터치센서 ↔ EZMaker 터치 모듈, BLE TOUCH 특성 재사용 |
| 센서 | 온도/습도 센서           | DHT11                     | O (`DHT` 특성)                     | O                 | 중복(DeepCo+EZMaker)   | 기존 DeepCo DHT11 블록/IoT 서비스와 완전히 동일 기능 |
| 센서 | 미세먼지 센서            | DustSensor / PMS7003M     | O (`DUST` 특성, 아날로그 센서 기준) | O                | 중복(DeepCo+EZMaker)   | 먼지 측정 기능 공통, DeepCo는 아날로그 DustSensor, EZMaker는 UART PMS7003M 사용 |
| 센서 | 자이로/가속도 센서       | ADXL345 / ICM20948        | O (`GYRO` 특성)                    | O                 | 중복(DeepCo+EZMaker)   | 자이로/가속도 기능 동일, 센서 칩과 축 수/정밀도만 차이 |
| 센서 | 심장박동 센서            | MAX30102                  | O (`HEART` 특성)                   | X                 | DeepCo 전용            | 심장박동/SpO₂ 측정, EZMaker 센서 리스트에는 없음 |
| 센서 | 토양수분센서             | YL-69                     | O (`SOIL` 특성)                    | X                 | DeepCo 전용            | 토양 수분 측정, 기존 DeepCo IoT 서비스에서만 사용 |
| 센서 | 빗방울센서               | 아날로그 모듈            | O (`RAIN` 특성)                    | X                 | DeepCo 전용            | 빗방울 감지 아날로그 센서, EZMaker 센서 리스트에는 없음 |
| 센서 | 소리센서                 | -                         | X                                  | O                 | EZMaker 전용           | 아날로그 음량 감지, IoT 서비스/명령은 EZMaker에서 신규 설계 대상 |
| 센서 | 가스센서                 | MQ2                       | X                                  | O                 | EZMaker 전용           | 가연성 가스 농도 측정 (300~10,000 ppm) |
| 센서 | 전압센서                 | -                         | X                                  | O                 | EZMaker 전용           | 0~16V 입력 전압 측정용 모듈 |
| 센서 | 자기장센서               | SLSS49E-3                 | X                                  | O                 | EZMaker 전용           | 자기장(홀 효과) 측정, 기존 DeepCo IoT 서비스에는 없음 |
| 센서 | 인체감지 센서            | BS312                     | X                                  | O                 | EZMaker 전용           | 적외선 인체 감지(PIR), EZMaker 전용 센서 |
| 센서 | 수중/접촉온도 센서       | DS18B20                   | X                                  | O                 | EZMaker 전용           | 1-Wire 기반 온도 센서, 현재는 EZMaker 테스트 코드 기준 |
| 센서 | 무게센서                 | HX711                     | X                                  | O                 | EZMaker 전용           | 로드셀 + HX711 기반 무게 측정 모듈 |
| 센서 | 이산화탄소 센서          | SCD40                     | X                                  | O                 | EZMaker 전용           | I2C CO₂ 센서, 0~40,000 ppm 측정 |
| 센서 | 전류센서                 | INA219                    | X                                  | O                 | EZMaker 전용           | I2C 전류/전압 측정 센서 |
| 센서 | 기압센서                 | BMP280                    | X                                  | O                 | EZMaker 전용           | I2C 기압/온도 센서 |
| 센서 | 고온센서                 | MAX31850                  | X                                  | O                 | EZMaker 전용           | 써모커플 기반 고온 측정 센서 |
| 센서 | 스위치                   | -                         | X                                  | O                 | EZMaker 전용           | 단순 디지털 On/Off 입력, EZMaker 포트에 최적화 |
| 센서 | DIY-A / DIY-B (DIY 포트) | -                         | △ (아날로그 핀만 제공)            | O                 | EZMaker 설계 중심     | DeepCo에도 아날로그 핀은 있지만, EZMaker에서 “DIY 포트” 개념으로 명시·패키징 |

### 8.2 액츄에이터 비교

| 구분 | 기능/이름                    | 칩셋/모듈 (예시) | 기존 DeepCo 보드 IoT 서비스 (BLE) | EZMaker 센서 라인 | 관계 (중복/신규)     | 비고 |
| :--- | :-------------------------- | :--------------- | :--------------------------------: | :---------------: | :------------------- | :--- |
| 액츄에이터 | 피에조부저              | -                | O (`BUZZER` 특성)                  | O                 | 중복(DeepCo+EZMaker) | 딥코 보드 내장 부저 ↔ EZMaker 외장 부저 모듈, 동일 BUZZER 명령 체계 사용 가능 |
| 액츄에이터 | NeoPixel (LED/RING/BAR) | WS2812           | O (`NEOPIXEL` 특성)                | O                 | 중복(DeepCo+EZMaker) | 스트립/링/바 모두 WS2812 기반, 개수·모양만 다르고 BLE/명령 구조는 동일 |
| 액츄에이터 | 서보모터                | -                | O (`SERVO` 특성)                   | O                 | 중복(DeepCo+EZMaker) | 각도 제어 방식 동일, 커넥터만 듀폰 ↔ EZMaker 포트 차이 |
| 액츄에이터 | DC 모터                 | -                | O (`DCMOTOR` 특성)                 | O                 | 중복(DeepCo+EZMaker) | PWM 속도 제어, 하드웨어 드라이버/연결 방식만 쉴드 형태로 변경 |
| 액츄에이터 | 보드 LED / 외부 LED     | -                | O (`LED` 특성)                     | (전용 모듈 없음)  | DeepCo 전용         | 보드 내장/일반 LED 제어, EZMaker에는 별도 “LED 모듈”은 없고 DIY 포트로 직접 연결 |
| 액츄에이터 | 카메라 모듈             | CameraModule     | O (`CAM` 특성)                     | X                 | DeepCo 전용         | 카메라 스트리밍/촬영용, EZMaker 센서 리스트에는 포함되지 않음 |
| 액츄에이터 | 레이저 모듈             | -                | X                                  | O                 | EZMaker 전용        | 디지털 On/Off 제어, 향후 단순 BLE 명령으로 노출 예정 |
| 액츄에이터 | LCD (16×2 / 20×4)       | I2C LCD          | X (현재는 MicroPython 테스트만)    | O                 | EZMaker 전용(서비스) | `test_16x2_lcd_i2c_ezmaker.py` 등 테스트 코드 존재, IoT 서비스/블록 통합 대상 |

## 9. EZMaker 레이저 모듈 작업 정리

레이저 모듈은 **EZMaker 전용 디지털 액츄에이터**로, 다음 순서로 작업·검증했습니다.  
(**펌웨어 업그레이드 → 펌웨어 테스트 → JS 업그레이드 → 웹 테스트**)

### 9.1 펌웨어 업그레이드 (MicroPython / BLE)

- **대상 파일**
  - `source/lib/bleBaseIoT.py`
  - `source/lib/bleIoT.py`
- **주요 변경 사항**
  - `bleBaseIoT.py`
    - `SENSOR_SERVICE` 아래에 EZMaker 전용 레이저 모듈 특성 추가  
      - UUID: `22223333-4444-5555-6666-777788889001` (기존 DeepCo 센서와 구분되는 별도 대역)  
      - 특성 이름: `_LASER_CHAR` (Write + Notify, 필요 시 알림용으로도 사용 가능)
    - `BLEUART` 클래스에 레이저용 핸들/헨들러 추가  
      - `self._laser_handle` 등록 및 GATT 서비스 등록 튜플에 포함  
      - `self._laser_handler = None`, `set_laser_handler(self, fn)` 추가  
      - `laser_notify(self, data)` 추가 (웹으로 상태/응답 알림 전송용)  
      - `_irq_handler`에서 `_laser_handle`로 들어온 명령을 `self._laser_handler`로 디스패치
  - `bleIoT.py`
    - 전역 핀 관리 변수 추가  
      - `PIN_LASER` (레이저 모듈이 사용하는 GPIO 번호)  
      - `laser_pin` (`machine.Pin` 객체, 디지털 출력)
    - `update_pin_config(pin_type, pin_number, ...)` 에 `'laser'` 타입 분기 추가  
      - 기존 핀이 있으면 `deinit()` 후 새 `machine.Pin(pin_number, OUT)` 생성  
      - 초기값 `0`(OFF)로 설정
    - `laser_handler(conn_handle, cmd_str)` 구현  
      - `LASER:PIN:<핀번호>`: `update_pin_config('laser', <핀번호>)` 호출  
      - `LASER:ON`: `laser_pin.value(1)` 으로 ON, `uart.laser_notify("LASER:ON:OK")` 등 응답  
      - `LASER:OFF`: `laser_pin.value(0)` 으로 OFF, `uart.laser_notify("LASER:OFF:OK")` 등 응답  
      - 알 수 없는 명령은 에러 로그/응답 처리
    - 초기화 시 `uart.set_laser_handler(laser_handler)` 로 BLE → 레이저 핸들러 연결

### 9.2 펌웨어 테스트 (REPL 기반, D0(GPIO 21) 연결)

- **테스트 스크립트**
  - `firmwareTest/test_laser_ezmaker_D0_fw.py`
- **역할**
  - 펌웨어 전체를 수정·배포하지 않고, **보드 REPL에서 레이저 모듈만 단독 검증**하기 위한 스크립트
  - 테스트 대상 하드웨어: **EZMaker Shield D0 포트 ↔ GPIO 21에 연결된 레이저 모듈**
- **구조**
  - `import bleIoT`  
    - 보드 `/lib` 폴더에 배포된 `bleIoT.mpy`를 직접 사용 (PC 상의 `.py`를 실행하지 않음)
  - `configure_laser_pin_for_D0()`  
    - 내부적으로 `LASER:PIN:21` 명령을 사용하여 레이저 핀을 GPIO 21(D0)으로 설정
  - `simple_on_off_test()`  
    - 일정 간격으로 `LASER:ON` → `LASER:OFF` 를 반복하며 눈으로 On/Off 여부 확인
  - `main()`  
    - 위 두 함수를 순서대로 호출하는 진입점
- **사용 방법 요약**
  1. 최신 `bleIoT.mpy` / `bleBaseIoT.mpy` 및 `test_laser_ezmaker_D0_fw.py` 를 보드에 업로드  
     (모두 `/lib` 또는 적절한 위치에 배치)
  2. Thonny 등의 “파일 실행 버튼” 대신, **보드 REPL에서 직접 실행**  
     - `>>> import test_laser_ezmaker_D0_fw`  
     - `>>> test_laser_ezmaker_D0_fw.main()`  
  3. 레이저 모듈이 D0(GPIO 21)에서 켜졌다 꺼지는지 육안으로 확인
  4. 이후에는 웹/BLE 환경에서  
     - `LASER:PIN:21`  
     - `LASER:ON` / `LASER:OFF`  
     명령으로 동일한 동작을 재현

### 9.3 웹서비스 JS 업그레이드 (BLE 라이브러리 연동)

- **대상 파일**
  - `IoTmode/test/integratedBleLib_Camera.js`
- **BLE 특성 정의**
  - 상단 상수에 레이저 특성 추가  
    - `const LASER_CHARACTERISTIC = '22223333-4444-5555-6666-777788889001';`
  - `CHARACTERISTIC_UUIDS`에 `laser` 키 추가  
    - `laser: LASER_CHARACTERISTIC`
  - `SERVICE_CHARACTERISTICS[SENSOR_SERVICE]` 에 `LASER_CHARACTERISTIC` 포함  
    - 레이저 모듈을 **센서 서비스(SENSOR_SERVICE)** 아래에서 관리
  - `_getServiceUUIDForCharacteristic()` 의 `sensor_characteristics` 목록에 `LASER_CHARACTERISTIC` 추가  
    - 레이저 명령이 자동으로 `SENSOR_SERVICE`를 타도록 라우팅
  - `notifyNotSupported` 목록에 `LASER_CHARACTERISTIC` 추가  
    - 레이저는 기본적으로 **쓰기(write) 기반 제어용 특성**으로 취급 (필수 알림 없음)
- **Laser 클래스 추가**
  - `class Laser extends SensorBase`  
    - 생성자: `super('Laser', LASER_CHARACTERISTIC); this.state = "unknown";`
    - `getState()` : `"on" / "off" / "unknown"` 상태 반환
    - `async turnOn()` : `"LASER:ON"` 명령 전송 후 상태를 `"on"` 으로 갱신  
    - `async turnOff()` : `"LASER:OFF"` 명령 전송 후 상태를 `"off"` 로 갱신  
    - `async setPin(pin)` : `"LASER:PIN:<pin>"` 명령으로 핀 설정 (예: D0 → 21)  
    - `_processData(data)` : `"LASER:ON"`, `"LASER:OFF"` 응답 문자열을 파싱해 `state` 보정
  - 전역 노출
    - `window.LASER_CHARACTERISTIC = LASER_CHARACTERISTIC;`
    - `window.Laser = Laser;`

### 9.4 웹 테스트 페이지 (블록코드 스타일의 최소 테스트 UI)

- **대상 파일**
  - `IoTmode/test/test_laser.html`
- **구성**
  - 별도 CSS/JS 파일 없이, **한 파일 안에 HTML + 최소 스타일 + 스크립트** 포함
  - UI 요소
    - `블루투스 연결` 버튼  
    - `레이저 켜기` 버튼  
    - `레이저 끄기` 버튼  
    - 간단한 로그 영역 (`<div id="log">`)
- **동작 흐름 (블록코드 스타일에 맞춘 구조)**
  - 스크립트 상단에서  
    - `let bleManager = null;`  
    - `let laser = null;`  
    전역 변수 선언
  - `window.addEventListener('load', ...)` 안에서
    - `bleManager = BLEManager.getInstance();`  
    - `bleManager.init();`  
    - `laser = new Laser();`  
    로 **블록 코드에서 쓰일 전역 객체를 초기화** (`let laser = new Laser();` 패턴)
    - 버튼 이벤트 핸들러 등록
  - `handleConnect()`  
    - `await bleManager.connect();` 로 IoT 모드 BLE 연결  
    - 연결 후 `await laser.setPin(21);` 로 레이저 핀을 **D0(GPIO 21)** 에 매핑  
    - 이후 `레이저 켜기/끄기` 버튼 활성화
  - `handleLaserOn()` / `handleLaserOff()`  
    - 각각 `laser.turnOn()`, `laser.turnOff()` 호출  
    - 성공/실패 메시지를 로그 영역에 출력

이 흐름을 기준으로, 향후 다른 EZMaker 액츄에이터(네오픽셀, DC 모터 등)도  
**“펌웨어 → 펌웨어 테스트 → JS 라이브러리 → 전용 테스트 페이지/블록”** 패턴으로 확장할 예정입니다.

## 10. EZMaker 자이로센서(ICM20948) 작업 정리

EZMaker 자이로센서는 **ICM20948 기반 9축 센서**로, 기존 DeepCo 보드에서 사용하던 ADXL345/MPU 계열과 **완전히 분리된 EZMaker 전용 자이로**로 취급합니다.  
BLE 레벨에서도 공통 `GYRO` 특성과 다른 **전용 캐릭터리스틱/명령**을 사용합니다.

### 10.1 펌웨어 업그레이드 (MicroPython / BLE)

- **대상 파일**
  - `source/lib/icm20948.py`
  - `source/lib/bleBaseIoT.py`
  - `source/lib/bleIoT.py`

- **`icm20948.py` (드라이버)**
  - SoftI2C 기반 ICM20948 9축 센서 드라이버
    - I2C 연결: SCL = D5(GPIO 40), SDA = D6(GPIO 41)
    - 주소: 0x68 (기본), 필요 시 0x69도 지원
  - 제공 기능:
    - `read_accel_gyro()`로 가속도/자이로/온도 값 읽기  
    - `calculate_rpy(accel)`로 Roll/Pitch 계산

- **`bleBaseIoT.py` (BLE 특성)**
  - 기존 공통 자이로(`_GYRO_CHAR`, UUID `1111...894`)와 별도로 **EZMaker 전용 자이로 특성** 추가
    - UUID: `22223333-4444-5555-6666-777788889002`
    - 특성 이름: `_EZ_GYRO_CHAR` (Write + Notify)
  - `SENSOR_SERVICE`에 `_EZ_GYRO_CHAR` 포함
  - `BLEUART`에 EZ 자이로용 핸들/핸들러/notify 추가
    - 핸들: `self._ez_gyro_handle`
    - 핸들러 설정: `set_ez_gyro_handler(self, fn)`
    - 알림: `ez_gyro_notify(self, data)`  
      → JS/Web 쪽에서 EZMaker 전용 자이로 값을 받는 통로
  - `_irq_handler`에서 EZ-GYRO 특성에 대한 쓰기 이벤트를 `self._ez_gyro_handler` 로 디스패치
    - 공통 GYRO(`GYRO:...`)와 EZGYRO(`EZGYRO:...`) 명령이 서로 섞이지 않도록 분리

- **`bleIoT.py` (명령 처리 로직)**
  - 전역 핀/객체를 **공통 자이로 / EZMaker 자이로**로 분리
    - 공통:
      - `PIN_GYRO_SDA`, `PIN_GYRO_SCL`, `gyro_i2c`, `gyro_sensor` (ADXL345)
    - EZMaker:
      - `PIN_EZ_GYRO_SDA`, `PIN_EZ_GYRO_SCL`, `ez_gyro_i2c`, `ez_gyro_sensor` (ICM20948)
  - `update_pin_config`에 EZMaker 자이로 타입 추가
    - `pin_type == 'ezgyro'` 분기
      - SoftI2C 기반으로 ICM20948 초기화 (`SoftI2C(scl=GPIO40, sda=GPIO41)` 등)
      - I2C 스캔 후 0x68 또는 0x69 주소 탐색
      - 성공 시 `ez_gyro_sensor = ICM20948(ez_gyro_i2c, addr)` 생성
  - EZMaker 자이로 전용 핸들러 `ez_gyro_handler(conn_handle, cmd_str)` 추가
    - 명령어:
      - `EZGYRO:PIN:SDA,SCL`
        - `update_pin_config('ezgyro', SDA, SCL)` 호출
        - 성공 시 `EZGYRO:PIN:OK:SDA,SCL` 알림 (`uart.ez_gyro_notify(...)`)
      - `EZGYRO:STATUS`
        - `ez_gyro_sensor.read_accel_gyro()` 로 가속도/자이로/온도 값 읽기
        - `calculate_rpy(...)` 로 Roll/Pitch 계산
        - BLE로 전송되는 문자열 포맷 (한 줄, 키=값):
          - `EZGYRO:AX=...,AY=...,AZ=...,GX=...,GY=...,GZ=...,ROLL=...,PITCH=...,TEMP=...`
        - `uart.ez_gyro_notify(...)` 를 통해 웹/블록에 전달
    - 마지막에 핸들러 등록:
      - `uart.set_gyro_handler(gyro_handler)`      → 기존 DeepCo 공통 자이로용
      - `uart.set_ez_gyro_handler(ez_gyro_handler)` → EZMaker ICM20948 전용

### 10.2 펌웨어 테스트 (REPL / 단위 테스트 코드)

- **기존 테스트 코드**
  - `test/test_GYRO_icm20948_ezmaker.py`
  - SoftI2C + `ICM20948` 드라이버를 직접 사용하여:
    - I2C 스캔 (`i2c.scan()`)
    - 장치 주소 확인 (0x68 또는 0x69)
    - `read_accel_gyro()` / `calculate_rpy()` 호출
    - 가속도, 자이로(dps), Roll/Pitch, 온도 값을 REPL 콘솔에 출력
- **역할**
  - BLE/웹과 독립적으로, **EZMaker ICM20948 센서 자체가 정상 동작하는지**를 확인
  - 핀맵(D5=GPIO40, D6=GPIO41)과 I2C 주소가 맞는지 검증

### 10.3 웹서비스 / 블록코딩 측 연동

- **BLE 라이브러리 (`IoTmode/test/integratedBleLib_Camera.js`)**
  - EZMaker 전용 자이로용 UUID/클래스 실제 구현
    - `const EZ_GYRO_CHARACTERISTIC = '22223333-4444-5555-6666-777788889002';`
    - `class EzGyroSensor extends SensorBase { ... }`
    - `_processData()` 에서  
      `EZGYRO:AX=...,AY=...,AZ=...,GX=...,GY=...,GZ=...,ROLL=...,PITCH=...,TEMP=...` 포맷을 파싱하여  
      `ax, ay, az, gx, gy, gz, roll, pitch, temp` 멤버 변수에 저장
  - 전역 노출:
    - `window.EZ_GYRO_CHARACTERISTIC`
    - `window.EzGyroSensor`
    - `window.getValidEzGyroValue` (Promise 기반 헬퍼)

- **블록코드 정의 (`IoTmode/test/DeepcoIoT_block_v1.6.xlsx` / `EZMaker_블록코드정의.md`)**
  - 기존 공통 자이로 블록과 **구분되는 EZGYRO 블록** 설계
    - 핀 설정: `EZ자이로센서 핀(SDA핀, SCL핀)으로 초기화 하기`  
      → `let ezGyroSensor = new EzGyroSensor(); ezGyroSensor.setPin(sdaPin, sclPin)...`
    - 값 읽기: `EZ자이로센서에서 (ax,ay,az,gx,gy,gz,roll,pitch,temp) 값 가져오기`  
      → `let ezGyroData = await getValidEzGyroValue(ezGyroSensor);`

- **전용 테스트 페이지 (`IoTmode/test/test_ezgyro.html`)**
  - 다른 센서와 같은 구조:
    - `블루투스 연결` → `EZGYRO:PIN:41,40` 전송 (SDA=41(D6), SCL=40(D5))
    - `자이로값 읽기` 버튼 → `EZGYRO:STATUS` 전송,  
      응답으로 받은 `AX,AY,AZ,GX,GY,GZ,ROLL,PITCH,TEMP` 를 표 형태로 화면에 표시

이 섹션을 기준으로, 향후에는 **EZMaker 전용 센서(ICM20948, SCD40, INA219 등)** 들도  
공통 센서와 분리된 UUID/명령/블록 구조로 정리해 나갈 예정입니다.


