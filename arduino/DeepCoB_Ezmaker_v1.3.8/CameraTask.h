/**
 * @file CameraTask.h
 * @brief ESP32-S3 camera capture + BLE streaming task (CAFE binary protocol)
 *
 * Design goals:
 * - Capture runs independently from BLE TX (two FreeRTOS tasks)
 * - Single pending-frame slot (drop-old policy) to avoid queue buildup
 * - BLE notify is MTU-aware (uses peer MTU) and chunks JPEG accordingly
 *
 * NOTE (vs MicroPython):
 * - MicroPython sets MTU=185 and uses text framing (CAM:START/SIZE/BINxx:/CAM:END)
 * - Arduino uses a dedicated CAFE service and a binary 8-byte header per chunk.
 */
 
#ifndef CAMERA_TASK_H
#define CAMERA_TASK_H

#include <Arduino.h>
#include <NimBLEDevice.h>
#include <esp_camera.h>

class BleServer;

class CameraTask {
public:
    explicit CameraTask(BleServer* bleServer);
    ~CameraTask();

    bool begin();
    void end();

    // Control (text commands come through Camera RX characteristic)
    bool startStreaming();
    bool stopStreaming();
    bool requestSnapshot();
    bool setStreamInterval(uint32_t intervalMs);
    bool setQuality(uint8_t quality);              // 0..63 (lower is better quality, larger JPEG)
    bool setFrameSize(framesize_t frameSize);      // e.g., FRAMESIZE_QQVGA/QVGA/VGA

    bool isInitialized() const { return _initialized; }
    bool isStreaming() const { return _streaming; }

private:
    BleServer* _bleServer;

    // runtime state
    bool _initialized = false;
    bool _streaming = false;
    volatile bool _snapshotRequested = false;

    uint32_t _streamIntervalMs = 200;
    // 0..63 (lower is better quality, larger JPEG)
    // Default tuned for better visual quality while keeping BLE streaming workable.
    uint8_t _jpegQuality = 18;  //25 -> 12 -> 18
    framesize_t _frameSize = FRAMESIZE_QVGA;

    // sequence for frames (per-frame, not per-chunk)
    uint16_t _frameSeq = 0;

    // FreeRTOS tasks
    TaskHandle_t _captureTaskHandle = nullptr;
    TaskHandle_t _txTaskHandle = nullptr;

    // Single-slot pending frame (drop-old policy)
    camera_fb_t* _pendingFrame = nullptr;
    bool _pendingIsStream = false;
    SemaphoreHandle_t _frameMutex = nullptr;

    static void captureTaskEntry(void* param);
    static void txTaskEntry(void* param);

    bool initCamera();
    void deinitCamera();

    bool captureOnce(bool isStreamFrame);
    void offerFrame(camera_fb_t* fb, bool isStreamFrame);

    bool sendFrame(camera_fb_t* fb, bool isStreamFrame);
    bool sendFrameChunks(const uint8_t* jpeg, size_t len, bool isStreamFrame, uint16_t frameSeq);
};

#endif // CAMERA_TASK_H

