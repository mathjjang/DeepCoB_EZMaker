/**
 * @file SensorManager.cpp
 * @brief Dynamic sensor/actuator manager implementation
 */

#include "SensorManager.h"
#include "src/sensors/DHTSensor.h"
#include "src/sensors/UltrasonicSensor.h"
#include "src/sensors/ServoMotor.h"
#include "src/sensors/NeoPixelController.h"
#include "src/sensors/GyroSensor.h"
#include "src/sensors/EZGyroSensor.h"
#include "src/sensors/EZPressureSensor.h"
#include "src/sensors/EZCO2Sensor.h"
#include "src/sensors/LCDDisplay.h"
#include "src/sensors/EZCurrentSensor.h"
#include "src/sensors/EZThermalSensor.h"
#include "src/sensors/EZWeightSensor.h"
#include "src/sensors/EZDustSensor.h"

SensorManager::SensorManager()
    : _dhtSensor(nullptr)
    , _ultrasonicSensor(nullptr)
    , _servo1(nullptr)
    , _servo2(nullptr)
    , _neoPixelController(nullptr)
    , _gyroSensor(nullptr)
    , _touchPin(-1)
    , _lightAnalogPin(-1)
    , _lightDigitalPin(-1)
    , _ledPin(-1)
    , _dcMotorPin(-1)
    , _humanPin(-1)
    , _dustLedPin(-1)
    , _dustAdcPin(-1)
    , _dustVoc_V(0.0f)
    , _diyaPin(-1)
    , _diybPin(-1)
    , _hallPin(-1)
    , _ezGyroSensor(nullptr)
    , _ezPressureSensor(nullptr)
    , _ezCO2Sensor(nullptr)
    , _ezLCDDisplay(nullptr)
    , _ezLaserPin(-1)
    , _ezLightPin(-1)
    , _ezVoltPin(-1)
    , _ezSoundPin(-1)
    , _ezCurrentSensor(nullptr)
    , _ezThermalSensor(nullptr)
    , _ezWeightSensor(nullptr)
    , _ezDustSensor(nullptr)
{
    Serial.println("[SENSOR] SensorManager initialized (all sensors: nullptr)");
}

SensorManager::~SensorManager() {
    deinitAll();
}

void SensorManager::deinitAll() {
    Serial.println("[SENSOR] Deinitializing all sensors...");
    
    deinitDHT();
    deinitUltrasonic();
    deinitServo(1);
    deinitServo(2);
    deinitNeoPixel();
    deinitGyro();
    deinitTouch();
    deinitLight();
    deinitLED();
    deinitDCMotor();
    deinitHuman();
    deinitDust();
    deinitDIYA();
    deinitDIYB();
    deinitHall();
    
    deinitEZGyro();
    deinitEZPressure();
    deinitEZCO2();
    deinitEZLCD();
    deinitEZLaser();
    deinitEZLight();
    deinitEZVolt();
    deinitEZCurrent();
    deinitEZThermal();
    deinitEZSound();
    deinitEZWeight();
    deinitEZDust();
}

// ============================================================================
// Dust Sensor (Analog: LED + ADC)
// ============================================================================

bool SensorManager::initDust(uint8_t ledPin, uint8_t adcPin) {
    _dustLedPin = (int8_t)ledPin;
    _dustAdcPin = (int8_t)adcPin;

    pinMode(_dustLedPin, OUTPUT);
    // Common dust modules (e.g., GP2Y1010) use LED control active LOW.
    digitalWrite(_dustLedPin, HIGH);
    pinMode(_dustAdcPin, INPUT);

    _dustVoc_V = 0.0f;
    Serial.printf("[SENSOR] Dust initialized LED=%d ADC=%d\n", _dustLedPin, _dustAdcPin);
    return true;
}

bool SensorManager::readDust(float& density_ug_m3, float& voltage_V, uint16_t& raw) {
    if (_dustLedPin < 0 || _dustAdcPin < 0) return false;

    // LED ON (active LOW), sampling window per typical datasheet timing
    digitalWrite(_dustLedPin, LOW);
    delayMicroseconds(280);
    raw = (uint16_t)analogRead(_dustAdcPin); // 0..4095 typical
    delayMicroseconds(40);
    digitalWrite(_dustLedPin, HIGH);
    delayMicroseconds(9680);

    voltage_V = ((float)raw * 3.3f) / 4095.0f;

    // Very simple conversion:
    // - Use VOC baseline if calibrated (in volts)
    // - 0.005 V per (mg/m^3) is a commonly used approximation for GP2Y1010
    float dv = voltage_V - _dustVoc_V;
    if (dv < 0) dv = 0;
    const float density_mg_m3 = dv / 0.005f;
    density_ug_m3 = density_mg_m3 * 1000.0f;
    return true;
}

