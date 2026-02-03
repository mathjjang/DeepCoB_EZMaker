# 딥코보드 vs 이지메이커 센서 구조 분석

## 1. 핵심 구조 차이

### 1.1 딥코보드 자체 (내장 센서/액츄에이터)

**특징**: 보드에 **물리적으로 고정 연결** (납땜/내장)

| 항목 | GPIO | 특징 |
|------|------|------|
| **버저** | 42 (고정) | 보드 내장, `PIN_BUZZER = const(42)` |
| **BLE 상태 LED** | 46 (고정) | 보드 내장, `PIN_BLE_STATUS_LED = const(46)` |
| **카메라** | (I2C/전용 인터페이스) | ESP32-S3 내장 카메라 인터페이스 사용 |

> **중요**: 이들은 **핀 설정 명령이 불필요**하며, BLE 명령도 `BUZ:BEEP`, `CAM:STREAM:ON` 등 핀 없이 직접 제어

---

### 1.2 딥코보드용 듀폰 센서 (외부 연결, 핀 동적 설정)

**특징**: 듀폰 케이블로 **자유롭게 연결**, **핀 설정 명령 필요**

| 센서 | BLE 특성 UUID | 명령 예시 | 핀 설정 |
|------|---------------|-----------|---------|
| LED | `...8889` | `LED:PIN:21`, `LED:ON` | 동적 |
| 초음파 | `...888B` | `ULTRA:PIN:TRIG,ECHO`, `ULTRA:READ` | 동적 (2핀) |
| 온습도(DHT) | `...888D` | `DHT:PIN:21`, `DHT:STATUS` | 동적 |
| 서보모터 | `...888E` | `SERVO:PIN:48`, `SERVO:90` | 동적 |
| 네오픽셀 | `...888F` | `NEO:PIN:47,4`, `NEO:ALL:255,0,0` | 동적 (핀+개수) |
| 터치센서 | `...8890` | `TOUCH:PIN:48`, `TOUCH:STATUS` | 동적 |
| 조도센서 | `...8891` | `LIGHT:PIN:2`, `LIGHT:STATUS` | 동적 |
| 자이로(ADXL345) | `...8894` | `GYRO:PIN:SDA,SCL`, `GYRO:STATUS` | 동적 (I2C) |
| 먼지센서 | `...8895` | `DUST:PIN:2`, `DUST:STATUS` | 동적 |
| DC모터 | `...8896` | `MOTOR:PIN:39`, `MOTOR:SPEED:50` | 동적 |

> **공통점**: 모두 `1111...888x` UUID 대역, `PREFIX:PIN:...` 명령으로 핀 설정 후 사용

---

### 1.3 이지메이커 쉴드 + 전용 센서 (포트 기반, 핀 동적 설정)

**특징**: 4핀 커넥터로 **D0~D13, A0~A4 포트에 연결**, **핀 설정 필수**, **`EZ` 접두사 사용**

