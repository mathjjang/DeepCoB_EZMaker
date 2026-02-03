## MicroPython → Arduino 전환 계획 (DeepCoB_Ezmaker_v1.3.7)

이 문서는 `DeepCoB_EZMaker`(MicroPython 기반)를 `arduino/DeepCoB_Ezmaker_v1.3.7`(Arduino/ESP-IDF/FreeRTOS 기반)로 단계적으로 이관하기 위한 **전환 전략/작업 순서/체크리스트**입니다.  
큰 프로젝트이므로 "한 번에 포팅"이 아니라, **통신(BLE) 기반을 먼저 안정화**하고 이후 **센서/액츄에이터를 모듈 단위로 확장**합니다.

> **중요(Arduino IDE 폴더 규칙)**  
> Arduino IDE 스케치 폴더(`arduino/DeepCoB_Ezmaker_v1.3.7/`)에는 **소스(.ino/.h/.cpp 등)만** 두고,  
> 문서/리소스는 스케치 폴더 밖(`arduino/`)에 별도로 관리합니다. (컴파일/빌드 충돌 방지)

---

### 1) 프로젝트 개요 (현재 상태 요약)

- **보드/플랫폼**: DeepCo Board v2.0 (ESP32‑S3) + EZMAKER Shield v2.0
- **현재 펌웨어**: MicroPython (`source/lib/bleBaseIoT.py`, `source/lib/bleIoT.py`)
- **현재 웹/블록 연동**: Web Bluetooth (`IoTmode/*`, 특히 `integratedBleLib_Camera.js`)
- **문서/블록 사양**:
  - `EZMaker_블록코드정의.md` (블록 ↔ JS 템플릿 ↔ BLE 문자열 프로토콜)
  - `EZMaker프로젝트.md` (핀맵/센서 목록/작업 기록)

---

### 2) 전환 목표(성능/구조)

- **성능 목표**
  - 카메라 스트리밍 도중에도 버저/센서 제어가 "즉시 반응"하도록 지터/지연 최소화
  - BLE 전송 파이프라인(특히 카메라 notify)이 병목이 되지 않도록 큐/스케줄링/MTU 최적화

- **구조 목표**
  - **Arduino/FreeRTOS 장점을 최대한 활용**: UUID/프로토콜/Task 분리 구조를 새로 설계
  - **블록 인터페이스만 유지**: JS API(예: `camera.startStreaming()`)는 동일하게, 내부(BLE UUID/전송 포맷)는 최적화
  - **MicroPython 전용 개념 제거**: REPL 서비스, MicroPython GC/버퍼 회피용 설계 등은 삭제
  - FreeRTOS Task/Queue로 모듈 분리
    - Camera capture/encode
    - BLE Tx (notify) / BLE Rx (write parsing)
    - Sensors polling/measurement
    - Actuators (buzzer/motor/neo 등)

---

### 3) 전환 전략 (권장 아키텍처)

#### 3.1 "Arduino 최적화 우선" 전략 ✅ (확정)
1) **BLE UUID/특성 구조**: MicroPython 구조(IoT/Sensor service)를 Arduino에 맞게 재설계
   - 카메라: 전용 서비스(Streaming 최적화)
   - 센서: 필요 시 특성을 더 세분화(status/config/streaming 등 분리)
   - **REPL 서비스/특성은 제거**(Arduino엔 불필요)
2) **프로토콜 포맷**: 카메라는 바이너리 중심, 센서/액츄에이터는 텍스트 간소화
3) **JS 라이브러리(`arduino/integratedBleLib_Camera.js`)도 새로 만들기**
   - 블록 API(예: `camera.startStreaming()`, `ezCo2Sensor.setPin(...)`)는 유지
   - 내부 UUID/파서/프레이밍은 Arduino 프로토콜에 맞게 구현

#### 3.2 Task 분리 전략(카메라/버저 유스케이스 중심)
- **BLE Rx Task**: write 수신 → 문자열 파싱 → 각 모듈 큐로 디스패치
- **Camera Task**: 캡처/압축(JPEG) → 프레임 큐(최신 1장 또는 링버퍼)
- **BLE Tx Task**: 바이너리 프레임 전송 + 센서 notify
- **Buzzer/Actuator Task**: PWM/타이밍 제어(카메라 전송과 무관하게 안정 동작)

> 핵심: "카메라 전송이 오래 걸려도" 버저 제어 명령이 큐를 통해 즉시 반영되도록 우선순위를 설계.

---

### 4) 작업 순서(추천)

