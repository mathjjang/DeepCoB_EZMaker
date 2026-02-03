/**
 * @file BleCommandParser.cpp
 * @brief BLE command parser implementation
 */

#include "BleCommandParser.h"
#include "BleServer.h"
#include "SensorManager.h"
#include "CameraTask.h"
#include "BuzzerController.h"

#include <cstring>
#include <cstdio>
#include <cmath>

BleCommandParser::BleCommandParser(SensorManager* sensorManager, BleServer* bleServer)
    : _sensorManager(sensorManager)
    , _bleServer(bleServer)
    , _cameraTask(nullptr)
    , _buzzer(nullptr) {
    _commandBuffer[0] = '\0';
}

BleCommandParser::~BleCommandParser() = default;

void BleCommandParser::setCameraTask(CameraTask* cameraTask) {
    _cameraTask = cameraTask;
}

void BleCommandParser::setBuzzer(BuzzerController* buzzer) {
    _buzzer = buzzer;
}

void BleCommandParser::parseCommand(const uint8_t* data, size_t length) {
    if (!data || length == 0 || length >= MAX_COMMAND_LENGTH) {
        return;
    }

    memcpy(_commandBuffer, data, length);
    _commandBuffer[length] = '\0';

    // Dispatch
    if (startsWith(_commandBuffer, "CAM:")) { handleCameraCommand(_commandBuffer); return; }
    if (startsWith(_commandBuffer, "BUZ:")) { handleBuzzerCommand(_commandBuffer); return; }

    // Sensors / actuators
    handleSensorCommand(_commandBuffer);
}

void BleCommandParser::handleCameraCommand(const char* cmd) {
    if (!_cameraTask) {
        sendResponse("CAM:ERROR:NOT_INITIALIZED");
        return;
    }

    if (strcmp(cmd, "CAM:STREAM:ON") == 0) {
        sendResponse(_cameraTask->startStreaming() ? "CAM:STREAM:ON:OK" : "CAM:STREAM:ON:ERROR");
        return;
    }
    if (strcmp(cmd, "CAM:STREAM:OFF") == 0) {
        sendResponse(_cameraTask->stopStreaming() ? "CAM:STREAM:OFF:OK" : "CAM:STREAM:OFF:ERROR");
        return;
    }
    if (strcmp(cmd, "CAM:SNAP") == 0) {
        sendResponse(_cameraTask->requestSnapshot() ? "CAM:SNAP:OK" : "CAM:SNAP:ERROR");
        return;
    }

    if (startsWith(cmd, "CAM:INTERVAL")) {
        const char* p = cmd + strlen("CAM:INTERVAL");
        while (*p == ' ' || *p == ':') p++;
        const int interval = parseInt(p);
        if (interval > 0 && _cameraTask->setStreamInterval((uint32_t)interval)) {
            sendResponse("CAM:INTERVAL:OK");
        } else {
            sendResponse("CAM:INTERVAL:ERROR");
        }
        return;
    }

    if (startsWith(cmd, "CAM:QUALITY:")) {
        const int q = parseInt(cmd + 12);
        if (q >= 0 && q <= 63 && _cameraTask->setQuality((uint8_t)q)) {
            sendResponse("CAM:QUALITY:OK");
        } else {
            sendResponse("CAM:QUALITY:ERROR");
        }
        return;
    }

    sendResponse("CAM:ERROR:UNKNOWN_CMD");
}