| 센서 | BLE 특성 UUID | 명령 예시 | 핀 설정 | 비고 |
|------|---------------|-----------|---------|------|
| **EZ레이저** | `2222...9001` | `LASER:PIN:21`, `LASER:ON` | D0~D4 | 디지털 |
| **EZ자이로(ICM20948)** | `2222...9002` | `EZGYRO:PIN:41,40`, `EZGYRO:STATUS` | D6(SDA), D5(SCL) | I2C |
| **EZ기압(BMP280)** | `2222...9003` | `EZPRESS:PIN:41,40`, `EZPRESS:STATUS` | D6(SDA), D5(SCL) | I2C |
| **EZCO2(SCD40)** | `2222...9004` | `EZCO2:PIN:41,40`, `EZCO2:STATUS` | D6(SDA), D5(SCL) | I2C |
| **EZDIY-A** | `2222...9005` | `DIYA:PIN:2`, `DIYA:STATUS` | A0~A4 | 아날로그 |
| **EZDIY-B** | `2222...9006` | `DIYB:PIN:1`, `DIYB:STATUS` | A0~A4 | 아날로그 |
| **EZ자기장(Hall)** | `2222...9007` | `HALL:PIN:2`, `HALL:STATUS` | A0~A4 | 아날로그 |
| **EZ밝기** | `2222...9008` | `EZLIGHT:PIN:2`, `EZLIGHT:STATUS` | A0~A4 | 아날로그 |
| **EZ전압** | `2222...9009` | `EZVOLT:PIN:3`, `EZVOLT:STATUS` | A0~A4 | 아날로그 |
| **EZ전류(INA219)** | `2222...900A` | `EZCURR:PIN:41,40`, `EZCURR:STATUS` | D6(SDA), D5(SCL) | I2C |
| **EZ온도(DS18B20)** | `2222...900B` | `EZTHERMAL:PIN:47`, `EZTHERMAL:STATUS` | D0~D4 | 1-Wire |
| **EZ소리** | `2222...900C` | `EZSOUND:PIN:2`, `EZSOUND:STATUS` | A0~A4 | 아날로그 |
| **EZ무게(HX711)** | `2222...900D` | `EZWEIGHT:PIN:42,14`, `EZWEIGHT:STATUS` | D11(DOUT), D10(SCK) | UART |
| **EZ먼지(PMS7003M)** | `2222...900E` | `EZDUST:PIN:14,42`, `EZDUST:STATUS` | D10(RX), D11(TX) | UART |
| **EZ인체감지(PIR)** | `2222...900F` | `HUMAN:PIN:47`, `HUMAN:STATUS` | D0~D4 | 디지털 |
| **EZLCD(16x2/20x4)** | `2222...9010` | `LCD:INIT:16X2:40,41`, `LCD:PRINT:0,0:Hello` | D5(SCL), D6(SDA) | I2C |

> **특징**:
> - **UUID 대역 분리**: `2222...9xxx` (EZMaker 전용)
> - **명령 접두사**: `EZ` 또는 센서명 (예: `EZGYRO`, `EZCO2`, `LASER`, `HUMAN`)
> - **포트 기반**: 학생이 D0~D13, A0~A4 포트에 자유롭게 연결 후 **핀 설정 명령으로 매핑**
> - **MicroPython 구현**: `PIN_LASER`, `PIN_EZGYRO_SDA/SCL` 등 모두 `None`으로 초기화 → 동적 설정

---

## 2. BLE UUID 체계 정리

### 2.1 MicroPython 현재 구조

