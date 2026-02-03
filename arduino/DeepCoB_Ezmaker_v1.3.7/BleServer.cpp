/**
 * @file BleServer.cpp
 * @brief BLE Server Manager Implementation
 */

#include "BleServer.h"
#include "BleCommandParser.h"
#include "pinmap.h"
#include <esp_mac.h>
#include <cstring>

// ============================================================================
// ServerCallbacks Implementation
// ============================================================================

void ServerCallbacks::onConnect(NimBLEServer* pServer, NimBLEConnInfo& connInfo) {
    uint16_t connHandle = connInfo.getConnHandle();
    uint16_t mtu = pServer->getPeerMTU(connHandle);
    
    Serial.printf("[BLE] Client connected: handle=%d, MTU=%d\n", connHandle, mtu);
    
    // Update connection parameters for lower latency
    // 6 * 1.25ms = 7.5ms (min)
    // 12 * 1.25ms = 15ms (max)
    pServer->updateConnParams(connHandle,
        6,   // minInterval (1.25ms units) -> 7.5ms
        12,  // maxInterval (1.25ms units) -> 15ms
        0,   // latency
        100  // timeout (10ms units) -> 1000ms
    );
    
    _server->onConnect(connHandle, mtu);
}

void ServerCallbacks::onDisconnect(NimBLEServer* pServer, NimBLEConnInfo& connInfo, int reason) {
    Serial.printf("[BLE] Client disconnected: reason=%d\n", reason);
    _server->onDisconnect();
}

void ServerCallbacks::onMTUChange(uint16_t MTU, NimBLEConnInfo& connInfo) {
    Serial.printf("[BLE] MTU changed: %d\n", MTU);
    _server->onMTUChange(MTU);
}

// ============================================================================
// Generic RX Characteristic Callbacks
// ============================================================================

void GenericRxCharCallbacks::onWrite(NimBLECharacteristic* pCharacteristic, NimBLEConnInfo& connInfo) {
    (void)connInfo;
    std::string value = pCharacteristic->getValue();
    if (value.length() > 0) {
        Serial.printf("[BLE] Received command: %s\n", value.c_str());
        _server->onCharacteristicWrite(pCharacteristic, (const uint8_t*)value.data(), value.length());
    }
}

// ============================================================================
// Camera RX Characteristic Callbacks
// ============================================================================

void CameraRxCharCallbacks::onWrite(NimBLECharacteristic* pCharacteristic, NimBLEConnInfo& connInfo) {
    std::string value = pCharacteristic->getValue();
    
    if (value.length() > 0) {
        Serial.printf("[BLE] Received camera control: %s\n", value.c_str());
        _server->onCameraRxWrite((const uint8_t*)value.data(), value.length());
    }
}

// ============================================================================
// BleServer Implementation
// ============================================================================

BleServer::BleServer()
    : _pServer(nullptr)
    , _pAdvertising(nullptr)
    , _pIotService(nullptr)
    , _pCameraService(nullptr)
    , _pSensorService(nullptr)
    , _pCamTxChar(nullptr)
    , _pCamRxChar(nullptr)
    , _pCamStatusChar(nullptr)
    , _pLegacyCamChar(nullptr)
    , _pLedChar(nullptr)
    , _pLastRxChar(nullptr)
    , _commandParser(nullptr)
    , _connected(false)
    , _connHandle(0)
    , _mtu(BLE_MTU_MIN)
{
}

BleServer::~BleServer() {
    end();
}

String BleServer::getDeviceName() {
    // Get MAC address
    uint8_t mac[6];
    esp_read_mac(mac, ESP_MAC_WIFI_STA);
    
    // Format: "DCB" + last 6 hex digits of MAC (uppercase)
    // Example: "DCB1A2B3C" if MAC is AA:BB:CC:DD:1A:2B:3C
    char deviceName[16];
    snprintf(deviceName, sizeof(deviceName), "%s%02X%02X%02X",
        BLE_DEVICE_NAME_PREFIX,
        mac[3], mac[4], mac[5]);
    
    return String(deviceName);
}

