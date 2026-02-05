/**
 * @file CameraTask.cpp
 * @brief Camera capture + BLE MTU-aware chunked notify implementation
 */

#include "CameraTask.h"
#include "BleServer.h"
#include "ble_uuids.h"

// ---------------------------------------------------------------------------
// Board pin mapping (matches MicroPython cameraModule.py)
// data_pins=[11, 9, 8, 10, 12, 18, 17, 16],
// vsync=6 href=7 sda=4 scl=5 pclk=13 xclk=15
// ---------------------------------------------------------------------------
#define CAM_PIN_PWDN    -1
#define CAM_PIN_RESET   -1
#define CAM_PIN_XCLK    15
#define CAM_PIN_SIOD    4
#define CAM_PIN_SIOC    5
#define CAM_PIN_D7      16
#define CAM_PIN_D6      17
#define CAM_PIN_D5      18
#define CAM_PIN_D4      12
#define CAM_PIN_D3      10
#define CAM_PIN_D2      8
#define CAM_PIN_D1      9
#define CAM_PIN_D0      11
#define CAM_PIN_VSYNC   6
#define CAM_PIN_HREF    7
#define CAM_PIN_PCLK    13

// ---------------------------------------------------------------------------
// Binary protocol (arduino/camera_protocol.md)
// Header: 8 bytes (big-endian)
// [MAGIC 0xFFCA][VERSION 0x01][FLAGS][SEQ][LEN]
// LEN is per-chunk payload length (not whole frame length)
// ---------------------------------------------------------------------------
static constexpr uint16_t FRAME_MAGIC = 0xFFCA;
static constexpr uint8_t FRAME_VERSION = 0x01;
static constexpr uint8_t FLAG_START = 0x01;
static constexpr uint8_t FLAG_END = 0x02;
static constexpr uint8_t FLAG_ERROR = 0x04;
static constexpr uint8_t FLAG_STREAM = 0x08;
static constexpr size_t FRAME_HEADER_SIZE = 10;

// Task config
static constexpr uint32_t CAPTURE_TASK_STACK = 8192;
static constexpr uint32_t TX_TASK_STACK = 4096;
static constexpr UBaseType_t CAPTURE_TASK_PRIO = 4;
static constexpr UBaseType_t TX_TASK_PRIO = 5;

// Prefer running BLE TX away from Arduino loop task
static constexpr BaseType_t CAPTURE_CORE = 1;
static constexpr BaseType_t TX_CORE = 0;

CameraTask::CameraTask(BleServer* bleServer)
    : _bleServer(bleServer) {}

CameraTask::~CameraTask() {
    end();
}

bool CameraTask::begin() {
    if (_initialized) return true;

    if (_bleServer == nullptr) {
        Serial.println("[CAM] BleServer is null");
        return false;
    }

    if (!initCamera()) {
        Serial.println("[CAM] Camera init failed");
        return false;
    }

    _frameMutex = xSemaphoreCreateMutex();
    if (_frameMutex == nullptr) {
        Serial.println("[CAM] Failed to create mutex");
        deinitCamera();
        return false;
    }

    if (xTaskCreatePinnedToCore(captureTaskEntry, "CamCap", CAPTURE_TASK_STACK, this,
                               CAPTURE_TASK_PRIO, &_captureTaskHandle, CAPTURE_CORE) != pdPASS) {
        Serial.println("[CAM] Failed to create capture task");
        vSemaphoreDelete(_frameMutex);
        _frameMutex = nullptr;
        deinitCamera();
        return false;
    }

    if (xTaskCreatePinnedToCore(txTaskEntry, "CamTx", TX_TASK_STACK, this,
                               TX_TASK_PRIO, &_txTaskHandle, TX_CORE) != pdPASS) {
        Serial.println("[CAM] Failed to create tx task");
        vTaskDelete(_captureTaskHandle);
        _captureTaskHandle = nullptr;
        vSemaphoreDelete(_frameMutex);
        _frameMutex = nullptr;
        deinitCamera();
        return false;
    }

    _initialized = true;
    Serial.println("[CAM] CameraTask started");
    return true;
}

void CameraTask::end() {
    if (!_initialized) return;

    _streaming = false;
    _snapshotRequested = false;

    if (_captureTaskHandle) {
        vTaskDelete(_captureTaskHandle);
        _captureTaskHandle = nullptr;
    }
    if (_txTaskHandle) {
        vTaskDelete(_txTaskHandle);
        _txTaskHandle = nullptr;
    }

    if (_frameMutex) {
        vSemaphoreDelete(_frameMutex);
        _frameMutex = nullptr;
    }

    if (_pendingFrame) {
        esp_camera_fb_return(_pendingFrame);
        _pendingFrame = nullptr;
        _pendingIsStream = false;
    }

    deinitCamera();
    _initialized = false;
    Serial.println("[CAM] CameraTask stopped");
}

bool CameraTask::startStreaming() {
    if (!_initialized) return false;
    _streaming = true;
    return true;
}

