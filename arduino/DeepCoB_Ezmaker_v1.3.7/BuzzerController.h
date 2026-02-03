/**
 * @file BuzzerController.h
 * @brief Buzzer controller using PWM (LEDC) on fixed pin 42
 * 
 * Supports beeps, tones, and melody playback.
 */

#ifndef BUZZER_CONTROLLER_H
#define BUZZER_CONTROLLER_H

#include <Arduino.h>
#include "pinmap.h"

/**
 * @class BuzzerController
 * @brief Controls buzzer on fixed pin 42 (DeepCo Board)
 * 
 * Features:
 * - PWM-based tone generation (LEDC)
 * - Beep patterns
 * - Melody playback (background task)
 * - Non-blocking operation
 */
class BuzzerController {
public:
    // Melody data (note, duration_ms pairs)
    struct Note {
        uint16_t frequency;
        uint16_t durationMs;
    };

    BuzzerController();
    ~BuzzerController();
    
    // Initialization
    bool begin();
    void end();
    
    // Basic control
    bool beep(uint16_t frequency = 2000, uint16_t durationMs = 100);
    bool beepPattern(uint8_t count, uint16_t frequency = 2000, uint16_t durationMs = 100, uint16_t intervalMs = 100);
    bool tone(uint16_t frequency, uint16_t durationMs = 0);  // 0 = continuous
    bool noTone();
    
    // Melody playback (non-blocking, uses FreeRTOS task)
    bool playMelody(const char* melodyName, uint16_t tempoBpm = 120);
    bool playPattern(uint8_t count, uint16_t frequency, uint16_t durationMs, uint16_t intervalMs);
    bool stopMelody();
    bool isPlaying() const { return _isPlaying; }
    
    // Volume control (0-100%)
    bool setVolume(uint8_t volume);
    uint8_t getVolume() const { return _volume; }
    
private:
    // Hardware
    static constexpr uint8_t PIN = PIN_BUZZER_FIXED;
    static constexpr uint8_t LEDC_CHANNEL = 0;
    static constexpr uint8_t LEDC_RESOLUTION = 10;  // 10-bit (0-1023)
    static constexpr uint32_t LEDC_BASE_FREQ = 2000;
    
    // State
    bool _initialized;
    bool _isPlaying;
    uint8_t _volume;  // 0-100
    
    // Melody task
    TaskHandle_t _melodyTaskHandle;
    static void melodyTaskFunc(void* param);

    enum class PlaybackMode : uint8_t { None = 0, Pattern, Melody };
    PlaybackMode _mode = PlaybackMode::None;

    // Pattern params
    uint8_t _patternCount = 0;
    uint16_t _patternFreq = 0;
    uint16_t _patternDurMs = 0;
    uint16_t _patternIntervalMs = 0;

    // Melody params
    uint16_t _tempoBpm = 120;
    const Note* _activeMelody = nullptr;
    size_t _activeMelodyLen = 0;
    
    // Note definitions (frequency in Hz)
    static constexpr uint16_t NOTE_C4 = 262;
    static constexpr uint16_t NOTE_D4 = 294;
    static constexpr uint16_t NOTE_E4 = 330;
    static constexpr uint16_t NOTE_F4 = 349;
    static constexpr uint16_t NOTE_G4 = 392;
    static constexpr uint16_t NOTE_A4 = 440;
    static constexpr uint16_t NOTE_B4 = 494;
    static constexpr uint16_t NOTE_C5 = 523;
    
    // Helper
    uint16_t calculateDuty(uint8_t volume);
};

#endif // BUZZER_CONTROLLER_H