bool BleServer::begin() {
    Serial.println("[BLE] Initializing BLE Server...");

    // Get device name (MAC-based)
    String deviceName = getDeviceName();
    Serial.printf("[BLE] Device name: %s\n", deviceName.c_str());

    // Initialize NimBLE
    NimBLEDevice::init(deviceName.c_str());
    
    // Set MTU size (512 for ESP32-S3)
    NimBLEDevice::setMTU(BLE_MTU_SIZE);
    Serial.printf("[BLE] Requested MTU: %d\n", BLE_MTU_SIZE);

    // Create BLE Server
    _pServer = NimBLEDevice::createServer();
    if (!_pServer) {
        Serial.println("[BLE] Failed to create server");
        return false;
    }

    // Set connection callbacks
    _pServer->setCallbacks(new ServerCallbacks(this));

    // Setup services
    if (!setupServices()) {
        Serial.println("[BLE] Failed to setup services");
        return false;
    }

    // Start advertising
    startAdvertising();

    // Initialize BLE status LED
    pinMode(PIN_BLE_STATUS_LED, OUTPUT);
    digitalWrite(PIN_BLE_STATUS_LED, LOW); // OFF when disconnected

    Serial.println("[BLE] BLE Server started successfully");
    return true;
}

void BleServer::end() {
    if (_pServer) {
        NimBLEDevice::deinit(true);
        _pServer = nullptr;
        _commandParser = nullptr;
    }
}

void BleServer::setCommandParser(BleCommandParser* parser) {
    _commandParser = parser;
}

void BleServer::onCharacteristicWrite(NimBLECharacteristic* source, const uint8_t* data, size_t length) {
    _pLastRxChar = source;
    if (_commandParser != nullptr) {
        _commandParser->parseCommand(data, length);
    } else {
        Serial.println("[BLE] Warning: Command parser not initialized");
    }
}

void BleServer::onCameraRxWrite(const uint8_t* data, size_t length) {
    // Reuse the same command parser (camera commands are still text-based control)
    if (_commandParser != nullptr) {
        _commandParser->parseCommand(data, length);
    } else {
        Serial.println("[BLE] Warning: Command parser not initialized");
    }
}

bool BleServer::notifyLastRx(const char* text) {
    if (!_connected || text == nullptr) {
        return false;
    }
    if (_pLastRxChar == nullptr) {
        return false;
    }
    if (!(_pLastRxChar->getProperties() & NIMBLE_PROPERTY::NOTIFY)) {
        return false;
    }
    _pLastRxChar->setValue((uint8_t*)text, strlen(text));
    // notify() without conn handle notifies all subscribed clients
    return _pLastRxChar->notify();
}

bool BleServer::notifyCameraStatus(const char* text) {
    if (!_connected || text == nullptr) {
        return false;
    }
    if (_pCamStatusChar == nullptr) {
        return false;
    }
    if (!(_pCamStatusChar->getProperties() & NIMBLE_PROPERTY::NOTIFY)) {
        return false;
    }
    _pCamStatusChar->setValue((uint8_t*)text, strlen(text));
    return _pCamStatusChar->notify();
}

bool BleServer::setupServices() {
    // Setup services in order of priority
    if (!setupCameraService()) return false;
    if (!setupIotService()) return false;
    if (!setupSensorService()) return false;
    
    return true;
}

bool BleServer::setupCameraService() {
    Serial.println("[BLE] Setting up Camera Service...");

    _pCameraService = _pServer->createService(CAMERA_SERVICE_UUID);
    if (!_pCameraService) {
        Serial.println("[BLE] Failed to create Camera Service");
        return false;
    }

    // TX Characteristic (Notify + Indicate)
    //
    // - Stream: NOTIFY (higher throughput; frames may be dropped under congestion)
    // - Snapshot: INDICATE (reliable, confirmed)
    //
    // NOTE (Web Bluetooth):
    // Chrome's `startNotifications()` typically enables NOTIFY (CCCD=0x0001) only.
    // Our web client explicitly writes CCCD=0x0003 (notify+indicate) for CAMERA_TX_CHAR_UUID
    // so that indications are also delivered when we use them for snapshots / end markers.
    _pCamTxChar = _pCameraService->createCharacteristic(
        CAM_TX_CHAR_UUID,
        NIMBLE_PROPERTY::NOTIFY | NIMBLE_PROPERTY::INDICATE
    );
    if (!_pCamTxChar) {
        Serial.println("[BLE] Failed to create Camera TX characteristic");
        return false;
    }

    // RX Characteristic (Write) - for control commands
    _pCamRxChar = _pCameraService->createCharacteristic(
        CAM_RX_CHAR_UUID,
        // Allow both write-with-response and write-without-response (faster, less error-prone during streaming)
        NIMBLE_PROPERTY::WRITE | NIMBLE_PROPERTY::WRITE_NR
    );
    if (!_pCamRxChar) {
        Serial.println("[BLE] Failed to create Camera RX characteristic");
        return false;
    }

    // Set callback for camera control commands
    _pCamRxChar->setCallbacks(new CameraRxCharCallbacks(this));

    // Status Characteristic (Read+Notify) - for status info
    _pCamStatusChar = _pCameraService->createCharacteristic(
        CAM_STATUS_CHAR_UUID,
        NIMBLE_PROPERTY::READ | NIMBLE_PROPERTY::NOTIFY
    );
    if (!_pCamStatusChar) {
        Serial.println("[BLE] Failed to create Camera Status characteristic");
        return false;
    }

    // Start the service
    _pCameraService->start();
    Serial.println("[BLE] Camera Service started");
    
    return true;
}