void BleCommandParser::handleBuzzerCommand(const char* cmd) {
    if (!_buzzer) {
        sendResponse("BUZ:ERROR:NOT_INITIALIZED");
        return;
    }

    if (strcmp(cmd, "BUZ:INIT") == 0) {
        sendResponse("INITIALIZED");
        return;
    }

    if (startsWith(cmd, "BUZ:BEEP:") && strstr(cmd, ":ON:") == nullptr && strstr(cmd, ",") == nullptr) {
        int count = 1, freq = 2000, dur = 100, interval = 100;
        sscanf(cmd + 9, "%d:%d:%d:%d", &count, &freq, &dur, &interval);
        const bool ok = _buzzer->playPattern((uint8_t)count, (uint16_t)freq, (uint16_t)dur, (uint16_t)interval);
        sendResponse(ok ? "PLAYING" : "ERROR:PATTERN");
        return;
    }

    if (startsWith(cmd, "BUZ:BEEP:") && strchr(cmd + 9, ',') != nullptr) {
        int freq = 2000, dur = 100;
        sscanf(cmd + 9, "%d,%d", &freq, &dur);
        _buzzer->beep((uint16_t)freq, (uint16_t)dur);
        sendResponse("PLAYING");
        return;
    }

    if (startsWith(cmd, "BUZ:BEEP:ON:")) {
        const int freq = parseInt(cmd + 12);
        const bool ok = _buzzer->tone((uint16_t)freq, 0);
        sendResponse(ok ? "PLAYING" : "ERROR:TONE");
        return;
    }

    if (startsWith(cmd, "BUZ:PLAY:")) {
        const char* p = cmd + 9;
        const char* colon = strchr(p, ':');
        if (!colon) { sendResponse("ERROR:BAD_CMD"); return; }
        char name[32] = {0};
        const size_t n = (size_t)min((ptrdiff_t)sizeof(name) - 1, colon - p);
        memcpy(name, p, n);
        const int tempo = parseInt(colon + 1);
        const bool ok = _buzzer->playMelody(name, (uint16_t)tempo);
        sendResponse(ok ? "PLAYING" : "ERROR:MELODY");
        return;
    }

    if (strcmp(cmd, "BUZ:STOP") == 0) {
        _buzzer->stopMelody();
        sendResponse("STOPPED");
        return;
    }

    if (strcmp(cmd, "BUZ:STATUS") == 0) {
        sendResponse(_buzzer->isPlaying() ? "PLAYING" : "STOPPED");
        return;
    }

    if (startsWith(cmd, "BUZ:OFF")) {
        _buzzer->stopMelody();
        _buzzer->noTone();
        sendResponse("STOPPED");
        return;
    }

    sendResponse("BUZ:ERROR:UNKNOWN_CMD");
}

void BleCommandParser::handleSensorCommand(const char* cmd) {
    if (!cmd) return;

    if (startsWith(cmd, "DHT:"))   { handleDHTCommand(cmd); return; }
    if (startsWith(cmd, "ULTRA:")) { handleUltrasonicCommand(cmd); return; }
    if (startsWith(cmd, "TOUCH:")) { handleTouchCommand(cmd); return; }
    if (startsWith(cmd, "LIGHT:")) { handleLightCommand(cmd); return; }
    if (startsWith(cmd, "LED:"))   { handleLEDCommand(cmd); return; }
    if (startsWith(cmd, "SERVO:") || startsWith(cmd, "SERVO2:")) { handleServoCommand(cmd); return; }
    if (startsWith(cmd, "NEO:"))   { handleNeoPixelCommand(cmd); return; }
    if (startsWith(cmd, "GYRO:"))  { handleGyroCommand(cmd); return; }
    if (startsWith(cmd, "MOTOR:")) { handleDCMotorCommand(cmd); return; }
    if (startsWith(cmd, "HUMAN:")) { handleHumanCommand(cmd); return; }
    if (startsWith(cmd, "DUST:"))  { handleDustCommand(cmd); return; }
    if (startsWith(cmd, "HEART:")) { handleHeartCommand(cmd); return; }
    if (startsWith(cmd, "DIYA:"))  { handleDIYACommand(cmd); return; }
    if (startsWith(cmd, "DIYB:"))  { handleDIYBCommand(cmd); return; }
    if (startsWith(cmd, "HALL:"))  { handleHallCommand(cmd); return; }

    if (startsWith(cmd, "LASER:"))   { handleEZLaserCommand(cmd); return; }
    if (startsWith(cmd, "EZGYRO:"))  { handleEZGyroCommand(cmd); return; }
    if (startsWith(cmd, "EZPRESS:")) { handleEZPressureCommand(cmd); return; }
    if (startsWith(cmd, "EZCO2:"))   { handleEZCO2Command(cmd); return; }
    if (startsWith(cmd, "LCD:"))     { handleEZLCDCommand(cmd); return; }
    if (startsWith(cmd, "EZLIGHT:")) { handleEZLightCommand(cmd); return; }
    if (startsWith(cmd, "EZVOLT:"))  { handleEZVoltCommand(cmd); return; }
    if (startsWith(cmd, "EZCURR:"))  { handleEZCurrentCommand(cmd); return; }
    if (startsWith(cmd, "EZTHERMAL:")){ handleEZThermalCommand(cmd); return; }
    if (startsWith(cmd, "EZSOUND:")) { handleEZSoundCommand(cmd); return; }
    if (startsWith(cmd, "EZWEIGHT:")){ handleEZWeightCommand(cmd); return; }
    if (startsWith(cmd, "EZDUST:"))  { handleEZDustCommand(cmd); return; }

    sendResponse("ERROR:UNKNOWN_CMD");
}

