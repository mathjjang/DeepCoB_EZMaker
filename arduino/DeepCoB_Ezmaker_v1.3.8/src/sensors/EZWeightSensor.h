/**
 * @file EZWeightSensor.h
 * @brief EZMaker HX711 weight sensor (minimal bit-bang, no external libs)
 */

#ifndef EZ_WEIGHT_SENSOR_H
#define EZ_WEIGHT_SENSOR_H

#include <Arduino.h>

class EZWeightSensor {
public:
    EZWeightSensor(uint8_t doutPin, uint8_t sckPin);
    ~EZWeightSensor() = default;

    bool begin();
    bool read(int32_t& raw, float& weight);

private:
    uint8_t _doutPin;
    uint8_t _sckPin;

    // Basic scaling (no calibration command in current JS protocol)
    int32_t _offset;
    float _scale;

    bool readRaw(int32_t& raw);
};

#endif // EZ_WEIGHT_SENSOR_H