bool SensorManager::calibrateDust(float& voc_V) {
    if (_dustLedPin < 0 || _dustAdcPin < 0) return false;

    // Average a few samples as baseline VOC.
    float sumV = 0.0f;
    const int samples = 20;
    for (int i = 0; i < samples; i++) {
        float density = 0, v = 0;
        uint16_t r = 0;
        if (!readDust(density, v, r)) return false;
        sumV += v;
        delay(10);
    }
    _dustVoc_V = sumV / (float)samples;
    voc_V = _dustVoc_V;
    Serial.printf("[SENSOR] Dust calibrated VOC=%.3fV\n", _dustVoc_V);
    return true;
}

void SensorManager::deinitDust() {
    if (_dustLedPin >= 0 || _dustAdcPin >= 0) {
        _dustLedPin = -1;
        _dustAdcPin = -1;
        _dustVoc_V = 0.0f;
        Serial.println("[SENSOR] Dust deinitialized");
    }
}

// ============================================================================
// DHT Temperature/Humidity Sensor
// ============================================================================

bool SensorManager::initDHT(uint8_t pin) {
    Serial.printf("[SENSOR] Initializing DHT on pin %d...\n", pin);
    
    // Deinit existing sensor
    deinitDHT();
    
    // Create new sensor
    _dhtSensor = new DHTSensor(pin);
    if (!_dhtSensor->begin()) {
        Serial.println("[SENSOR] DHT initialization failed");
        delete _dhtSensor;
        _dhtSensor = nullptr;
        return false;
    }
    
    Serial.println("[SENSOR] DHT initialized successfully");
    return true;
}

bool SensorManager::readDHT(float& temp, float& humidity) {
    if (_dhtSensor == nullptr) {
        Serial.println("[SENSOR] DHT not configured");
        return false;
    }
    return _dhtSensor->read(temp, humidity);
}

void SensorManager::deinitDHT() {
    if (_dhtSensor != nullptr) {
        delete _dhtSensor;
        _dhtSensor = nullptr;
        Serial.println("[SENSOR] DHT deinitialized");
    }
}

// ============================================================================
// Ultrasonic Distance Sensor
// ============================================================================

bool SensorManager::initUltrasonic(uint8_t trigPin, uint8_t echoPin) {
    Serial.printf("[SENSOR] Initializing Ultrasonic on Trig=%d, Echo=%d...\n", trigPin, echoPin);
    
    deinitUltrasonic();
    
    _ultrasonicSensor = new UltrasonicSensor(trigPin, echoPin);
    if (!_ultrasonicSensor->begin()) {
        Serial.println("[SENSOR] Ultrasonic initialization failed");
        delete _ultrasonicSensor;
        _ultrasonicSensor = nullptr;
        return false;
    }
    
    Serial.println("[SENSOR] Ultrasonic initialized successfully");
    return true;
}

bool SensorManager::readUltrasonic(float& distance) {
    if (_ultrasonicSensor == nullptr) {
        Serial.println("[SENSOR] Ultrasonic not configured");
        return false;
    }
    return _ultrasonicSensor->read(distance);
}

void SensorManager::deinitUltrasonic() {
    if (_ultrasonicSensor != nullptr) {
        delete _ultrasonicSensor;
        _ultrasonicSensor = nullptr;
        Serial.println("[SENSOR] Ultrasonic deinitialized");
    }
}

// ============================================================================
// Servo Motor
// ============================================================================

bool SensorManager::initServo(uint8_t index, uint8_t pin) {
    Serial.printf("[SENSOR] Initializing Servo%d on pin %d...\n", index, pin);
    
    if (index == 1) {
        deinitServo(1);
        _servo1 = new ServoMotor(pin);
        if (!_servo1->begin()) {
            Serial.println("[SENSOR] Servo1 initialization failed");
            delete _servo1;
            _servo1 = nullptr;
            return false;
        }
        Serial.println("[SENSOR] Servo1 initialized successfully");
        return true;
    }
    else if (index == 2) {
        deinitServo(2);
        _servo2 = new ServoMotor(pin);
        if (!_servo2->begin()) {
            Serial.println("[SENSOR] Servo2 initialization failed");
            delete _servo2;
            _servo2 = nullptr;
            return false;
        }
        Serial.println("[SENSOR] Servo2 initialized successfully");
        return true;
    }
    else {
        Serial.printf("[SENSOR] Invalid servo index: %d\n", index);
        return false;
    }
}

