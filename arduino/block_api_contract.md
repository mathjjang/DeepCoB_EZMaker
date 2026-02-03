# 블록 API 계약서 (Block API Contract)

## 1. 목적

이 문서는 **Arduino 펌웨어 전환 시 절대 변경해서는 안 되는 JS API**를 정의합니다.  
블록코딩 플랫폼의 블록은 이 API를 호출하며, **이 API 시그니처(함수명/파라미터/반환값)가 바뀌면 모든 블록이 동작하지 않습니다.**

**원칙**:
- ✅ **내부 구현은 자유롭게 변경 가능** (BLE UUID, 프로토콜 포맷, 전송 방식 등)
- ❌ **API 시그니처는 절대 변경 불가** (함수명, 파라미터 순서/타입, 반환값 구조)

---

## 2. 공통 패턴

### 2.1 센서/액츄에이터 초기화 패턴

```javascript
// 클래스 인스턴스 생성 (블록: "센서 초기화 하기")
let sensor = new SensorClass();

// 핀 설정 (비동기, Promise 반환)
sensor.setPin(...args).then(() => {
    console.log("핀 설정 완료");
}).catch(err => {
    console.error("핀 설정 실패:", err);
});

// 또는 async/await
await sensor.setPin(...args);
```

**계약**:
- `new SensorClass()`: 생성자는 파라미터 없음
- `setPin(...args)`: 반드시 **Promise를 반환**, 성공/실패 구분
- 핀 설정은 **센서 사용 전 필수 호출**

### 2.2 센서 값 읽기 패턴

```javascript
// 패턴 A: 헬퍼 함수 (Promise 반환)
let data = await getValidXXXValue(sensor);
let value1 = data.field1;
let value2 = data.field2;

// 패턴 B: 클래스 메서드
await sensor.getStatus();
let value = sensor.getValue(); // 동기 getter
```

**계약**:
- 헬퍼 함수: `getValidXXXValue(sensor)` → `Promise<object>`
- 반환 객체의 **필드명(key)은 불변**
- 값의 **단위/범위는 명시된 대로 유지**

### 2.3 액츄에이터 제어 패턴

```javascript
// 명령 전송 (비동기)
await actuator.doAction(...args);

// 예: 서보 각도 설정
await servo.setAngle(90);

// 예: DC 모터 속도 설정
await motor.setSpeed(50);
```

**계약**:
- 제어 메서드는 **Promise 반환** (성공/실패 구분 가능)
- 메서드명/파라미터는 **불변**

---

## 3. 센서별 API 계약

### 3.1 온습도 센서 (DHT)

**클래스**: `DHTSensor`

```javascript
// 초기화
let dhtSensor = new DHTSensor();
await dhtSensor.setPin(pinNum);

// 값 읽기
let dhtData = await getValidDHTValue(dhtSensor);
let temperature = dhtData.temperature; // 섭씨 (℃)
let humidity = dhtData.humidity;       // 백분율 (%)
```

**계약**:
- `setPin(pinNum: number): Promise<void>`
- `getValidDHTValue(sensor): Promise<{ temperature: number, humidity: number }>`

---

### 3.2 서보모터 (Servo)

**클래스**: `ServoMotor`

```javascript
// 초기화
let servo = new ServoMotor();
await servo.setPin(pinNum);

// 각도 설정
await servo.setAngle(angle); // 0~180도
```

**계약**:
- `setPin(pinNum: number): Promise<void>`
- `setAngle(angle: number): Promise<void>` // 0~180

---

### 3.3 DC 모터 (DCMotor)

**클래스**: `DCMotor`

```javascript
// 초기화
let motor = new DCMotor();
await motor.setPin(pinNum);

// 속도 설정
await motor.setSpeed(speed); // 0~100%

// 정지
await motor.stop();
```

**계약**:
- `setPin(pinNum: number): Promise<void>`
- `setSpeed(speed: number): Promise<void>` // 0~100
- `stop(): Promise<void>`

---

### 3.4 터치센서 (Touch)

**클래스**: `TouchSensor`

```javascript
// 초기화
let touchSensor = new TouchSensor();
await touchSensor.setPin(pinNum);

// 값 읽기
await touchSensor.getStatus();
let touched = touchSensor.isTouched(); // true/false
```

**계약**:
- `setPin(pinNum: number): Promise<void>`
- `getStatus(): Promise<void>`
- `isTouched(): boolean`

