/**
 * @file LCDDisplay.cpp
 * @brief I2C Character LCD Display Implementation
 */

#include "LCDDisplay.h"

LCDDisplay::LCDDisplay(uint8_t sdaPin, uint8_t sclPin, uint8_t rows, uint8_t cols)
    : _sdaPin(sdaPin)
    , _sclPin(sclPin)
    , _rows(rows)
    , _cols(cols)
{
}

LCDDisplay::~LCDDisplay() {
    _inited = false;
}

bool LCDDisplay::begin() {
    Wire.begin(_sdaPin, _sclPin);
    Wire.setClock(400000);

    if (!detectAddress()) {
        Serial.println("[LCD] PCF8574 not found (0x27/0x3F)");
        _inited = false;
        return false;
    }

    delay(50);

    // Initialize in 4-bit mode, per HD44780 init sequence.
    // Send 0x03 three times (8-bit init), then 0x02 (4-bit init).
    (void)write4bits(0x03, 0);
    delay(5);
    (void)write4bits(0x03, 0);
    delay(5);
    (void)write4bits(0x03, 0);
    delay(1);
    (void)write4bits(0x02, 0);
    delay(1);

    // Function set: 4-bit, 2-line, 5x8 dots
    (void)command(0x28);
    // Display control: display on, cursor off, blink off
    (void)command(0x0C);
    // Clear display
    (void)command(0x01);
    delay(2);
    // Entry mode set: increment, no shift
    (void)command(0x06);

    _inited = true;
    Serial.printf("[LCD] Initialized (addr=0x%02X, %dx%d)\n", _addr, _cols, _rows);
    return true;
}

bool LCDDisplay::print(const char* text, uint8_t row, uint8_t col) {
    if (!_inited || !text) return false;
    if (!setCursor(row, col)) return false;

    uint8_t written = 0;
    for (const char* p = text; *p; p++) {
        if (written >= _cols) break;
        if (!writeChar((uint8_t)*p)) return false;
        written++;
    }
    return true;
}

bool LCDDisplay::clear() {
    if (!_inited) return false;
    if (!command(0x01)) return false;
    delay(2);
    return true;
}

bool LCDDisplay::setBacklight(bool on) {
    _backlight = on;
    // Write a no-op expander byte to apply BL state
    return expanderWrite(_backlight ? PIN_BL : 0);
}

bool LCDDisplay::detectAddress() {
    const uint8_t addrs[2] = {0x27, 0x3F};
    for (uint8_t i = 0; i < 2; i++) {
        _addr = addrs[i];
        Wire.beginTransmission(_addr);
        if (Wire.endTransmission() == 0) {
            return true;
        }
    }
    return false;
}

bool LCDDisplay::expanderWrite(uint8_t data) {
    Wire.beginTransmission(_addr);
    Wire.write(data);
    return Wire.endTransmission() == 0;
}

bool LCDDisplay::pulseEnable(uint8_t data) {
    if (!expanderWrite(data | PIN_EN)) return false;
    delayMicroseconds(1);
    if (!expanderWrite(data & ~PIN_EN)) return false;
    delayMicroseconds(50);
    return true;
}

bool LCDDisplay::write4bits(uint8_t nibble, uint8_t mode) {
    uint8_t out = (uint8_t)((nibble & 0x0F) << 4);
    if (mode) out |= PIN_RS;
    if (_backlight) out |= PIN_BL;
    // RW kept low (write)
    if (!expanderWrite(out)) return false;
    return pulseEnable(out);
}

bool LCDDisplay::send(uint8_t value, uint8_t mode) {
    const uint8_t high = (uint8_t)(value >> 4);
    const uint8_t low = (uint8_t)(value & 0x0F);
    return write4bits(high, mode) && write4bits(low, mode);
}

bool LCDDisplay::command(uint8_t value) {
    return send(value, 0);
}

bool LCDDisplay::writeChar(uint8_t value) {
    return send(value, 1);
}

bool LCDDisplay::setCursor(uint8_t row, uint8_t col) {
    if (row >= _rows) row = (uint8_t)(_rows - 1);
    if (col >= _cols) col = (uint8_t)(_cols - 1);
    static const uint8_t rowOffsets[4] = {0x00, 0x40, 0x14, 0x54};
    const uint8_t addr = (uint8_t)(rowOffsets[row] + col);
    return command((uint8_t)(0x80 | addr));
}