bool SensorManager::setServoAngle(uint8_t index, uint8_t angle) {
    if (index == 1) {
        if (_servo1 == nullptr) {
            Serial.println("[SENSOR] Servo1 not configured");
            return false;
        }
        return _servo1->setAngle(angle);
    }
    else if (index == 2) {
        if (_servo2 == nullptr) {
            Serial.println("[SENSOR] Servo2 not configured");
            return false;
        }
        return _servo2->setAngle(angle);
    }
    return false;
}

void SensorManager::deinitServo(uint8_t index) {
    if (index == 1 && _servo1 != nullptr) {
        delete _servo1;
        _servo1 = nullptr;
        Serial.println("[SENSOR] Servo1 deinitialized");
    }
    else if (index == 2 && _servo2 != nullptr) {
        delete _servo2;
        _servo2 = nullptr;
        Serial.println("[SENSOR] Servo2 deinitialized");
    }
}

bool SensorManager::isServoInitialized(uint8_t index) const {
    if (index == 1) return _servo1 != nullptr;
    if (index == 2) return _servo2 != nullptr;
    return false;
}

// ============================================================================
// NeoPixel LED Strip
// ============================================================================

bool SensorManager::initNeoPixel(uint8_t pin, uint16_t numPixels) {
    Serial.printf("[SENSOR] Initializing NeoPixel on pin %d with %d pixels...\n", pin, numPixels);
    
    deinitNeoPixel();
    
    _neoPixelController = new NeoPixelController(pin, numPixels);
    if (!_neoPixelController->begin()) {
        Serial.println("[SENSOR] NeoPixel initialization failed");
        delete _neoPixelController;
        _neoPixelController = nullptr;
        return false;
    }
    
    Serial.println("[SENSOR] NeoPixel initialized successfully");
    return true;
}

bool SensorManager::setNeoPixelColor(uint16_t index, uint8_t r, uint8_t g, uint8_t b) {
    if (_neoPixelController == nullptr) {
        Serial.println("[SENSOR] NeoPixel not configured");
        return false;
    }
    return _neoPixelController->setPixelColor(index, r, g, b);
}

bool SensorManager::setNeoPixelBrightness(uint8_t brightness) {
    if (_neoPixelController == nullptr) {
        Serial.println("[SENSOR] NeoPixel not configured");
        return false;
    }
    return _neoPixelController->setBrightness(brightness);
}

bool SensorManager::showNeoPixel() {
    if (_neoPixelController == nullptr) {
        Serial.println("[SENSOR] NeoPixel not configured");
        return false;
    }
    return _neoPixelController->show();
}

uint16_t SensorManager::getNeoPixelCount() const {
    if (_neoPixelController == nullptr) return 0;
    return _neoPixelController->getNumPixels();
}

void SensorManager::deinitNeoPixel() {
    if (_neoPixelController != nullptr) {
        delete _neoPixelController;
        _neoPixelController = nullptr;
        Serial.println("[SENSOR] NeoPixel deinitialized");
    }
}

// ============================================================================
// Gyro Sensor (ADXL345)
// ============================================================================

bool SensorManager::initGyro(uint8_t sdaPin, uint8_t sclPin) {
    Serial.printf("[SENSOR] Initializing Gyro on SDA=%d, SCL=%d...\n", sdaPin, sclPin);
    
    deinitGyro();
    
    _gyroSensor = new GyroSensor(sdaPin, sclPin);
    if (!_gyroSensor->begin()) {
        Serial.println("[SENSOR] Gyro initialization failed");
        delete _gyroSensor;
        _gyroSensor = nullptr;
        return false;
    }
    
    Serial.println("[SENSOR] Gyro initialized successfully");
    return true;
}

bool SensorManager::readGyro(float& x, float& y, float& z) {
    if (_gyroSensor == nullptr) {
        Serial.println("[SENSOR] Gyro not configured");
        return false;
    }
    return _gyroSensor->read(x, y, z);
}

void SensorManager::deinitGyro() {
    if (_gyroSensor != nullptr) {
        delete _gyroSensor;
        _gyroSensor = nullptr;
        Serial.println("[SENSOR] Gyro deinitialized");
    }
}

// ============================================================================
// Touch Sensor (Simple Digital Pin)
// ============================================================================

bool SensorManager::initTouch(uint8_t pin) {
    Serial.printf("[SENSOR] Initializing Touch on pin %d...\n", pin);
    
    _touchPin = pin;
    pinMode(_touchPin, INPUT);
    
    Serial.println("[SENSOR] Touch initialized successfully");
    return true;
}

bool SensorManager::readTouch(bool& touched) {
    if (_touchPin < 0) {
        Serial.println("[SENSOR] Touch not configured");
        return false;
    }
    touched = digitalRead(_touchPin);
    return true;
}

