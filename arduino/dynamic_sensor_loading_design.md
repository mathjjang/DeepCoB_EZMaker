# 동적 센서 로딩 설계 (Arduino)

## 문제 정의

MicroPython 펌웨어는 **동적 로딩 방식**을 사용:
- 부팅 시 센서 객체들이 `None`으로 초기화
- 사용자가 `DHT:PIN:10` 같은 명령을 보낼 때 센서 초기화
- 메모리 효율적 (20+ 센서를 모두 메모리에 로드하지 않음)
- 사용하지 않는 센서는 초기화하지 않음

Arduino에서도 **동일한 방식을 구현**해야 합니다.

---

## 현재 Arduino 설계의 문제

```cpp
// BleServer.cpp - 현재 방식 (❌)
bool BleServer::begin() {
    setupCameraService();    // 항상 로드
    setupIoTService();       // 항상 로드
    setupDeepCoService();    // 항상 로드
    setupEZMakerService();   // 항상 로드
    // 🚨 모든 서비스가 부팅 시 초기화됨
    // 🚨 사용하지 않는 센서도 메모리 점유
}
```

---

## 올바른 설계 방향

### 1. BLE 서비스는 부팅 시 등록 (OK)

BLE 서비스 자체는 부팅 시 등록해도 됩니다. 이것은 단순히 GATT 테이블 등록일 뿐입니다.

```cpp
// BLE 서비스/특성 등록 (메모리 부담 낮음)
setupCameraService();    // ✅ GATT 테이블에 등록만
setupIoTService();       // ✅ GATT 테이블에 등록만
```

### 2. 센서 객체는 명령 받을 때 초기화 (IMPORTANT!)

센서 드라이버와 하드웨어 초기화는 **PIN 명령 받을 때** 수행합니다.

```cpp
// ============================================================================
// SensorManager.h - 동적 센서 관리자
// ============================================================================

class SensorManager {
private:
    // 센서 포인터 (초기값: nullptr)
    DHTSensor* dhtSensor = nullptr;
    UltrasonicSensor* ultraSensor = nullptr;
    GyroSensor* gyroSensor = nullptr;
    ServoMotor* servo1 = nullptr;
    ServoMotor* servo2 = nullptr;
    // ... 20+ 센서들

public:
    // PIN 명령 받을 때 초기화
    bool initDHT(uint8_t pin) {
        if (dhtSensor != nullptr) {
            delete dhtSensor;  // 기존 센서 해제
        }
        dhtSensor = new DHTSensor(pin);
        return dhtSensor->begin();
    }

    // 센서 읽기 (초기화 체크)
    bool readDHT(float& temp, float& humi) {
        if (dhtSensor == nullptr) {
            Serial.println("[DHT] Sensor not configured");
            return false;
        }
        return dhtSensor->read(temp, humi);
    }

    // 센서 해제
    void deinitDHT() {
        if (dhtSensor != nullptr) {
            delete dhtSensor;
            dhtSensor = nullptr;
        }
    }
};
```

### 3. 명령 파서에서 동적 초기화

```cpp
// BleCommandParser.cpp
void BleCommandParser::handleSensorCommand(const char* cmd) {
    if (startsWith(cmd, "DHT:PIN:")) {
        // "DHT:PIN:10" -> 핀 10에 DHT 센서 초기화
        uint8_t pin = parsePin(cmd + 8);
        if (sensorManager->initDHT(pin)) {
            sendResponse("DHT:PIN:OK");
        } else {
            sendResponse("DHT:PIN:ERROR");
        }
    }
    else if (startsWith(cmd, "DHT:READ")) {
        // DHT 센서 읽기
        float temp, humi;
        if (sensorManager->readDHT(temp, humi)) {
            char resp[64];
            snprintf(resp, sizeof(resp), "DHT:%.1f,%.1f", temp, humi);
            sendResponse(resp);
        } else {
            sendResponse("DHT:ERROR:Not configured");
        }
    }
}
```

---

## 동작 흐름 비교

### MicroPython (기존)