bool CameraTask::stopStreaming() {
    _streaming = false;
    
    // Clear any pending frame to stop TX immediately
    if (_frameMutex && xSemaphoreTake(_frameMutex, pdMS_TO_TICKS(50)) == pdTRUE) {
        if (_pendingFrame) {
            esp_camera_fb_return(_pendingFrame);
            _pendingFrame = nullptr;
            _pendingIsStream = false;
        }
        xSemaphoreGive(_frameMutex);
    }
    return true;
}

bool CameraTask::requestSnapshot() {
    if (!_initialized) return false;
    _snapshotRequested = true;
    return true;
}

bool CameraTask::setStreamInterval(uint32_t intervalMs) {
    if (intervalMs < 50) intervalMs = 50;
    if (intervalMs > 2000) intervalMs = 2000;
    _streamIntervalMs = intervalMs;
    return true;
}

bool CameraTask::setQuality(uint8_t quality) {
    if (quality > 63) quality = 63;
    _jpegQuality = quality;
    sensor_t* s = esp_camera_sensor_get();
    if (s) {
        s->set_quality(s, _jpegQuality);
        return true;
    }
    return false;
}

bool CameraTask::setFrameSize(framesize_t frameSize) {
    _frameSize = frameSize;
    sensor_t* s = esp_camera_sensor_get();
    if (s) {
        s->set_framesize(s, _frameSize);
        return true;
    }
    return false;
}

void CameraTask::captureTaskEntry(void* param) {
    auto* self = static_cast<CameraTask*>(param);
    TickType_t lastStreamTick = 0;

    for (;;) {
        if (self->_snapshotRequested) {
            self->_snapshotRequested = false;
            self->captureOnce(false);
        }

        if (self->_streaming) {
            const TickType_t now = xTaskGetTickCount();
            const TickType_t interval = pdMS_TO_TICKS(self->_streamIntervalMs);
            if (now - lastStreamTick >= interval) {
                self->captureOnce(true);
                lastStreamTick = now;
            }
        }

        vTaskDelay(pdMS_TO_TICKS(5));
    }
}

void CameraTask::txTaskEntry(void* param) {
    auto* self = static_cast<CameraTask*>(param);

    for (;;) {
        camera_fb_t* fb = nullptr;
        bool isStream = false;

        if (self->_frameMutex && xSemaphoreTake(self->_frameMutex, pdMS_TO_TICKS(20)) == pdTRUE) {
            if (self->_pendingFrame) {
                fb = self->_pendingFrame;
                isStream = self->_pendingIsStream;
                self->_pendingFrame = nullptr;
                self->_pendingIsStream = false;
            }
            xSemaphoreGive(self->_frameMutex);
        }

        if (fb) {
            self->sendFrame(fb, isStream);
            esp_camera_fb_return(fb);
        } else {
            vTaskDelay(pdMS_TO_TICKS(10));
        }
    }
}

bool CameraTask::captureOnce(bool isStreamFrame) {
    camera_fb_t* fb = esp_camera_fb_get();
    if (!fb) return false;

    // Quick JPEG sanity: SOI
    if (fb->len < 2 || fb->buf[0] != 0xFF || fb->buf[1] != 0xD8) {
        esp_camera_fb_return(fb);
        return false;
    }

    offerFrame(fb, isStreamFrame);
    return true;
}

void CameraTask::offerFrame(camera_fb_t* fb, bool isStreamFrame) {
    if (!_frameMutex) {
        esp_camera_fb_return(fb);
        return;
    }

    if (xSemaphoreTake(_frameMutex, pdMS_TO_TICKS(10)) == pdTRUE) {
        // drop-old policy (keeps latest frame)
        if (_pendingFrame) {
            esp_camera_fb_return(_pendingFrame);
        }
        _pendingFrame = fb;
        _pendingIsStream = isStreamFrame;
        xSemaphoreGive(_frameMutex);
    } else {
        esp_camera_fb_return(fb);
    }
}

bool CameraTask::sendFrame(camera_fb_t* fb, bool isStreamFrame) {
    if (!_initialized || fb == nullptr || fb->len == 0) return false;
    if (!_bleServer->isConnected()) return false;

    const uint16_t seq = _frameSeq++;
    return sendFrameChunks(fb->buf, fb->len, isStreamFrame, seq);
}

