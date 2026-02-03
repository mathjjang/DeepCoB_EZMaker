/**
 * @file UltrasonicSensor.cpp
 * @brief HC-SR04 Ultrasonic Distance Sensor Implementation
 */

#include "UltrasonicSensor.h"

UltrasonicSensor::UltrasonicSensor(uint8_t trigPin, uint8_t echoPin)
    : _trigPin(trigPin)
    , _echoPin(echoPin)
{
}

UltrasonicSensor::~UltrasonicSensor() {
}

bool UltrasonicSensor::begin() {
    pinMode(_trigPin, OUTPUT);
    pinMode(_echoPin, INPUT);

    // Initialize trig pin to LOW
    digitalWrite(_trigPin, LOW);
    delayMicroseconds(2);

    return true;
}

bool UltrasonicSensor::read(float& distance) {
    // Send 10us pulse to trigger
    digitalWrite(_trigPin, LOW);
    delayMicroseconds(2);
    digitalWrite(_trigPin, HIGH);
    delayMicroseconds(10);
    digitalWrite(_trigPin, LOW);

    // Measure echo pulse duration
    unsigned long duration = pulseIn(_echoPin, HIGH, TIMEOUT_US);

    if (duration == 0) {
        Serial.println("[ULTRA] Timeout or no echo");
        return false;
    }

    // Calculate distance: duration (us) * speed / 2 (round trip)
    distance = (duration * SOUND_SPEED_CM_US) / 2.0;

    // Sanity check (HC-SR04 range: 2-400 cm)
    if (distance < 2.0 || distance > 400.0) {
        Serial.printf("[ULTRA] Distance out of range: %.2f cm\n", distance);
        return false;
    }

    return true;
}
