/**
 * @file LCDDisplay.h
 * @brief I2C Character LCD Display (16x2, 20x4, etc.)
 */

#ifndef LCD_DISPLAY_H
#define LCD_DISPLAY_H

#include <Arduino.h>
#include <Wire.h>

class LCDDisplay {
public:
    LCDDisplay(uint8_t sdaPin, uint8_t sclPin, uint8_t rows, uint8_t cols);
    ~LCDDisplay();

    bool begin();
    bool print(const char* text, uint8_t row, uint8_t col);
    bool clear();
    bool setBacklight(bool on);

private:
    uint8_t _sdaPin;
    uint8_t _sclPin;
    uint8_t _rows;
    uint8_t _cols;
    uint8_t _addr = 0x27; // common PCF8574 backpack address (alt: 0x3F)
    bool _inited = false;
    bool _backlight = true;

    // PCF8574 pin mapping (common)
    // P0=RS, P1=RW, P2=EN, P3=Backlight, P4..P7=D4..D7
    static constexpr uint8_t PIN_RS = 0x01;
    static constexpr uint8_t PIN_RW = 0x02;
    static constexpr uint8_t PIN_EN = 0x04;
    static constexpr uint8_t PIN_BL = 0x08;

    bool expanderWrite(uint8_t data);
    bool pulseEnable(uint8_t data);
    bool write4bits(uint8_t nibble, uint8_t mode);
    bool send(uint8_t value, uint8_t mode);
    bool command(uint8_t value);
    bool writeChar(uint8_t value);
    bool setCursor(uint8_t row, uint8_t col);
    bool detectAddress();
};

#endif // LCD_DISPLAY_H
