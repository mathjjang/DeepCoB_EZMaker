## EZMaker 블록코드 정의서 (요약)

이 문서는 `IoTmode/test/DeepcoIoT_block_v1.6.xlsx` 에 정의된 블록 사양을  
**Markdown 형태로 간단히 정리한 버전**입니다.  
우선 LED / 레이저 모듈 위주로, 블록 형태와 연결되는 JS 코드를 정리합니다.

### 1. 공통 규칙

- **카테고리**: 블록이 속하는 기능 그룹 (예: `LED`, `LASER` 등)
- **블록 한글 문구**: 블록 UI 상에 학생에게 보이는 한국어 문구
- **영문 설명**: 문서/툴팁용 간단 설명
- **JS 코드 템플릿**: 블록이 실행될 때 호출되는 JavaScript 코드 패턴  
  - 실제 값(핀 번호, 시간, 밝기 등)은 블록 인자의 자리 `( )` 에 매핑
- **핀 순서 규칙(중요)**: 일반 I2C 센서는 `setPin(sdaPin, sclPin)` 순서를 사용하지만, LCD는 펌웨어 명령 포맷이 `LCD:INIT:...:SCL,SDA` 이므로 템플릿에서도 `lcd.init(type, sclPin, sdaPin)` 순서를 사용합니다.

---

### 2. 공통 블록 (DeepCo + EZMaker)

#### 2.1 온습도 센서 블록 (DHT, 공통)

온습도 센서는 **기존 DeepCo 보드 + EZMaker 센서 라인에서 공통으로 사용하는 DHT11 기반 센서**입니다.  
펌웨어/JS 레벨에서는 `DHT` 특성과 `DHTSensor` 클래스를 공유합니다.

| 카테고리   | 블록 한글 문구                                      | 영문 설명                                             | JS 코드 템플릿 (예시) |
| :--------- | :-------------------------------------------------- | :---------------------------------------------------- | :-------------------- |
| 온습도센서 | 온습도센서 핀(pinNum)으로 초기화 하기               | initialize dhtSensor pin: (pinNum)                   | `let dhtSensor = new DHTSensor();`<br>`dhtSensor.setPin(pinNum).then(() => {`<br>`    console.log("온습도 센서 핀 설정 완료");`<br>`}).catch(err => {`<br>`    console.error("온습도 센서 핀 설정 실패:", err);`<br>`});` |
| 온습도센서 | 온습도센서에서 온도(temperature)와 습도(humidity)값 가져오기 | get (temperature) and (humidity) from dhtSensor      | `let dhtData = await getValidDHTValue(dhtSensor);`<br>`let temperature = dhtData.temperature;`<br>`let humidity = dhtData.humidity;` |

> 실제 구현에서는 `integratedBleLib_Camera.js` 의 `DHTSensor` 클래스와  
> 보조 함수 `getValidDHTValue(sensor)` 를 통해  
> **`DHT:PIN:…` 설정 → `DHT:STATUS` 명령 전송 → 응답 파싱 → 온도/습도 값 객체 반환** 흐름을 사용합니다.  
> 위 표의 두 블록으로 “핀 초기화 → 온도/습도 값 동시 읽기” 패턴을 표현할 수 있습니다.

#### 2.2 서보모터 블록 (SERVO, 공통)

서보모터는 **기존 DeepCo 보드 + EZMaker 센서 라인에서 공통으로 사용하는 디지털 액츄에이터**입니다.  
펌웨어/JS 레벨에서는 `SERVO` 특성과 `ServoMotor` 클래스를 공유합니다.

| 카테고리 | 블록 한글 문구                              | 영문 설명                                   | JS 코드 템플릿 (예시) |
| :------- | :------------------------------------------- | :------------------------------------------ | :-------------------- |
| 서보모터 | 서보모터 핀(pinNum)으로 초기화 하기          | initialize servo motor pin: (pinNum)       | `let servo = new ServoMotor();`<br>`servo.setPin(pinNum).then(() => {`<br>`    console.log("서보모터 핀 설정 완료");`<br>`}).catch(err => {`<br>`    console.error("서보모터 핀 설정 실패:", err);`<br>`});` |
| 서보모터 | 서보모터 각도를 (angle)도로 맞추기           | set servo motor angle to (angle) degrees   | `await servo.setAngle(angle);` |

> 실제 구현에서는 `integratedBleLib_Camera.js` 의 `ServoMotor` 클래스가  
> `SERVO:PIN:…`, `SERVO:<angle>` 명령을 BLE로 전송하여 서보 각도를 제어합니다.  
> 위 두 블록으로 “핀 초기화 → 원하는 각도로 회전” 패턴을 표현할 수 있습니다.

#### 2.3 DC 모터 블록 (DCMOTOR, 공통)

DC 모터는 **기존 DeepCo 보드 + EZMaker 센서 라인에서 공통으로 사용하는 디지털 액츄에이터**입니다.  
펌웨어/JS 레벨에서는 `DCMOTOR` 특성과 `DCMotor` 클래스를 공유합니다.

| 카테고리 | 블록 한글 문구                              | 영문 설명                                     | JS 코드 템플릿 (예시) |
| :------- | :------------------------------------------- | :-------------------------------------------- | :-------------------- |
| DC모터   | DC모터 핀(pinNum)으로 초기화 하기            | initialize dc motor pin: (pinNum)            | `let motor = new DCMotor();`<br>`motor.setPin(pinNum).then(() => {`<br>`    console.log("DC 모터 핀 설정 완료");`<br>`}).catch(err => {`<br>`    console.error("DC 모터 핀 설정 실패:", err);`<br>`});` |
| DC모터   | DC모터 속도를 (speed)% 로 설정하기           | set dc motor speed to (speed)% (0~100)       | `await motor.setSpeed(speed);` |
| DC모터   | DC모터 정지하기                               | stop dc motor                                 | `await motor.stop();` |

> 실제 구현에서는 `integratedBleLib_Camera.js` 의 `DCMotor` 클래스가  
> `MOTOR:PIN:…`, `MOTOR:SPEED:<value>`, `MOTOR:STOP` 명령을 BLE로 전송하여 속도를 제어합니다.  
> 위 세 블록으로 “핀 초기화 → 원하는 속도로 회전 → 정지” 패턴을 표현할 수 있습니다.

#### 2.4 터치센서 블록 (TOUCH, 공통)

터치센서(TTP223)는 **기존 DeepCo 보드 + EZMaker 라인에서 공통으로 사용하는 디지털 입력 센서**입니다.  
펌웨어/JS 레벨에서는 `TOUCH` 특성과 `TouchSensor` 클래스를 공유합니다.

