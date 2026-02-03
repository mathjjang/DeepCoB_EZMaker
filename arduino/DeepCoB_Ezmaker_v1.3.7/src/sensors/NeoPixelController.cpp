/**
 * @file NeoPixelController.cpp
 * @brief NeoPixel (WS2812) LED Strip Controller Implementation
 */

#include "NeoPixelController.h"

NeoPixelController::NeoPixelController(uint8_t pin, uint16_t numPixels)
    : _pin(pin)
    , _numPixels(numPixels)
    , _strip(nullptr)
{
}

NeoPixelController::~NeoPixelController() {
    if (_strip != nullptr) {
        delete _strip;
    }
}

bool NeoPixelController::begin() {
    _strip = new Adafruit_NeoPixel(_numPixels, _pin, NEO_GRB + NEO_KHZ800);
    _strip->begin();
    _strip->clear();
    _strip->show();

    return true;
}

bool NeoPixelController::setPixelColor(uint16_t index, uint8_t r, uint8_t g, uint8_t b) {
    if (_strip == nullptr) {
        return false;
    }

    if (index >= _numPixels) {
        Serial.printf("[NEO] Pixel index %d out of range (max: %d)\n", index, _numPixels - 1);
        return false;
    }

    _strip->setPixelColor(index, _strip->Color(r, g, b));
    return true;
}

bool NeoPixelController::setBrightness(uint8_t brightness) {
    if (_strip == nullptr) {
        return false;
    }

    _strip->setBrightness(brightness);
    return true;
}

bool NeoPixelController::show() {
    if (_strip == nullptr) {
        return false;
    }

    _strip->show();
    return true;
}

bool NeoPixelController::clear() {
    if (_strip == nullptr) {
        return false;
    }

    _strip->clear();
    _strip->show();
    return true;
}