void SensorManager::deinitTouch() {
    if (_touchPin >= 0) {
        _touchPin = -1;
        Serial.println("[SENSOR] Touch deinitialized");
    }
}

// ============================================================================
// Light Sensor (Analog + Digital)
// ============================================================================

bool SensorManager::initLight(uint8_t analogPin, uint8_t digitalPin) {
    Serial.printf("[SENSOR] Initializing Light on analog=%d, digital=%d...\n", analogPin, digitalPin);
    
    _lightAnalogPin = analogPin;
    _lightDigitalPin = digitalPin;
    
    pinMode(_lightDigitalPin, INPUT);
    
    Serial.println("[SENSOR] Light initialized successfully");
    return true;
}

bool SensorManager::readLight(uint16_t& analogValue, bool& isDark) {
    if (_lightAnalogPin < 0) {
        Serial.println("[SENSOR] Light not configured");
        return false;
    }
    
    analogValue = analogRead(_lightAnalogPin);
    isDark = digitalRead(_lightDigitalPin);
    return true;
}

void SensorManager::deinitLight() {
    if (_lightAnalogPin >= 0) {
        _lightAnalogPin = -1;
        _lightDigitalPin = -1;
        Serial.println("[SENSOR] Light deinitialized");
    }
}

// ============================================================================
// LED (Simple Digital Output)
// ============================================================================

bool SensorManager::initLED(uint8_t pin) {
    Serial.printf("[SENSOR] Initializing LED on pin %d...\n", pin);
    
    _ledPin = pin;
    pinMode(_ledPin, OUTPUT);
    digitalWrite(_ledPin, LOW);
    
    Serial.println("[SENSOR] LED initialized successfully");
    return true;
}

bool SensorManager::setLED(bool state) {
    if (_ledPin < 0) {
        Serial.println("[SENSOR] LED not configured");
        return false;
    }
    digitalWrite(_ledPin, state ? HIGH : LOW);
    return true;
}

void SensorManager::deinitLED() {
    if (_ledPin >= 0) {
        _ledPin = -1;
        Serial.println("[SENSOR] LED deinitialized");
    }
}

// ============================================================================
// DC Motor (Single PWM Pin)
// ============================================================================

bool SensorManager::initDCMotor(uint8_t pin) {
    Serial.printf("[SENSOR] Initializing DCMotor on pin %d...\n", pin);

    deinitDCMotor();

    _dcMotorPin = pin;
    pinMode(_dcMotorPin, OUTPUT);

    // Use separate LEDC channel for motor PWM
    constexpr uint8_t kChannel = 1;
    constexpr uint32_t kFreqHz = 20000; // above audible range
    constexpr uint8_t kResolutionBits = 8; // 0..255
    ledcSetup(kChannel, kFreqHz, kResolutionBits);
    ledcAttachPin(_dcMotorPin, kChannel);
    ledcWrite(kChannel, 0);

    Serial.println("[SENSOR] DCMotor initialized successfully");
    return true;
}

bool SensorManager::setDCMotorSpeed(uint8_t speedPercent) {
    if (_dcMotorPin < 0) {
        Serial.println("[SENSOR] DCMotor not configured");
        return false;
    }
    constexpr uint8_t kChannel = 1;
    const uint8_t sp = (uint8_t)constrain((int)speedPercent, 0, 100);
    const uint8_t duty = (uint8_t)((uint16_t)sp * 255 / 100);
    ledcWrite(kChannel, duty);
    return true;
}

bool SensorManager::stopDCMotor() {
    if (_dcMotorPin < 0) {
        Serial.println("[SENSOR] DCMotor not configured");
        return false;
    }
    constexpr uint8_t kChannel = 1;
    ledcWrite(kChannel, 0);
    return true;
}

void SensorManager::deinitDCMotor() {
    if (_dcMotorPin >= 0) {
        constexpr uint8_t kChannel = 1;
        ledcWrite(kChannel, 0);
        ledcDetachPin(_dcMotorPin);
        _dcMotorPin = -1;
        Serial.println("[SENSOR] DCMotor deinitialized");
    }
}

// ============================================================================
// Human (PIR) Sensor
// ============================================================================

bool SensorManager::initHuman(uint8_t pin) {
    Serial.printf("[SENSOR] Initializing Human(PIR) on pin %d...\n", pin);
    _humanPin = pin;
    pinMode(_humanPin, INPUT);
    Serial.println("[SENSOR] Human(PIR) initialized successfully");
    return true;
}

bool SensorManager::readHuman(bool& detected) {
    if (_humanPin < 0) {
        Serial.println("[SENSOR] Human(PIR) not configured");
        return false;
    }
    detected = digitalRead(_humanPin) ? true : false;
    return true;
}