| 카테고리 | 블록 한글 문구                                 | 영문 설명                                        | JS 코드 템플릿 (예시) |
| :------- | :---------------------------------------------- | :----------------------------------------------- | :-------------------- |
| 터치센서 | 터치센서 핀(pinNum)으로 초기화 하기            | initialize touch sensor pin: (pinNum)           | `let touchSensor = new TouchSensor();`<br>`touchSensor.setPin(pinNum).then(() => {`<br>`    console.log("터치센서 핀 설정 완료");`<br>`}).catch(err => {`<br>`    console.error("터치센서 핀 설정 실패:", err);`<br>`});` |
| 터치센서 | 터치센서에서 터치 상태(touched) 값 가져오기    | get touch state (touched / not touched)         | `await touchSensor.getStatus();`<br>`let touched = touchSensor.isTouched();` |

> 실제 구현에서는 `integratedBleLib_Camera.js` 의 `TouchSensor` 클래스가  
> `TOUCH:PIN:…`, `TOUCH:STATUS` 명령을 BLE로 전송하여,  
> 펌웨어의 `touch_handler` 가 `TOUCH:1`(터치됨) 또는 `TOUCH:0`(터치 안 됨)을 응답합니다.  
> JS 측 `TouchSensor._processData` 는 이 문자열을 파싱하여 내부 상태(`this.touched`)를 갱신하고,  
> 블록 코드에서는 `touchSensor.isTouched()` 값을 사용해 조건 분기 등을 구현할 수 있습니다.

#### 2.5 네오픽셀 블록 (NEOPIXEL, 공통)

네오픽셀(WS2812 계열)은 **1구, 4구, 7구 등 여러 개의 RGB LED가 직렬로 연결된 디지털 LED 모듈**입니다.  
펌웨어/JS 레벨에서는 `NEOPIXEL` 캐릭터리스틱과 `NEO:PIN / NEO:PX / NEO:ALL / NEO:RAINBOW / NEO:OFF` 명령을 사용하며,  
JS 쪽에서는 `integratedBleLib_Camera.js` 의 `NeoPixel` 클래스를 통해 제어합니다.

| 카테고리 | 블록 한글 문구                                                  | 영문 설명                                                           | JS 코드 템플릿 (예시) |
| :------- | :-------------------------------------------------------------- | :------------------------------------------------------------------ | :-------------------- |
| 네오픽셀 | 네오픽셀1 핀(pinNum), LED개수(numPixels)로 초기화 하기          | initialize neoPixel1 on (pinNum) with (numPixels) LEDs (1/4/7 등)  | `let neoPixel = new NeoPixel();`<br>`neoPixel.setPin(pinNum, numPixels);` |
| 네오픽셀 | 네오픽셀1 밝기를 (brightness)로 하기 (0~255)                    | set neoPixel1 brightness to (brightness) (0~255)                   | `neoPixel.setBrightness(brightness);` |
| 네오픽셀 | 네오픽셀1 모든 LED를 색상(color)으로 켜기                       | set all neoPixel1 LEDs to (color)                                  | `neoPixel.setAllPixels(color);` |
| 네오픽셀 | 네오픽셀1의 (index)번 LED를 색상(color)으로 켜기                | set (index)-th LED of neoPixel1 to (color)                         | `neoPixel.setPixelColor(index, color);` |
| 네오픽셀 | 네오픽셀1 무지개 효과를 속도(speed)로 켜기                      | enable rainbow effect on neoPixel1 with speed (1~10)               | `neoPixel.setRainbow(speed);` |
| 네오픽셀 | 네오픽셀1 끄기                                                  | turn off all neoPixel1 LEDs                                        | `neoPixel.turnOff();` |

> `setPin(pinNum, numPixels)` 에서 `numPixels` 인자를 통해 **1구 / 4구 / 7구 등 다양한 개수의 네오픽셀 모듈을 지원**합니다.  
> 이때 내부적으로는 `NEO:PIN:<pinNum>,<numPixels>` 명령을 보내며, 펌웨어의 `bleIoT.py` 에서 실제 LED 개수에 맞게  
> `NeoPixel` 객체를 재생성합니다. 이후 `NEO:PX`, `NEO:ALL`, `NEO:RAINBOW`, `NEO:OFF` 명령으로 각각  
> **특정 인덱스 색 설정 / 전체 색 설정 / 무지개 효과 / 전체 끄기** 를 수행합니다.

### 3. EZMaker 전용 블록

#### 3.1 레이저 모듈 블록 (LASER, EZMaker 전용)

레이저 모듈은 **LED와 유사한 디지털 On/Off 제어**를 하므로,  
블록 포맷도 LED와 거의 동일한 구조를 따릅니다.

| 카테고리 | 블록 한글 문구                          | 영문 설명                                   | JS 코드 템플릿 (예시) |
| :------- | :--------------------------------------- | :------------------------------------------ | :-------------------- |
| LASER    | LASER1 핀(pinNum)으로 초기화 하기        | initialize LASER pin: (pinNum)              | `let laser = new Laser();`<br>`// 기본 예: EZMaker D0 → GPIO 21`<br>`laser.setPin(pinNum);` |
| LASER    | LASER1 켜기                              | turn LASER ON                               | `laser.turnOn();` |
| LASER    | LASER1 끄기                              | turn LASER OFF                              | `laser.turnOff();` |

> D0 포트 기준 GPIO 21을 기본값으로 사용하며,  
> 내부적으로는 `integratedBleLib_Camera.js` 의 `Laser` 클래스가  
> `LASER:PIN:…`, `LASER:ON`, `LASER:OFF` 명령을 BLE로 전송합니다.

#### 3.2 EZMaker 자이로센서 블록 (EZGYRO, ICM20948 전용)