bool CameraTask::sendFrameChunks(const uint8_t* jpeg, size_t len, bool isStreamFrame, uint16_t frameSeq) {
    // Use legacy single-channel CAM characteristic (IoT service) so the old MicroPython JS works unchanged.
    // Fallback to CAFE TX if legacy is not available (shouldn't happen in normal builds).
    NimBLECharacteristic* tx = _bleServer->getLegacyCamChar();
    if (!tx) tx = _bleServer->getCamTxChar();
    if (!tx || !jpeg || len == 0) return false;
    const uint16_t connHandle = _bleServer->getConnHandle();
    if (connHandle == BLE_HS_CONN_HANDLE_NONE) return false;

    // --------------------------------------------------------------------
    // MicroPython-compatible protocol (simple + paced)
    //
    //   CAM:START
    //   SIZE:<n>
    //   BIN<seq>:<payload bytes>   (chunk size ~160B)
    //   CAM:END
    //
    // This mirrors source/lib/bleIoT.py and allows us to match MicroPython behavior first.
    // We use this for BOTH stream and snapshot so the old JS can be reused without changes.
    // --------------------------------------------------------------------
    const uint16_t mtu = _bleServer->getMTU();
    const int32_t attMax = (int32_t)mtu - 3; // max payload per notify
    if (attMax <= 20) return false;

    auto allowAbort = [&]() -> bool {
        return isStreamFrame && !_streaming;
    };

    auto notifyText = [&](const char* s) -> bool {
        if (allowAbort()) return false;
        const size_t n = strlen(s);
        bool ok = tx->notify((const uint8_t*)s, n, connHandle);
        if (!ok) {
            for (int i = 0; i < 3 && !ok; i++) {
                if (allowAbort()) return false;
                vTaskDelay(pdMS_TO_TICKS(20));
                ok = tx->notify((const uint8_t*)s, n, connHandle);
            }
        }
        return ok;
    };

    if (!notifyText("CAM:START")) return false;

    char sizeMsg[32];
    snprintf(sizeMsg, sizeof(sizeMsg), "SIZE:%u", (unsigned)len);
    if (!notifyText(sizeMsg)) {
        (void)notifyText("CAM:END");
        return false;
    }

    // Chunking (MicroPython default 160 bytes)
    static constexpr size_t MP_CHUNK = 160;
    size_t offset = 0;
    uint16_t seq = 0;
    while (offset < len) {
        if (allowAbort()) {
            (void)notifyText("CAM:END");
            return false;
        }

        char hdr[16];
        const int hdrLen = snprintf(hdr, sizeof(hdr), "BIN%u:", (unsigned)seq);
        if (hdrLen <= 0) {
            (void)notifyText("CAM:END");
            return false;
        }

        const size_t remain = len - offset;
        size_t payloadLen = remain < MP_CHUNK ? remain : MP_CHUNK;
        // Ensure header+payload fits ATT
        if ((int32_t)payloadLen > (attMax - hdrLen)) {
            payloadLen = (size_t)max(0, attMax - hdrLen);
        }
        if (payloadLen == 0) {
            (void)notifyText("CAM:END");
            return false;
        }

        // Build packet: "BINn:" + data
        uint8_t out[16 + MP_CHUNK];
        memcpy(out, hdr, (size_t)hdrLen);
        memcpy(out + hdrLen, jpeg + offset, payloadLen);

        bool ok = tx->notify(out, (size_t)hdrLen + payloadLen, connHandle);
        if (!ok) {
            // ENOMEM/backpressure style retry (MicroPython-like)
            for (int i = 0; i < 3 && !ok; i++) {
                if (allowAbort()) break;
                vTaskDelay(pdMS_TO_TICKS(20));
                ok = tx->notify(out, (size_t)hdrLen + payloadLen, connHandle);
            }
        }
        if (!ok) {
            (void)notifyText("CAM:END");
            return false;
        }

        offset += payloadLen;
        seq++;

        // MicroPython pacing
        vTaskDelay(pdMS_TO_TICKS(5));
    }

    (void)notifyText("CAM:END");
    return true;
}

bool CameraTask::initCamera() {
    camera_config_t cfg = {};

    cfg.ledc_channel = LEDC_CHANNEL_0;
    cfg.ledc_timer = LEDC_TIMER_0;

    cfg.pin_d0 = CAM_PIN_D0;
    cfg.pin_d1 = CAM_PIN_D1;
    cfg.pin_d2 = CAM_PIN_D2;
    cfg.pin_d3 = CAM_PIN_D3;
    cfg.pin_d4 = CAM_PIN_D4;
    cfg.pin_d5 = CAM_PIN_D5;
    cfg.pin_d6 = CAM_PIN_D6;
    cfg.pin_d7 = CAM_PIN_D7;

    cfg.pin_xclk = CAM_PIN_XCLK;
    cfg.pin_pclk = CAM_PIN_PCLK;
    cfg.pin_vsync = CAM_PIN_VSYNC;
    cfg.pin_href = CAM_PIN_HREF;
    cfg.pin_sscb_sda = CAM_PIN_SIOD;
    cfg.pin_sscb_scl = CAM_PIN_SIOC;
    cfg.pin_pwdn = CAM_PIN_PWDN;
    cfg.pin_reset = CAM_PIN_RESET;

    cfg.xclk_freq_hz = 20000000;
    cfg.pixel_format = PIXFORMAT_JPEG;
    cfg.frame_size = _frameSize;
    cfg.jpeg_quality = _jpegQuality;
    cfg.fb_count = 2; // 안정성을 위해 2개로 복구
    cfg.grab_mode = CAMERA_GRAB_LATEST; // 지연 방지를 위해 최신 프레임 모드 유지
    cfg.fb_location = CAMERA_FB_IN_PSRAM;

    esp_err_t err = esp_camera_init(&cfg);
    if (err != ESP_OK) {
        Serial.printf("[CAM] esp_camera_init failed: 0x%x\n", (unsigned)err);
        return false;
    }
    return true;
}

void CameraTask::deinitCamera() {
    esp_camera_deinit();
}