void SensorManager::deinitHuman() {
    if (_humanPin >= 0) {
        _humanPin = -1;
        Serial.println("[SENSOR] Human(PIR) deinitialized");
    }
}

// ============================================================================
// EZMaker Shield Sensors (Stubs for now - implement later)
// ============================================================================

bool SensorManager::initEZGyro(uint8_t sdaPin, uint8_t sclPin) {
    Serial.printf("[SENSOR] Initializing EZGyro on SDA=%d, SCL=%d...\n", sdaPin, sclPin);

    deinitEZGyro();

    _ezGyroSensor = new EZGyroSensor(sdaPin, sclPin);
    if (!_ezGyroSensor->begin()) {
        Serial.println("[SENSOR] EZGyro initialization failed");
        delete _ezGyroSensor;
        _ezGyroSensor = nullptr;
        return false;
    }

    Serial.println("[SENSOR] EZGyro initialized successfully");
    return true;
}

bool SensorManager::readEZGyro(float& ax, float& ay, float& az,
                               float& gx, float& gy, float& gz,
                               float& tempC) {
    if (_ezGyroSensor == nullptr) {
        Serial.println("[SENSOR] EZGyro not configured");
        return false;
    }
    return _ezGyroSensor->read(ax, ay, az, gx, gy, gz, tempC);
}

void SensorManager::deinitEZGyro() {
    if (_ezGyroSensor != nullptr) {
        delete _ezGyroSensor;
        _ezGyroSensor = nullptr;
        Serial.println("[SENSOR] EZGyro deinitialized");
    }
}

bool SensorManager::initEZPressure(uint8_t sdaPin, uint8_t sclPin) {
    Serial.printf("[SENSOR] Initializing EZPressure on SDA=%d, SCL=%d...\n", sdaPin, sclPin);

    deinitEZPressure();

    _ezPressureSensor = new EZPressureSensor(sdaPin, sclPin);
    if (!_ezPressureSensor->begin()) {
        Serial.println("[SENSOR] EZPressure initialization failed");
        delete _ezPressureSensor;
        _ezPressureSensor = nullptr;
        return false;
    }

    Serial.println("[SENSOR] EZPressure initialized successfully");
    return true;
}

bool SensorManager::readEZPressure(float& pressure, float& temperature) {
    if (_ezPressureSensor == nullptr) {
        Serial.println("[SENSOR] EZPressure not configured");
        return false;
    }
    return _ezPressureSensor->read(pressure, temperature);
}

void SensorManager::deinitEZPressure() {
    if (_ezPressureSensor != nullptr) {
        delete _ezPressureSensor;
        _ezPressureSensor = nullptr;
        Serial.println("[SENSOR] EZPressure deinitialized");
    }
}

bool SensorManager::initEZCO2(uint8_t sdaPin, uint8_t sclPin) {
    Serial.printf("[SENSOR] Initializing EZCO2 on SDA=%d, SCL=%d...\n", sdaPin, sclPin);

    deinitEZCO2();

    _ezCO2Sensor = new EZCO2Sensor(sdaPin, sclPin);
    if (!_ezCO2Sensor->begin()) {
        Serial.println("[SENSOR] EZCO2 initialization failed");
        delete _ezCO2Sensor;
        _ezCO2Sensor = nullptr;
        return false;
    }

    Serial.println("[SENSOR] EZCO2 initialized successfully");
    return true;
}

bool SensorManager::readEZCO2(uint16_t& co2, float& temp, float& humidity) {
    if (_ezCO2Sensor == nullptr) {
        Serial.println("[SENSOR] EZCO2 not configured");
        return false;
    }
    return _ezCO2Sensor->read(co2, temp, humidity);
}

void SensorManager::deinitEZCO2() {
    if (_ezCO2Sensor != nullptr) {
        delete _ezCO2Sensor;
        _ezCO2Sensor = nullptr;
        Serial.println("[SENSOR] EZCO2 deinitialized");
    }
}

bool SensorManager::initEZLCD(uint8_t sdaPin, uint8_t sclPin, uint8_t rows, uint8_t cols) {
    Serial.printf("[SENSOR] Initializing EZLCD (SDA=%d, SCL=%d, %dx%d)...\n",
                  sdaPin, sclPin, cols, rows);

    deinitEZLCD();

    _ezLCDDisplay = new LCDDisplay(sdaPin, sclPin, rows, cols);
    if (!_ezLCDDisplay->begin()) {
        Serial.println("[SENSOR] EZLCD initialization failed");
        delete _ezLCDDisplay;
        _ezLCDDisplay = nullptr;
        return false;
    }

    Serial.println("[SENSOR] EZLCD initialized successfully");
    return true;
}