| 카테고리   | 블록 한글 문구                                                 | 영문 설명                                                     | JS 코드 템플릿 (예시) |
| :--------- | :-------------------------------------------------------------- | :------------------------------------------------------------ | :-------------------- |
| EZ자이로센서 | EZ자이로센서 I2C 핀으로 초기화 하기                         | initialize ezGyroSensor on I2C pins                           | `let ezGyroSensor = new EzGyroSensor();`<br>`// I2C 공통 핀 상수(단일 소스): EZ_I2C_SDA_PIN / EZ_I2C_SCL_PIN`<br>`ezGyroSensor.setPin(EZ_I2C_SDA_PIN, EZ_I2C_SCL_PIN).then(() => {`<br>`    console.log("EZ 자이로센서 핀 설정 완료");`<br>`}).catch(err => {`<br>`    console.error("EZ 자이로센서 핀 설정 실패:", err);`<br>`});` |
| EZ자이로센서 | EZ자이로센서에서 가속도(ax,ay,az) 값 가져오기 | get acceleration (ax, ay, az) from ezGyroSensor | `// 150ms 이내에서는 캐시 재사용(중복 BLE 요청 방지), 150ms 초과 시 자동 재측정`<br>`let ezGyroData = await ensureEzGyroCache(ezGyroSensor, 150);`<br>`let ax = ezGyroData.ax;`<br>`let ay = ezGyroData.ay;`<br>`let az = ezGyroData.az;` |
| EZ자이로센서 | EZ자이로센서에서 각속도(gx,gy,gz) 값 가져오기 | get angular velocity(gx, gy, gz) from ezGyroSensor | `// (ax,ay,az) 블록과 같은 샘플을 공유(캐시), 필요 시(150ms 초과) 자동 재측정`<br>`let ezGyroData = await ensureEzGyroCache(ezGyroSensor, 150);`<br>`let gx = ezGyroData.gx;`<br>`let gy = ezGyroData.gy;`<br>`let gz = ezGyroData.gz;` |
| EZ자이로센서 | EZ자이로센서에서 자세(roll,pitch) 값 가져오기 | get (roll, pitch) from ezGyroSensor | `// (ax,ay,az)/(gx,gy,gz) 블록과 같은 샘플을 공유(캐시), 필요 시(150ms 초과) 자동 재측정`<br>`let ezGyroData = await ensureEzGyroCache(ezGyroSensor, 150);`<br>`let roll = ezGyroData.roll;`<br>`let pitch = ezGyroData.pitch;` |

> EZ자이로센서 블록은 `EZGYRO:PIN:...`, `EZGYRO:STATUS` 명령을 사용하며,  
> 펌웨어에서는 `icm20948.py` 의 `ICM20948` 드라이버를 통해  
> 가속도(AX,AY,AZ), 자이로(GX,GY,GZ), Roll/Pitch, 온도(TEMP)를 한 번에 읽어와  
> `EZGYRO:AX=...,AY=...,AZ=...,GX=...,GY=...,GZ=...,ROLL=...,PITCH=...,TEMP=...` 포맷으로 BLE에 전송합니다.
>
> 블록이 3개로 나뉘더라도, `ensureEzGyroCache(ezGyroSensor, 150)` 를 사용하면  
> **같은 실행 흐름(짧은 시간)에서는 1번만 측정한 데이터를 공유**하고,  
> **150ms가 지나면 자동으로 다시 측정**하여 최신값을 반영할 수 있습니다.

#### 3.3 EZMaker 기압센서 블록 (BMP280, EZPRESS 전용)

EZMaker 기압센서(BMP280)는 **EZMaker 전용 I2C 기압/온도 센서**로,  
펌웨어/JS 레벨에서는 `EZPRESS` 명령과 전용 캐릭터리스틱을 사용합니다.

| 카테고리   | 블록 한글 문구                                              | 영문 설명                                                 | JS 코드 템플릿 (예시) |
| :--------- | :----------------------------------------------------------- | :-------------------------------------------------------- | :-------------------- |
| EZ기압센서 | EZ기압센서 I2C 핀으로 초기화 하기                         | initialize ezPressSensor on I2C pins                      | `let ezPressSensor = new EzPressSensor();`<br>`// I2C 공통 핀 상수(단일 소스): EZ_I2C_SDA_PIN / EZ_I2C_SCL_PIN`<br>`ezPressSensor.setPin(EZ_I2C_SDA_PIN, EZ_I2C_SCL_PIN).then(() => {`<br>`    console.log("EZ 기압센서 핀 설정 완료");`<br>`}).catch(err => {`<br>`    console.error("EZ 기압센서 핀 설정 실패:", err);`<br>`});` |
| EZ기압센서 | EZ기압센서에서 온도(temperature)와 기압(pressure) 값 가져오기 | get (temperature, pressure) from ezPressSensor (°C, Pa) | `let ezPressData = await getValidEzPressValue(ezPressSensor);`<br>`let temperature = ezPressData.temperature;`<br>`let pressure = ezPressData.pressure;` |

> EZ기압센서 블록은 `EZPRESS:PIN:SDA,SCL`, `EZPRESS:STATUS` 명령을 사용하며,  
> 펌웨어에서는 `bmp280.py` 의 `BMP280` 드라이버를 통해  
> 온도(T)와 기압(P, Pa 단위)을 한 번에 읽어와  
> `EZPRESS:T=...,P=...` 포맷으로 BLE에 전송합니다.  
> JS 쪽에서는 `EzPressSensor` 클래스와 `getValidEzPressValue(sensor)` 보조 함수를 통해  
> **핀 설정 → 상태 요청 → 응답 파싱 → `{ temperature, pressure }` 객체 반환** 흐름을 사용합니다.

---

#### 3.4 EZMaker 이산화탄소 센서 블록 (SCD40, EZCO2 전용)

EZMaker 이산화탄소 센서(SCD40)는 **EZMaker 전용 I2C CO2/온도/습도 센서**로,  
펌웨어/JS 레벨에서는 `EZCO2` 명령과 전용 캐릭터리스틱을 사용합니다.

| 카테고리   | 블록 한글 문구                                                         | 영문 설명                                                           | JS 코드 템플릿 (예시) |
| :--------- | :---------------------------------------------------------------------- | :------------------------------------------------------------------ | :-------------------- |
| EZCO2센서  | EZCO2 센서 I2C 핀으로 초기화 하기                                  | initialize ezCo2Sensor on I2C pins                                 | `let ezCo2Sensor = new EzCo2Sensor();`<br>`// I2C 공통 핀 상수(단일 소스): EZ_I2C_SDA_PIN / EZ_I2C_SCL_PIN`<br>`ezCo2Sensor.setPin(EZ_I2C_SDA_PIN, EZ_I2C_SCL_PIN).then(() => {`<br>`    console.log("EZ CO2 센서 핀 설정 완료");`<br>`}).catch(err => {`<br>`    console.error("EZ CO2 센서 핀 설정 실패:", err);`<br>`});` |
| EZCO2센서  | EZCO2 센서에서 CO2(co2), 온도(temperature), 습도(humidity) 값 가져오기 | get (co2, temperature, humidity) from ezCo2Sensor (ppm, °C, %RH)   | `let ezCo2Data = await getValidEzCo2Value(ezCo2Sensor);`<br>`let co2  = ezCo2Data.co2;`<br>`let temperature = ezCo2Data.temp;`<br>`let humidity    = ezCo2Data.humidity;` |

