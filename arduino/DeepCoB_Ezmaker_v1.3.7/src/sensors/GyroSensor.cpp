/**
 * @file GyroSensor.cpp
 * @brief ADXL345 Accelerometer/Gyro Sensor Implementation
 */

#include "GyroSensor.h"

GyroSensor::GyroSensor(uint8_t sdaPin, uint8_t sclPin)
    : _sdaPin(sdaPin)
    , _sclPin(sclPin)
{
}

GyroSensor::~GyroSensor() {
    _inited = false;
}

bool GyroSensor::begin() {
    Wire.begin(_sdaPin, _sclPin);
    Wire.setClock(400000);

    // Verify device id (DEVID = 0xE5)
    uint8_t id = 0;
    if (!readRegs(0x00, &id, 1) || id != 0xE5) {
        Serial.printf("[GYRO] ADXL345 not found (DEVID=0x%02X)\n", id);
        _inited = false;
        return false;
    }

    // POWER_CTL (0x2D): set measure bit (D3)
    if (!writeReg(0x2D, 0x08)) {
        Serial.println("[GYRO] Failed to set MEASURE mode");
        _inited = false;
        return false;
    }

    // DATA_FORMAT (0x31): FULL_RES (D3) + range = +/- 16g (0x03)
    if (!writeReg(0x31, 0x08 | 0x03)) {
        Serial.println("[GYRO] Failed to set DATA_FORMAT");
        _inited = false;
        return false;
    }

    // BW_RATE (0x2C): 100 Hz (0x0A) is a good default
    (void)writeReg(0x2C, 0x0A);

    _inited = true;
    Serial.println("[GYRO] ADXL345 initialized");
    return true;
}

bool GyroSensor::read(float& x, float& y, float& z) {
    if (!_inited) return false;

    uint8_t buf[6] = {0};
    if (!readRegs(0x32, buf, sizeof(buf))) {
        return false;
    }

    const int16_t rawX = (int16_t)((uint16_t)buf[0] | ((uint16_t)buf[1] << 8));
    const int16_t rawY = (int16_t)((uint16_t)buf[2] | ((uint16_t)buf[3] << 8));
    const int16_t rawZ = (int16_t)((uint16_t)buf[4] | ((uint16_t)buf[5] << 8));

    // In FULL_RES mode, scale factor is ~4mg/LSB (0.0039 g/LSB)
    constexpr float kGPerLsb = 0.0039f;
    x = rawX * kGPerLsb;
    y = rawY * kGPerLsb;
    z = rawZ * kGPerLsb;
    return true;
}

bool GyroSensor::writeReg(uint8_t reg, uint8_t val) {
    Wire.beginTransmission(_addr);
    Wire.write(reg);
    Wire.write(val);
    const uint8_t rc = Wire.endTransmission();
    return rc == 0;
}

bool GyroSensor::readRegs(uint8_t startReg, uint8_t* out, size_t len) {
    if (!out || len == 0) return false;
    Wire.beginTransmission(_addr);
    Wire.write(startReg);
    if (Wire.endTransmission(false) != 0) { // repeated start
        return false;
    }

    const size_t got = Wire.requestFrom((int)_addr, (int)len);
    if (got != len) {
        // Drain
        while (Wire.available()) (void)Wire.read();
        return false;
    }
    for (size_t i = 0; i < len; i++) {
        out[i] = (uint8_t)Wire.read();
    }
    return true;
}
