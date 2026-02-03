/**
 * @file EZThermalSensor.cpp
 * @brief Minimal DS18B20 1-Wire implementation (no external libs)
 */

#include "EZThermalSensor.h"

EZThermalSensor::EZThermalSensor(uint8_t pin) : _pin(pin) {}

bool EZThermalSensor::begin() {
    pinMode(_pin, INPUT_PULLUP);
    return true;
}

bool EZThermalSensor::read(float& tempC) {
    // Start conversion
    if (!resetPulse()) return false;
    writeByte(0xCC); // SKIP ROM
    writeByte(0x44); // CONVERT T
    delay(750);

    // Read scratchpad
    if (!resetPulse()) return false;
    writeByte(0xCC); // SKIP ROM
    writeByte(0xBE); // READ SCRATCHPAD

    uint8_t data[9];
    for (uint8_t i = 0; i < 9; i++) {
        data[i] = readByte();
    }

    if (crc8(data, 8) != data[8]) {
        return false;
    }

    const int16_t raw = (int16_t)((int16_t)data[1] << 8 | data[0]);
    tempC = (float)raw / 16.0f;
    return true;
}

bool EZThermalSensor::resetPulse() {
    // Reset: pull low 480us, then release and wait for presence.
    pinMode(_pin, OUTPUT);
    digitalWrite(_pin, LOW);
    delayMicroseconds(480);
    pinMode(_pin, INPUT_PULLUP);
    delayMicroseconds(70);

    const bool presence = (digitalRead(_pin) == LOW);
    delayMicroseconds(410);
    return presence;
}

void EZThermalSensor::writeBit(uint8_t bit) {
    pinMode(_pin, OUTPUT);
    digitalWrite(_pin, LOW);
    if (bit) {
        // Write '1' slot: low 1-15us, then release
        delayMicroseconds(6);
        pinMode(_pin, INPUT_PULLUP);
        delayMicroseconds(64);
    } else {
        // Write '0' slot: keep low ~60us
        delayMicroseconds(60);
        pinMode(_pin, INPUT_PULLUP);
        delayMicroseconds(10);
    }
}

uint8_t EZThermalSensor::readBit() {
    uint8_t bit = 0;
    pinMode(_pin, OUTPUT);
    digitalWrite(_pin, LOW);
    delayMicroseconds(6);
    pinMode(_pin, INPUT_PULLUP);
    delayMicroseconds(9);
    bit = (uint8_t)digitalRead(_pin);
    delayMicroseconds(55);
    return bit;
}

void EZThermalSensor::writeByte(uint8_t b) {
    for (uint8_t i = 0; i < 8; i++) {
        writeBit((b >> i) & 0x01);
    }
}

uint8_t EZThermalSensor::readByte() {
    uint8_t b = 0;
    for (uint8_t i = 0; i < 8; i++) {
        b |= (readBit() << i);
    }
    return b;
}

uint8_t EZThermalSensor::crc8(const uint8_t* data, uint8_t len) {
    uint8_t crc = 0;
    for (uint8_t i = 0; i < len; i++) {
        uint8_t inbyte = data[i];
        for (uint8_t j = 0; j < 8; j++) {
            const uint8_t mix = (crc ^ inbyte) & 0x01;
            crc >>= 1;
            if (mix) crc ^= 0x8C;
            inbyte >>= 1;
        }
    }
    return crc;
}

