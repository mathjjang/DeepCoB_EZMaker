/**
 * @file BleServer.h
 * @brief BLE Server Manager for DeepCoB_EZMaker
 * 
 * Manages BLE server initialization, MTU negotiation, and connection handling.
 * Uses NimBLE library for ESP32-S3.
 */

#ifndef BLE_SERVER_H
#define BLE_SERVER_H

#include <NimBLEDevice.h>
#include "ble_uuids.h"

// Forward declarations
class BleServer;

// ============================================================================
// Connection Callbacks
// ============================================================================

class ServerCallbacks : public NimBLEServerCallbacks {
public:
    ServerCallbacks(BleServer* server) : _server(server) {}
    
    void onConnect(NimBLEServer* pServer, NimBLEConnInfo& connInfo) override;
    void onDisconnect(NimBLEServer* pServer, NimBLEConnInfo& connInfo, int reason) override;
    void onMTUChange(uint16_t MTU, NimBLEConnInfo& connInfo) override;

private:
    BleServer* _server;
};

// ============================================================================
// Generic RX Characteristic Callbacks
// ============================================================================

class GenericRxCharCallbacks : public NimBLECharacteristicCallbacks {
public:
    GenericRxCharCallbacks(BleServer* server) : _server(server) {}
    
    void onWrite(NimBLECharacteristic* pCharacteristic, NimBLEConnInfo& connInfo) override;
    
private:
    BleServer* _server;
};

// ============================================================================
// Camera RX Characteristic Callbacks
// ============================================================================

class CameraRxCharCallbacks : public NimBLECharacteristicCallbacks {
public:
    CameraRxCharCallbacks(BleServer* server) : _server(server) {}
    
    void onWrite(NimBLECharacteristic* pCharacteristic, NimBLEConnInfo& connInfo) override;
    
private:
    BleServer* _server;
};

// ============================================================================
// BLE Server Manager
// ============================================================================

class BleServer {
public:
    BleServer();
    ~BleServer();

    // Initialization
    bool begin();
    void end();
    
    // Device name generation (MAC-based)
    String getDeviceName();
    
    // Set command parser (for handling incoming commands)
    void setCommandParser(class BleCommandParser* parser);

    // Connection management
    bool isConnected() const { return _connected; }
    uint16_t getMTU() const { return _mtu; }
    uint16_t getConnHandle() const { return _connHandle; }

    // Service/Characteristic accessors
    NimBLEServer* getServer() { return _pServer; }
    NimBLEService* getIotService() { return _pIotService; }
    NimBLEService* getCameraService() { return _pCameraService; }
    NimBLEService* getSensorService() { return _pSensorService; }

    // Characteristic accessors (Camera)
    NimBLECharacteristic* getCamTxChar() { return _pCamTxChar; }
    NimBLECharacteristic* getCamRxChar() { return _pCamRxChar; }
    NimBLECharacteristic* getCamStatusChar() { return _pCamStatusChar; }
    // Legacy camera characteristic (IoT service, single Write+Notify channel)
    NimBLECharacteristic* getLegacyCamChar() { return _pLegacyCamChar; }
    
    // Incoming command handler (called by GenericRxCharCallbacks)
    void onCharacteristicWrite(NimBLECharacteristic* source, const uint8_t* data, size_t length);
    // Incoming camera control handler (called by CameraRxCharCallbacks)
    void onCameraRxWrite(const uint8_t* data, size_t length);

    // Notify back on the last-written characteristic (Web BLE expects per-characteristic notify)
    bool notifyLastRx(const char* text);
    // Camera status notify (CAM_STATUS_CHAR_UUID)
    bool notifyCameraStatus(const char* text);

    // Connection event handlers (called by ServerCallbacks)
    void onConnect(uint16_t connHandle, uint16_t mtu);
    void onDisconnect();
    void onMTUChange(uint16_t mtu);

private:
    // BLE objects
    NimBLEServer* _pServer;
    NimBLEAdvertising* _pAdvertising;
    
    // Command parser reference
    class BleCommandParser* _commandParser;

    // Services
    NimBLEService* _pIotService;
    NimBLEService* _pCameraService;
    NimBLEService* _pSensorService;

    // Camera characteristics (primary focus for Phase 1)
    NimBLECharacteristic* _pCamTxChar;    // Notify (binary frames)
    NimBLECharacteristic* _pCamRxChar;    // Write (control commands)
    NimBLECharacteristic* _pCamStatusChar; // Read+Notify (status)
    NimBLECharacteristic* _pLegacyCamChar; // Write+Notify (legacy CAM characteristic in IoT service)

    // IoT characteristics
    NimBLECharacteristic* _pLedChar;   // Write

    // Sensor characteristics (one service, multiple characteristics)
    NimBLECharacteristic* _pLastRxChar; // last command source (for responses)

    // Connection state
    bool _connected;
    uint16_t _connHandle;
    uint16_t _mtu;

    // Setup methods
    bool setupServices();
    bool setupCameraService();
    bool setupIotService();
    bool setupSensorService();
    
    void startAdvertising();
};

#endif // BLE_SERVER_H
