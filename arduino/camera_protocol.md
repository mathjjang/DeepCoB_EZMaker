# 카메라 바이너리 프로토콜 설계 (Arduino 최적화)

## 1. 설계 목표

- **텍스트 오버헤드 제거**: MicroPython의 `CAM:START`, `SIZE:1234`, `BIN123:<data>` 등 텍스트 헤더를 제거
- **MTU 최대 활용**: ESP32-S3 BLE는 최대 512바이트 MTU 협상 가능, payload를 최대한 키워 notify 횟수 감소
- **고정 길이 헤더**: 파싱 속도 최적화 (offset 계산 불필요)
- **에러 감지**: 프레임 경계/순서 확인 가능한 구조

---

## 2. 프레임 헤더 구조 (8바이트 고정)

```
Offset | Size | Field   | Description
-------|------|---------|--------------------------------------------
0      | 2B   | MAGIC   | 0xFF 0xCA (고정, 프레임 경계 식별)
2      | 1B   | VERSION | 프로토콜 버전 (현재: 0x01)
3      | 1B   | FLAGS   | 비트 플래그 (아래 참조)
4      | 2B   | SEQ     | 프레임 번호 (0~65535, 순환)
6      | 2B   | LEN     | 이 패킷의 payload 길이 (0~504)
```

### FLAGS 비트 정의 (1바이트)

```
Bit 7 6 5 4 3 2 1 0
    | | | | | | | +-- START  (0x01): 프레임 시작 청크
    | | | | | | +---- END    (0x02): 프레임 마지막 청크
    | | | | | +------ ERROR  (0x04): 에러 발생 (전송 중단)
    | | | | +-------- STREAM (0x08): 스트리밍 모드 (vs 스냅샷)
    | | | +---------- reserved
    | | +------------ reserved
    | +-------------- reserved
    +---------------- reserved
```

**예시**:
- 첫 청크: `FLAGS = 0x09` (START | STREAM)
- 중간 청크: `FLAGS = 0x08` (STREAM)
- 마지막 청크: `FLAGS = 0x0A` (END | STREAM)
- 단일 청크 스냅샷: `FLAGS = 0x03` (START | END)

---

## 3. MTU 협상 전략

### MTU 크기별 Payload

| MTU  | 헤더 | Payload | 프레임당 청크 수 (10KB 기준) |
|------|------|---------|------------------------------|
| 23   | 8B   | 15B     | ~682개 (비효율적)            |
| 185  | 8B   | 177B    | ~58개                        |
| 247  | 8B   | 239B    | ~43개                        |
| 512  | 8B   | 504B    | ~20개 (최적)                 |

**목표**: **MTU 512바이트 협상** (ESP32-S3 BLE5 기준 최대값)

### Arduino 구현

```cpp
// BLE Server 초기화 시
NimBLEDevice::setMTU(512);

// 연결 후 협상
uint16_t mtu = pServer->getPeerMTU(connId);
Serial.printf("Negotiated MTU: %d\n", mtu);

// Payload 크기 계산
const uint16_t FRAME_HEADER_SIZE = 8;
uint16_t maxPayload = mtu - 3 - FRAME_HEADER_SIZE; // BLE overhead 3B
```

---

## 4. 전송 프로토콜 흐름

### 4.1 단일 프레임 전송 (예: 10KB JPEG)

```
┌─────────────────────────────────────────────────────────────┐
│ 청크 0: [0xFF 0xCA 01 09 0000 01F8] + 504B payload (START)  │
├─────────────────────────────────────────────────────────────┤
│ 청크 1: [0xFF 0xCA 01 08 0001 01F8] + 504B payload          │
├─────────────────────────────────────────────────────────────┤
│ 청크 2: [0xFF 0xCA 01 08 0002 01F8] + 504B payload          │
├─────────────────────────────────────────────────────────────┤
│ ...                                                          │
├─────────────────────────────────────────────────────────────┤
│ 청크 19: [0xFF 0xCA 01 0A 0013 0100] + 256B payload (END)   │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 스트리밍 모드

- 프레임 번호(`SEQ`)는 **프레임마다 증가** (청크마다가 아님)
- 각 프레임의 첫 청크는 `START` 플래그 포함
- 마지막 청크는 `END` 플래그 포함
- JS 파서는 `END` 플래그를 받으면 프레임 완성 → 콜백 호출

### 4.3 에러 처리

- **전송 중단**: `FLAGS = 0x04` (ERROR) 패킷 전송 → JS에서 현재 프레임 버림
- **타임아웃**: JS에서 `START` 후 2초 내에 `END` 안 오면 프레임 폐기
- **순서 보장**: `SEQ`가 연속되지 않으면 경고 (BLE는 순서 보장하지만 검증용)

---

## 5. JS 파서 구조 (Web Bluetooth)

### 5.1 수신 버퍼 관리

```javascript
class CameraBinaryParser {
    constructor() {
        this.currentFrame = {
            seq: null,
            chunks: [],
            totalBytes: 0,
            startTime: null
        };
    }

