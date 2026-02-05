/**
 * @file EZCO2Sensor.h
 * @brief SCD40 CO2 Sensor (EZMaker Shield)
 */

#ifndef EZ_CO2_SENSOR_H
#define EZ_CO2_SENSOR_H

#include <Arduino.h>
#include <Wire.h>

class EZCO2Sensor {
public:
    EZCO2Sensor(uint8_t sdaPin, uint8_t sclPin);
    ~EZCO2Sensor();

    bool begin();
    bool read(uint16_t& co2, float& temperature, float& humidity);

private:
    uint8_t _sdaPin;
    uint8_t _sclPin;
    uint8_t _addr = 0x62; // SCD40 fixed address
    bool _inited = false;
    bool _started = false;
    uint32_t _startMs = 0;

    static uint8_t crc8(const uint8_t* data, size_t len);
    bool sendCmd(uint16_t cmd);
    bool readBytes(uint8_t* out, size_t len);
    bool dataReady(bool& ready);
};

#endif // EZ_CO2_SENSOR_H
