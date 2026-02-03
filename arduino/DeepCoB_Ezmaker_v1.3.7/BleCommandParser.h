/**
 * @file BleCommandParser.h
 * @brief BLE command parser with dynamic sensor loading support
 * 
 * Parses BLE commands and manages dynamic sensor initialization (MicroPython compatible).
 */

#ifndef BLE_COMMAND_PARSER_H
#define BLE_COMMAND_PARSER_H

#include <Arduino.h>

// Forward declarations
class BleServer;
class SensorManager;
class CameraTask;
class BuzzerController;

/**
 * @class BleCommandParser
 * @brief Parses and dispatches BLE commands to appropriate handlers
 * 
 * Supports dynamic sensor initialization via PIN commands (MicroPython compatible).
 */
class BleCommandParser {
public:
    BleCommandParser(SensorManager* sensorManager, BleServer* bleServer);
    ~BleCommandParser();
    
    // Parse incoming command from BLE RX characteristic
    void parseCommand(const uint8_t* data, size_t length);
    
    // Set component references
    void setCameraTask(CameraTask* cameraTask);
    void setBuzzer(BuzzerController* buzzer);
    
private:
    // References to other components
    SensorManager* _sensorManager;
    BleServer* _bleServer;
    CameraTask* _cameraTask;
    BuzzerController* _buzzer;
    
    // Internal command dispatch
    void handleCameraCommand(const char* cmd);
    void handleSensorCommand(const char* cmd);
    void handleBuzzerCommand(const char* cmd);
    
    // Sensor-specific handlers
    void handleDHTCommand(const char* cmd);
    void handleUltrasonicCommand(const char* cmd);
    void handleServoCommand(const char* cmd);
    void handleNeoPixelCommand(const char* cmd);
    void handleLEDCommand(const char* cmd);
    void handleTouchCommand(const char* cmd);
    void handleLightCommand(const char* cmd);
    void handleGyroCommand(const char* cmd);
    void handleDCMotorCommand(const char* cmd);
    void handleHumanCommand(const char* cmd);
    void handleDustCommand(const char* cmd);
    void handleHeartCommand(const char* cmd);
    void handleDIYACommand(const char* cmd);
    void handleDIYBCommand(const char* cmd);
    void handleHallCommand(const char* cmd);
    
    // EZMaker sensor handlers
    void handleEZGyroCommand(const char* cmd);
    void handleEZPressureCommand(const char* cmd);
    void handleEZCO2Command(const char* cmd);
    void handleEZLCDCommand(const char* cmd);
    void handleEZLaserCommand(const char* cmd);
    void handleEZLightCommand(const char* cmd);
    void handleEZVoltCommand(const char* cmd);
    void handleEZCurrentCommand(const char* cmd);
    void handleEZThermalCommand(const char* cmd);
    void handleEZSoundCommand(const char* cmd);
    void handleEZWeightCommand(const char* cmd);
    void handleEZDustCommand(const char* cmd);
    
    // Helper functions
    bool startsWith(const char* str, const char* prefix);
    int parseInt(const char* str);
    float parseFloat(const char* str);
    void sendResponse(const char* response);
    
    // Command buffer
    static constexpr size_t MAX_COMMAND_LENGTH = 256;
    char _commandBuffer[MAX_COMMAND_LENGTH];
};

#endif // BLE_COMMAND_PARSER_H