// Sensor Handlers
void BleCommandParser::handleDHTCommand(const char* cmd) {
    if (!_sensorManager) return;
    if (startsWith(cmd, "DHT:PIN:")) {
        const int pin = parseInt(cmd + 8);
        sendResponse(_sensorManager->initDHT((uint8_t)pin) ? "DHT:PIN:OK" : "DHT:PIN:ERROR");
    } else if (strcmp(cmd, "DHT:STATUS") == 0) {
        float t = 0, h = 0;
        if (_sensorManager->readDHT(t, h)) {
            char out[64];
            snprintf(out, sizeof(out), "DHT:T=%.2f,H=%.2f", t, h);
            sendResponse(out);
        } else sendResponse("DHT:STATUS:ERROR");
    }
}

void BleCommandParser::handleUltrasonicCommand(const char* cmd) {
    if (!_sensorManager) return;
    if (startsWith(cmd, "ULTRA:PIN:")) {
        int trig = -1, echo = -1;
        sscanf(cmd + 10, "%d,%d", &trig, &echo);
        sendResponse(_sensorManager->initUltrasonic((uint8_t)trig, (uint8_t)echo) ? "ULTRA:PIN:OK" : "ULTRA:PIN:ERROR");
    } else if (strcmp(cmd, "ULTRA:STATUS") == 0) {
        float dist = 0;
        if (_sensorManager->readUltrasonic(dist)) {
            char out[48];
            snprintf(out, sizeof(out), "ULTRA:%.2f", dist);
            sendResponse(out);
        } else sendResponse("ULTRA:STATUS:ERROR");
    }
}

void BleCommandParser::handleServoCommand(const char* cmd) {
    if (!_sensorManager) return;
    if (startsWith(cmd, "SERVO:PIN2:")) {
        sendResponse(_sensorManager->initServo(2, (uint8_t)parseInt(cmd + 11)) ? "SERVO:PIN2:OK" : "SERVO:PIN2:ERROR");
    } else if (startsWith(cmd, "SERVO:PIN:")) {
        sendResponse(_sensorManager->initServo(1, (uint8_t)parseInt(cmd + 10)) ? "SERVO:PIN:OK" : "SERVO:PIN:ERROR");
    } else if (startsWith(cmd, "SERVO2:")) {
        sendResponse(_sensorManager->setServoAngle(2, (uint8_t)parseInt(cmd + 7)) ? "SERVO2:OK" : "SERVO2:ERROR");
    } else if (startsWith(cmd, "SERVO:")) {
        sendResponse(_sensorManager->setServoAngle(1, (uint8_t)parseInt(cmd + 6)) ? "SERVO:OK" : "SERVO:ERROR");
    }
}

void BleCommandParser::handleNeoPixelCommand(const char* cmd) {
    if (!_sensorManager) return;
    if (startsWith(cmd, "NEO:PIN:")) {
        int pin = -1, n = 0;
        sscanf(cmd + 8, "%d,%d", &pin, &n);
        sendResponse(_sensorManager->initNeoPixel((uint8_t)pin, (uint16_t)n) ? "NEO:PIN:OK" : "NEO:PIN:ERROR");
    } else if (startsWith(cmd, "NEO:BRIGHTNESS:")) {
        sendResponse(_sensorManager->setNeoPixelBrightness((uint8_t)parseInt(cmd + 15)) ? "NEO:BRIGHTNESS:OK" : "NEO:BRIGHTNESS:ERROR");
    } else if (startsWith(cmd, "NEO:PX:")) {
        int idx, r, g, b;
        sscanf(cmd + 7, "%d,%d,%d,%d", &idx, &r, &g, &b);
        sendResponse(_sensorManager->setNeoPixelColor(idx, r, g, b) && _sensorManager->showNeoPixel() ? "NEO:PIXEL:OK" : "NEO:PIXEL:ERROR");
    }
}