> EZCO2 센서 블록은 `EZCO2:PIN:SDA,SCL`, `EZCO2:STATUS` 명령을 사용하며,  
> 펌웨어에서는 `scd40.py` 의 `SCD40` 드라이버를 통해  
> CO2 농도(CO2, ppm), 온도(T, ℃), 습도(H, %RH)를 읽어와  
> `EZCO2:CO2=...,T=...,H=...` 포맷으로 BLE에 전송합니다.  
> JS 쪽에서는 `EzCo2Sensor` 클래스와 `getValidEzCo2Value(sensor)` 보조 함수를 통해  
> **핀 설정 → 상태 요청 → 응답 파싱 → `{ co2, temp, humidity }` 객체 반환** 흐름을 사용합니다.

#### 3.5 EZMaker DIY-A 전자기 유도 센서 블록 (DIY-A 전용)

DIY-A 전자기 유도 센서는 **EZMaker 전용 아날로그 센서**로,  
코일 양 끝 전압(유도 전압)을 10비트(0~1023) 스케일과 0~5V 개념 전압으로 측정합니다.  
펌웨어/JS 레벨에서는 `DIYA` 명령과 전용 캐릭터리스틱을 사용합니다.

| 카테고리    | 블록 한글 문구                                                   | 영문 설명                                                          | JS 코드 템플릿 (예시) |
| :---------- | :---------------------------------------------------------------- | :----------------------------------------------------------------- | :-------------------- |
| DIY-A센서   | DIY-A 센서 핀(ADC 핀)으로 초기화 하기                             | initialize diyASensor adc pin: (adcPin)                           | `let diyASensor = new DiyASensor();`<br>`diyASensor.setPin(adcPin).then(() => {`<br>`    console.log("DIY-A 센서 핀 설정 완료");`<br>`}).catch(err => {`<br>`    console.error("DIY-A 센서 핀 설정 실패:", err);`<br>`});` |
| DIY-A센서   | DIY-A 센서에서 Raw(raw)와 전압(voltage) 값 가져오기              | get (raw, voltage) from diyASensor (10bit, 0~5V scaled)           | `let diyAData = await getValidDiyAValue(diyASensor);`<br>`let raw = diyAData.raw;`<br>`let voltage = diyAData.voltage;` |

> DIY-A 센서 블록은 `DIYA:PIN:<핀번호>`, `DIYA:STATUS` 명령을 사용하며,  
> 펌웨어에서는 `diyA_sensor.py` 의 `DiyASensor` 드라이버와 `bleIoT.py` 의 DIY-A 핸들러를 통해  
> 0~1023(10bit) Raw 값과 0~5V 환산 전압을 한 번에 측정해  
> `DIYA:<voltage>,<raw>` 포맷으로 BLE에 전송합니다.  
> JS 쪽에서는 `integratedBleLib_Camera.js` 의 `DiyASensor` 클래스와  
> `getValidDiyAValue(sensor)` 보조 함수를 통해  
> **핀 설정 → 상태 요청 → 응답 파싱 → `{ raw, voltage }` 객체 반환** 흐름을 사용합니다.

#### 3.6 EZMaker DIY-B 전류/전도도 센서 블록 (DIY-B 전용)

DIY-B 전류/전도도 센서는 **EZMaker 전용 아날로그 센서**로,  
회로에 흐르는 전류(또는 전도도)에 비례하는 전압을 10비트(0~1023) 스케일과 0~5V 개념 전압으로 측정합니다.  
펌웨어/JS 레벨에서는 `DIYB` 명령과 전용 캐릭터리스틱을 사용합니다.

| 카테고리    | 블록 한글 문구                                                       | 영문 설명                                                                | JS 코드 템플릿 (예시) |
| :---------- | :-------------------------------------------------------------------- | :----------------------------------------------------------------------- | :-------------------- |
| DIY-B센서   | DIY-B 센서 핀(ADC 핀)으로 초기화 하기                                 | initialize diyBSensor adc pin: (adcPin)                                 | `let diyBSensor = new DiyBSensor();`<br>`diyBSensor.setPin(adcPin).then(() => {`<br>`    console.log("DIY-B 센서 핀 설정 완료");`<br>`}).catch(err => {`<br>`    console.error("DIY-B 센서 핀 설정 실패:", err);`<br>`});` |
| DIY-B센서   | DIY-B 센서에서 Raw(raw)값 가져오기                                    | get (raw) from diyBSensor                                                | `let diyBData = await getValidDiyBValue(diyBSensor);`<br>`let raw = diyBData.raw;` |

> DIY-B 센서 블록은 `DIYB:PIN:<핀번호>`, `DIYB:STATUS` 명령을 사용하며,  
> 펌웨어에서는 `diyB_sensor.py` 의 `DiyBSensor` 드라이버와 `bleIoT.py` 의 DIY-B 핸들러를 통해  
> 0~1023(10bit) Raw 값과 0~5V 환산 전압을 한 번에 측정해  
> `DIYB:<voltage>,<raw>` 포맷으로 BLE에 전송합니다.  
> JS 쪽에서는 `integratedBleLib_Camera.js` 의 `DiyBSensor` 클래스와  
> `getValidDiyBValue(sensor)` 보조 함수를 통해  
> **핀 설정 → 상태 요청 → 응답 파싱 → `{ raw, voltage }` 객체 반환** 흐름을 DIY-A와 동일한 방식으로 사용할 수 있습니다.

#### 3.7 EZMaker 자기장(Hall) 센서 블록

자기장(Hall) 센서는 **자기장(자력)의 세기와 방향(N/S)을 측정하는 아날로그 센서**입니다.  
EZMaker에서는 다음과 같은 세 가지 정보를 제공합니다.

- 아날로그 값: 0~1023 (10비트)
- N/S 극성 세기: -512 ~ +512 (기준 대비 방향과 세기)
- 자속 밀도: 0 ~ 512 (세기만, 방향 없음)

펌웨어/JS 레벨에서는 `HALL` 명령과 전용 캐릭터리스틱을 사용합니다.

| 카테고리     | 블록 한글 문구                                                       | 영문 설명                                                                   | JS 코드 템플릿 (예시) |
| :----------- | :-------------------------------------------------------------------- | :-------------------------------------------------------------------------- | :-------------------- |
| 자기장센서   | 자기장 센서 핀(ADC 핀)으로 초기화 하기                              | initialize hallSensor adc pin: (adcPin)                                    | `let hallSensor = new HallSensor();`<br>`hallSensor.setPin(adcPin).then(() => {`<br>`    console.log("Hall 센서 핀 설정 완료");`<br>`}).catch(err => {`<br>`    console.error("Hall 센서 핀 설정 실패:", err);`<br>`});` |
| 자기장센서   | 자기장 센서에서 아날로그, 극성(N/S), 자속밀도 값 가져오기           | get (raw, strength, density) from hallSensor (0~1023, -512~+512, 0~512)    | `let hallData = await getValidHallValue(hallSensor);`<br>`let analog   = hallData.raw;`<br>`let strength = hallData.strength;`<br>`let density  = hallData.density;` |

