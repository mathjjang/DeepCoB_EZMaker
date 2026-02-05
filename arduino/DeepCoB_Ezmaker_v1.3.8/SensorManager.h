/**
 * @file SensorManager.h
 * @brief Dynamic sensor/actuator manager for EZMaker
 * 
 * Manages all sensors and actuators with lazy loading (MicroPython compatible).
 * Sensors are initialized only when PIN commands are received.
 */

#ifndef SENSOR_MANAGER_H
#define SENSOR_MANAGER_H

#include <Arduino.h>

// Forward declarations for sensor classes
class DHTSensor;
class UltrasonicSensor;
class ServoMotor;
class NeoPixelController;
class GyroSensor;
class EZGyroSensor;
class EZPressureSensor;
class EZCO2Sensor;
class LCDDisplay;
class EZCurrentSensor;
class EZThermalSensor;
class EZWeightSensor;
class EZDustSensor;

/**
 * @class SensorManager
 * @brief Central manager for all sensors and actuators
 * 
 * Features:
 * - Lazy loading: sensors initialized only when needed
 * - Runtime pin configuration via BLE commands
 * - Memory efficient: only used sensors consume RAM
 */
class SensorManager {
public:
    SensorManager();
    ~SensorManager();

    // ========================================================================
    // DeepCo Common Sensors (Dupont-connected, dynamic pins)
    // ========================================================================
    
    // DHT Temperature/Humidity Sensor
    bool initDHT(uint8_t pin);
    bool readDHT(float& temp, float& humidity);
    void deinitDHT();
    bool isDHTInitialized() const { return _dhtSensor != nullptr; }
    
    // Ultrasonic Distance Sensor (HC-SR04)
    bool initUltrasonic(uint8_t trigPin, uint8_t echoPin);
    bool readUltrasonic(float& distance);
    void deinitUltrasonic();
    bool isUltrasonicInitialized() const { return _ultrasonicSensor != nullptr; }
    
    // Servo Motor (180 degree)
    bool initServo(uint8_t index, uint8_t pin);  // index: 1 or 2
    bool setServoAngle(uint8_t index, uint8_t angle);
    void deinitServo(uint8_t index);
    bool isServoInitialized(uint8_t index) const;
    
    // NeoPixel LED Strip
    bool initNeoPixel(uint8_t pin, uint16_t numPixels);
    bool setNeoPixelColor(uint16_t index, uint8_t r, uint8_t g, uint8_t b);
    bool setNeoPixelBrightness(uint8_t brightness);
    bool showNeoPixel();
    uint16_t getNeoPixelCount() const;
    void deinitNeoPixel();
    bool isNeoPixelInitialized() const { return _neoPixelController != nullptr; }
    
    // Gyro Sensor (ADXL345)
    bool initGyro(uint8_t sdaPin, uint8_t sclPin);
    bool readGyro(float& x, float& y, float& z);
    void deinitGyro();
    bool isGyroInitialized() const { return _gyroSensor != nullptr; }
    
    // Touch Sensor (Digital)
    bool initTouch(uint8_t pin);
    bool readTouch(bool& touched);
    void deinitTouch();
    bool isTouchInitialized() const { return _touchPin >= 0; }
    
    // Light Sensor (Analog)
    bool initLight(uint8_t analogPin, uint8_t digitalPin);
    bool readLight(uint16_t& analogValue, bool& isDark);
    void deinitLight();
    bool isLightInitialized() const { return _lightAnalogPin >= 0; }
    
    // LED (Digital output)
    bool initLED(uint8_t pin);
    bool setLED(bool state);
    void deinitLED();
    bool isLEDInitialized() const { return _ledPin >= 0; }

    // DC Motor (single PWM pin)
    bool initDCMotor(uint8_t pin);
    bool setDCMotorSpeed(uint8_t speedPercent); // 0..100
    bool stopDCMotor();
    void deinitDCMotor();
    bool isDCMotorInitialized() const { return _dcMotorPin >= 0; }

    // Human (PIR) Sensor (Digital)
    bool initHuman(uint8_t pin);
    bool readHuman(bool& detected);
    void deinitHuman();
    bool isHumanInitialized() const { return _humanPin >= 0; }

    // Dust Sensor (Analog dust sensor, LED + ADC)
    bool initDust(uint8_t ledPin, uint8_t adcPin);
    bool readDust(float& density_ug_m3, float& voltage_V, uint16_t& raw);
    bool calibrateDust(float& voc_V);
    void deinitDust();
    bool isDustInitialized() const { return _dustLedPin >= 0 && _dustAdcPin >= 0; }

    // DIY-A (Analog)
    bool initDIYA(uint8_t adcPin);
    bool readDIYA(float& voltage, uint16_t& raw10bit);
    void deinitDIYA();
    bool isDIYAInitialized() const { return _diyaPin >= 0; }

    // DIY-B (Analog)
    bool initDIYB(uint8_t adcPin);
    bool readDIYB(float& voltage, uint16_t& raw10bit);
    void deinitDIYB();
    bool isDIYBInitialized() const { return _diybPin >= 0; }

    // Hall (Analog)
    bool initHall(uint8_t adcPin);
    bool readHall(uint16_t& raw10bit, int& strength, int& density);
    void deinitHall();
    bool isHallInitialized() const { return _hallPin >= 0; }
    
    // ========================================================================
    // EZMaker Shield Sensors (dynamic pins, EZ prefix)
    // ========================================================================
    
    // EZ Gyro Sensor (ICM20948)
    bool initEZGyro(uint8_t sdaPin, uint8_t sclPin);
    bool readEZGyro(float& ax, float& ay, float& az,
                    float& gx, float& gy, float& gz,
                    float& tempC);
    void deinitEZGyro();
    bool isEZGyroInitialized() const { return _ezGyroSensor != nullptr; }
    