```python
# bleBaseIoT.py

# ============================================================================
# 1) IoT Service (LED/CAM/REPL/UPGRADE)
# ============================================================================
_LED_CAM_UUID = "11112222-3333-4444-5555-666677778888"

_LED_CHAR     = "11112222-3333-4444-5555-666677778889"  # Write
_CAM_CHAR     = "11112222-3333-4444-5555-66667777888A"  # Write+Notify
_REPL_CHAR    = "11112222-3333-4444-5555-666677778893"  # Write+Notify
_UPGRADE_CHAR = "11112222-3333-4444-5555-666677778898"  # Write+Notify

# ============================================================================
# 2) Sensor Service (DeepCo 공통 + 일부 EZMaker)
# ============================================================================
_SENSOR_UUID = "11112222-3333-4444-5555-66667777888C"

# DeepCo 공통 센서/액츄에이터 (동적 핀)
_ULTRA_CHAR   = "11112222-3333-4444-5555-66667777888B"  # Write+Notify
_DHT_CHAR     = "11112222-3333-4444-5555-66667777888D"  # Write+Notify
_SERVO_CHAR   = "11112222-3333-4444-5555-66667777888E"  # Write
_NEO_CHAR     = "11112222-3333-4444-5555-66667777888F"  # Write
_TOUCH_CHAR   = "11112222-3333-4444-5555-666677778890"  # Write+Notify
_LIGHT_CHAR   = "11112222-3333-4444-5555-666677778891"  # Write+Notify
_BUZZER_CHAR  = "11112222-3333-4444-5555-666677778892"  # Write+Notify (고정핀이지만 여기 포함)
_GYRO_CHAR    = "11112222-3333-4444-5555-666677778894"  # Write+Notify (ADXL345)
_DUST_CHAR    = "11112222-3333-4444-5555-666677778895"  # Write+Notify
_DCMOTOR_CHAR = "11112222-3333-4444-5555-666677778896"  # Write

# EZMaker 전용 센서 (동적 핀, 별도 UUID 대역)
_EZ_LASER_CHAR   = "22223333-4444-5555-6666-777788889001"  # Write+Notify
_EZ_GYRO_CHAR    = "22223333-4444-5555-6666-777788889002"  # Write+Notify (ICM20948)
_EZ_PRESS_CHAR   = "22223333-4444-5555-6666-777788889003"  # Write+Notify (BMP280)
_EZ_CO2_CHAR     = "22223333-4444-5555-6666-777788889004"  # Write+Notify (SCD40)
_EZ_DIYA_CHAR    = "22223333-4444-5555-6666-777788889005"  # Write+Notify
_EZ_DIYB_CHAR    = "22223333-4444-5555-6666-777788889006"  # Write+Notify
_EZ_HALL_CHAR    = "22223333-4444-5555-6666-777788889007"  # Write+Notify
_EZ_LIGHT_CHAR   = "22223333-4444-5555-6666-777788889008"  # Write+Notify
_EZ_VOLT_CHAR    = "22223333-4444-5555-6666-777788889009"  # Write+Notify
_EZ_CURR_CHAR    = "22223333-4444-5555-6666-77778888900A"  # Write+Notify (INA219)
_EZ_THERMAL_CHAR = "22223333-4444-5555-6666-77778888900B"  # Write+Notify (DS18B20)
_EZ_SOUND_CHAR   = "22223333-4444-5555-6666-77778888900C"  # Write+Notify
_EZ_WEIGHT_CHAR  = "22223333-4444-5555-6666-77778888900D"  # Write+Notify (HX711)
_EZ_DUST_CHAR    = "22223333-4444-5555-6666-77778888900E"  # Write+Notify (PMS7003M)
_EZ_HUMAN_CHAR   = "22223333-4444-5555-6666-77778888900F"  # Write+Notify (PIR)
_EZ_LCD_CHAR     = "22223333-4444-5555-6666-777788889010"  # Write+Notify (I2C LCD)
```

### 2.2 명명 규칙 요약

| 분류 | UUID 대역 | 명령 접두사 | 예시 |
|------|-----------|-------------|------|
| **딥코보드 고정 핀** | `1111...888x` | `BUZ`, `CAM` | `BUZ:BEEP`, `CAM:STREAM:ON` |
| **딥코보드 동적 핀** | `1111...888x` | `LED`, `DHT`, `GYRO`, `ULTRA`, `SERVO`, `NEO`, `TOUCH`, `LIGHT`, `DUST`, `MOTOR` | `DHT:PIN:21`, `GYRO:PIN:41,40` |
| **이지메이커 전용** | `2222...9xxx` | `EZ` 접두사 또는 고유명 | `EZGYRO:PIN:41,40`, `LASER:PIN:21`, `HUMAN:PIN:47` |

---

## 3. Arduino 전환 시 UUID 설계 전략

### 3.1 옵션 A: MicroPython 구조 유지 (하위 호환 중심)

**장점**: 기존 웹/블록 코드 재사용 가능
**단점**: 
- 고정 핀 센서(BUZ, CAM)와 동적 핀 센서가 같은 서비스에 혼재
- EZMaker 센서가 여전히 Sensor Service에 묶임

```cpp
// Arduino에서도 동일한 UUID 사용
#define IOT_SERVICE_UUID        "11112222-3333-4444-5555-666677778888"
#define SENSOR_SERVICE_UUID     "11112222-3333-4444-5555-66667777888C"

#define CAM_CHAR_UUID           "11112222-3333-4444-5555-66667777888A"
#define BUZZER_CHAR_UUID        "11112222-3333-4444-5555-666677778892"
#define EZGYRO_CHAR_UUID        "22223333-4444-5555-6666-777788889002"
// ... (나머지 동일)
```