    parseChunk(data) {
        const view = new DataView(data.buffer);
        
        // 헤더 파싱 (8바이트)
        const magic = view.getUint16(0, false); // Big-endian
        if (magic !== 0xFFCA) {
            console.error('Invalid magic:', magic.toString(16));
            return null;
        }
        
        const version = view.getUint8(2);
        const flags = view.getUint8(3);
        const seq = view.getUint16(4, false);
        const len = view.getUint16(6, false);
        
        // Payload 추출
        const payload = new Uint8Array(data.buffer, 8, len);
        
        // START 플래그: 새 프레임 시작
        if (flags & 0x01) {
            this.currentFrame = {
                seq: seq,
                chunks: [payload],
                totalBytes: len,
                startTime: Date.now()
            };
        } else {
            // 중간 청크: 추가
            this.currentFrame.chunks.push(payload);
            this.currentFrame.totalBytes += len;
        }
        
        // END 플래그: 프레임 완성
        if (flags & 0x02) {
            return this.assembleFrame();
        }
        
        // ERROR 플래그: 프레임 버림
        if (flags & 0x04) {
            console.warn('Frame error, discarding');
            this.currentFrame = { seq: null, chunks: [], totalBytes: 0 };
            return null;
        }
        
        return null; // 아직 완성 안 됨
    }
    
    assembleFrame() {
        const total = this.currentFrame.totalBytes;
        const result = new Uint8Array(total);
        let offset = 0;
        
        for (const chunk of this.currentFrame.chunks) {
            result.set(chunk, offset);
            offset += chunk.length;
        }
        
        // Blob 생성 (JPEG)
        const blob = new Blob([result], { type: 'image/jpeg' });
        const elapsed = Date.now() - this.currentFrame.startTime;
        
        console.log(`Frame ${this.currentFrame.seq} complete: ${total} bytes in ${elapsed}ms`);
        
        // 초기화
        this.currentFrame = { seq: null, chunks: [], totalBytes: 0 };
        
        return blob;
    }
}
```

### 5.2 Camera 클래스 연동

```javascript
class Camera extends SensorBase {
    constructor() {
        super('Camera', CAMERA_TX_CHARACTERISTIC, { useCentralOnDataReceived: false });
        this.parser = new CameraBinaryParser();
        this.onImageComplete = null;
    }
    
    _processData(data) {
        const frame = this.parser.parseChunk(data);
        if (frame && this.onImageComplete) {
            this.onImageComplete(frame);
        }
    }
    
    async startStreaming() {
        await this.sendCommand('CAM:STREAM:ON'); // 제어 명령은 텍스트 유지 가능
    }
    
    async stopStreaming() {
        await this.sendCommand('CAM:STREAM:OFF');
    }
}
```

---

## 6. Arduino 전송 코드 예시

### 6.1 프레임 전송 Task

```cpp
#define FRAME_HEADER_SIZE 8
#define MAX_PAYLOAD_SIZE 504 // MTU 512 - 3(BLE) - 8(header)

struct FrameHeader {
    uint16_t magic;   // 0xFFCA
    uint8_t version;  // 0x01
    uint8_t flags;    // START/END/ERROR/STREAM
    uint16_t seq;     // Frame number
    uint16_t len;     // Payload length
} __attribute__((packed));