    // EZ Pressure Sensor (BMP280)
    bool initEZPressure(uint8_t sdaPin, uint8_t sclPin);
    bool readEZPressure(float& pressure, float& temperature);
    void deinitEZPressure();
    bool isEZPressureInitialized() const { return _ezPressureSensor != nullptr; }
    
    // EZ CO2 Sensor (SCD40)
    bool initEZCO2(uint8_t sdaPin, uint8_t sclPin);
    bool readEZCO2(uint16_t& co2, float& temp, float& humidity);
    void deinitEZCO2();
    bool isEZCO2Initialized() const { return _ezCO2Sensor != nullptr; }
    
    // EZ LCD Display (I2C Character LCD)
    bool initEZLCD(uint8_t sdaPin, uint8_t sclPin, uint8_t rows, uint8_t cols);
    bool printEZLCD(const char* text, uint8_t row, uint8_t col);
    bool clearEZLCD();
    bool setEZLCDBacklight(bool on);
    void deinitEZLCD();
    bool isEZLCDInitialized() const { return _ezLCDDisplay != nullptr; }
    
    // EZ Laser Module (Digital output)
    bool initEZLaser(uint8_t pin);
    bool setEZLaser(bool state);
    void deinitEZLaser();
    bool isEZLaserInitialized() const { return _ezLaserPin >= 0; }

    // EZ Light Sensor (Analog)
    bool initEZLight(uint8_t adcPin);
    bool readEZLight(uint16_t& raw10bit, float& percent);
    void deinitEZLight();
    bool isEZLightInitialized() const { return _ezLightPin >= 0; }

    // EZ Current Sensor (INA219)
    bool initEZCurrent(uint8_t sdaPin, uint8_t sclPin);
    bool readEZCurrent(float& current_mA, float& voltage_V);
    void deinitEZCurrent();
    bool isEZCurrentInitialized() const { return _ezCurrentSensor != nullptr; }

    // EZ Volt Sensor (Analog)
    bool initEZVolt(uint8_t adcPin);
    bool readEZVolt(uint16_t& raw10bit, float& voltage);
    void deinitEZVolt();
    bool isEZVoltInitialized() const { return _ezVoltPin >= 0; }

    // EZ Sound Sensor (Analog)
    bool initEZSound(uint8_t adcPin);
    bool readEZSound(uint16_t& raw10bit, float& percent);
    void deinitEZSound();
    bool isEZSoundInitialized() const { return _ezSoundPin >= 0; }

    // EZ Thermal (DS18B20)
    bool initEZThermal(uint8_t pin);
    bool readEZThermal(float& tempC);
    void deinitEZThermal();
    bool isEZThermalInitialized() const { return _ezThermalSensor != nullptr; }

    // EZ Weight (HX711)
    bool initEZWeight(uint8_t doutPin, uint8_t sckPin);
    bool readEZWeight(int32_t& raw, float& weight);
    void deinitEZWeight();
    bool isEZWeightInitialized() const { return _ezWeightSensor != nullptr; }

    // EZ Dust (PMS7003M)
    bool initEZDust(uint8_t rxPin, uint8_t txPin);
    bool readEZDust(uint16_t& pm10, uint16_t& pm2_5, uint16_t& pm1_0);
    void deinitEZDust();
    bool isEZDustInitialized() const { return _ezDustSensor != nullptr; }
    
    // TODO: Add more EZ sensors
    // - EZHuman (PIR sensor)
    // - EZDust (PMS7003M)
    // - EZWeight (HX711)
    // - EZThermal (DS18B20)
    // - EZSound (Microphone)
    // - EZCurrent (INA219)
    // - EZVolt, EZLight, EZDIYA, EZDIYB, EZHall, etc.
    
    // ========================================================================
    // DeepCo Board Fixed Sensors (no pin config needed)
    // ========================================================================
    
    // Buzzer is handled separately in BuzzerController
    // Camera is handled separately in CameraTask
    
    // ========================================================================
    // Utility
    // ========================================================================
    
    // Deinitialize all sensors (for cleanup)
    void deinitAll();
    
    // Get sensor status (for debugging)
    void printStatus();

private:
    // DeepCo Common Sensor objects (nullptr when not initialized)
    DHTSensor* _dhtSensor;
    UltrasonicSensor* _ultrasonicSensor;
    ServoMotor* _servo1;
    ServoMotor* _servo2;
    NeoPixelController* _neoPixelController;
    GyroSensor* _gyroSensor;
    
    // Simple digital/analog sensors (use pin number, -1 when not initialized)
    int8_t _touchPin;
    int8_t _lightAnalogPin;
    int8_t _lightDigitalPin;
    int8_t _ledPin;
    int8_t _dcMotorPin;
    int8_t _humanPin;
    int8_t _dustLedPin;
    int8_t _dustAdcPin;
    float _dustVoc_V;
    int8_t _diyaPin;
    int8_t _diybPin;
    int8_t _hallPin;
    
    // EZMaker Shield Sensor objects
    EZGyroSensor* _ezGyroSensor;
    EZPressureSensor* _ezPressureSensor;
    EZCO2Sensor* _ezCO2Sensor;
    LCDDisplay* _ezLCDDisplay;
    int8_t _ezLaserPin;
    int8_t _ezLightPin;
    int8_t _ezVoltPin;
    int8_t _ezSoundPin;
    EZCurrentSensor* _ezCurrentSensor;
    EZThermalSensor* _ezThermalSensor;
    EZWeightSensor* _ezWeightSensor;
    EZDustSensor* _ezDustSensor;
    
    // TODO: Add more EZ sensor pointers
};

#endif // SENSOR_MANAGER_H
