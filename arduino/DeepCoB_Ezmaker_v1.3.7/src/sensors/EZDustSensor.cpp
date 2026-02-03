/**
 * @file EZDustSensor.cpp
 * @brief PMS7003M UART frame reader (no external libs)
 */

#include "EZDustSensor.h"

EZDustSensor::EZDustSensor(uint8_t rxPin, uint8_t txPin)
    : _rxPin(rxPin)
    , _txPin(txPin)
    , _serial(nullptr)
{
}

EZDustSensor::~EZDustSensor() {
    if (_serial) {
        _serial->end();
        delete _serial;
        _serial = nullptr;
    }
}

bool EZDustSensor::begin() {
    if (_serial == nullptr) {
        _serial = new HardwareSerial(1);
    }
    // PMS7003 default: 9600 8N1
    _serial->begin(9600, SERIAL_8N1, _rxPin, _txPin);
    return true;
}

static bool readExact(HardwareSerial& s, uint8_t* buf, size_t n, uint32_t timeoutMs) {
    const uint32_t start = millis();
    size_t got = 0;
    while (got < n) {
        if ((millis() - start) > timeoutMs) return false;
        if (s.available()) {
            buf[got++] = (uint8_t)s.read();
        } else {
            delay(1);
        }
    }
    return true;
}

bool EZDustSensor::read(uint16_t& pm10, uint16_t& pm2_5, uint16_t& pm1_0) {
    if (_serial == nullptr) return false;

    // Find header 0x42 0x4D then read 30 more bytes (total 32).
    const uint32_t start = millis();
    while ((millis() - start) < 1200) {
        if (_serial->available() < 2) {
            delay(1);
            continue;
        }
        int b0 = _serial->read();
        if (b0 < 0) continue;
        if ((uint8_t)b0 != 0x42) continue;

        int b1 = _serial->read();
        if (b1 < 0) continue;
        if ((uint8_t)b1 != 0x4D) continue;

        uint8_t frame[32];
        frame[0] = 0x42;
        frame[1] = 0x4D;
        if (!readExact(*_serial, frame + 2, 30, 400)) {
            return false;
        }

        // Checksum: sum of bytes 0..29 equals bytes 30..31
        uint16_t sum = 0;
        for (int i = 0; i < 30; i++) sum += frame[i];
        const uint16_t chk = (uint16_t)((uint16_t)frame[30] << 8 | frame[31]);
        if (sum != chk) {
            continue; // try next frame
        }

        // Atmospheric environment values:
        // PM1.0 at [10..11], PM2.5 at [12..13], PM10 at [14..15]
        pm1_0 = (uint16_t)((uint16_t)frame[10] << 8 | frame[11]);
        pm2_5 = (uint16_t)((uint16_t)frame[12] << 8 | frame[13]);
        pm10  = (uint16_t)((uint16_t)frame[14] << 8 | frame[15]);
        return true;
    }

    return false;
}