bool SensorManager::printEZLCD(const char* text, uint8_t row, uint8_t col) {
    if (_ezLCDDisplay == nullptr) {
        Serial.println("[SENSOR] EZLCD not configured");
        return false;
    }
    return _ezLCDDisplay->print(text, row, col);
}

bool SensorManager::clearEZLCD() {
    if (_ezLCDDisplay == nullptr) {
        Serial.println("[SENSOR] EZLCD not configured");
        return false;
    }
    return _ezLCDDisplay->clear();
}

void SensorManager::deinitEZLCD() {
    if (_ezLCDDisplay != nullptr) {
        delete _ezLCDDisplay;
        _ezLCDDisplay = nullptr;
        Serial.println("[SENSOR] EZLCD deinitialized");
    }
}

bool SensorManager::setEZLCDBacklight(bool on) {
    if (_ezLCDDisplay == nullptr) {
        Serial.println("[SENSOR] EZLCD not configured");
        return false;
    }
    return _ezLCDDisplay->setBacklight(on);
}

bool SensorManager::initEZLaser(uint8_t pin) {
    Serial.printf("[SENSOR] Initializing EZLaser on pin %d...\n", pin);
    
    _ezLaserPin = pin;
    pinMode(_ezLaserPin, OUTPUT);
    digitalWrite(_ezLaserPin, LOW);
    
    Serial.println("[SENSOR] EZLaser initialized successfully");
    return true;
}

bool SensorManager::setEZLaser(bool state) {
    if (_ezLaserPin < 0) {
        Serial.println("[SENSOR] EZLaser not configured");
        return false;
    }
    digitalWrite(_ezLaserPin, state ? HIGH : LOW);
    return true;
}

void SensorManager::deinitEZLaser() {
    if (_ezLaserPin >= 0) {
        _ezLaserPin = -1;
        Serial.println("[SENSOR] EZLaser deinitialized");
    }
}

// ============================================================================
// EZ Light Sensor (Analog)
// ============================================================================

bool SensorManager::initEZLight(uint8_t adcPin) {
    Serial.printf("[SENSOR] Initializing EZLight on pin %d...\n", adcPin);
    _ezLightPin = adcPin;
    // analogRead pinMode is not strictly required on ESP32 Arduino, but keep consistent
    pinMode(_ezLightPin, INPUT);
    Serial.println("[SENSOR] EZLight initialized successfully");
    return true;
}

bool SensorManager::readEZLight(uint16_t& raw10bit, float& percent) {
    if (_ezLightPin < 0) {
        Serial.println("[SENSOR] EZLight not configured");
        return false;
    }
    const uint16_t raw = (uint16_t)analogRead(_ezLightPin); // typically 0..4095
    raw10bit = (uint16_t)min<uint16_t>(1023, (uint16_t)(raw >> 2)); // approx 10-bit
    percent = ((float)raw10bit * 100.0f) / 1023.0f;
    return true;
}

void SensorManager::deinitEZLight() {
    if (_ezLightPin >= 0) {
        _ezLightPin = -1;
        Serial.println("[SENSOR] EZLight deinitialized");
    }
}

// ============================================================================
// EZ Current Sensor (INA219)
// ============================================================================

bool SensorManager::initEZCurrent(uint8_t sdaPin, uint8_t sclPin) {
    Serial.printf("[SENSOR] Initializing EZCurrent (INA219) SDA=%d SCL=%d...\n", sdaPin, sclPin);
    deinitEZCurrent();

    _ezCurrentSensor = new EZCurrentSensor(sdaPin, sclPin);
    if (!_ezCurrentSensor->begin()) {
        Serial.println("[SENSOR] EZCurrent initialization failed");
        delete _ezCurrentSensor;
        _ezCurrentSensor = nullptr;
        return false;
    }
    Serial.println("[SENSOR] EZCurrent initialized successfully");
    return true;
}

bool SensorManager::readEZCurrent(float& current_mA, float& voltage_V) {
    if (_ezCurrentSensor == nullptr) {
        return false;
    }
    return _ezCurrentSensor->read(current_mA, voltage_V);
}

void SensorManager::deinitEZCurrent() {
    if (_ezCurrentSensor != nullptr) {
        delete _ezCurrentSensor;
        _ezCurrentSensor = nullptr;
        Serial.println("[SENSOR] EZCurrent deinitialized");
    }
}

// ============================================================================
// DIY-A / DIY-B / HALL (Analog sensors)
// ============================================================================

static inline uint16_t adc12To10(int raw12) {
    if (raw12 < 0) raw12 = 0;
    // analogRead(ESP32) typically 0..4095
    uint16_t v = (uint16_t)raw12;
    v = (uint16_t)min<uint16_t>(1023, (uint16_t)(v >> 2));
    return v;
}