```
1. 부팅
   └─> dht_sensor = None

2. 블록 코드: dhtSensor.setPin(10)
   └─> BLE: "DHT:PIN:10"
   └─> update_pin_config('dht', 10)
   └─> dht_sensor = dht.DHT11(Pin(10))  # 🎯 이때 초기화

3. 블록 코드: dhtSensor.read()
   └─> BLE: "DHT:READ"
   └─> if dht_sensor is None: return error
   └─> return dht_sensor.read()
```

### Arduino (구현 필요)

```
1. 부팅
   └─> DHTSensor* dhtSensor = nullptr

2. 블록 코드: dhtSensor.setPin(10)
   └─> BLE: "DHT:PIN:10"
   └─> sensorManager->initDHT(10)
   └─> dhtSensor = new DHTSensor(10)  # 🎯 이때 초기화

3. 블록 코드: dhtSensor.read()
   └─> BLE: "DHT:READ"
   └─> if (dhtSensor == nullptr) return error
   └─> return dhtSensor->read()
```

---

## 메모리 효율성 비교

### 정적 로딩 (❌)
```cpp
// 모든 센서를 부팅 시 생성
DHTSensor dht1(10);
UltrasonicSensor ultra1(11, 12);
GyroSensor gyro1();
ServoMotor servo1(13);
// ... 20+ 센서
// 🚨 사용하지 않는 센서도 메모리 점유
// 🚨 약 10-20KB RAM 낭비
```

### 동적 로딩 (✅)
```cpp
// 센서 포인터만 저장
DHTSensor* dht1 = nullptr;         // 8 bytes
UltrasonicSensor* ultra1 = nullptr; // 8 bytes
// ... 20+ 센서 = 약 200 bytes
// ✅ 실제 사용할 때만 초기화
// ✅ 약 10-20KB RAM 절약
```

---

## 구현 계획

### Phase 2 수정사항

1. **SensorManager 클래스 생성**
   - `arduino/DeepCoB_Ezmaker_v1.3.7/SensorManager.h/cpp`
   - 모든 센서 포인터를 `nullptr`로 초기화
   - `init*()`/`deinit*()` 메서드 제공

2. **개별 센서 클래스 (lazy loading)**
   - `DHTSensor.h/cpp`
   - `UltrasonicSensor.h/cpp`
   - `GyroSensor.h/cpp`
   - ... (필요할 때 추가)

3. **BleCommandParser 수정**
   - `PIN:` 명령 처리 시 `sensorManager->init*()` 호출
   - 센서 사용 시 `nullptr` 체크

4. **BleServer는 그대로 유지**
   - GATT 서비스/특성 등록은 부팅 시 수행 (OK)
   - 실제 센서 초기화는 명령 받을 때 수행

---

## 장점

1. **메모리 효율**: 사용하지 않는 센서는 메모리에 로드 안 됨
2. **MicroPython 호환**: 동일한 동작 방식
3. **유연성**: 런타임에 핀 변경 가능
4. **확장성**: 새 센서 추가가 쉬움 (클래스만 추가)

---

## 카메라는 예외?

카메라는 **부팅 시 초기화**해도 됩니다:
- ESP32-S3의 전용 카메라 인터페이스 사용 (핀 고정)
- 카메라는 대부분의 프로젝트에서 사용
- Task 분리로 성능 최적화 필요

```cpp
// Camera는 부팅 시 초기화 OK
void setup() {
    // ...
    cameraTask.begin();  // ✅ 고정 핀, 항상 사용
}
```

버저도 고정 핀이므로 부팅 시 초기화 가능:
```cpp
// Buzzer (고정 핀 42)
buzzer.begin(PIN_BUZZER_FIXED);  // ✅ 고정 핀
```

---

## 다음 단계

Phase 2 진행 전에 이 설계를 반영해야 합니다:

1. `SensorManager` 골격 작성
2. 샘플 센서 1-2개 구현 (DHT, Servo 등)
3. 명령 파서에서 동적 초기화 테스트
4. 나머지 센서들 순차 추가