---

### 3.2 옵션 B: 서비스 재구성 (최적화 중심) ✅ **추천**

**목표**: 
1. **고정 핀 센서**는 별도 서비스 (IoT Service)
2. **동적 핀 센서**는 기능별 서비스로 분리
3. **EZMaker 전용 센서**는 독립 서비스

#### 서비스 구조

```cpp
// ============================================================================
// 1) IoT Service (고정 핀 센서/액츄에이터)
// ============================================================================
#define IOT_SERVICE_UUID           "11112222-3333-4444-5555-666677778888"

#define BUZZER_CHAR_UUID           "11112222-3333-4444-5555-666677778892"  // Write+Notify
#define BLE_STATUS_LED_CHAR_UUID   "11112222-3333-4444-5555-666677778897"  // Write (system)

// ============================================================================
// 2) Camera Service (카메라 전용, 바이너리 최적화)
// ============================================================================
#define CAMERA_SERVICE_UUID        "CAFE0000-1111-2222-3333-444455556666"

#define CAM_TX_CHAR_UUID           "CAFE0001-1111-2222-3333-444455556666"  // Notify (바이너리 프레임)
#define CAM_RX_CHAR_UUID           "CAFE0002-1111-2222-3333-444455556666"  // Write (제어 명령)
#define CAM_STATUS_CHAR_UUID       "CAFE0003-1111-2222-3333-444455556666"  // Read+Notify (상태)

// ============================================================================
// 3) DeepCo Sensor Service (듀폰 센서, 동적 핀)
// ============================================================================
#define DEEPCO_SENSOR_SERVICE_UUID "11112222-3333-4444-5555-66667777888C"

#define LED_CHAR_UUID              "11112222-3333-4444-5555-666677778889"  // Write
#define ULTRA_CHAR_UUID            "11112222-3333-4444-5555-66667777888B"  // Write+Notify
#define DHT_CHAR_UUID              "11112222-3333-4444-5555-66667777888D"  // Write+Notify
#define SERVO_CHAR_UUID            "11112222-3333-4444-5555-66667777888E"  // Write
#define NEO_CHAR_UUID              "11112222-3333-4444-5555-66667777888F"  // Write
#define TOUCH_CHAR_UUID            "11112222-3333-4444-5555-666677778890"  // Write+Notify
#define LIGHT_CHAR_UUID            "11112222-3333-4444-5555-666677778891"  // Write+Notify
#define GYRO_CHAR_UUID             "11112222-3333-4444-5555-666677778894"  // Write+Notify (ADXL345)
#define DUST_CHAR_UUID             "11112222-3333-4444-5555-666677778895"  // Write+Notify
#define DCMOTOR_CHAR_UUID          "11112222-3333-4444-5555-666677778896"  // Write

// ============================================================================
// 4) EZMaker Service (이지메이커 쉴드 전용, 동적 핀)
// ============================================================================
#define EZMAKER_SERVICE_UUID       "22223333-4444-5555-6666-777788889000"

#define EZ_LASER_CHAR_UUID         "22223333-4444-5555-6666-777788889001"  // Write+Notify
#define EZ_GYRO_CHAR_UUID          "22223333-4444-5555-6666-777788889002"  // Write+Notify (ICM20948)
#define EZ_PRESS_CHAR_UUID         "22223333-4444-5555-6666-777788889003"  // Write+Notify (BMP280)
#define EZ_CO2_CHAR_UUID           "22223333-4444-5555-6666-777788889004"  // Write+Notify (SCD40)
#define EZ_DIYA_CHAR_UUID          "22223333-4444-5555-6666-777788889005"  // Write+Notify
#define EZ_DIYB_CHAR_UUID          "22223333-4444-5555-6666-777788889006"  // Write+Notify
#define EZ_HALL_CHAR_UUID          "22223333-4444-5555-6666-777788889007"  // Write+Notify
#define EZ_LIGHT_CHAR_UUID         "22223333-4444-5555-6666-777788889008"  // Write+Notify
#define EZ_VOLT_CHAR_UUID          "22223333-4444-5555-6666-777788889009"  // Write+Notify
#define EZ_CURR_CHAR_UUID          "22223333-4444-5555-6666-77778888900A"  // Write+Notify (INA219)
#define EZ_THERMAL_CHAR_UUID       "22223333-4444-5555-6666-77778888900B"  // Write+Notify (DS18B20)
#define EZ_SOUND_CHAR_UUID         "22223333-4444-5555-6666-77778888900C"  // Write+Notify
#define EZ_WEIGHT_CHAR_UUID        "22223333-4444-5555-6666-77778888900D"  // Write+Notify (HX711)
#define EZ_DUST_CHAR_UUID          "22223333-4444-5555-6666-77778888900E"  // Write+Notify (PMS7003M)
#define EZ_HUMAN_CHAR_UUID         "22223333-4444-5555-6666-77778888900F"  // Write+Notify (PIR)
#define EZ_LCD_CHAR_UUID           "22223333-4444-5555-6666-777788889010"  // Write+Notify (I2C LCD)
```