#### Phase 0. 기준선/환경 확정
- **보드 정의/핀맵 확정**: `EZMaker프로젝트.md` 기준으로 Arduino 핀 매핑 정리
- **BLE 스택 선택**: Arduino-ESP32(ESP-IDF) BLE 라이브러리 선택(가능하면 BLE5 기능/성능이 좋은 스택)
- **결정사항 정리**:
  - [ ] 카메라 바이너리 프로토콜 설계(프레임 헤더 포맷/MTU 전략)
  - [ ] 새 BLE 서비스/특성 UUID 매핑 설계(MicroPython 구조와 다르게 갈 수 있음)
  - [ ] 블록 API 계약 확정(절대 바꾸지 않을 JS 함수/파라미터/콜백)

#### Phase 1. BLE 통신 기반(최우선)
- **서비스/특성(UUID) 새로 설계**
  - Camera Service(전용): TX(notify), RX(write), STATUS(notify) 분리
  - Sensor/Actuator Service: 센서별 특성(PIN/STATUS/STREAM 등)
  - **REPL Service 제거**(Arduino에서 불필요)
- **MTU/버퍼/연결 파라미터 튜닝**
  - MTU 최대 협상(512 이상 목표)
  - 연결 interval/latency 최소화
- **명령 파서**
  - 센서/액츄에이터 제어는 여전히 텍스트 기반 명령(간소화)
  - 카메라는 바이너리 헤더 + 커맨드 코드 방식

#### Phase 2. 카메라 프로토콜부터 붙이기(스트리밍)
- **Arduino 펌웨어: 바이너리 중심 카메라 전송**
  - 프레임 헤더(magic/버전/seq/len/flags) + JPEG payload
  - notify당 최대 MTU 활용(텍스트 헤더 오버헤드 제거)
  - FreeRTOS Task: Camera Task(캡처) → TX Queue → BLE TX Task(notify)

- **웹(`arduino/integratedBleLib_Camera.js`): 바이너리 파서 새로 구현**
  - 블록 API는 기존과 동일(`camera.startStreaming()`, `camera.takeSnapshot()`, `camera.onImageComplete(callback)` 등)
  - 내부: 새 Camera Service UUID + 바이너리 프레임 파서로 교체

- **성능 체크포인트**
  - 프레임 크기(평균 KB)
  - notify rate(초당 packet 수)
  - JS에서 프레임 완성 FPS
  - 버저 제어 응답시간(카메라 ON 중에도 100ms 이내 목표)

#### Phase 3. 버저(Actuator) 우선 통합
- 카메라 스트리밍 ON 상태에서
  - 버저 제어가 지연 없이 동작하는지 검증
  - PWM/타이머가 카메라와 무관하게 동작하는지 확인

#### Phase 4. 센서/액츄에이터 모듈별 추가(우선순위 기반)
- **우선순위 추천**(웹 테스트/블록 사용 빈도 + 구현 난이도)
  - 디지털 단순: LASER, HUMAN(PIR), TOUCH
  - 아날로그 단순: EZLIGHT, EZSOUND, DIYA/DIYB, HALL
  - I2C: EZPRESS(BMP280), EZCO2(SCD40), EZCURR(INA219), LCD
  - UART: EZDUST(PMS7003M), EZWEIGHT(HX711)
  - PWM/구동: SERVO, DCMOTOR, NEOPIXEL

---

### 5) "MicroPython → Arduino" 매핑 가이드

- **BLE 스펙/프로토콜 기준 소스**
  - MicroPython: `source/lib/bleBaseIoT.py`, `source/lib/bleIoT.py`
  - Web(JS 신규): `arduino/integratedBleLib_Camera.js`

- **카메라**
  - MicroPython: `source/lib/cameraModule.py` + `bleIoT.py` 카메라 핸들러/프레임 전송
  - Arduino: Camera Service(새 UUID) + 바이너리 프레임 전송(Task 분리)
  - Web(JS 신규): `class Camera`의 바이너리 프레임 파서(블록 API는 동일 유지)

- **버저**
  - MicroPython: `source/lib/buzzerModule.py` + `bleIoT.py`의 `buzzer_handler`
  - Arduino: PWM(LEDC) + 별도 Task/Timer 기반 재생(카메라와 독립)

- **제거 대상(Arduino에서 불필요)**
  - REPL 서비스/특성(MicroPython 인터프리터 전용)
  - 펌웨어 업그레이드 특성(Arduino는 OTA 표준 사용 가능)
  - MicroPython 특유 GC/메모리 회피 패턴(Arduino는 정적 할당 가능)

---

### 6) 산출물(파일/폴더 구조 제안)

#### 스케치 폴더(Arduino IDE가 여는 폴더: 소스만)

