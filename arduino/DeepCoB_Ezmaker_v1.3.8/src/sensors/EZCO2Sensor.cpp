/**
 * @file EZCO2Sensor.cpp
 * @brief SCD40 CO2 Sensor Implementation
 */

#include "EZCO2Sensor.h"

EZCO2Sensor::EZCO2Sensor(uint8_t sdaPin, uint8_t sclPin)
    : _sdaPin(sdaPin)
    , _sclPin(sclPin)
{
}

EZCO2Sensor::~EZCO2Sensor() {
    _inited = false;
    _started = false;
}

bool EZCO2Sensor::begin() {
    Wire.begin(_sdaPin, _sclPin);
    Wire.setClock(400000);

    // Stop any previous measurement session (ignore failure)
    (void)sendCmd(0x3F86); // stop_periodic_measurement
    delay(1);

    // Start periodic measurement
    if (!sendCmd(0x21B1)) { // start_periodic_measurement
        Serial.println("[EZCO2] Failed to start periodic measurement");
        _inited = false;
        return false;
    }

    _inited = true;
    _started = true;
    _startMs = millis();
    Serial.println("[EZCO2] SCD40 initialized (periodic measurement started)");
    return true;
}

bool EZCO2Sensor::read(uint16_t& co2, float& temperature, float& humidity) {
    if (!_inited || !_started) return false;

    // SCD40 needs some time after start; first valid sample is ~5s later.
    if ((millis() - _startMs) < 5000) {
        return false;
    }

    bool ready = false;
    if (!dataReady(ready) || !ready) {
        return false;
    }

    if (!sendCmd(0xEC05)) { // read_measurement
        return false;
    }

    uint8_t buf[9] = {0};
    if (!readBytes(buf, sizeof(buf))) {
        return false;
    }

    // Each value is 2 bytes + CRC
    if (crc8(buf + 0, 2) != buf[2]) return false;
    if (crc8(buf + 3, 2) != buf[5]) return false;
    if (crc8(buf + 6, 2) != buf[8]) return false;

    const uint16_t rawCo2 = (uint16_t)((uint16_t)buf[0] << 8 | buf[1]);
    const uint16_t rawT = (uint16_t)((uint16_t)buf[3] << 8 | buf[4]);
    const uint16_t rawRh = (uint16_t)((uint16_t)buf[6] << 8 | buf[7]);

    co2 = rawCo2;
    temperature = -45.0f + (175.0f * ((float)rawT / 65535.0f));
    humidity = 100.0f * ((float)rawRh / 65535.0f);
    return true;
}

uint8_t EZCO2Sensor::crc8(const uint8_t* data, size_t len) {
    // Sensirion CRC-8: poly 0x31, init 0xFF
    uint8_t crc = 0xFF;
    for (size_t i = 0; i < len; i++) {
        crc ^= data[i];
        for (uint8_t b = 0; b < 8; b++) {
            if (crc & 0x80) crc = (uint8_t)((crc << 1) ^ 0x31);
            else crc <<= 1;
        }
    }
    return crc;
}

bool EZCO2Sensor::sendCmd(uint16_t cmd) {
    Wire.beginTransmission(_addr);
    Wire.write((uint8_t)(cmd >> 8));
    Wire.write((uint8_t)(cmd & 0xFF));
    return Wire.endTransmission() == 0;
}

bool EZCO2Sensor::readBytes(uint8_t* out, size_t len) {
    if (!out || len == 0) return false;
    const size_t got = Wire.requestFrom((int)_addr, (int)len);
    if (got != len) {
        while (Wire.available()) (void)Wire.read();
        return false;
    }
    for (size_t i = 0; i < len; i++) out[i] = (uint8_t)Wire.read();
    return true;
}

bool EZCO2Sensor::dataReady(bool& ready) {
    ready = false;
    if (!sendCmd(0xE4B8)) { // get_data_ready_status
        return false;
    }
    uint8_t buf[3] = {0};
    if (!readBytes(buf, sizeof(buf))) {
        return false;
    }
    if (crc8(buf, 2) != buf[2]) {
        return false;
    }
    const uint16_t status = (uint16_t)((uint16_t)buf[0] << 8 | buf[1]);
    // Data ready indicated by bit 11 (0x0800)
    ready = (status & 0x0800) != 0;
    return true;
}
