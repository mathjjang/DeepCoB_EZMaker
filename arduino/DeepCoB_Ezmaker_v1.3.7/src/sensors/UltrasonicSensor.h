/**
 * @file UltrasonicSensor.h
 * @brief HC-SR04 Ultrasonic Distance Sensor
 */

#ifndef ULTRASONIC_SENSOR_H
#define ULTRASONIC_SENSOR_H

#include <Arduino.h>

class UltrasonicSensor {
public:
    UltrasonicSensor(uint8_t trigPin, uint8_t echoPin);
    ~UltrasonicSensor();

    bool begin();
    bool read(float& distance);  // Returns distance in cm

private:
    uint8_t _trigPin;
    uint8_t _echoPin;

    static constexpr float SOUND_SPEED_CM_US = 0.0343;  // cm/us
    static constexpr unsigned long TIMEOUT_US = 30000;   // 30ms timeout
};

#endif // ULTRASONIC_SENSOR_H
