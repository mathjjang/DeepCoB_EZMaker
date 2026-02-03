/**
 * @file pinmap.h
 * @brief DeepCo Board v2.0 + EZMAKER Shield v2.0 Pin Mapping
 * 
 * ESP32-S3 GPIO mapping for EZMAKER Shield v2.0
 * Source: DeepcoBoard v2.0 Pinmap for EZMAKER Sheild2.xlsx
 * Reference: EZMaker프로젝트.md, sensor_architecture_analysis.md
 * 
 * NAMING CONVENTION:
 * 1. DeepCo Board Fixed Pins (no configuration needed):
 *    - PIN_BUZZER_FIXED (GPIO 42)
 *    - PIN_BLE_STATUS_LED (GPIO 46)
 *    - Camera (dedicated interface, no GPIO)
 * 
 * 2. DeepCo Common Sensors (Dupont cable, dynamic pin, UUID: 1111...888x):
 *    - DEFAULT_XXX_PIN (no EZ prefix)
 *    - Examples: DEFAULT_DHT_PIN, DEFAULT_SERVO1_PIN, DEFAULT_NEOPIXEL_PIN
 * 
 * 3. EZMaker Shield Sensors (4-pin connector, dynamic pin, UUID: 2222...9xxx):
 *    - DEFAULT_EZXXX_PIN (EZ prefix)
 *    - Examples: DEFAULT_EZGYRO_SDA, DEFAULT_EZLASER_PIN, DEFAULT_EZHUMAN_PIN
 */

#ifndef PINMAP_H
#define PINMAP_H

// ============================================================================
// IMPORTANT: Pin assignments are DYNAMIC (configured via BLE commands)
// ============================================================================
// Arduino firmware does NOT use hardcoded pin mappings.
// All sensor pins are configured at runtime via BLE commands like:
//   "EZGYRO:PIN:41,40" → SDA=41, SCL=40
//   "LASER:PIN:21"     → GPIO 21
//
// Block code (JavaScript) uses constants like EZ_I2C_SDA_PIN, which are
// defined in the JS library (integratedBleLib_Camera.js), NOT in this file.

// ============================================================================
// DeepCo Board Fixed Pins (no pin configuration needed)
// ============================================================================
#define PIN_BUZZER_FIXED    42    // GPIO 42 - Built-in buzzer (fixed)
#define PIN_BLE_STATUS_LED  46    // GPIO 46 - BLE Status LED (system use, fixed)
// Note: Camera uses dedicated ESP32-S3 interface (no GPIO pin needed)

// ============================================================================
// I2C Device Addresses (for firmware use)
// ============================================================================
#define I2C_ADDR_BMP280     0x76  // BMP280 pressure sensor (EZPRESS)
#define I2C_ADDR_SCD40      0x62  // SCD40 CO2 sensor (EZCO2)
#define I2C_ADDR_ICM20948   0x68  // ICM20948 gyro sensor (EZGYRO), alt: 0x69
#define I2C_ADDR_INA219     0x40  // INA219 current sensor (EZCURR)
#define I2C_ADDR_LCD        0x27  // LCD PCF8574 I2C expander, alt: 0x3F