bool SensorManager::initDIYA(uint8_t adcPin) {
    _diyaPin = adcPin;
    pinMode(_diyaPin, INPUT);
    Serial.printf("[SENSOR] DIYA initialized on pin %d\n", _diyaPin);
    return true;
}

bool SensorManager::readDIYA(float& voltage, uint16_t& raw10bit) {
    if (_diyaPin < 0) return false;
    raw10bit = adc12To10(analogRead(_diyaPin));
    voltage = ((float)raw10bit * 5.0f) / 1023.0f;
    return true;
}

void SensorManager::deinitDIYA() {
    if (_diyaPin >= 0) {
        _diyaPin = -1;
        Serial.println("[SENSOR] DIYA deinitialized");
    }
}

bool SensorManager::initDIYB(uint8_t adcPin) {
    _diybPin = adcPin;
    pinMode(_diybPin, INPUT);
    Serial.printf("[SENSOR] DIYB initialized on pin %d\n", _diybPin);
    return true;
}

bool SensorManager::readDIYB(float& voltage, uint16_t& raw10bit) {
    if (_diybPin < 0) return false;
    raw10bit = adc12To10(analogRead(_diybPin));
    voltage = ((float)raw10bit * 5.0f) / 1023.0f;
    return true;
}

void SensorManager::deinitDIYB() {
    if (_diybPin >= 0) {
        _diybPin = -1;
        Serial.println("[SENSOR] DIYB deinitialized");
    }
}

bool SensorManager::initHall(uint8_t adcPin) {
    _hallPin = adcPin;
    pinMode(_hallPin, INPUT);
    Serial.printf("[SENSOR] Hall initialized on pin %d\n", _hallPin);
    return true;
}

bool SensorManager::readHall(uint16_t& raw10bit, int& strength, int& density) {
    if (_hallPin < 0) return false;
    raw10bit = adc12To10(analogRead(_hallPin));
    strength = (int)raw10bit - 512;
    density = abs(strength);
    return true;
}

void SensorManager::deinitHall() {
    if (_hallPin >= 0) {
        _hallPin = -1;
        Serial.println("[SENSOR] Hall deinitialized");
    }
}

// ============================================================================
// EZ Volt / EZ Sound (Analog sensors)
// ============================================================================

bool SensorManager::initEZVolt(uint8_t adcPin) {
    _ezVoltPin = adcPin;
    pinMode(_ezVoltPin, INPUT);
    Serial.printf("[SENSOR] EZVolt initialized on pin %d\n", _ezVoltPin);
    return true;
}

bool SensorManager::readEZVolt(uint16_t& raw10bit, float& voltage) {
    if (_ezVoltPin < 0) return false;
    raw10bit = adc12To10(analogRead(_ezVoltPin));
    voltage = ((float)raw10bit * 25.0f) / 1023.0f;
    return true;
}

void SensorManager::deinitEZVolt() {
    if (_ezVoltPin >= 0) {
        _ezVoltPin = -1;
        Serial.println("[SENSOR] EZVolt deinitialized");
    }
}

bool SensorManager::initEZSound(uint8_t adcPin) {
    _ezSoundPin = adcPin;
    pinMode(_ezSoundPin, INPUT);
    Serial.printf("[SENSOR] EZSound initialized on pin %d\n", _ezSoundPin);
    return true;
}

bool SensorManager::readEZSound(uint16_t& raw10bit, float& percent) {
    if (_ezSoundPin < 0) return false;
    raw10bit = adc12To10(analogRead(_ezSoundPin));
    percent = ((float)raw10bit * 100.0f) / 1023.0f;
    return true;
}

void SensorManager::deinitEZSound() {
    if (_ezSoundPin >= 0) {
        _ezSoundPin = -1;
        Serial.println("[SENSOR] EZSound deinitialized");
    }
}

// ============================================================================
// EZ Thermal (DS18B20)
// ============================================================================

bool SensorManager::initEZThermal(uint8_t pin) {
    deinitEZThermal();
    _ezThermalSensor = new EZThermalSensor(pin);
    if (!_ezThermalSensor->begin()) {
        delete _ezThermalSensor;
        _ezThermalSensor = nullptr;
        return false;
    }
    Serial.println("[SENSOR] EZThermal initialized successfully");
    return true;
}

bool SensorManager::readEZThermal(float& tempC) {
    if (_ezThermalSensor == nullptr) return false;
    return _ezThermalSensor->read(tempC);
}

void SensorManager::deinitEZThermal() {
    if (_ezThermalSensor != nullptr) {
        delete _ezThermalSensor;
        _ezThermalSensor = nullptr;
        Serial.println("[SENSOR] EZThermal deinitialized");
    }
}

