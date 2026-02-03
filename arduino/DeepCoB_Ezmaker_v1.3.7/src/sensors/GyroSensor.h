/**
 * @file GyroSensor.h
 * @brief ADXL345 Accelerometer/Gyro Sensor (DeepCo Common)
 */

#ifndef GYRO_SENSOR_H
#define GYRO_SENSOR_H

#include <Arduino.h>
#include <Wire.h>

class GyroSensor {
public:
    GyroSensor(uint8_t sdaPin, uint8_t sclPin);
    ~GyroSensor();

    bool begin();
    bool read(float& x, float& y, float& z);

private:
    uint8_t _sdaPin;
    uint8_t _sclPin;
    uint8_t _addr = 0x53; // ADXL345 default I2C address
    bool _inited = false;

    bool writeReg(uint8_t reg, uint8_t val);
    bool readRegs(uint8_t startReg, uint8_t* out, size_t len);
};

#endif // GYRO_SENSOR_H
