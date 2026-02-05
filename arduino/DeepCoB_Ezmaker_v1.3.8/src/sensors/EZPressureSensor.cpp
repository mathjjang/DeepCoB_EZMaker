/**
 * @file EZPressureSensor.cpp
 * @brief BMP280 Pressure/Temperature Sensor Implementation
 */

#include "EZPressureSensor.h"

EZPressureSensor::EZPressureSensor(uint8_t sdaPin, uint8_t sclPin)
    : _sdaPin(sdaPin)
    , _sclPin(sclPin)
{
}

EZPressureSensor::~EZPressureSensor() {
    _inited = false;
}

bool EZPressureSensor::begin() {
    Wire.begin(_sdaPin, _sclPin);
    Wire.setClock(400000);

    if (!detectAndLoadCalib()) {
        Serial.println("[EZPRESS] BMP280 detection/calibration failed");
        _inited = false;
        return false;
    }

    // config (0xF5): t_sb=0.5ms (000), filter=off(000), spi3w=0
    (void)writeReg(0xF5, 0x00);

    // ctrl_meas (0xF4): osrs_t=x1 (001), osrs_p=x1 (001), mode=forced (001)
    (void)writeReg(0xF4, (1 << 5) | (1 << 2) | 0x01);

    _inited = true;
    Serial.printf("[EZPRESS] BMP280 initialized (addr=0x%02X)\n", _addr);
    return true;
}

bool EZPressureSensor::read(float& pressure, float& temperature) {
    if (!_inited) return false;

    // Trigger forced measurement again (same ctrl_meas write)
    if (!writeReg(0xF4, (1 << 5) | (1 << 2) | 0x01)) {
        return false;
    }
    delay(10);

    uint8_t buf[6] = {0};
    if (!readRegs(0xF7, buf, sizeof(buf))) {
        return false;
    }

    const int32_t adc_P = (int32_t)(((uint32_t)buf[0] << 12) | ((uint32_t)buf[1] << 4) | ((uint32_t)buf[2] >> 4));
    const int32_t adc_T = (int32_t)(((uint32_t)buf[3] << 12) | ((uint32_t)buf[4] << 4) | ((uint32_t)buf[5] >> 4));

    (void)compensateTemp(adc_T, temperature);
    const uint32_t pPa = compensatePress(adc_P);

    // JS expects hPa
    pressure = (float)pPa / 100.0f;
    return true;
}

bool EZPressureSensor::writeReg(uint8_t reg, uint8_t val) {
    Wire.beginTransmission(_addr);
    Wire.write(reg);
    Wire.write(val);
    return Wire.endTransmission() == 0;
}

bool EZPressureSensor::readRegs(uint8_t startReg, uint8_t* out, size_t len) {
    if (!out || len == 0) return false;
    Wire.beginTransmission(_addr);
    Wire.write(startReg);
    if (Wire.endTransmission(false) != 0) return false;

    const size_t got = Wire.requestFrom((int)_addr, (int)len);
    if (got != len) {
        while (Wire.available()) (void)Wire.read();
        return false;
    }
    for (size_t i = 0; i < len; i++) out[i] = (uint8_t)Wire.read();
    return true;
}

bool EZPressureSensor::detectAndLoadCalib() {
    // Try 0x76 then 0x77
    const uint8_t addrs[2] = {0x76, 0x77};
    for (uint8_t i = 0; i < 2; i++) {
        _addr = addrs[i];
        uint8_t id = 0;
        if (!readRegs(0xD0, &id, 1)) continue;
        if (id != 0x58) continue; // BMP280 chip id

        uint8_t calib[24] = {0};
        if (!readRegs(0x88, calib, sizeof(calib))) continue;

        dig_T1 = (uint16_t)((uint16_t)calib[1] << 8 | calib[0]);
        dig_T2 = (int16_t)((uint16_t)calib[3] << 8 | calib[2]);
        dig_T3 = (int16_t)((uint16_t)calib[5] << 8 | calib[4]);

        dig_P1 = (uint16_t)((uint16_t)calib[7] << 8 | calib[6]);
        dig_P2 = (int16_t)((uint16_t)calib[9] << 8 | calib[8]);
        dig_P3 = (int16_t)((uint16_t)calib[11] << 8 | calib[10]);
        dig_P4 = (int16_t)((uint16_t)calib[13] << 8 | calib[12]);
        dig_P5 = (int16_t)((uint16_t)calib[15] << 8 | calib[14]);
        dig_P6 = (int16_t)((uint16_t)calib[17] << 8 | calib[16]);
        dig_P7 = (int16_t)((uint16_t)calib[19] << 8 | calib[18]);
        dig_P8 = (int16_t)((uint16_t)calib[21] << 8 | calib[20]);
        dig_P9 = (int16_t)((uint16_t)calib[23] << 8 | calib[22]);

        return true;
    }
    return false;
}

int32_t EZPressureSensor::compensateTemp(int32_t adc_T, float& tempC) {
    // From BMP280 datasheet (integer compensation)
    int32_t var1 = ((((adc_T >> 3) - ((int32_t)dig_T1 << 1))) * ((int32_t)dig_T2)) >> 11;
    int32_t var2 = (((((adc_T >> 4) - ((int32_t)dig_T1)) * ((adc_T >> 4) - ((int32_t)dig_T1))) >> 12) *
                    ((int32_t)dig_T3)) >> 14;
    t_fine = var1 + var2;
    const int32_t T = (t_fine * 5 + 128) >> 8; // 0.01°C
    tempC = (float)T / 100.0f;
    return t_fine;
}

uint32_t EZPressureSensor::compensatePress(int32_t adc_P) {
    // From BMP280 datasheet (integer compensation)
    int64_t var1 = ((int64_t)t_fine) - 128000;
    int64_t var2 = var1 * var1 * (int64_t)dig_P6;
    var2 = var2 + ((var1 * (int64_t)dig_P5) << 17);
    var2 = var2 + (((int64_t)dig_P4) << 35);
    var1 = ((var1 * var1 * (int64_t)dig_P3) >> 8) + ((var1 * (int64_t)dig_P2) << 12);
    var1 = (((((int64_t)1) << 47) + var1)) * ((int64_t)dig_P1) >> 33;
    if (var1 == 0) return 0; // avoid division by zero

    int64_t p = 1048576 - adc_P;
    p = (((p << 31) - var2) * 3125) / var1;
    var1 = (((int64_t)dig_P9) * (p >> 13) * (p >> 13)) >> 25;
    var2 = (((int64_t)dig_P8) * p) >> 19;
    p = ((p + var1 + var2) >> 8) + (((int64_t)dig_P7) << 4);

    // p is in Q24.8 (Pa * 256)
    return (uint32_t)(p >> 8);
}
