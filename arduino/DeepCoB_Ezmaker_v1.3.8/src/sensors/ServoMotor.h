/**
 * @file ServoMotor.h
 * @brief 180-degree Servo Motor Controller
 */

#ifndef SERVO_MOTOR_H
#define SERVO_MOTOR_H

#include <Arduino.h>

// Servo library strategy:
// - ESP32: use built-in LEDC PWM (no external libraries required).
// - Other MCUs: fall back to Arduino Servo library (<Servo.h>).
#if !defined(ARDUINO_ARCH_ESP32)
  #include <Servo.h>
#endif

class ServoMotor {
public:
    ServoMotor(uint8_t pin);
    ~ServoMotor();

    bool begin();
    bool setAngle(uint8_t angle);  // 0-180 degrees
    uint8_t getAngle() const { return _currentAngle; }

private:
    uint8_t _pin;
    uint8_t _currentAngle;

#if defined(ARDUINO_ARCH_ESP32)
    bool _begun;
    int8_t _channel;
    uint16_t _minPulseUs;
    uint16_t _maxPulseUs;
    void writePulseUs(uint16_t pulseUs);
#else
    Servo _servo;
#endif
};

#endif // SERVO_MOTOR_H