bool BleServer::setupIotService() {
    Serial.println("[BLE] Setting up IoT Service...");
    
    _pIotService = _pServer->createService(IOT_SERVICE_UUID);
    if (!_pIotService) {
        Serial.println("[BLE] Failed to create IoT Service");
        return false;
    }

    // LED (Write)
    _pLedChar = _pIotService->createCharacteristic(LED_CHAR_UUID, NIMBLE_PROPERTY::WRITE);
    if (!_pLedChar) {
        Serial.println("[BLE] Failed to create LED characteristic");
        return false;
    }
    _pLedChar->setCallbacks(new GenericRxCharCallbacks(this));

    // Legacy camera characteristic (MicroPython/IoTmode compatibility)
    // - Single characteristic used for both commands(write) and stream(notify)
    _pLegacyCamChar = _pIotService->createCharacteristic(
        CAM_CHAR_UUID,
        NIMBLE_PROPERTY::WRITE | NIMBLE_PROPERTY::WRITE_NR | NIMBLE_PROPERTY::NOTIFY
    );
    if (!_pLegacyCamChar) {
        Serial.println("[BLE] Failed to create legacy CAM characteristic");
        return false;
    }
    _pLegacyCamChar->setCallbacks(new GenericRxCharCallbacks(this));
    
    _pIotService->start();
    Serial.println("[BLE] IoT Service started");
    
    return true;
}

bool BleServer::setupSensorService() {
    Serial.println("[BLE] Setting up Sensor Service...");

    _pSensorService = _pServer->createService(SENSOR_SERVICE_UUID);
    if (!_pSensorService) {
        Serial.println("[BLE] Failed to create Sensor Service");
        return false;
    }

    auto addWriteNotify = [&](const char* uuid) -> bool {
        NimBLECharacteristic* c = _pSensorService->createCharacteristic(uuid, NIMBLE_PROPERTY::WRITE | NIMBLE_PROPERTY::NOTIFY);
        if (!c) return false;
        c->setCallbacks(new GenericRxCharCallbacks(this));
        return true;
    };
    auto addWriteOnly = [&](const char* uuid) -> bool {
        NimBLECharacteristic* c = _pSensorService->createCharacteristic(uuid, NIMBLE_PROPERTY::WRITE);
        if (!c) return false;
        c->setCallbacks(new GenericRxCharCallbacks(this));
        return true;
    };

    // DeepCo common
    if (!addWriteNotify(ULTRA_CHAR_UUID)) return false;
    if (!addWriteNotify(DHT_CHAR_UUID)) return false;
    if (!addWriteOnly(SERVO_CHAR_UUID)) return false;
    if (!addWriteOnly(NEO_CHAR_UUID)) return false;
    if (!addWriteNotify(TOUCH_CHAR_UUID)) return false;
    if (!addWriteNotify(LIGHT_CHAR_UUID)) return false;
    if (!addWriteNotify(BUZZER_CHAR_UUID)) return false;
    if (!addWriteNotify(GYRO_CHAR_UUID)) return false;
    if (!addWriteNotify(DUST_CHAR_UUID)) return false;
    if (!addWriteOnly(DCMOTOR_CHAR_UUID)) return false;
    if (!addWriteNotify(HEART_CHAR_UUID)) return false;

    // EZMaker
    if (!addWriteNotify(EZ_LASER_CHAR_UUID)) return false;
    if (!addWriteNotify(EZ_GYRO_CHAR_UUID)) return false;
    if (!addWriteNotify(EZ_PRESS_CHAR_UUID)) return false;
    if (!addWriteNotify(EZ_CO2_CHAR_UUID)) return false;
    if (!addWriteNotify(EZ_DIYA_CHAR_UUID)) return false;
    if (!addWriteNotify(EZ_DIYB_CHAR_UUID)) return false;
    if (!addWriteNotify(EZ_HALL_CHAR_UUID)) return false;
    if (!addWriteNotify(EZ_LCD_CHAR_UUID)) return false;
    if (!addWriteNotify(EZ_LIGHT_CHAR_UUID)) return false;
    if (!addWriteNotify(EZ_VOLT_CHAR_UUID)) return false;
    if (!addWriteNotify(EZ_CURR_CHAR_UUID)) return false;
    if (!addWriteNotify(EZ_HUMAN_CHAR_UUID)) return false;
    if (!addWriteNotify(EZ_THERMAL_CHAR_UUID)) return false;
    if (!addWriteNotify(EZ_SOUND_CHAR_UUID)) return false;
    if (!addWriteNotify(EZ_WEIGHT_CHAR_UUID)) return false;
    if (!addWriteNotify(EZ_DUST_CHAR_UUID)) return false;

    _pSensorService->start();
    Serial.println("[BLE] Sensor Service started");
    return true;
}