void BleCommandParser::handleLEDCommand(const char* cmd) {
    if (!_sensorManager) return;
    if (startsWith(cmd, "LED:PIN:")) {
        sendResponse(_sensorManager->initLED((uint8_t)parseInt(cmd + 8)) ? "LED:PIN:OK" : "LED:PIN:ERROR");
    } else if (strcmp(cmd, "LED:ON") == 0) {
        sendResponse(_sensorManager->setLED(true) ? "LED:ON:OK" : "LED:ON:ERROR");
    } else if (strcmp(cmd, "LED:OFF") == 0) {
        sendResponse(_sensorManager->setLED(false) ? "LED:OFF:OK" : "LED:OFF:ERROR");
    }
}

void BleCommandParser::handleTouchCommand(const char* cmd) {
    if (!_sensorManager) return;
    if (startsWith(cmd, "TOUCH:PIN:")) {
        sendResponse(_sensorManager->initTouch((uint8_t)parseInt(cmd + 10)) ? "TOUCH:PIN:OK" : "TOUCH:PIN:ERROR");
    } else if (strcmp(cmd, "TOUCH:STATUS") == 0) {
        bool t;
        if (_sensorManager->readTouch(t)) sendResponse(t ? "TOUCH:1" : "TOUCH:0");
        else sendResponse("TOUCH:STATUS:ERROR");
    }
}

void BleCommandParser::handleLightCommand(const char* cmd) {
    if (!_sensorManager) return;
    if (startsWith(cmd, "LIGHT:PIN:")) {
        int a, d;
        if (sscanf(cmd + 10, "%d,%d", &a, &d) == 2) sendResponse(_sensorManager->initLight(a, d) ? "LIGHT:PIN:OK" : "LIGHT:PIN:ERROR");
        else sendResponse(_sensorManager->initLight(parseInt(cmd + 10), parseInt(cmd + 10)) ? "LIGHT:PIN:OK" : "LIGHT:PIN:ERROR");
    } else if (strcmp(cmd, "LIGHT:STATUS") == 0) {
        uint16_t a; bool d;
        if (_sensorManager->readLight(a, d)) {
            char out[48]; snprintf(out, sizeof(out), "LIGHT:%u,%d", a, d ? 1 : 0);
            sendResponse(out);
        } else sendResponse("LIGHT:STATUS:ERROR");
    }
}

void BleCommandParser::handleGyroCommand(const char* cmd) {
    if (!_sensorManager) return;
    if (startsWith(cmd, "GYRO:PIN:")) {
        int sda, scl; sscanf(cmd + 9, "%d,%d", &sda, &scl);
        sendResponse(_sensorManager->initGyro(sda, scl) ? "GYRO:PIN:OK" : "GYRO:PIN:ERROR");
    } else if (strcmp(cmd, "GYRO:STATUS") == 0) {
        float x, y, z;
        if (_sensorManager->readGyro(x, y, z)) {
            char out[80]; snprintf(out, sizeof(out), "GYRO:X=%.3f,Y=%.3f,Z=%.3f", x, y, z);
            sendResponse(out);
        } else sendResponse("GYRO:STATUS:ERROR");
    }
}

void BleCommandParser::handleDCMotorCommand(const char* cmd) {
    if (!_sensorManager) return;
    if (startsWith(cmd, "MOTOR:PIN:")) {
        sendResponse(_sensorManager->initDCMotor((uint8_t)parseInt(cmd + 10)) ? "MOTOR:PIN:OK" : "MOTOR:ERROR:PIN");
    } else if (startsWith(cmd, "MOTOR:SPEED:")) {
        sendResponse(_sensorManager->setDCMotorSpeed((uint8_t)parseInt(cmd + 12)) ? "MOTOR:SPEED:OK" : "MOTOR:ERROR:SPEED");
    } else if (strcmp(cmd, "MOTOR:STOP") == 0) {
        sendResponse(_sensorManager->stopDCMotor() ? "MOTOR:STOP:OK" : "MOTOR:ERROR:STOP");
    }
}

void BleCommandParser::handleHumanCommand(const char* cmd) {
    if (!_sensorManager) return;
    if (startsWith(cmd, "HUMAN:PIN:")) {
        sendResponse(_sensorManager->initHuman((uint8_t)parseInt(cmd + 10)) ? "HUMAN:PIN:OK" : "HUMAN:PIN:ERROR");
    } else if (strcmp(cmd, "HUMAN:STATUS") == 0) {
        bool d;
        if (_sensorManager->readHuman(d)) sendResponse(d ? "HUMAN:1" : "HUMAN:0");
        else sendResponse("HUMAN:STATUS:ERROR");
    }
}