> Hall 센서 블록은 `HALL:PIN:<핀번호>`, `HALL:STATUS` 명령을 사용하며,  
> 펌웨어에서는 `hall_sensor.py` 의 `HallSensor` 드라이버와 `bleIoT.py` 의 Hall 핸들러를 통해  
> 0~1023(10bit) 아날로그 값과 -512~+512 N/S 세기, 0~512 자속 밀도 값을 한 번에 측정해  
> `HALL:<raw>,<strength>,<density>` 포맷으로 BLE에 전송합니다.  
> JS 쪽에서는 `integratedBleLib_Camera.js` 의 `HallSensor` 클래스와  
> `getValidHallValue(sensor)` 보조 함수를 통해  
> **핀 설정 → 상태 요청 → 응답 파싱 → `{ raw, strength, density }` 객체 반환** 흐름을 사용할 수 있습니다.

#### 3.8 EZMaker I2C LCD 블록 (16x2 / 20x4)

EZMaker I2C LCD 모듈은 **HD44780 호환 16x2 / 20x4 캐릭터 LCD + PCF8574 I2C 확장 보드** 조합입니다.  
펌웨어/JS 레벨에서는 `LCD` 명령과 전용 캐릭터리스틱을 사용하며,  
LCD 타입(16x2 / 20x4)에 따라 **초기화(setPin) 블록을 아예 구분**해서 사용합니다.

| 카테고리 | 블록 한글 문구                                           | 영문 설명                                                         | JS 코드 템플릿 (예시) |
| :------- | :-------------------------------------------------------- | :---------------------------------------------------------------- | :-------------------- |
| I2C LCD  | LCD(16x2)를 I2C 핀으로 초기화 하기                 | initialize LCD 16x2 on I2C pins                                 | `let lcd = new LcdDisplay();`<br>`// I2C 공통 핀 상수(단일 소스): EZ_I2C_SDA_PIN / EZ_I2C_SCL_PIN`<br>`// LCD:INIT:... 은 SCL,SDA 순서이므로 (SCL=EZ_I2C_SCL_PIN, SDA=EZ_I2C_SDA_PIN)`<br>`lcd.init("16X2", EZ_I2C_SCL_PIN, EZ_I2C_SDA_PIN).then(() => {`<br>`    console.log("LCD(16x2) 초기화 완료");`<br>`}).catch(err => {`<br>`    console.error("LCD(16x2) 초기화 실패:", err);`<br>`});` |
| I2C LCD  | LCD(20x4)를 I2C 핀으로 초기화 하기                 | initialize I2C LCD 20x4 on I2C pins                              | `let lcd = new LcdDisplay();`<br>`// I2C 공통 핀 상수(단일 소스): EZ_I2C_SDA_PIN / EZ_I2C_SCL_PIN`<br>`// LCD:INIT:... 은 SCL,SDA 순서이므로 (SCL=EZ_I2C_SCL_PIN, SDA=EZ_I2C_SDA_PIN)`<br>`lcd.init("20X4", EZ_I2C_SCL_PIN, EZ_I2C_SDA_PIN).then(() => {`<br>`    console.log("LCD(20x4) 초기화 완료");`<br>`}).catch(err => {`<br>`    console.error("LCD(20x4) 초기화 실패:", err);`<br>`});` |
| I2C LCD  | LCD 화면 지우기                                      | clear I2C LCD display                                             | `await lcd.clear();` |
| I2C LCD  | LCD 백라이트 켜기                                    | turn I2C LCD backlight ON                                         | `await lcd.setBacklight(true);` |
| I2C LCD  | LCD 백라이트 끄기                                    | turn I2C LCD backlight OFF                                        | `await lcd.setBacklight(false);` |
| I2C LCD  | LCD (row)행 (col)열 위치에 텍스트(text) 출력하기     | print (text) at (row, col) on I2C LCD                             | `await lcd.print(row, col, text);` |

> 블록 코드 관점에서는 **16x2와 20x4가 서로 다른 초기화 블록**으로 제공되어,  
> 학생이 타입을 블록 단계에서 명확히 선택할 수 있습니다.  
> 내부적으로는 `integratedBleLib_Camera.js` 의 `LcdDisplay` 클래스가  
> `lcd.init("16X2", EZ_I2C_SCL_PIN, EZ_I2C_SDA_PIN)` 또는 `lcd.init("20X4", EZ_I2C_SCL_PIN, EZ_I2C_SDA_PIN)` 을 호출하며,  
> 이 호출은 BLE를 통해 각각 `LCD:INIT:16X2:SCL,SDA`, `LCD:INIT:20X4:SCL,SDA` 명령으로 변환됩니다.  
> 이후 `lcd.clear()` → `LCD:CLEAR`, `lcd.setBacklight(true/false)` → `LCD:BACKLIGHT:ON/OFF`,  
> `lcd.print(row, col, text)` → `LCD:PRINT:row,col:텍스트` 형태의 명령으로 LCD를 제어합니다.

#### 3.9 EZMaker 밝기센서 블록 (EZLIGHT 전용)

EZMaker 밝기센서(EZLIGHT)는 **딥코보드의 기본 조도센서(LIGHT)와는 처리 방식이 다른, EZMaker 전용 아날로그 센서**입니다.  
펌웨어/JS 레벨에서는 공통 `LIGHT` 센서와 분리하여, 별도의 `EZLIGHT` 명령과 전용 캐릭터리스틱을 사용합니다.

| 카테고리     | 블록 한글 문구                                            | 영문 설명                                                         | JS 코드 템플릿 (예시) |
| :----------- | :--------------------------------------------------------- | :---------------------------------------------------------------- | :-------------------- |
| EZ밝기센서   | EZ 밝기센서 핀(ADC 핀)으로 초기화 하기                  | initialize ezLightSensor adc pin: (adcPin)                       | `let ezLightSensor = new EzLightSensor();`<br>`ezLightSensor.setPin(adcPin).then(() => {`<br>`    console.log("EZLIGHT 센서 핀 설정 완료");`<br>`}).catch(err => {`<br>`    console.error("EZLIGHT 센서 핀 설정 실패:", err);`<br>`});` |
| EZ밝기센서   | EZ 밝기센서에서 (Raw), (Percent) 값 가져오기                | get (raw, percent) from ezLightSensor (0~1023, 0~100%)           | `let ezLightData = await getValidEzLightValue(ezLightSensor);`<br>`let raw     = ezLightData.raw;`<br>`let percent = ezLightData.percent;` |