void BleServer::startAdvertising() {
    _pAdvertising = NimBLEDevice::getAdvertising();

    /**
     * IMPORTANT (Windows / Web Bluetooth 호환성):
     * - 128-bit Service UUID를 여러 개(예: 3개) 광고 데이터에 넣으면 레거시 광고(31 bytes) 한계를 쉽게 초과합니다.
     *   일부 스캐너/브라우저/OS에서는 이런 광고 패킷을 무시해서 "장치 목록에 안 보이는" 문제가 발생할 수 있습니다.
     * - Web BLE 연결은 `requestDevice()`에서 namePrefix로 선택하고, 연결 후 `optionalServices`로 GATT를 접근하므로
     *   광고 데이터에 모든 서비스 UUID를 넣을 필요가 없습니다.
     */
    _pAdvertising->reset();                 // stop + clear adv/scan data to defaults
    _pAdvertising->enableScanResponse(true); // allow scan response (name will go here if needed)
    _pAdvertising->setDiscoverableMode(BLE_GAP_DISC_MODE_GEN);
    _pAdvertising->setConnectableMode(BLE_GAP_CONN_MODE_UND);

    // Advertise device name explicitly so namePrefix 필터가 안정적으로 동작하도록 함.
    // (길면 자동으로 잘림)
    _pAdvertising->setName(getDeviceName().c_str());

    // Keep advertising payload small for maximum compatibility.
    // (필요 시 1개만 추가하세요. 현재는 namePrefix 기반 선택을 사용하므로 생략)
    // _pAdvertising->addServiceUUID(SENSOR_SERVICE_UUID);

    // Start advertising
    _pAdvertising->start();
    Serial.println("[BLE] Advertising started");
}

void BleServer::onConnect(uint16_t connHandle, uint16_t mtu) {
    _connected = true;
    _connHandle = connHandle;
    _mtu = mtu;
    
    // Turn on BLE status LED
    digitalWrite(PIN_BLE_STATUS_LED, HIGH);
    
    Serial.printf("[BLE] Connected: handle=%d, MTU=%d\n", connHandle, mtu);

    // Publish negotiated MTU to web client (diagnostic/tuning)
    {
        char msg[32];
        snprintf(msg, sizeof(msg), "MTU:%u", (unsigned)mtu);
        (void)notifyCameraStatus(msg);
    }
}

void BleServer::onDisconnect() {
    _connected = false;
    _connHandle = 0;
    _mtu = BLE_MTU_MIN;
    
    // Turn off BLE status LED
    digitalWrite(PIN_BLE_STATUS_LED, LOW);
    
    // Restart advertising
    startAdvertising();
    
    Serial.println("[BLE] Disconnected, advertising restarted");
}

void BleServer::onMTUChange(uint16_t mtu) {
    _mtu = mtu;
    Serial.printf("[BLE] MTU updated: %d\n", mtu);

    // Publish MTU changes (some stacks renegotiate after connect)
    {
        char msg[32];
        snprintf(msg, sizeof(msg), "MTU:%u", (unsigned)mtu);
        (void)notifyCameraStatus(msg);
    }
}