---

### 3.5 네오픽셀 (NeoPixel)

**클래스**: `NeoPixel`

```javascript
// 초기화
let neoPixel = new NeoPixel();
await neoPixel.setPin(pinNum, numPixels); // 핀 + LED 개수

// 밝기 설정
await neoPixel.setBrightness(brightness); // 0~255

// 전체 LED 색상 설정
await neoPixel.setAllPixels(color); // color: {r, g, b} 또는 "#RRGGBB"

// 특정 LED 색상 설정
await neoPixel.setPixelColor(index, color); // index: 0부터 시작

// 무지개 효과
await neoPixel.setRainbow(speed); // speed: 1~10

// 끄기
await neoPixel.turnOff();
```

**계약**:
- `setPin(pinNum: number, numPixels: number): Promise<void>`
- `setBrightness(brightness: number): Promise<void>` // 0~255
- `setAllPixels(color): Promise<void>` // color: {r, g, b} | string
- `setPixelColor(index: number, color): Promise<void>`
- `setRainbow(speed: number): Promise<void>` // 1~10
- `turnOff(): Promise<void>`

---

### 3.6 EZMaker 자이로센서 (ICM20948)

**클래스**: `EzGyroSensor`

```javascript
// 초기화
let ezGyroSensor = new EzGyroSensor();
await ezGyroSensor.setPin(sdaPin, sclPin); // I2C 핀

// 값 읽기 (캐시 지원, 150ms 이내 재사용)
let ezGyroData = await ensureEzGyroCache(ezGyroSensor, 150);
let ax = ezGyroData.ax; // 가속도 X (m/s²)
let ay = ezGyroData.ay;
let az = ezGyroData.az;
let gx = ezGyroData.gx; // 각속도 X (dps)
let gy = ezGyroData.gy;
let gz = ezGyroData.gz;
let roll = ezGyroData.roll;   // Roll (도)
let pitch = ezGyroData.pitch; // Pitch (도)
```

**계약**:
- `setPin(sdaPin: number, sclPin: number): Promise<void>`
- `ensureEzGyroCache(sensor, cacheMs: number): Promise<object>`
- 반환 객체: `{ ax, ay, az, gx, gy, gz, roll, pitch }`

---

### 3.7 EZMaker 기압센서 (BMP280)

**클래스**: `EzPressSensor`

```javascript
// 초기화
let ezPressSensor = new EzPressSensor();
await ezPressSensor.setPin(sdaPin, sclPin);

// 값 읽기
let ezPressData = await getValidEzPressValue(ezPressSensor);
let temperature = ezPressData.temperature; // 섭씨 (℃)
let pressure = ezPressData.pressure;       // 파스칼 (Pa)
```

**계약**:
- `setPin(sdaPin: number, sclPin: number): Promise<void>`
- `getValidEzPressValue(sensor): Promise<{ temperature: number, pressure: number }>`

---

### 3.8 EZMaker CO2 센서 (SCD40)

**클래스**: `EzCo2Sensor`

```javascript
// 초기화
let ezCo2Sensor = new EzCo2Sensor();
await ezCo2Sensor.setPin(sdaPin, sclPin);

// 값 읽기
let ezCo2Data = await getValidEzCo2Value(ezCo2Sensor);
let co2 = ezCo2Data.co2;               // ppm
let temperature = ezCo2Data.temp;      // 섭씨 (℃)
let humidity = ezCo2Data.humidity;     // 백분율 (%)
```

**계약**:
- `setPin(sdaPin: number, sclPin: number): Promise<void>`
- `getValidEzCo2Value(sensor): Promise<{ co2: number, temp: number, humidity: number }>`

---

### 3.9 EZMaker 레이저

**클래스**: `Laser`

```javascript
// 초기화
let laser = new Laser();
await laser.setPin(pinNum);

// 제어
await laser.turnOn();
await laser.turnOff();

// 상태 확인
let state = laser.getState(); // "on" | "off" | "unknown"
```

**계약**:
- `setPin(pinNum: number): Promise<void>`
- `turnOn(): Promise<void>`
- `turnOff(): Promise<void>`
- `getState(): string` // "on" | "off" | "unknown"

---

### 3.10 EZMaker DIY-A 센서

**클래스**: `DiyASensor`