> EZLIGHT 센서 블록은 `EZLIGHT:PIN:<핀번호>`, `EZLIGHT:STATUS` 명령을 사용하며,  
> 펌웨어에서는 `ez_light_sensor.py` 의 `EzLightSensor` 드라이버와 `bleIoT.py` 의 EZLIGHT 핸들러를 통해  
> 0~1023(10bit) Raw 값과 0~100% 밝기 비율을 한 번에 측정해  
> `EZLIGHT:<raw>,<percent>` 포맷으로 BLE에 전송합니다.  
> JS 쪽에서는 `integratedBleLib_Camera.js` 의 `EzLightSensor` 클래스와  
> `getValidEzLightValue(sensor)` 보조 함수를 통해  
> **핀 설정 → 상태 요청 → 응답 파싱 → `{ raw, percent }` 객체 반환** 흐름을 사용할 수 있습니다.

#### 3.10 EZMaker 전압센서 블록 (EZVOLT 전용)

EZMaker 전압센서(EZVOLT)는 **두 단자 사이의 직류(DC) 전압(0~25V)을 측정하는 EZMaker 전용 아날로그 센서**입니다.  
내부적으로는 0~25V 입력을 보드의 0~3.3V ADC 범위로 분할한 뒤, 10비트(0~1023) Raw 값과 0~25V 환산 전압을 제공합니다.

| 카테고리   | 블록 한글 문구                                           | 영문 설명                                                           | JS 코드 템플릿 (예시) |
| :--------- | :-------------------------------------------------------- | :------------------------------------------------------------------ | :-------------------- |
| EZ전압센서 | EZ 전압센서 핀(ADC 핀)으로 초기화 하기                    | initialize ezVoltSensor adc pin: (adcPin)                          | `let ezVoltSensor = new EzVoltSensor();`<br>`ezVoltSensor.setPin(adcPin).then(() => {`<br>`    console.log("EZVOLT 센서 핀 설정 완료");`<br>`}).catch(err => {`<br>`    console.error("EZVOLT 센서 핀 설정 실패:", err);`<br>`});` |
| EZ전압센서 | EZ 전압센서에서 Raw, 전압(voltage) 값 가져오기             | get (raw, voltage) from ezVoltSensor (0~1023, 0~25V scaled)        | `let ezVoltData = await getValidEzVoltValue(ezVoltSensor);`<br>`let raw     = ezVoltData.raw;`<br>`let voltage = ezVoltData.voltage;` |

> EZVOLT 센서 블록은 `EZVOLT:PIN:<핀번호>`, `EZVOLT:STATUS` 명령을 사용하며,  
> 펌웨어에서는 `ez_volt_sensor.py` 의 `EzVoltSensor` 드라이버와 `bleIoT.py` 의 EZVOLT 핸들러를 통해  
> 0~1023(10bit) Raw 값과 0~25V 환산 전압을 한 번에 측정해  
> `EZVOLT:<raw>,<voltage>` 포맷으로 BLE에 전송합니다.  
> JS 쪽에서는 `integratedBleLib_Camera.js` 의 `EzVoltSensor` 클래스와  
> `getValidEzVoltValue(sensor)` 보조 함수를 통해  
> **핀 설정 → 상태 요청 → 응답 파싱 → `{ raw, voltage }` 객체 반환** 흐름을 사용할 수 있습니다.

#### 3.11 EZMaker 전류센서 블록 (EZCURR 전용)

EZMaker 전류센서(EZCURR)는 **INA219 기반 I2C 전류/전압 센서**로, 샌트 저항을 통해 **측정 회로에 흐르는 전류(mA)** 와 **버스 전압(V)** 을 동시에 측정합니다.  
펌웨어/JS 레벨에서는 `EZCURR` 명령과 전용 캐릭터리스틱을 사용하며, I2C SDA/SCL 핀을 설정한 뒤 전류/전압 값을 읽어옵니다.

| 카테고리   | 블록 한글 문구                                                 | 영문 설명                                                                    | JS 코드 템플릿 (예시) |
| :--------- | :-------------------------------------------------------------- | :--------------------------------------------------------------------------- | :-------------------- |
| EZ전류센서 | EZ 전류센서 I2C 핀으로 초기화 하기                           | initialize ezCurrSensor on I2C pins                                           | `let ezCurrSensor = new EzCurrSensor();`<br>`// I2C 공통 핀 상수(단일 소스): EZ_I2C_SDA_PIN / EZ_I2C_SCL_PIN`<br>`ezCurrSensor.setPin(EZ_I2C_SDA_PIN, EZ_I2C_SCL_PIN).then(() => {`<br>`    console.log("EZCURR 센서 I2C 핀 설정 완료");`<br>`}).catch(err => {`<br>`    console.error("EZCURR 센서 I2C 핀 설정 실패:", err);`<br>`});` |
| EZ전류센서 | EZ 전류센서에서 전류(current mA), 전압(voltage V) 값 가져오기  | get (current_mA, voltage) from ezCurrSensor (mA, V from INA219 measurement) | `let ezCurrData = await getValidEzCurrValue(ezCurrSensor);`<br>`let current_mA = ezCurrData.current_mA;`<br>`let voltage    = ezCurrData.voltage;` |

> EZCURR 센서 블록은 `EZCURR:PIN:SDA,SCL`, `EZCURR:STATUS` 명령을 사용하며,  
> 펌웨어에서는 `ez_curr_sensor.py` 의 `EzCurrSensor` 드라이버와 `bleIoT.py` 의 EZCURR 핸들러를 통해  
> INA219로부터 버스 전압과 샌트 전류를 읽어 **전류(mA)와 전압(V)** 를 계산한 뒤  
> `EZCURR:<current_mA>,<voltage>` 포맷으로 BLE에 전송합니다.  
> JS 쪽에서는 `integratedBleLib_Camera.js` 의 `EzCurrSensor` 클래스와  
> `getValidEzCurrValue(sensor)` 보조 함수를 통해  
> **I2C 핀 설정 → 상태 요청 → 응답 파싱 → `{ current_mA, voltage }` 객체 반환** 흐름을 사용할 수 있습니다.

#### 3.12 EZMaker 인체감지 센서 블록 (HUMAN 전용)

EZMaker 인체감지 센서(HUMAN)는 **PIR 방식의 디지털 인체감지 센서**로,  
사람의 움직임(열 변화)을 감지하면 `1`, 감지하지 못하면 `0`을 반환합니다.  
펌웨어/JS 레벨에서는 `HUMAN` 명령과 전용 EZMaker 캐릭터리스틱을 사용합니다.