// ============================================================================
// EZMAKER Shield v2.0 - Port to GPIO Mapping (for documentation)
// ============================================================================
/*
 * This mapping is for REFERENCE ONLY. Arduino firmware receives GPIO numbers
 * dynamically via BLE commands (e.g., "EZGYRO:PIN:41,40").
 * 
 * Shield Port | ESP32 GPIO | Type         | Typical Use Examples
 * ------------|------------|--------------|--------------------------------
 * D0          | 21         | Digital      | Laser, DHT, LED
 * D1          | 47         | Digital      | PIR, NeoPixel, DS18B20
 * D2          | 48         | Digital      | Touch, Servo 1
 * D3          | 38         | Digital      | Servo 2, Touch
 * D4          | 39         | Digital      | DC Motor
 * D5 (SCL)    | 40         | I2C          | ICM20948, BMP280, SCD40, INA219, LCD
 * D6 (SDA)    | 41         | I2C          | ICM20948, BMP280, SCD40, INA219, LCD
 * A0 (D7)     | 2          | Analog/Dig   | Light, Sound, Hall, DIY-A
 * A1 (D8)     | 1          | Analog/Dig   | DIY-B (Warning: conflicts with TX0)
 * A2 (D9)     | 3          | Analog/Dig   | Voltage sensor
 * D10 (RXD)   | 14         | UART         | PMS7003M(RX), HX711(SCK)
 * D11 (TXD)   | 42         | UART         | PMS7003M(TX), HX711(DOUT)
 * A3 (D12)    | 20         | Analog/Dig   | (Available)
 * A4 (D13)    | 19         | Analog/Dig   | (Available)
 * 
 * DeepCo Board Fixed Pins (not on shield, not configurable):
 * ------------|------------|--------------|--------------------------------
 * Buzzer      | 42         | PWM          | Built-in buzzer
 * BLE LED     | 46         | Digital Out  | BLE connection status indicator
 * Camera      | (CSI/I2C)  | Dedicated    | ESP32-S3 camera interface
 * 
 * How pin configuration works:
 * 1. Block code: ezGyroSensor.setPin(EZ_I2C_SDA_PIN, EZ_I2C_SCL_PIN)
 *    (JS constants defined in integratedBleLib_Camera.js: SDA=41, SCL=40)
 * 2. JS library sends: "EZGYRO:PIN:41,40"
 * 3. Arduino firmware parses: sda=41, scl=40
 * 4. Firmware initializes I2C: Wire.begin(41, 40)
 */

// ============================================================================
// Sensor/Actuator Pin Assignment Guide (for reference only)
// ============================================================================
// NOTE: In MicroPython firmware, ALL sensor pins are initialized to None.
//       Users MUST call setPin() from block code before using sensors.
//       Only fixed pins (Buzzer, BLE LED) are hardcoded.
//
// This section provides RECOMMENDED port-to-sensor mappings for documentation.
// These are NOT used in firmware initialization.
//
// DYNAMIC PIN SENSORS (require setPin() call):
// 
// DeepCo Common Sensors (Dupont cable, UUID: 1111...888x):
//   - DHT (temp/humidity):    D0~D4 (digital)
//   - Ultrasonic (HCSR04):    D0~D4 (trigger + echo, 2 pins)
//   - Servo motor:            D2 (Servo1), D3 (Servo2)
//   - DC Motor:               D4 (PWM)
//   - Touch sensor (TTP223):  D2, D3 (digital)
//   - NeoPixel LED:           D0~D4 (digital)
//   - Light sensor:           A0~A4 (analog)
//   - Gyro (ADXL345):         D6(SDA), D5(SCL) (I2C)
//   - Dust sensor:            A0~A4 (analog, DeepCo version)
//   - External LED:           D0~D4 (digital)
//
// EZMaker Shield Sensors (4-pin connector, UUID: 2222...9xxx):
//   - EZGyro (ICM20948):      D6(SDA), D5(SCL) (I2C)
//   - EZPress (BMP280):       D6(SDA), D5(SCL) (I2C)
//   - EZCO2 (SCD40):          D6(SDA), D5(SCL) (I2C)
//   - EZCurr (INA219):        D6(SDA), D5(SCL) (I2C)
//   - EZLCD (16x2/20x4):      D6(SDA), D5(SCL) (I2C)
//   - EZDust (PMS7003M):      D10(RX), D11(TX) (UART)
//   - EZWeight (HX711):       D11(DOUT), D10(SCK) (UART pins)
//   - EZLaser:                D0~D4 (digital)
//   - EZHuman (PIR):          D0~D4 (digital)
//   - EZLight:                A0~A4 (analog)
//   - EZSound:                A0~A4 (analog)
//   - EZHall (magnetic):      A0~A4 (analog)
//   - EZDIY-A:                A0~A4 (analog)
//   - EZDIY-B:                A0~A4 (analog)
//   - EZVolt:                 A0~A4 (analog)
//   - EZThermal (DS18B20):    D0~D4 (1-Wire)
//
// Example block code usage:
//   let ezGyroSensor = new EzGyroSensor();
//   await ezGyroSensor.setPin(41, 40);  // User provides SDA=41(D6), SCL=40(D5)
//
// Firmware behavior:
//   - On setPin() command: Allocate GPIO and initialize sensor
//   - Before setPin(): Sensor is unavailable (returns error)

#endif // PINMAP_H