`arduino/DeepCoB_Ezmaker_v1.3.7/`
- `DeepCoB_Ezmaker_v1.3.7.ino` (엔트리, setup/loop 최소화)
- `src/` (모듈화 권장: .h/.cpp)
  - `BleProtocol.h/.cpp` (명령 파서/디스패치)
  - `BleServices.h/.cpp` (UUID/특성 등록)
  - `CameraTask.h/.cpp`
  - `BuzzerTask.h/.cpp`
  - `Sensors/*.h/.cpp`
  - `Actuators/*.h/.cpp`

#### 문서/웹 코드(스케치 폴더 밖)

`arduino/`
- `마이크로파이썬to아두이노.md` (본 문서)
- `integratedBleLib_Camera.js` (Arduino 펌웨어 프로토콜에 맞춘 Web Bluetooth 라이브러리(블록 API는 유지))

---

### 7) 작업 체크리스트 (TODO)

다음 순서로 하나씩 구현/검증합니다.

#### Phase 0 (환경/결정사항)
- [ ] Arduino 핀맵 정리(`EZMaker프로젝트.md` 기준) → `arduino/pinmap.h`
- [ ] 카메라 바이너리 프로토콜 설계 확정(프레임 헤더 구조/크기/필드)
- [ ] 새 BLE UUID 체계 설계(Camera Service 등)
- [ ] 블록 API 계약 확정(절대 바꾸지 않을 JS 함수/파라미터/콜백)

#### Phase 1 (BLE 기반)
- [ ] BLE Server 초기화(Arduino-ESP32 BLE 라이브러리)
- [ ] Camera Service UUID/특성 등록(TX/RX/STATUS)
- [ ] MTU 협상 구현(최대 512+)
- [ ] Write 수신/파서 뼈대(문자열 명령 → Queue)
- [ ] Notify 전송 뼈대(Queue → BLE TX)

#### Phase 2 (카메라)
- [ ] Camera Task: `esp_camera.h` 기반 캡처 루프
- [ ] 프레임 큐(최신 1장 유지 정책)
- [ ] BLE TX Task: 바이너리 헤더 + 청크 전송
- [ ] JS(`arduino/integratedBleLib_Camera.js`): 바이너리 파서 구현(블록 API 유지)
- [ ] 테스트: 웹에서 스트리밍/스냅샷 동작 확인

#### Phase 3 (버저)
- [ ] Buzzer Task: PWM/멜로디 재생(카메라와 독립)
- [ ] 명령 파서(예: `BUZ:BEEP`, `BUZ:PLAY:MELODY`, `BUZ:STOP`)
- [ ] 테스트: 카메라 스트리밍 중 버저 즉시 반응 확인

#### Phase 4+ (센서/액츄에이터)
- [ ] 우선순위 센서(EZCO2, EZGYRO, EZPRESS, LASER 등)를 순차 추가
- [ ] 각 센서별로 특성 등록 → 명령 파서 → 드라이버 구현 → 웹 JS 매핑 → 테스트

---

### 8) 전환 시 고려사항/노트

#### 8.1 블록 API 계약(변경 금지)
블록코딩이 호출하는 JS 메서드/프로퍼티는 이름/파라미터/반환값이 바뀌면 안 됩니다.

**카메라 예시(유지해야 할 API)**:
- `let camera = new Camera();`
- `await camera.startStreaming();`
- `await camera.stopStreaming();`
- `await camera.takeSnapshot();`
- `camera.onImageComplete = (blob) => { ... };`
- `camera.getLatestImage()` 등

**센서 예시(유지해야 할 API)**:
- `let ezCo2Sensor = new EzCo2Sensor();`
- `await ezCo2Sensor.setPin(sdaPin, sclPin);`
- `let data = await getValidEzCo2Value(ezCo2Sensor);`
- `data.co2`, `data.temp`, `data.humidity` 등

#### 8.2 MicroPython → Arduino 제거 대상
- **REPL 서비스/특성** (`REPL_SERVICE`, `REPL_CHARACTERISTIC` 등)
- **펌웨어 업그레이드 특성** (`UPGRADE_CHAR` 등, Arduino OTA 표준 사용)
- `gc.collect()` 회피용 설계(Arduino는 메모리 정적 관리 가능)
- MicroPython 텍스트 프레임 프로토콜(`CAM:START/SIZE/BIN{seq}:...`)

#### 8.3 카메라 바이너리 프로토콜 제안(Phase 0에서 확정 필요)
- **프레임 헤더**(예시, 고정 8바이트):
  - `0xFF 0xCA` (magic, 2B)
  - `version` (1B, 프로토콜 버전)
  - `flags` (1B, 비트: START/END/ERROR 등)
  - `seq` (2B, 프레임 번호)
  - `len` (2B, 이 패킷의 payload 길이)
- **장점**: 헤더 파싱 빠름, 텍스트 인코딩 불필요, MTU 최대 활용
- **JS 구현**: `DataView`로 고정 offset 읽기 → Uint8Array로 payload 추출