| 카테고리     | 블록 한글 문구                                       | 영문 설명                                                     | JS 코드 템플릿 (예시) |
| :----------- | :---------------------------------------------------- | :------------------------------------------------------------ | :-------------------- |
| 인체감지센서 | 인체감지 센서 핀(pinNum)으로 초기화 하기             | initialize humanSensor pin: (pinNum)                         | `let humanSensor = new HumanSensor();`<br>`humanSensor.setPin(pinNum).then(() => {`<br>`    console.log("HUMAN 센서 핀 설정 완료");`<br>`}).catch(err => {`<br>`    console.error("HUMAN 센서 핀 설정 실패:", err);`<br>`});` |
| 인체감지센서 | 인체감지 센서에서 감지 여부(humanValue) 값 가져오기  | get (humanValue) from humanSensor                            | `let humanValue = await getValidHumanValue(humanSensor);`  // 0 또는 1 |

> 인체감지 센서 블록은 `HUMAN:PIN:<핀번호>`, `HUMAN:STATUS` 명령을 사용하며,  
> 펌웨어에서는 `human_sensor.py` 의 `HumanSensor` 드라이버와 `bleIoT.py` 의 HUMAN 핸들러를 통해  
> 디지털 입력 값을 읽어 **감지(1) / 미감지(0)** 를 판별한 뒤  
> `HUMAN:<value>` 포맷으로 BLE에 전송합니다.  
> JS 쪽에서는 `integratedBleLib_Camera.js` 의 `HumanSensor` 클래스와  
> `getValidHumanValue(sensor)` 보조 함수를 통해  
> **핀 설정 → 상태 요청 → 응답 파싱 → `0/1 값 반환`** 흐름을 사용할 수 있습니다.

#### 3.13 EZMaker 수중/접촉 온도센서 블록 (EZTHERMAL, DS18B20 전용)

EZMaker 수중/접촉 온도센서(EZTHERMAL)는 **DS18B20 기반 1-Wire 디지털 온도 프로브**로,  
액체(물) 속이나 물체 표면, 공기 중의 온도를 \(-55℃ \sim +125℃\) 범위에서 측정할 수 있습니다.  
펌웨어/JS 레벨에서는 `EZTHERMAL` 명령과 전용 EZMaker 캐릭터리스틱을 사용합니다.

| 카테고리         | 블록 한글 문구                                         | 영문 설명                                                  | JS 코드 템플릿 (예시) |
| :--------------- | :----------------------------------------------------- | :--------------------------------------------------------- | :-------------------- |
| 수중/접촉온도센서 | 수중/접촉 온도센서 핀(pinNum)으로 초기화 하기          | initialize ezThermalSensor pin: (pinNum)                  | `let ezThermalSensor = new EzThermalSensor();`<br>`ezThermalSensor.setPin(pinNum).then(() => {`<br>`    console.log("EZTHERMAL 센서 핀 설정 완료");`<br>`}).catch(err => {`<br>`    console.error("EZTHERMAL 센서 핀 설정 실패:", err);`<br>`});` |
| 수중/접촉온도센서 | 수중/접촉 온도센서에서 온도(temperature) 값 가져오기   | get (temperature) from ezThermalSensor (°C)               | `let ezThermalData = await getValidEzThermalValue(ezThermalSensor);`<br>`let temperature = ezThermalData.temperature;` |

> 수중/접촉 온도센서 블록은 `EZTHERMAL:PIN:<핀번호>`, `EZTHERMAL:STATUS` 명령을 사용하며,  
> 펌웨어에서는 `ez_thermal_sensor.py` 의 `EzThermalSensor` 드라이버와 `bleIoT.py` 의 EZTHERMAL 핸들러를 통해  
> DS18B20 으로부터 현재 온도(섭씨, ℃)를 읽어  
> `EZTHERMAL:<temperatureC>` 포맷으로 BLE에 전송합니다.  
> JS 쪽에서는 `integratedBleLib_Camera.js` 의 `EzThermalSensor` 클래스와  
> `getValidEzThermalValue(sensor)` 보조 함수를 통해  
> **핀 설정 → 상태 요청 → 응답 파싱 → `{ temperature }` 객체 반환** 흐름을 사용할 수 있습니다.

#### 3.14 EZMaker 소리센서 블록 (EZSOUND 전용)

EZMaker 소리센서(EZSOUND)는 **마이크 기반 아날로그 소리 레벨 센서**로,  
주변 음량을 0~1023(10비트) Raw 값과 0~100% 비율 값으로 표현합니다.  
펌웨어/JS 레벨에서는 `EZSOUND` 명령과 전용 EZMaker 캐릭터리스틱을 사용합니다.

| 카테고리   | 블록 한글 문구                                           | 영문 설명                                                          | JS 코드 템플릿 (예시) |
| :--------- | :-------------------------------------------------------- | :----------------------------------------------------------------- | :-------------------- |
| EZ소리센서 | EZ 소리센서 핀(ADC 핀)으로 초기화 하기                    | initialize ezSoundSensor adc pin: (adcPin)                         | `let ezSoundSensor = new EzSoundSensor();`<br>`ezSoundSensor.setPin(adcPin).then(() => {`<br>`    console.log("EZSOUND 센서 핀 설정 완료");`<br>`}).catch(err => {`<br>`    console.error("EZSOUND 센서 핀 설정 실패:", err);`<br>`});` |
| EZ소리센서 | EZ 소리센서에서 (Raw), (Percent) 값 가져오기              | get (raw, percent) from ezSoundSensor (0~1023, 0~100%)             | `let ezSoundData = await getValidEzSoundValue(ezSoundSensor);`<br>`let raw     = ezSoundData.raw;`<br>`let percent = ezSoundData.percent;` |

> EZSOUND 센서 블록은 `EZSOUND:PIN:<핀번호>`, `EZSOUND:STATUS` 명령을 사용하며,  
> 펌웨어에서는 `ez_sound_sensor.py` 의 `EzSoundSensor` 드라이버와 `bleIoT.py` 의 EZSOUND 핸들러를 통해  
> 0~1023(10bit) Raw 값과 0~100% 소리 레벨 비율을 측정해  
> `EZSOUND:<raw>,<percent>` 포맷으로 BLE에 전송합니다.  
> JS 쪽에서는 `integratedBleLib_Camera.js` 의 `EzSoundSensor` 클래스와  
> `getValidEzSoundValue(sensor)` 보조 함수를 통해  
> **핀 설정 → 상태 요청 → 응답 파싱 → `{ raw, percent }` 객체 반환** 흐름을 사용할 수 있습니다.

#### 3.15 EZMaker 무게센서 블록 (EZWEIGHT, HX711 전용)

