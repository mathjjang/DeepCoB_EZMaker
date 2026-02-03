/**
 * @file EZWeightSensor.cpp
 * @brief Minimal HX711 implementation (no external libs)
 */

#include "EZWeightSensor.h"

EZWeightSensor::EZWeightSensor(uint8_t doutPin, uint8_t sckPin)
    : _doutPin(doutPin)
    , _sckPin(sckPin)
    , _offset(0)
    , _scale(1000.0f) // default scale (needs calibration for real grams)
{
}

bool EZWeightSensor::begin() {
    pinMode(_doutPin, INPUT);
    pinMode(_sckPin, OUTPUT);
    digitalWrite(_sckPin, LOW);
    return true;
}

bool EZWeightSensor::read(int32_t& raw, float& weight) {
    if (!readRaw(raw)) return false;
    weight = ((float)(raw - _offset)) / _scale;
    return true;
}

bool EZWeightSensor::readRaw(int32_t& raw) {
    // Wait for data ready (DOUT low)
    const uint32_t start = millis();
    while (digitalRead(_doutPin) == HIGH) {
        if ((millis() - start) > 2000) {
            return false;
        }
        delay(1);
    }

    uint32_t value = 0;
    for (uint8_t i = 0; i < 24; i++) {
        digitalWrite(_sckPin, HIGH);
        delayMicroseconds(1);
        value = (value << 1) | (uint32_t)(digitalRead(_doutPin) ? 1 : 0);
        digitalWrite(_sckPin, LOW);
        delayMicroseconds(1);
    }

    // Set gain/channel: 128 (1 extra pulse)
    digitalWrite(_sckPin, HIGH);
    delayMicroseconds(1);
    digitalWrite(_sckPin, LOW);

    // Sign extend 24-bit two's complement
    if (value & 0x800000) {
        value |= 0xFF000000;
    }
    raw = (int32_t)value;
    return true;
}

