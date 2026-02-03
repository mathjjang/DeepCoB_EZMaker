/**
 * @file DHTSensor.h
 * @brief DHT11/DHT22 Temperature and Humidity Sensor
 */

#ifndef DHT_SENSOR_H
#define DHT_SENSOR_H

#include <Arduino.h>

// DHT type constants (so this header compiles even without external libs)
#ifndef DHT11
  #define DHT11 11
#endif
#ifndef DHT22
  #define DHT22 22
#endif
#ifndef DHT21
  #define DHT21 21
#endif

// Optional external DHT libraries:
// - Adafruit "DHT sensor library" provides <DHT.h>
// - Adafruit TinyDHT provides <TinyDHT.h>
#if __has_include(<DHT.h>)
  #include <DHT.h>
  #define EZMAKER_HAS_EXTERNAL_DHT 1
#elif __has_include(<TinyDHT.h>)
  #include <TinyDHT.h>
  #define EZMAKER_HAS_EXTERNAL_DHT 1
#endif

class DHTSensor {
public:
    DHTSensor(uint8_t pin, uint8_t type = DHT11);
    ~DHTSensor();

    bool begin();
    bool read(float& temperature, float& humidity);

private:
    uint8_t _pin;
    uint8_t _type;

#if defined(EZMAKER_HAS_EXTERNAL_DHT)
    DHT* _dht;
#else
    bool _begun;
    bool readInternal(float& temperature, float& humidity);
#endif
};

#endif // DHT_SENSOR_H