EZMaker 무게센서(EZWEIGHT)는 **HX711 로드셀 앰프 기반의 무게 측정 센서**입니다.  
딥코보드 + EZMaker 쉴드 조합에서는 HX711의 DOUT(DT), SCK(CLK) 핀이 **보드의 특정 UART 핀 쌍(예: GPIO 42, 14)** 에 고정 배선되어 있으며,  
펌웨어/JS 레벨에서는 이 **미리 정의된 핀 매핑**을 사용하여 센서를 초기화합니다.  
따라서 블록코드에서는 I2C LCD 나 EZCURR 전류센서처럼, **사용자가 핀을 직접 고르지 않고 무게센서를 선택만 하면** 되도록 설계합니다.

| 카테고리   | 블록 한글 문구                                     | 영문 설명                                              | JS 코드 템플릿 (예시) |
| :--------- | :-------------------------------------------------- | :----------------------------------------------------- | :-------------------- |
| EZ무게센서 | 무게센서를 UART 핀으로 초기화 하기                  | initialize ezWeightSensor on UART pins                | `let ezWeightSensor = new EzWeightSensor();`<br>`// UART 핀 상수(단일 소스): EZ_UART_TX_PIN / EZ_UART_RX_PIN`<br>`// EZWEIGHT:PIN:DOUT,SCK 이므로 (DOUT=EZ_UART_TX_PIN, SCK=EZ_UART_RX_PIN)`<br>`ezWeightSensor.setPin(EZ_UART_TX_PIN, EZ_UART_RX_PIN).then(() => {`<br>`    console.log("EZWEIGHT 센서 setPin 완료");`<br>`}).catch(err => {`<br>`    console.error("EZWEIGHT 센서 setPin 실패:", err);`<br>`});` |
| EZ무게센서 | EZ 무게센서에서 무게(weight)g 값 가져오기          | get (weight)g from ezWeightSensor                     | `let ezWeightData = await getValidEzWeightValue(ezWeightSensor);`<br>`let raw    = ezWeightData.raw;`<br>`let weight = ezWeightData.weight;` |

> EZWEIGHT 센서 블록은 `EZWEIGHT:PIN:DOUT,SCK`, `EZWEIGHT:STATUS` 명령을 사용하며,  
> 펌웨어에서는 `ez_weight_sensor.py` 의 `EzWeightSensor` 드라이버와 `bleIoT.py` 의 EZWEIGHT 핸들러를 통해  
> HX711 로부터 Raw 카운트 값을 읽고, 보정 스케일을 적용해 **무게(g)** 값을 계산한 뒤  
> `EZWEIGHT:<raw>,<weight>` 포맷으로 BLE에 전송합니다.  
> JS 쪽에서는 `integratedBleLib_Camera.js` 의 `EzWeightSensor` 클래스와  
> `EZ_UART_TX_PIN` / `EZ_UART_RX_PIN` 상수를 통해  
> **(미리 정의된 UART 공통 핀으로 setPin) → 상태 요청 → 응답 파싱 → `{ raw, weight }` 객체 반환** 흐름을 사용할 수 있습니다.

#### 3.16 EZMaker 미세먼지 센서 블록 (EZDUST, PMS7003M 전용)

EZMaker 미세먼지 센서(EZDUST)는 **PMS7003M 기반 레이저 산란 방식 디지털 미세먼지 센서**로,  
한 번의 측정으로 **PM10 / PM2.5 / PM1.0** 세 가지 농도 값을 동시에 제공합니다.  
펌웨어/JS 레벨에서는 `EZDUST` 명령과 전용 EZMaker 캐릭터리스틱을 사용하며,  
UART 핀은 무게센서와 동일한 **UART 공통 핀(42, 14)** 을 사용합니다.

| 카테고리       | 블록 한글 문구                                                                                 | 영문 설명                                                                                 | JS 코드 템플릿 (예시) |
| :------------- | :---------------------------------------------------------------------------------------------- | :---------------------------------------------------------------------------------------- | :-------------------- |
| EZ미세먼지센서 | 먼지 센서를 UART 핀으로 초기화 하기                                                         | initialize ezDustSensor on UART pins                                               | `let ezDustSensor = new EzDustSensor();`<br>`// UART 핀 상수(단일 소스): EZ_UART_TX_PIN / EZ_UART_RX_PIN`<br>`// EZDUST:PIN:RX,TX 이므로 (RX=EZ_UART_RX_PIN, TX=EZ_UART_TX_PIN)`<br>`ezDustSensor.setPin(EZ_UART_RX_PIN, EZ_UART_TX_PIN).then(() => {`<br>`    console.log("EZDUST 센서 setPin 완료");`<br>`}).catch(err => {`<br>`    console.error("EZDUST 센서 setPin 실패:", err);`<br>`});` |
| EZ미세먼지센서 | 먼지 센서에서 미세먼지값(pm10), 초미세먼지값(pm2_5), 극초미세먼지값(pm1_0) 가져오기         | get (pm10, pm2_5, pm1_0) from ezDustSensor (all at once)                          | `let ezDustData = await getValidEzDustValue(ezDustSensor);`<br>`let pm10  = ezDustData.pm10;`<br>`let pm2_5 = ezDustData.pm2_5;`<br>`let pm1_0 = ezDustData.pm1_0;` |

> EZDUST 센서 블록은 `EZDUST:PIN:RX,TX`, `EZDUST:STATUS` 명령을 사용하며,  
> 펌웨어에서는 `ez_dust_pms7003.py` 의 `EzDustSensor` 드라이버와 `bleIoT.py` 의 EZDUST 핸들러를 통해  
> PMS7003M 으로부터 **PM10 / PM2.5 / PM1.0** 세 가지 농도(μg/m³)를 읽어  
> `EZDUST:PM10,PM2.5,PM1.0` 포맷으로 BLE에 전송합니다.  
> JS 쪽에서는 `integratedBleLib_Camera.js` 의 `EzDustSensor` 클래스와  
> `getValidEzDustValue(sensor)` 보조 함수를 통해  
> **(미리 정의된 UART 공통 핀으로 setPin) → 상태 요청 → 응답 파싱 → `{ pm10, pm2_5, pm1_0 }` 객체 반환** 흐름을 사용할 수 있습니다.  
> 즉, 한 번의 측정으로 **미세먼지(PM10) / 초미세먼지(PM2.5) / 극초미세먼지(PM1.0)** 세 값을 동시에 가져옵니다.
>
> 참고: 초미세먼지(PM2.5)는 데이터 키/변수명 모두 `pm2_5` 로 통일합니다.

---

### 4. 향후 확장 메모

- 이 문서는 **엑셀 파일의 전체 내용을 대체하지 않고**,  
  중요한 블록(LED, 레이저, EZMaker 센서 등)을 markdown으로 빠르게 확인하기 위한 요약본입니다.
- 이후 다른 EZMaker 센서/액츄에이터(초음파, 네오픽셀, DC 모터 등)에 대해서도  
  같은 형식의 표를 추가하여 관리할 수 있습니다.