```javascript
// 초기화
let diyASensor = new DiyASensor();
await diyASensor.setPin(adcPin);

// 값 읽기
let diyAData = await getValidDiyAValue(diyASensor);
let raw = diyAData.raw;         // 0~1023 (10bit)
let voltage = diyAData.voltage; // 0~5V (환산값)
```

**계약**:
- `setPin(adcPin: number): Promise<void>`
- `getValidDiyAValue(sensor): Promise<{ raw: number, voltage: number }>`

---

### 3.11 EZMaker DIY-B 센서

**클래스**: `DiyBSensor`

```javascript
// 초기화
let diyBSensor = new DiyBSensor();
await diyBSensor.setPin(adcPin);

// 값 읽기
let diyBData = await getValidDiyBValue(diyBSensor);
let raw = diyBData.raw; // 0~1023
```

**계약**:
- `setPin(adcPin: number): Promise<void>`
- `getValidDiyBValue(sensor): Promise<{ raw: number }>`

---

### 3.12 EZMaker 자기장(Hall) 센서

**클래스**: `HallSensor`

```javascript
// 초기화
let hallSensor = new HallSensor();
await hallSensor.setPin(adcPin);

// 값 읽기
let hallData = await getValidHallValue(hallSensor);
let analog = hallData.raw;       // 0~1023
let strength = hallData.strength; // -512~+512 (N/S 극성)
let density = hallData.density;   // 0~512 (자속 밀도)
```

**계약**:
- `setPin(adcPin: number): Promise<void>`
- `getValidHallValue(sensor): Promise<{ raw: number, strength: number, density: number }>`

---

### 3.13 EZMaker 밝기 센서

**클래스**: `EzLightSensor`

```javascript
// 초기화
let ezLightSensor = new EzLightSensor();
await ezLightSensor.setPin(adcPin);

// 값 읽기
let ezLightData = await getValidEzLightValue(ezLightSensor);
let raw = ezLightData.raw;         // 0~1023
let percent = ezLightData.percent; // 0~100%
```

**계약**:
- `setPin(adcPin: number): Promise<void>`
- `getValidEzLightValue(sensor): Promise<{ raw: number, percent: number }>`

---

### 3.14 EZMaker 전압 센서

**클래스**: `EzVoltSensor`

```javascript
// 초기화
let ezVoltSensor = new EzVoltSensor();
await ezVoltSensor.setPin(adcPin);

// 값 읽기
let ezVoltData = await getValidEzVoltValue(ezVoltSensor);
let raw = ezVoltData.raw;         // 0~1023
let voltage = ezVoltData.voltage; // 0~25V
```

**계약**:
- `setPin(adcPin: number): Promise<void>`
- `getValidEzVoltValue(sensor): Promise<{ raw: number, voltage: number }>`

---

### 3.15 EZMaker 전류 센서 (INA219)

**클래스**: `EzCurrSensor`

```javascript
// 초기화
let ezCurrSensor = new EzCurrSensor();
await ezCurrSensor.setPin(sdaPin, sclPin);

// 값 읽기
let ezCurrData = await getValidEzCurrValue(ezCurrSensor);
let current_mA = ezCurrData.current_mA; // mA
let voltage = ezCurrData.voltage;       // V
```

**계약**:
- `setPin(sdaPin: number, sclPin: number): Promise<void>`
- `getValidEzCurrValue(sensor): Promise<{ current_mA: number, voltage: number }>`

---

### 3.16 EZMaker 수중/접촉 온도 센서 (DS18B20)

**클래스**: `EzThermalSensor`

```javascript
// 초기화
let ezThermalSensor = new EzThermalSensor();
await ezThermalSensor.setPin(pinNum);

// 값 읽기
let ezThermalData = await getValidEzThermalValue(ezThermalSensor);
let temperature = ezThermalData.temperature; // 섭씨 (℃)
```

**계약**:
- `setPin(pinNum: number): Promise<void>`
- `getValidEzThermalValue(sensor): Promise<{ temperature: number }>`

---

### 3.17 EZMaker 소리 센서

**클래스**: `EzSoundSensor`

```javascript
// 초기화
let ezSoundSensor = new EzSoundSensor();
await ezSoundSensor.setPin(adcPin);

// 값 읽기
let ezSoundData = await getValidEzSoundValue(ezSoundSensor);
let raw = ezSoundData.raw;         // 0~1023
let percent = ezSoundData.percent; // 0~100%
```

