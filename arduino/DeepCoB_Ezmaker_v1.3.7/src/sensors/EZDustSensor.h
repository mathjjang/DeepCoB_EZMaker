/**
 * @file EZDustSensor.h
 * @brief EZMaker PMS7003M fine dust sensor (UART, minimal parser)
 */

#ifndef EZ_DUST_SENSOR_H
#define EZ_DUST_SENSOR_H

#include <Arduino.h>
#include <HardwareSerial.h>

class EZDustSensor {
public:
    EZDustSensor(uint8_t rxPin, uint8_t txPin);
    ~EZDustSensor();

    bool begin();
    bool read(uint16_t& pm10, uint16_t& pm2_5, uint16_t& pm1_0);

private:
    uint8_t _rxPin;
    uint8_t _txPin;

    // Use a dedicated UART port (Serial1) by default.
    HardwareSerial* _serial;
};

#endif // EZ_DUST_SENSOR_H
