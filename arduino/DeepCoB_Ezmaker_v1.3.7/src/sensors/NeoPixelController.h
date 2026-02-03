/**
 * @file NeoPixelController.h
 * @brief NeoPixel (WS2812) LED Strip Controller
 */

#ifndef NEOPIXEL_CONTROLLER_H
#define NEOPIXEL_CONTROLLER_H

#include <Arduino.h>
#include <Adafruit_NeoPixel.h>

class NeoPixelController {
public:
    NeoPixelController(uint8_t pin, uint16_t numPixels);
    ~NeoPixelController();

    bool begin();
    bool setPixelColor(uint16_t index, uint8_t r, uint8_t g, uint8_t b);
    bool setBrightness(uint8_t brightness);  // 0-255
    bool show();
    bool clear();

    uint16_t getNumPixels() const { return _numPixels; }

private:
    uint8_t _pin;
    uint16_t _numPixels;
    Adafruit_NeoPixel* _strip;
};

#endif // NEOPIXEL_CONTROLLER_H