void sendFrame(uint8_t* jpegData, size_t jpegSize, uint16_t frameSeq) {
    size_t offset = 0;
    uint16_t chunkIndex = 0;
    
    while (offset < jpegSize) {
        size_t remaining = jpegSize - offset;
        size_t payloadSize = (remaining > MAX_PAYLOAD_SIZE) ? MAX_PAYLOAD_SIZE : remaining;
        
        // 헤더 구성
        FrameHeader header;
        header.magic = 0xFFCA;
        header.version = 0x01;
        header.flags = 0x08; // STREAM
        
        if (offset == 0) {
            header.flags |= 0x01; // START
        }
        if (offset + payloadSize >= jpegSize) {
            header.flags |= 0x02; // END
        }
        
        header.seq = frameSeq;
        header.len = payloadSize;
        
        // 패킷 조립 (헤더 + payload)
        uint8_t packet[FRAME_HEADER_SIZE + MAX_PAYLOAD_SIZE];
        memcpy(packet, &header, FRAME_HEADER_SIZE);
        memcpy(packet + FRAME_HEADER_SIZE, jpegData + offset, payloadSize);
        
        // BLE notify 전송
        pCameraCharacteristic->setValue(packet, FRAME_HEADER_SIZE + payloadSize);
        pCameraCharacteristic->notify();
        
        offset += payloadSize;
        chunkIndex++;
        
        // Yield to other tasks (카메라 전송 중에도 버저 제어 가능)
        vTaskDelay(1 / portTICK_PERIOD_MS); // 1ms delay
    }
}
```

---

## 7. 제어 명령 (별도 특성, 텍스트 유지 가능)

카메라 **제어 명령**(시작/정지/설정 등)은 **별도 RX 특성**을 사용하며, 텍스트 프로토콜을 유지해도 무방합니다.

### 7.1 Camera Service UUID 구조

```
Camera Service: 0xCAFE0000-...
├─ TX Characteristic (notify):  0xCAFE0001-... → 바이너리 프레임 전송
├─ RX Characteristic (write):   0xCAFE0002-... → 텍스트 제어 명령
└─ STATUS Characteristic (read): 0xCAFE0003-... → 상태 정보 (텍스트 or JSON)
```

### 7.2 제어 명령 예시 (RX, 텍스트)

- `CAM:STREAM:ON` → 스트리밍 시작
- `CAM:STREAM:OFF` → 스트리밍 중지
- `CAM:SNAP` → 단일 스냅샷 촬영
- `CAM:QUALITY:10` → JPEG 품질 설정 (0~63)
- `CAM:FRAMESIZE:9` → 프레임 크기 설정 (UXGA 등)

**이유**: 제어 명령은 빈도가 낮고 사람이 읽기 쉬운 형태가 디버깅에 유리

---

## 8. 성능 예측 (MTU 512 기준)

### 프레임 크기별 전송 시간

| 프레임 크기 | 청크 수 | 전송 시간 (7.5ms/청크 가정) | FPS |
|-------------|---------|------------------------------|-----|
| 5KB         | ~10개   | ~75ms                        | ~13 |
| 10KB        | ~20개   | ~150ms                       | ~6  |
| 15KB        | ~30개   | ~225ms                       | ~4  |

**목표**: 카메라 캡처(~100ms) + 전송(~150ms) = **총 ~250ms** → **4 FPS 목표**

### MicroPython 대비 개선

| 항목          | MicroPython (텍스트)    | Arduino (바이너리)  | 개선율  |
|---------------|-------------------------|---------------------|---------|
| 헤더 오버헤드 | `BIN123:` (7B/청크)     | 고정 8B/프레임      | ~95%↓   |
| 청크 크기     | 160B                    | 504B                | 3.15배↑ |
| 프레임 전송   | ~70개 청크 (10KB)       | ~20개 청크 (10KB)   | 71%↓    |
| 파싱 속도     | 문자열 split/parseInt   | DataView offset     | ~5배↑   |

---

## 9. Phase 2 구현 체크리스트

### Arduino 펌웨어
- [ ] `CameraService.h/.cpp`: BLE 서비스/특성 등록
- [ ] `CameraBinaryProtocol.h`: 헤더 구조체 정의
- [ ] `CameraTask.cpp`: 캡처 → 인코딩 → TX Queue
- [ ] `BLE_TX_Task.cpp`: Queue → 바이너리 프레이밍 → notify

### JS 라이브러리
- [ ] `CameraBinaryParser` 클래스 구현
- [ ] `Camera` 클래스 `_processData()` 수정
- [ ] 타임아웃/에러 처리 로직
- [ ] FPS 측정/로그 (debug 레벨)

### 테스트
- [ ] MTU 협상 확인 (512 달성 여부)
- [ ] 단일 스냅샷 전송/조립 검증
- [ ] 스트리밍 모드 FPS 측정
- [ ] 카메라 스트리밍 중 버저 제어 응답시간 측정 (100ms 이내 목표)

---

## 10. 참고: MicroPython 기존 프로토콜 (비교용)

```
CAM:START           (텍스트 시작 마커)
SIZE:10240          (프레임 크기 알림)
BIN0:<160바이트>    (청크 0, 헤더 5바이트 + payload 160바이트)
BIN1:<160바이트>    (청크 1)
...
BIN63:<160바이트>   (청크 63)
CAM:END             (텍스트 종료 마커)
```

**문제점**:
- 매 청크마다 `BIN123:` (5~7바이트) 텍스트 헤더 오버헤드
- 청크 크기 160바이트 (MTU 185 기준, payload 효율 86%)
- JS에서 문자열 파싱 → ArrayBuffer 변환 비용
- 프레임당 ~70개 청크 (10KB 기준)

**Arduino 바이너리 프로토콜은 이 모든 문제를 해결합니다.**