**계약**:
- `setPin(adcPin: number): Promise<void>`
- `getValidEzSoundValue(sensor): Promise<{ raw: number, percent: number }>`

---

### 3.18 EZMaker 무게 센서 (HX711)

**클래스**: `EzWeightSensor`

```javascript
// 초기화 (고정 핀 사용, 상수로 정의됨)
let ezWeightSensor = new EzWeightSensor();
await ezWeightSensor.setPin(EZ_UART_TX_PIN, EZ_UART_RX_PIN); // DOUT, SCK

// 값 읽기
let ezWeightData = await getValidEzWeightValue(ezWeightSensor);
let raw = ezWeightData.raw;       // Raw 카운트
let weight = ezWeightData.weight; // 그램 (g)
```

**계약**:
- `setPin(doutPin: number, sckPin: number): Promise<void>`
- `getValidEzWeightValue(sensor): Promise<{ raw: number, weight: number }>`

---

### 3.19 EZMaker 미세먼지 센서 (PMS7003M)

**클래스**: `EzDustSensor`

```javascript
// 초기화 (고정 핀 사용, 상수로 정의됨)
let ezDustSensor = new EzDustSensor();
await ezDustSensor.setPin(EZ_UART_RX_PIN, EZ_UART_TX_PIN); // RX, TX

// 값 읽기
let ezDustData = await getValidEzDustValue(ezDustSensor);
let pm10 = ezDustData.pm10;   // μg/m³
let pm2_5 = ezDustData.pm2_5; // μg/m³
let pm1_0 = ezDustData.pm1_0; // μg/m³
```

**계약**:
- `setPin(rxPin: number, txPin: number): Promise<void>`
- `getValidEzDustValue(sensor): Promise<{ pm10: number, pm2_5: number, pm1_0: number }>`

---

### 3.20 EZMaker 인체감지 센서 (PIR)

**클래스**: `HumanSensor`

```javascript
// 초기화
let humanSensor = new HumanSensor();
await humanSensor.setPin(pinNum);

// 값 읽기
let humanValue = await getValidHumanValue(humanSensor); // 0 (미감지) 또는 1 (감지)
```

**계약**:
- `setPin(pinNum: number): Promise<void>`
- `getValidHumanValue(sensor): Promise<number>` // 0 | 1

---

### 3.21 EZMaker LCD (16x2 / 20x4)

**클래스**: `LcdDisplay`

```javascript
// 초기화 (타입별 분리)
let lcd = new LcdDisplay();
await lcd.init("16X2", sclPin, sdaPin); // 또는 "20X4"

// 제어
await lcd.clear();
await lcd.setBacklight(true); // true: ON, false: OFF
await lcd.print(row, col, text); // row: 0부터, col: 0부터
```

**계약**:
- `init(type: "16X2" | "20X4", sclPin: number, sdaPin: number): Promise<void>`
- `clear(): Promise<void>`
- `setBacklight(on: boolean): Promise<void>`
- `print(row: number, col: number, text: string): Promise<void>`

---

### 3.22 카메라

**클래스**: `Camera`

```javascript
// 초기화
let camera = new Camera();

// 제어
await camera.startStreaming();
await camera.stopStreaming();
await camera.takeSnapshot();

// 이벤트 핸들러
camera.onImageComplete = (blob) => {
    // blob: Blob 객체 (image/jpeg)
    let url = URL.createObjectURL(blob);
    // ...이미지 표시
};

// 최신 이미지 가져오기
let latestBlob = camera.getLatestImage(); // Blob | null
```

**계약**:
- `startStreaming(): Promise<void>`
- `stopStreaming(): Promise<void>`
- `takeSnapshot(): Promise<void>`
- `onImageComplete: (blob: Blob) => void` // 콜백 프로퍼티
- `getLatestImage(): Blob | null`

---

## 4. 공통 상수 (핀 매핑)

Arduino 전환 후에도 **JS에서 사용하는 핀 상수는 동일하게 유지**해야 합니다.

```javascript
// I2C 공통 핀 (EZMaker Shield v2.0)
const EZ_I2C_SDA_PIN = 41; // D6 (GPIO 41)
const EZ_I2C_SCL_PIN = 40; // D5 (GPIO 40)

// UART 공통 핀 (무게/미세먼지 센서)
const EZ_UART_TX_PIN = 42; // D11 (GPIO 42)
const EZ_UART_RX_PIN = 14; // D10 (GPIO 14)
```

