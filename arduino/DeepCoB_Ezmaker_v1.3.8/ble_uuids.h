/**
 * @file ble_uuids.h
 * @brief BLE Service and Characteristic UUIDs for DeepCoB_EZMaker
 * 
 * Reference: sensor_architecture_analysis.md
 * 
 * UUID Organization (Arduino 기준):
 * - IoT Service (1111...8888):         LED (status LED control)
 * - Sensor Service (1111...888C):      All sensors/actuators (DeepCo + EZMaker)
 */

#ifndef BLE_UUIDS_H
#define BLE_UUIDS_H

// ============================================================================
// Service UUIDs
// ============================================================================

// IoT Service (Fixed pin devices: Buzzer, BLE LED)
#define IOT_SERVICE_UUID            "11112222-3333-4444-5555-666677778888"

// Optional Camera Service (Arduino optimized, binary protocol)
// - Camera control/streaming uses a dedicated service for high-throughput use-cases
#define CAMERA_SERVICE_UUID         "CAFE0000-1111-2222-3333-444455556666"

// Sensor Service (DeepCo + EZMaker sensors, dynamic pins)
#define SENSOR_SERVICE_UUID         "11112222-3333-4444-5555-66667777888C"

// ============================================================================
// IoT Service Characteristics
// ============================================================================

#define LED_CHAR_UUID               "11112222-3333-4444-5555-666677778889"  // Write
// Camera (Legacy / MicroPython compatible)
// - Single characteristic used for both Write (commands) and Notify (stream)
// - Matches IoTmode/test integratedBleLib_Camera.js: CAM_CHARACTERISTIC
#define CAM_CHAR_UUID               "11112222-3333-4444-5555-66667777888A"  // Write+Notify

// ============================================================================
// Optional Camera Service Characteristics (Binary Protocol)
// ============================================================================

#define CAM_TX_CHAR_UUID            "CAFE0001-1111-2222-3333-444455556666"  // Notify (binary frames)
#define CAM_RX_CHAR_UUID            "CAFE0002-1111-2222-3333-444455556666"  // Write (control commands)
#define CAM_STATUS_CHAR_UUID        "CAFE0003-1111-2222-3333-444455556666"  // Read+Notify (status info)

// ============================================================================
// Sensor Service Characteristics (DeepCo + EZMaker, Dynamic Pins)
// ============================================================================

#define ULTRA_CHAR_UUID             "11112222-3333-4444-5555-66667777888B"  // Write+Notify
#define DHT_CHAR_UUID               "11112222-3333-4444-5555-66667777888D"  // Write+Notify
#define SERVO_CHAR_UUID             "11112222-3333-4444-5555-66667777888E"  // Write
#define NEO_CHAR_UUID               "11112222-3333-4444-5555-66667777888F"  // Write
#define TOUCH_CHAR_UUID             "11112222-3333-4444-5555-666677778890"  // Write+Notify
#define LIGHT_CHAR_UUID             "11112222-3333-4444-5555-666677778891"  // Write+Notify
#define BUZZER_CHAR_UUID            "11112222-3333-4444-5555-666677778892"  // Write+Notify
#define GYRO_CHAR_UUID              "11112222-3333-4444-5555-666677778894"  // Write+Notify (ADXL345)
#define DUST_CHAR_UUID              "11112222-3333-4444-5555-666677778895"  // Write+Notify
#define DCMOTOR_CHAR_UUID           "11112222-3333-4444-5555-666677778896"  // Write
#define HEART_CHAR_UUID             "11112222-3333-4444-5555-666677778897"  // Write+Notify

// EZMaker characteristics (all live under SENSOR_SERVICE in Web BLE)
#define EZ_LASER_CHAR_UUID          "22223333-4444-5555-6666-777788889001"  // Write+Notify
#define EZ_GYRO_CHAR_UUID           "22223333-4444-5555-6666-777788889002"  // Write+Notify (ICM20948)
#define EZ_PRESS_CHAR_UUID          "22223333-4444-5555-6666-777788889003"  // Write+Notify (BMP280)
#define EZ_CO2_CHAR_UUID            "22223333-4444-5555-6666-777788889004"  // Write+Notify (SCD40)
#define EZ_DIYA_CHAR_UUID           "22223333-4444-5555-6666-777788889005"  // Write+Notify
#define EZ_DIYB_CHAR_UUID           "22223333-4444-5555-6666-777788889006"  // Write+Notify
#define EZ_HALL_CHAR_UUID           "22223333-4444-5555-6666-777788889007"  // Write+Notify
#define EZ_LCD_CHAR_UUID            "22223333-4444-5555-6666-777788889008"  // Write+Notify (I2C LCD)
#define EZ_LIGHT_CHAR_UUID          "22223333-4444-5555-6666-777788889009"  // Write+Notify
#define EZ_VOLT_CHAR_UUID           "22223333-4444-5555-6666-77778888900A"  // Write+Notify
#define EZ_CURR_CHAR_UUID           "22223333-4444-5555-6666-77778888900B"  // Write+Notify (INA219)
#define EZ_HUMAN_CHAR_UUID          "22223333-4444-5555-6666-77778888900C"  // Write+Notify (PIR)
#define EZ_THERMAL_CHAR_UUID        "22223333-4444-5555-6666-77778888900D"  // Write+Notify (DS18B20)
#define EZ_SOUND_CHAR_UUID          "22223333-4444-5555-6666-77778888900E"  // Write+Notify
#define EZ_WEIGHT_CHAR_UUID         "22223333-4444-5555-6666-77778888900F"  // Write+Notify (HX711)
#define EZ_DUST_CHAR_UUID           "22223333-4444-5555-6666-777788889010"  // Write+Notify (PMS7003M)

// ============================================================================
// Removed UUIDs / Notes
// ============================================================================
// - This Arduino firmware targets the Web BLE UUID set used by IoTmode/test.

// ============================================================================
// BLE Configuration
// ============================================================================

// Device name format: "DCB" + last 6 hex digits of MAC address
// Example: "DCB1A2B3C" (if MAC is AA:BB:CC:DD:1A:2B:3C)
// Fallback name if MAC read fails:
#define BLE_DEVICE_NAME_PREFIX      "DCB"
#define BLE_DEVICE_NAME_FALLBACK    "DeepCoBoard"

#define BLE_MTU_SIZE                512    // Target MTU (ESP32-S3 supports up to 512)
#define BLE_MTU_MIN                 23     // Minimum MTU (BLE standard)

// ============================================================================
// Characteristic Properties (for NimBLE)
// ============================================================================

// Property flags for NimBLE characteristic creation
#define CHAR_PROP_READ              (1 << 1)
#define CHAR_PROP_WRITE             (1 << 3)
#define CHAR_PROP_NOTIFY            (1 << 4)
#define CHAR_PROP_INDICATE          (1 << 5)

// Common combinations
#define CHAR_PROP_WRITE_ONLY        (CHAR_PROP_WRITE)
#define CHAR_PROP_READ_NOTIFY       (CHAR_PROP_READ | CHAR_PROP_NOTIFY)
#define CHAR_PROP_WRITE_NOTIFY      (CHAR_PROP_WRITE | CHAR_PROP_NOTIFY)

#endif // BLE_UUIDS_H
