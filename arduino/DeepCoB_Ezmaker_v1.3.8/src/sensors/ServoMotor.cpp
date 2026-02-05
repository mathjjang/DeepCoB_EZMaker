/**
 * @file ServoMotor.cpp
 * @brief 180-degree Servo Motor Controller Implementation
 */

#include "ServoMotor.h"

ServoMotor::ServoMotor(uint8_t pin)
    : _pin(pin)
    , _currentAngle(90)  // Default to center position
#if defined(ARDUINO_ARCH_ESP32)
    , _begun(false)
    , _channel(-1)
    , _minPulseUs(500)
    , _maxPulseUs(2500)
#endif
{
}

ServoMotor::~ServoMotor() {
#if defined(ARDUINO_ARCH_ESP32)
    // No hard detach dependency (API differs across core versions).
    // Best-effort "stop": return pin to input and free the channel.
    if (_begun) {
        pinMode(_pin, INPUT);
    }
    // Channel free is best-effort; OK if reused across sketches.
#else
    _servo.detach();
#endif
}

bool ServoMotor::begin() {
#if defined(ARDUINO_ARCH_ESP32)
    // ESP32 built-in PWM (LEDC): 50Hz, 16-bit resolution.
    // Allocate a channel on first begin().
    if (_begun) {
        setAngle(_currentAngle);
        return true;
    }

    // Very small static allocator for up to 16 channels.
    static bool s_used[16] = {false};
    int8_t ch = -1;
    for (int8_t i = 0; i < 16; i++) {
        if (!s_used[i]) {
            s_used[i] = true;
            ch = i;
            break;
        }
    }
    if (ch < 0) {
        Serial.println("[SERVO] No free LEDC channels");
        return false;
    }

    _channel = ch;

    // Arduino-ESP32 classic LEDC API (widely supported).
    // Period: 20ms (50Hz), duty range: 0..65535.
    ledcSetup(_channel, 50, 16);
    ledcAttachPin(_pin, _channel);

    _begun = true;
    setAngle(90);
    return true;
#else
    // Generic Arduino Servo library path.
    if (!_servo.attach(_pin)) {
        Serial.printf("[SERVO] Failed to attach to pin %d\n", _pin);
        return false;
    }
    setAngle(90);
    return true;
#endif
}

bool ServoMotor::setAngle(uint8_t angle) {
    // Clamp angle to 0-180 range
    if (angle > 180) {
        angle = 180;
    }

#if defined(ARDUINO_ARCH_ESP32)
    if (!_begun) {
        return false;
    }

    // Map angle -> pulse width.
    const uint16_t pulseUs = (uint16_t)(_minPulseUs +
        ((uint32_t)angle * (uint32_t)(_maxPulseUs - _minPulseUs)) / 180u);
    writePulseUs(pulseUs);
    _currentAngle = angle;
    return true;
#else
    _servo.write(angle);
    _currentAngle = angle;
    return true;
#endif
}

#if defined(ARDUINO_ARCH_ESP32)
void ServoMotor::writePulseUs(uint16_t pulseUs) {
    // Convert microseconds to 16-bit duty for 50Hz (period 20000us).
    // duty = pulseUs / 20000 * 65535
    const uint32_t duty = ((uint32_t)pulseUs * 65535u) / 20000u;
    ledcWrite(_channel, duty);
}
#endif