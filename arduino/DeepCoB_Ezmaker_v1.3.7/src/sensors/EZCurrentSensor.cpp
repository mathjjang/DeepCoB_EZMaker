/**
 * @file EZCurrentSensor.cpp
 * @brief INA219 current sensor implementation (EZCURR)
 */

#include "EZCurrentSensor.h"

EZCurrentSensor::EZCurrentSensor(uint8_t sdaPin, uint8_t sclPin, uint8_t addr)
    : _sdaPin(sdaPin)
    , _sclPin(sclPin)
    , _addr(addr)
{
}

EZCurrentSensor::~EZCurrentSensor() {
    _inited = false;
}

bool EZCurrentSensor::begin() {
    Wire.begin(_sdaPin, _sclPin);
    Wire.setClock(400000);

    // Minimal probe: read config register (0x00)
    uint16_t cfg = 0;
    if (!readReg16(0x00, cfg)) {
        _inited = false;
        return false;
    }

    _inited = true;
    return true;
}

bool EZCurrentSensor::read(float& current_mA, float& busVoltage_V) {
    if (!_inited) return false;

    // INA219 registers:
    // 0x01 Shunt voltage (signed, 10uV LSB)
    // 0x02 Bus voltage   (bits [15:3], 4mV LSB)
    uint16_t rawBus = 0;
    uint16_t rawShunt = 0;
    if (!readReg16(0x02, rawBus)) return false;
    if (!readReg16(0x01, rawShunt)) return false;

    // Bus voltage: 4mV per bit (after shifting right by 3)
    const uint16_t busBits = (uint16_t)(rawBus >> 3);
    busVoltage_V = (float)busBits * 0.004f;

    // Shunt voltage: signed 16-bit, 10uV per bit
    const int16_t shuntSigned = (int16_t)rawShunt;
    const float shuntVoltage_V = (float)shuntSigned * 0.00001f;

    // Approx current using assumed shunt value
    const float current_A = shuntVoltage_V / DEFAULT_RSHUNT_OHMS;
    current_mA = current_A * 1000.0f;
    return true;
}

bool EZCurrentSensor::writeReg16(uint8_t reg, uint16_t value) {
    Wire.beginTransmission(_addr);
    Wire.write(reg);
    Wire.write((uint8_t)(value >> 8));
    Wire.write((uint8_t)(value & 0xFF));
    return Wire.endTransmission() == 0;
}

bool EZCurrentSensor::readReg16(uint8_t reg, uint16_t& value) {
    Wire.beginTransmission(_addr);
    Wire.write(reg);
    if (Wire.endTransmission(false) != 0) {
        return false;
    }
    const size_t got = Wire.requestFrom((int)_addr, 2);
    if (got != 2) {
        while (Wire.available()) (void)Wire.read();
        return false;
    }
    const uint8_t msb = (uint8_t)Wire.read();
    const uint8_t lsb = (uint8_t)Wire.read();
    value = (uint16_t)((uint16_t)msb << 8 | (uint16_t)lsb);
    return true;
}
