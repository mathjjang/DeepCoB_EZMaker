/**
 * @file EZThermalSensor.h
 * @brief EZMaker DS18B20 temperature probe (minimal 1-Wire, no external libs)
 */

#ifndef EZ_THERMAL_SENSOR_H
#define EZ_THERMAL_SENSOR_H

#include <Arduino.h>

class EZThermalSensor {
public:
    explicit EZThermalSensor(uint8_t pin);
    ~EZThermalSensor() = default;

    bool begin();
    bool read(float& tempC);

private:
    uint8_t _pin;

    bool resetPulse();
    void writeBit(uint8_t bit);
    uint8_t readBit();
    void writeByte(uint8_t b);
    uint8_t readByte();

    static uint8_t crc8(const uint8_t* data, uint8_t len);
};

#endif // EZ_THERMAL_SENSOR_H