// ============================================================================
// EZ Weight (HX711)
// ============================================================================

bool SensorManager::initEZWeight(uint8_t doutPin, uint8_t sckPin) {
    deinitEZWeight();
    _ezWeightSensor = new EZWeightSensor(doutPin, sckPin);
    if (!_ezWeightSensor->begin()) {
        delete _ezWeightSensor;
        _ezWeightSensor = nullptr;
        return false;
    }
    Serial.println("[SENSOR] EZWeight initialized successfully");
    return true;
}

bool SensorManager::readEZWeight(int32_t& raw, float& weight) {
    if (_ezWeightSensor == nullptr) return false;
    return _ezWeightSensor->read(raw, weight);
}

void SensorManager::deinitEZWeight() {
    if (_ezWeightSensor != nullptr) {
        delete _ezWeightSensor;
        _ezWeightSensor = nullptr;
        Serial.println("[SENSOR] EZWeight deinitialized");
    }
}

// ============================================================================
// EZ Dust (PMS7003M)
// ============================================================================

bool SensorManager::initEZDust(uint8_t rxPin, uint8_t txPin) {
    deinitEZDust();
    _ezDustSensor = new EZDustSensor(rxPin, txPin);
    if (!_ezDustSensor->begin()) {
        delete _ezDustSensor;
        _ezDustSensor = nullptr;
        return false;
    }
    Serial.println("[SENSOR] EZDust initialized successfully");
    return true;
}

bool SensorManager::readEZDust(uint16_t& pm10, uint16_t& pm2_5, uint16_t& pm1_0) {
    if (_ezDustSensor == nullptr) return false;
    return _ezDustSensor->read(pm10, pm2_5, pm1_0);
}

void SensorManager::deinitEZDust() {
    if (_ezDustSensor != nullptr) {
        delete _ezDustSensor;
        _ezDustSensor = nullptr;
        Serial.println("[SENSOR] EZDust deinitialized");
    }
}

// ============================================================================
// Utility
// ============================================================================

void SensorManager::printStatus() {
    Serial.println("\n========== Sensor Status ==========");
    Serial.printf("DHT:        %s\n", isDHTInitialized() ? "INIT" : "----");
    Serial.printf("Ultrasonic: %s\n", isUltrasonicInitialized() ? "INIT" : "----");
    Serial.printf("Servo1:     %s\n", isServoInitialized(1) ? "INIT" : "----");
    Serial.printf("Servo2:     %s\n", isServoInitialized(2) ? "INIT" : "----");
    Serial.printf("NeoPixel:   %s\n", isNeoPixelInitialized() ? "INIT" : "----");
    Serial.printf("Gyro:       %s\n", isGyroInitialized() ? "INIT" : "----");
    Serial.printf("Touch:      %s\n", isTouchInitialized() ? "INIT" : "----");
    Serial.printf("Light:      %s\n", isLightInitialized() ? "INIT" : "----");
    Serial.printf("LED:        %s\n", isLEDInitialized() ? "INIT" : "----");
    Serial.printf("Dust:       %s\n", isDustInitialized() ? "INIT" : "----");
    Serial.printf("Human:      %s\n", isHumanInitialized() ? "INIT" : "----");
    Serial.printf("DIYA:       %s\n", isDIYAInitialized() ? "INIT" : "----");
    Serial.printf("DIYB:       %s\n", isDIYBInitialized() ? "INIT" : "----");
    Serial.printf("Hall:       %s\n", isHallInitialized() ? "INIT" : "----");
    Serial.printf("EZVolt:     %s\n", isEZVoltInitialized() ? "INIT" : "----");
    Serial.printf("EZSound:    %s\n", isEZSoundInitialized() ? "INIT" : "----");
    Serial.printf("EZGyro:     %s\n", isEZGyroInitialized() ? "INIT" : "----");
    Serial.printf("EZPressure: %s\n", isEZPressureInitialized() ? "INIT" : "----");
    Serial.printf("EZCO2:      %s\n", isEZCO2Initialized() ? "INIT" : "----");
    Serial.printf("EZLCD:      %s\n", isEZLCDInitialized() ? "INIT" : "----");
    Serial.printf("EZLaser:    %s\n", isEZLaserInitialized() ? "INIT" : "----");
    Serial.printf("EZThermal:  %s\n", isEZThermalInitialized() ? "INIT" : "----");
    Serial.printf("EZWeight:   %s\n", isEZWeightInitialized() ? "INIT" : "----");
    Serial.printf("EZDust:     %s\n", isEZDustInitialized() ? "INIT" : "----");
    Serial.println("===================================\n");
}
