/**
 * @file EZGyroSensor.cpp
 * @brief ICM20948 9-axis Sensor Implementation
 */

#include "EZGyroSensor.h"

EZGyroSensor::EZGyroSensor(uint8_t sdaPin, uint8_t sclPin)
    : _sdaPin(sdaPin)
    , _sclPin(sclPin)
{
}

EZGyroSensor::~EZGyroSensor() {
    _inited = false;
}

bool EZGyroSensor::begin() {
    Wire.begin(_sdaPin, _sclPin);
    Wire.setClock(400000);

    // WHO_AM_I (bank 0, 0x00) should be 0xEA for ICM-20948
    uint8_t who = 0;
    if (!readRegs(0x00, &who, 1) || who != 0xEA) {
        Serial.printf("[EZGYRO] ICM-20948 not found (WHO_AM_I=0x%02X)\n", who);
        _inited = false;
        return false;
    }

    // Wake from sleep + select best clock (CLKSEL=1)
    // PWR_MGMT_1 (0x06): [6]=SLEEP, [2:0]=CLKSEL
    if (!writeReg(0x06, 0x01)) {
        Serial.println("[EZGYRO] Failed to write PWR_MGMT_1");
        _inited = false;
        return false;
    }

    // Enable accel+gyro (PWR_MGMT_2: disable bits; 0x00 enables all)
    (void)writeReg(0x07, 0x00);

    _inited = true;
    Serial.println("[EZGYRO] ICM-20948 initialized");
    return true;
}

bool EZGyroSensor::read(float& ax, float& ay, float& az,
                        float& gx, float& gy, float& gz,
                        float& tempC) {
    if (!_inited) return false;

    // Burst read from ACCEL_XOUT_H (0x2D) through TEMP_OUT_L (0x3A)
    uint8_t buf[14] = {0};
    if (!readRegs(0x2D, buf, sizeof(buf))) {
        return false;
    }

    const int16_t rawAx = (int16_t)((uint16_t)buf[0] << 8 | (uint16_t)buf[1]);
    const int16_t rawAy = (int16_t)((uint16_t)buf[2] << 8 | (uint16_t)buf[3]);
    const int16_t rawAz = (int16_t)((uint16_t)buf[4] << 8 | (uint16_t)buf[5]);
    const int16_t rawGx = (int16_t)((uint16_t)buf[6] << 8 | (uint16_t)buf[7]);
    const int16_t rawGy = (int16_t)((uint16_t)buf[8] << 8 | (uint16_t)buf[9]);
    const int16_t rawGz = (int16_t)((uint16_t)buf[10] << 8 | (uint16_t)buf[11]);
    const int16_t rawT  = (int16_t)((uint16_t)buf[12] << 8 | (uint16_t)buf[13]);

    // Defaults after reset are typically:
    // - accel full-scale +/-2g  => 16384 LSB/g
    // - gyro  full-scale +/-250 => 131 LSB/dps
    constexpr float kAccelLsbPerG = 16384.0f;
    constexpr float kGyroLsbPerDps = 131.0f;

    ax = rawAx / kAccelLsbPerG;
    ay = rawAy / kAccelLsbPerG;
    az = rawAz / kAccelLsbPerG;

    gx = rawGx / kGyroLsbPerDps;
    gy = rawGy / kGyroLsbPerDps;
    gz = rawGz / kGyroLsbPerDps;

    // Datasheet: Temp in °C = (TEMP_OUT - RoomTemp_Offset)/Temp_Sensitivity + 21
    // With typical sensitivity 333.87 LSB/°C and offset 0 at 21°C.
    tempC = ((float)rawT / 333.87f) + 21.0f;
    return true;
}

bool EZGyroSensor::writeReg(uint8_t reg, uint8_t val) {
    Wire.beginTransmission(_addr);
    Wire.write(reg);
    Wire.write(val);
    return Wire.endTransmission() == 0;
}

bool EZGyroSensor::readRegs(uint8_t startReg, uint8_t* out, size_t len) {
    if (!out || len == 0) return false;

    Wire.beginTransmission(_addr);
    Wire.write(startReg);
    if (Wire.endTransmission(false) != 0) {
        return false;
    }

    const size_t got = Wire.requestFrom((int)_addr, (int)len);
    if (got != len) {
        while (Wire.available()) (void)Wire.read();
        return false;
    }
    for (size_t i = 0; i < len; i++) {
        out[i] = (uint8_t)Wire.read();
    }
    return true;
}