#### 제거 대상 (Arduino에서 불필요)

```cpp
// REPL Service - MicroPython 인터프리터 전용, Arduino에서 불필요
// _REPL_CHAR = "11112222-3333-4444-5555-666677778893"

// UPGRADE CHAR - Arduino OTA 표준 사용
// _UPGRADE_CHAR = "11112222-3333-4444-5555-666677778898"
```

---

## 4. 핀 설정 명령 규칙

### 4.1 고정 핀 센서 (핀 설정 불필요)

```
BUZ:BEEP:1000,500        → GPIO 42 고정
BUZ:PLAY:MELODY1
CAM:STREAM:ON            → 카메라 인터페이스 고정
CAM:SNAP
```

### 4.2 동적 핀 센서 (핀 설정 필수)

#### 단일 핀 (디지털/아날로그)

```
LED:PIN:21               → D0(GPIO 21)에 LED 연결
LASER:PIN:21             → D0(GPIO 21)에 레이저 연결
DHT:PIN:47               → D1(GPIO 47)에 DHT 연결
TOUCH:PIN:48             → D2(GPIO 48)에 터치센서 연결
EZLIGHT:PIN:2            → A0(GPIO 2)에 밝기센서 연결
HALL:PIN:3               → A2(GPIO 3)에 자기장센서 연결
HUMAN:PIN:47             → D1(GPIO 47)에 인체감지센서 연결
EZTHERMAL:PIN:47         → D1(GPIO 47)에 DS18B20 연결
```

#### 2핀 (I2C, UART, HX711 등)

```
GYRO:PIN:41,40           → SDA=41(D6), SCL=40(D5)
EZGYRO:PIN:41,40         → ICM20948, SDA=41, SCL=40
EZPRESS:PIN:41,40        → BMP280, SDA=41, SCL=40
EZCO2:PIN:41,40          → SCD40, SDA=41, SCL=40
EZCURR:PIN:41,40         → INA219, SDA=41, SCL=40
LCD:INIT:16X2:40,41      → SCL=40, SDA=41 (순서 주의!)
EZDUST:PIN:14,42         → RX=14, TX=42
EZWEIGHT:PIN:42,14       → DOUT=42, SCK=14
ULTRA:PIN:21,47          → TRIG=21, ECHO=47
```

#### 핀+개수 (NeoPixel)

```
NEO:PIN:47,4             → D1(GPIO 47), 4개 LED
NEO:PIN:21,7             → D0(GPIO 21), 7개 LED
```

---

## 5. Arduino 전환 시 권장 사항

### 5.1 UUID 관리

**`arduino/DeepCoB_Ezmaker_v1.3.7/ble_uuids.h` 생성**