**계약**:
- 상수명 불변: `EZ_I2C_SDA_PIN`, `EZ_I2C_SCL_PIN`, `EZ_UART_TX_PIN`, `EZ_UART_RX_PIN`
- 값 불변: 각각 `41`, `40`, `42`, `14`

---

## 5. BLE 연결 관리 (BLEManager)

```javascript
// BLE Manager 싱글톤
let bleManager = BLEManager.getInstance();
await bleManager.init();

// 연결
await bleManager.connect();

// 연결 상태 확인
let isConnected = bleManager.isConnected(); // boolean

// 연결 해제
await bleManager.disconnect();
```

**계약**:
- `BLEManager.getInstance(): BLEManager` // 싱글톤
- `init(): Promise<void>`
- `connect(): Promise<void>`
- `disconnect(): Promise<void>`
- `isConnected(): boolean`

---

## 6. 로깅 (EZ_LOG)

```javascript
// 로그 레벨 설정
EZ_LOG.setLevel('debug'); // 'none' | 'info' | 'debug'

// 로그 출력
EZ_LOG.info('정보 메시지');
EZ_LOG.debug('디버그 메시지');
EZ_LOG.warn('경고 메시지');
EZ_LOG.error('에러 메시지');
```

**계약**:
- `EZ_LOG.setLevel(level: 'none' | 'info' | 'debug'): void`
- `EZ_LOG.info(...args): void`
- `EZ_LOG.debug(...args): void`
- `EZ_LOG.warn(...args): void`
- `EZ_LOG.error(...args): void`

---

## 7. 버전 정보

```javascript
// 라이브러리 버전
console.log(EZ_LIB_VERSION); // "1.3.7" (예시)
```

**계약**:
- `EZ_LIB_VERSION: string` // 전역 상수

---

## 8. 변경 가능한 것 vs 변경 불가능한 것

### ✅ 변경 가능 (내부 구현)

- BLE UUID (펌웨어와 JS가 일치하면 됨)
- 프로토콜 포맷 (텍스트 → 바이너리)
- 전송 방식 (MTU, 청크 크기, 헤더 구조)
- 클래스 내부 로직 (`_processData`, `_sendCommand` 등)
- 에러 처리 방식
- 캐싱/최적화 로직

### ❌ 변경 불가 (Public API)

- 클래스명: `Camera`, `EzGyroSensor`, `Laser`, `DHTSensor` 등
- 메서드명: `setPin()`, `turnOn()`, `getStatus()`, `setAngle()` 등
- 파라미터 순서/타입: `setPin(sdaPin, sclPin)` → 순서 변경 불가
- 반환값 구조: `{ temperature, humidity }` → 필드명 변경 불가
- 콜백 프로퍼티: `onImageComplete` → 이름/시그니처 변경 불가
- 전역 상수: `EZ_I2C_SDA_PIN`, `EZ_LOG`, `EZ_LIB_VERSION` 등

---

## 9. 테스트 체크리스트

Arduino 펌웨어 전환 후, 다음을 확인하여 **API 계약 준수**를 검증합니다.

- [ ] 모든 센서 클래스 생성 가능 (`new XxxSensor()`)
- [ ] `setPin()` 호출 후 Promise 정상 resolve
- [ ] 값 읽기 함수 반환 객체의 필드명 일치
- [ ] 액츄에이터 제어 메서드 정상 동작
- [ ] 카메라 `onImageComplete` 콜백 정상 호출 (Blob 타입)
- [ ] 핀 상수 값 일치 (`EZ_I2C_SDA_PIN === 41` 등)
- [ ] BLEManager 연결/해제 정상 동작
- [ ] 로그 레벨 전환 정상 동작

---

## 10. 버전 관리

| 버전 | 날짜 | 변경 사항 |
|------|------|-----------|
| 1.0 | - | 초기 계약 정의 (MicroPython 기준) |
| 1.1 | - | Arduino 전환 대비 명확화 |

> Arduino 전환 시 이 문서의 버전을 `2.0`으로 올리고, 실제 변경된 내부 구현을 기록하되,  
> **Public API는 1.x와 100% 호환 유지**를 목표로 합니다.
