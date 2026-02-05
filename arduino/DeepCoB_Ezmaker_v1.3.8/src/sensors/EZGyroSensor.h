/**
 * @file EZGyroSensor.h
 * @brief ICM20948 9-axis Sensor (EZMaker Shield)
 */

#ifndef EZ_GYRO_SENSOR_H
#define EZ_GYRO_SENSOR_H

#include <Arduino.h>
#include <Wire.h>

class EZGyroSensor {
public:
    EZGyroSensor(uint8_t sdaPin, uint8_t sclPin);
    ~EZGyroSensor();

    bool begin();
    // Units:
    // - accel: g
    // - gyro:  dps
    // - temp:  degC
    bool read(float& ax, float& ay, float& az,
              float& gx, float& gy, float& gz,
              float& tempC);

private:
    uint8_t _sdaPin;
    uint8_t _sclPin;
    uint8_t _addr = 0x68; // ICM-20948 default I2C address (AD0=0)
    bool _inited = false;

    bool writeReg(uint8_t reg, uint8_t val);
    bool readRegs(uint8_t startReg, uint8_t* out, size_t len);
};

#endif // EZ_GYRO_SENSOR_H