// Stubs for missing common sensors
void BleCommandParser::handleDustCommand(const char* cmd) { sendResponse("DUST:ERROR:NOT_IMPLEMENTED"); }
void BleCommandParser::handleHeartCommand(const char* cmd) { sendResponse("HEART:ERROR:NOT_IMPLEMENTED"); }
void BleCommandParser::handleDIYACommand(const char* cmd) { sendResponse("DIYA:ERROR:NOT_IMPLEMENTED"); }
void BleCommandParser::handleDIYBCommand(const char* cmd) { sendResponse("DIYB:ERROR:NOT_IMPLEMENTED"); }
void BleCommandParser::handleHallCommand(const char* cmd) { sendResponse("HALL:ERROR:NOT_IMPLEMENTED"); }

// EZMaker Handlers
void BleCommandParser::handleEZGyroCommand(const char* cmd) {
    if (!_sensorManager) return;
    if (startsWith(cmd, "EZGYRO:PIN:")) {
        int sda, scl; sscanf(cmd + 11, "%d,%d", &sda, &scl);
        sendResponse(_sensorManager->initEZGyro(sda, scl) ? "EZGYRO:PIN:OK" : "EZGYRO:PIN:ERROR");
    } else if (strcmp(cmd, "EZGYRO:STATUS") == 0) {
        float ax, ay, az, gx, gy, gz, t;
        if (_sensorManager->readEZGyro(ax, ay, az, gx, gy, gz, t)) {
            char out[180]; snprintf(out, sizeof(out), "EZGYRO:AX=%.3f,AY=%.3f,AZ=%.3f,GX=%.3f,GY=%.3f,GZ=%.3f,TEMP=%.2f", ax, ay, az, gx, gy, gz, t);
            sendResponse(out);
        } else sendResponse("EZGYRO:STATUS:ERROR");
    }
}

void BleCommandParser::handleEZPressureCommand(const char* cmd) {
    if (!_sensorManager) return;
    if (startsWith(cmd, "EZPRESS:PIN:")) {
        int sda, scl; sscanf(cmd + 12, "%d,%d", &sda, &scl);
        sendResponse(_sensorManager->initEZPressure(sda, scl) ? "EZPRESS:PIN:OK" : "EZPRESS:PIN:ERROR");
    } else if (strcmp(cmd, "EZPRESS:STATUS") == 0) {
        float p, t;
        if (_sensorManager->readEZPressure(p, t)) {
            char out[80]; snprintf(out, sizeof(out), "EZPRESS:P=%.2f,T=%.2f", p, t);
            sendResponse(out);
        } else sendResponse("EZPRESS:STATUS:ERROR");
    }
}

void BleCommandParser::handleEZCO2Command(const char* cmd) {
    if (!_sensorManager) return;
    if (startsWith(cmd, "EZCO2:PIN:")) {
        int sda, scl; sscanf(cmd + 10, "%d,%d", &sda, &scl);
        sendResponse(_sensorManager->initEZCO2(sda, scl) ? "EZCO2:PIN:OK" : "EZCO2:PIN:ERROR");
    } else if (strcmp(cmd, "EZCO2:STATUS") == 0) {
        uint16_t c; float t, h;
        if (_sensorManager->readEZCO2(c, t, h)) {
            char out[96]; snprintf(out, sizeof(out), "EZCO2:CO2=%u,T=%.2f,H=%.2f", c, t, h);
            sendResponse(out);
        } else sendResponse("EZCO2:STATUS:ERROR");
    }
}

void BleCommandParser::handleEZLCDCommand(const char* cmd) {
    if (!_sensorManager) return;
    if (startsWith(cmd, "LCD:INIT:")) {
        const char* p = cmd + 9; uint8_t r = 2, c = 16;
        if (startsWith(p, "20X4:")) { r = 4; c = 20; p += 5; }
        else if (startsWith(p, "16X2:")) { r = 2; c = 16; p += 5; }
        int scl, sda; sscanf(p, "%d,%d", &scl, &sda);
        sendResponse(_sensorManager->initEZLCD(sda, scl, r, c) ? "LCD:INIT:OK" : "LCD:INIT:ERROR");
    } else if (strcmp(cmd, "LCD:CLEAR") == 0) {
        sendResponse(_sensorManager->clearEZLCD() ? "LCD:CLEAR:OK" : "LCD:CLEAR:ERROR");
    } else if (startsWith(cmd, "LCD:PRINT:")) {
        int r, c; const char* p = cmd + 10; const char* colon = strchr(p, ':');
        if (colon) {
            char rc[16] = {0}; memcpy(rc, p, (size_t)min((ptrdiff_t)sizeof(rc)-1, colon-p));
            sscanf(rc, "%d,%d", &r, &c);
            sendResponse(_sensorManager->printEZLCD(colon + 1, r, c) ? "LCD:PRINT:OK" : "LCD:PRINT:ERROR");
        }
    }
}

