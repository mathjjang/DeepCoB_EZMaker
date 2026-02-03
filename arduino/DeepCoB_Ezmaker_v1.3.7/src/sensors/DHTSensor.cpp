/**
 * @file DHTSensor.cpp
 * @brief DHT11/DHT22 Temperature and Humidity Sensor Implementation
 */

#include "DHTSensor.h"

DHTSensor::DHTSensor(uint8_t pin, uint8_t type)
    : _pin(pin)
    , _type(type)
#if defined(EZMAKER_HAS_EXTERNAL_DHT)
    , _dht(nullptr)
#else
    , _begun(false)
#endif
{
}

DHTSensor::~DHTSensor() {
#if defined(EZMAKER_HAS_EXTERNAL_DHT)
    if (_dht != nullptr) {
        delete _dht;
    }
#endif
}

bool DHTSensor::begin() {
#if defined(EZMAKER_HAS_EXTERNAL_DHT)
    _dht = new DHT(_pin, _type);
    _dht->begin();

    // Wait for sensor to stabilize
    delay(2000);

    return true;
#else
    // Minimal built-in implementation (no external libs).
    pinMode(_pin, INPUT_PULLUP);
    _begun = true;
    delay(2000);
    return true;
#endif
}

bool DHTSensor::read(float& temperature, float& humidity) {
#if defined(EZMAKER_HAS_EXTERNAL_DHT)
    if (_dht == nullptr) {
        return false;
    }

    humidity = _dht->readHumidity();
    temperature = _dht->readTemperature();

    // Check if reads failed
    if (isnan(humidity) || isnan(temperature)) {
        Serial.println("[DHT] Read failed");
        return false;
    }

    return true;
#else
    if (!_begun) {
        return false;
    }
    return readInternal(temperature, humidity);
#endif
}

#if !defined(EZMAKER_HAS_EXTERNAL_DHT)
static inline bool dhtWaitForState(uint8_t pin, uint8_t state, uint32_t timeoutUs) {
    const uint32_t start = micros();
    while ((uint8_t)digitalRead(pin) != state) {
        if ((micros() - start) > timeoutUs) {
            return false;
        }
    }
    return true;
}

static inline uint32_t dhtPulseInState(uint8_t pin, uint8_t state, uint32_t timeoutUs) {
    const uint32_t start = micros();
    while ((uint8_t)digitalRead(pin) == state) {
        if ((micros() - start) > timeoutUs) {
            return 0;
        }
    }
    return micros() - start;
}

bool DHTSensor::readInternal(float& temperature, float& humidity) {
    uint8_t data[5] = {0, 0, 0, 0, 0};

    // Send start signal.
    pinMode(_pin, OUTPUT);
    digitalWrite(_pin, LOW);
    if (_type == DHT11) {
        delay(20); // >=18ms
    } else {
        delay(2);  // >=1ms is typically enough for DHT22/21
    }
    digitalWrite(_pin, HIGH);
    delayMicroseconds(40);
    pinMode(_pin, INPUT_PULLUP);

    // Sensor response: LOW ~80us, HIGH ~80us.
    if (!dhtWaitForState(_pin, LOW, 100)) return false;
    if (!dhtPulseInState(_pin, LOW, 120)) return false;
    if (!dhtWaitForState(_pin, HIGH, 100)) return false;
    if (!dhtPulseInState(_pin, HIGH, 120)) return false;

    // Read 40 bits (5 bytes).
    for (uint8_t i = 0; i < 40; i++) {
        if (!dhtWaitForState(_pin, LOW, 120)) return false;
        if (!dhtPulseInState(_pin, LOW, 120)) return false;       // each bit starts with ~50us LOW
        if (!dhtWaitForState(_pin, HIGH, 120)) return false;
        const uint32_t highLen = dhtPulseInState(_pin, HIGH, 200); // then HIGH length determines 0/1
        if (highLen == 0) return false;

        data[i / 8] <<= 1;
        if (highLen > 50) { // ~70us => 1, ~26-28us => 0
            data[i / 8] |= 1;
        }
    }

    // Verify checksum.
    const uint8_t sum = (uint8_t)(data[0] + data[1] + data[2] + data[3]);
    if (sum != data[4]) {
        Serial.println("[DHT] Checksum failed");
        return false;
    }

    if (_type == DHT11) {
        humidity = (float)data[0];
        temperature = (float)data[2];
        return true;
    }

    // DHT22/DHT21: 16-bit humidity, 16-bit temperature (signed).
    const uint16_t rawHum = (uint16_t)(((uint16_t)data[0] << 8) | data[1]);
    const uint16_t rawTemp = (uint16_t)(((uint16_t)data[2] << 8) | data[3]);

    humidity = rawHum / 10.0f;

    int16_t t = (int16_t)(rawTemp & 0x7FFF);
    if (rawTemp & 0x8000) {
        t = (int16_t)(-t);
    }
    temperature = t / 10.0f;
    return true;
}
#endif
