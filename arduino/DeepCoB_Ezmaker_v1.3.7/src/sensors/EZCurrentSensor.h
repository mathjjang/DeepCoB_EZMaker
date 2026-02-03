/**
 * @file EZCurrentSensor.h
 * @brief INA219 current sensor (EZCURR, I2C)
 */

#ifndef EZ_CURRENT_SENSOR_H
#define EZ_CURRENT_SENSOR_H

#include <Arduino.h>
#include <Wire.h>

class EZCurrentSensor {
public:
    EZCurrentSensor(uint8_t sdaPin, uint8_t sclPin, uint8_t addr = 0x40);
    ~EZCurrentSensor();

    bool begin();
    bool read(float& current_mA, float& busVoltage_V);

private:
    uint8_t _sdaPin;
    uint8_t _sclPin;
    uint8_t _addr;
    bool _inited = false;

    static constexpr float DEFAULT_RSHUNT_OHMS = 0.1f; // common INA219 breakout shunt

    bool writeReg16(uint8_t reg, uint16_t value);
    bool readReg16(uint8_t reg, uint16_t& value);
};

#endif // EZ_CURRENT_SENSOR_H
