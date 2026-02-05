/**
 * @file EZPressureSensor.h
 * @brief BMP280 Pressure/Temperature Sensor (EZMaker Shield)
 */

#ifndef EZ_PRESSURE_SENSOR_H
#define EZ_PRESSURE_SENSOR_H

#include <Arduino.h>
#include <Wire.h>

class EZPressureSensor {
public:
    EZPressureSensor(uint8_t sdaPin, uint8_t sclPin);
    ~EZPressureSensor();

    bool begin();
    bool read(float& pressure, float& temperature);

private:
    uint8_t _sdaPin;
    uint8_t _sclPin;
    uint8_t _addr = 0x76; // BMP280 default
    bool _inited = false;

    // Calibration data
    uint16_t dig_T1 = 0;
    int16_t dig_T2 = 0;
    int16_t dig_T3 = 0;
    uint16_t dig_P1 = 0;
    int16_t dig_P2 = 0;
    int16_t dig_P3 = 0;
    int16_t dig_P4 = 0;
    int16_t dig_P5 = 0;
    int16_t dig_P6 = 0;
    int16_t dig_P7 = 0;
    int16_t dig_P8 = 0;
    int16_t dig_P9 = 0;
    int32_t t_fine = 0;

    bool writeReg(uint8_t reg, uint8_t val);
    bool readRegs(uint8_t startReg, uint8_t* out, size_t len);
    bool detectAndLoadCalib();
    int32_t compensateTemp(int32_t adc_T, float& tempC);
    uint32_t compensatePress(int32_t adc_P);
};

#endif // EZ_PRESSURE_SENSOR_H