void BleCommandParser::handleEZLaserCommand(const char* cmd) {
    if (!_sensorManager) return;
    if (startsWith(cmd, "LASER:PIN:")) {
        sendResponse(_sensorManager->initEZLaser((uint8_t)parseInt(cmd + 10)) ? "LASER:PIN:OK" : "LASER:PIN:ERROR");
    } else if (strcmp(cmd, "LASER:ON") == 0) {
        sendResponse(_sensorManager->setEZLaser(true) ? "LASER:ON:OK" : "LASER:ON:ERROR");
    } else if (strcmp(cmd, "LASER:OFF") == 0) {
        sendResponse(_sensorManager->setEZLaser(false) ? "LASER:OFF:OK" : "LASER:OFF:ERROR");
    }
}

void BleCommandParser::handleEZLightCommand(const char* cmd) {
    if (!_sensorManager) return;
    if (startsWith(cmd, "EZLIGHT:PIN:")) {
        sendResponse(_sensorManager->initEZLight((uint8_t)parseInt(cmd + 12)) ? "EZLIGHT:PIN:OK" : "EZLIGHT:PIN:ERROR");
    } else if (strcmp(cmd, "EZLIGHT:STATUS") == 0) {
        uint16_t r; float p;
        if (_sensorManager->readEZLight(r, p)) {
            char out[48]; snprintf(out, sizeof(out), "EZLIGHT:%u,%.1f", r, p);
            sendResponse(out);
        } else sendResponse("EZLIGHT:STATUS:ERROR");
    }
}

void BleCommandParser::handleEZCurrentCommand(const char* cmd) {
    if (!_sensorManager) return;
    if (startsWith(cmd, "EZCURR:PIN:")) {
        int sda, scl; sscanf(cmd + 11, "%d,%d", &sda, &scl);
        sendResponse(_sensorManager->initEZCurrent(sda, scl) ? "EZCURR:PIN:OK" : "EZCURR:PIN:ERROR");
    } else if (strcmp(cmd, "EZCURR:STATUS") == 0) {
        float c, v;
        if (_sensorManager->readEZCurrent(c, v)) {
            char out[64]; snprintf(out, sizeof(out), "EZCURR:%.2f,%.3f", c, v);
            sendResponse(out);
        } else sendResponse("EZCURR:STATUS:ERROR");
    }
}

// Stubs for missing EZMaker sensors
void BleCommandParser::handleEZVoltCommand(const char* cmd) { sendResponse("EZVOLT:ERROR:NOT_IMPLEMENTED"); }
void BleCommandParser::handleEZThermalCommand(const char* cmd) { sendResponse("EZTHERMAL:ERROR:NOT_IMPLEMENTED"); }
void BleCommandParser::handleEZSoundCommand(const char* cmd) { sendResponse("EZSOUND:ERROR:NOT_IMPLEMENTED"); }
void BleCommandParser::handleEZWeightCommand(const char* cmd) { sendResponse("EZWEIGHT:ERROR:NOT_IMPLEMENTED"); }
void BleCommandParser::handleEZDustCommand(const char* cmd) { sendResponse("EZDUST:ERROR:NOT_IMPLEMENTED"); }

// Helpers
bool BleCommandParser::startsWith(const char* str, const char* prefix) {
    return str && prefix && strncmp(str, prefix, strlen(prefix)) == 0;
}

int BleCommandParser::parseInt(const char* str) { return str ? atoi(str) : 0; }
float BleCommandParser::parseFloat(const char* str) { return str ? (float)atof(str) : 0.0f; }
void BleCommandParser::sendResponse(const char* response) {
    if (_bleServer && response) _bleServer->notifyLastRx(response);
}