```cpp
#ifndef BLE_UUIDS_H
#define BLE_UUIDS_H

// IoT Service (고정 핀)
#define IOT_SERVICE_UUID        "11112222-3333-4444-5555-666677778888"
#define BUZZER_CHAR_UUID        "11112222-3333-4444-5555-666677778892"

// Camera Service (카메라 전용)
#define CAMERA_SERVICE_UUID     "CAFE0000-1111-2222-3333-444455556666"
#define CAM_TX_CHAR_UUID        "CAFE0001-1111-2222-3333-444455556666"
#define CAM_RX_CHAR_UUID        "CAFE0002-1111-2222-3333-444455556666"
#define CAM_STATUS_CHAR_UUID    "CAFE0003-1111-2222-3333-444455556666"

// DeepCo Sensor Service (듀폰 센서)
#define DEEPCO_SENSOR_SERVICE_UUID "11112222-3333-4444-5555-66667777888C"
// ... (나머지 듀폰 센서)

// EZMaker Service (쉴드 전용)
#define EZMAKER_SERVICE_UUID    "22223333-4444-5555-6666-777788889000"
// ... (나머지 EZ 센서)

#endif // BLE_UUIDS_H
```

### 5.2 JS 라이브러리 대응

`arduino/integratedBleLib_Camera.js`에서:

```javascript
// 서비스 UUID
const IOT_SERVICE = '11112222-3333-4444-5555-666677778888';
const CAMERA_SERVICE = 'cafe0000-1111-2222-3333-444455556666';
const DEEPCO_SENSOR_SERVICE = '11112222-3333-4444-5555-66667777888c';
const EZMAKER_SERVICE = '22223333-4444-5555-6666-777788889000';

// 특성 UUID (서비스별 분류)
const CHARACTERISTIC_UUIDS = {
    // IoT (고정 핀)
    buzzer: '11112222-3333-4444-5555-666677778892',
    
    // Camera (전용)
    cameraT x: 'cafe0001-1111-2222-3333-444455556666',
    cameraRx: 'cafe0002-1111-2222-3333-444455556666',
    cameraStatus: 'cafe0003-1111-2222-3333-444455556666',
    
    // DeepCo 센서 (동적 핀)
    led: '11112222-3333-4444-5555-666677778889',
    ultra: '11112222-3333-4444-5555-66667777888b',
    dht: '11112222-3333-4444-5555-66667777888d',
    // ...
    
    // EZMaker 센서 (동적 핀)
    ezLaser: '22223333-4444-5555-6666-777788889001',
    ezGyro: '22223333-4444-5555-6666-777788889002',
    ezPress: '22223333-4444-5555-6666-777788889003',
    ezCo2: '22223333-4444-5555-6666-777788889004',
    // ...
};
```

---

## 6. 결론

### 핵심 정리

1. **딥코보드 고정 핀** (2개): 버저(GPIO 42), BLE LED(GPIO 46)
   - 핀 설정 불필요, 명령만 전송 (`BUZ:BEEP`, `CAM:STREAM:ON`)

2. **딥코보드 동적 핀** (듀폰 센서): LED, DHT, GYRO, ULTRA, SERVO, NEO, TOUCH, LIGHT, DUST, MOTOR
   - UUID: `1111...888x` 대역
   - 핀 설정 필수 (`DHT:PIN:21`, `GYRO:PIN:41,40`)

3. **이지메이커 쉴드 전용** (포트 기반): 모든 EZ 센서
   - UUID: `2222...9xxx` 대역
   - 명령 접두사: `EZ` 또는 고유명 (`EZGYRO`, `LASER`, `HUMAN`)
   - 핀 설정 필수 (`EZGYRO:PIN:41,40`, `LASER:PIN:21`)

### Arduino 전환 시 권장 전략

- **카메라 Service**: 전용 UUID (`CAFE...`) + 바이너리 프로토콜
- **REPL/UPGRADE**: 제거 (Arduino에서 불필요)
- **EZ 센서**: `2222...9xxx` 대역 유지, 명명 규칙 준수
- **고정/동적 핀 명확히 분리**: 코드 가독성/유지보수성 향상
