/**
 * @file DeepCoB_Ezmaker_v1.3.8.ino
 * @brief Main entry point for DeepCoB_EZMaker Arduino firmware
 * 
 * This is the Arduino/FreeRTOS version of the MicroPython DeepCoB_EZMaker firmware.
 * See arduino/마이크로파이썬to아두이노.md for migration strategy.
 */

#include "BleServer.h"
#include "SensorManager.h"
#include "BleCommandParser.h"
#include "CameraTask.h"
#include "BuzzerController.h"
#include "pinmap.h"

// Global objects
BleServer* bleServer = nullptr;
SensorManager* sensorManager = nullptr;
BleCommandParser* commandParser = nullptr;
CameraTask* cameraTask = nullptr;
BuzzerController* buzzer = nullptr;

void setup() {
  // Initialize serial communication
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("=================================");
  Serial.println("DeepCoB_EZMaker v1.3.8 (Arduino)");
  Serial.println("=================================");
  Serial.println();
  
  // Initialize Sensor Manager
  Serial.println("[MAIN] Initializing Sensor Manager...");
  sensorManager = new SensorManager();
  Serial.println("[MAIN] Sensor Manager initialized (all sensors: nullptr)");
  Serial.println();
  
  // Initialize BLE Server
  Serial.println("[MAIN] Initializing BLE Server...");
  bleServer = new BleServer();
  if (!bleServer->begin()) {
    Serial.println("[MAIN] FATAL: BLE Server initialization failed!");
    while(1) {
      delay(1000);
      Serial.println("[MAIN] Please reset the board.");
    }
  }
  
  // Print device name
  String deviceName = bleServer->getDeviceName();
  Serial.println("[MAIN] BLE Server initialized successfully");
  Serial.print("[MAIN] Device Name: ");
  Serial.println(deviceName);
  Serial.println();
  
  // Buzzer is lazy-loaded (like other sensors).
  // It will be initialized only when a BUZ:INIT command is received.
  buzzer = nullptr;
  
  // Initialize Command Parser
  Serial.println("[MAIN] Initializing Command Parser...");
  commandParser = new BleCommandParser(sensorManager, bleServer);
  bleServer->setCommandParser(commandParser);
  Serial.println("[MAIN] Command Parser initialized");
  Serial.println();
  
  // Initialize Camera Task
  Serial.println("[MAIN] Initializing Camera Task...");
  cameraTask = new CameraTask(bleServer);
  if (!cameraTask->begin()) {
    Serial.println("[MAIN] WARNING: Camera Task initialization failed!");
    Serial.println("[MAIN] Camera features will be unavailable.");
  } else {
    Serial.println("[MAIN] Camera Task initialized successfully");
  }
  Serial.println();
  
  // Connect components to command parser
  if (cameraTask) commandParser->setCameraTask(cameraTask);
  // NOTE: buzzer pointer is created/owned lazily inside the command parser on BUZ:INIT
  
  Serial.println("[MAIN] Setup complete!");
  Serial.println("[MAIN] Waiting for BLE connection...");
  Serial.println("[MAIN] Sensors will be initialized dynamically via BLE commands.");
  Serial.println();
}

void loop() {
  // Main loop - most work is done in FreeRTOS tasks
  // This loop handles housekeeping tasks
  
  static unsigned long lastPrint = 0;
  unsigned long now = millis();
  
  // Print connection status every 5 seconds (only when disconnected)
  if (!bleServer->isConnected() && now - lastPrint > 5000) {
    Serial.println("[MAIN] Waiting for BLE connection...");
    lastPrint = now;
  }
  
  delay(100);
}
