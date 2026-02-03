/**
 * @file BuzzerController.cpp
 * @brief Buzzer controller implementation
 */

#include "BuzzerController.h"

// Simple built-in melodies (durations tuned for ~120 BPM)
static const BuzzerController::Note MELODY_SCALE[] = {
    {262, 150}, {294, 150}, {330, 150}, {349, 150},
    {392, 150}, {440, 150}, {494, 150}, {523, 250},
};

static const BuzzerController::Note MELODY_SUCCESS[] = {
    {523, 120}, {0, 40}, {659, 180},
};

static const BuzzerController::Note MELODY_FAIL[] = {
    {392, 180}, {0, 40}, {262, 300},
};

BuzzerController::BuzzerController()
    : _initialized(false)
    , _isPlaying(false)
    , _volume(50)  // 50% default volume
    , _melodyTaskHandle(nullptr)
{
}

BuzzerController::~BuzzerController() {
    end();
}

bool BuzzerController::begin() {
    Serial.printf("[BUZZER] Initializing buzzer on pin %u...\n", (unsigned)PIN);
    
    // Setup LEDC (PWM) for buzzer
    ledcSetup(LEDC_CHANNEL, LEDC_BASE_FREQ, LEDC_RESOLUTION);
    ledcAttachPin(PIN, LEDC_CHANNEL);
    ledcWrite(LEDC_CHANNEL, 0);  // Start muted
    
    _initialized = true;
    Serial.println("[BUZZER] Buzzer initialized successfully");
    
    return true;
}

void BuzzerController::end() {
    if (_initialized) {
        stopMelody();
        noTone();
        ledcDetachPin(PIN);
        _initialized = false;
    }
}

bool BuzzerController::beep(uint16_t frequency, uint16_t durationMs) {
    if (!_initialized) {
        return false;
    }
    
    tone(frequency, durationMs);
    return true;
}

bool BuzzerController::beepPattern(uint8_t count, uint16_t frequency, uint16_t durationMs, uint16_t intervalMs) {
    if (!_initialized) {
        return false;
    }
    
    for (uint8_t i = 0; i < count; i++) {
        tone(frequency, durationMs);
        if (i < count - 1) {
            delay(intervalMs);
        }
    }
    
    return true;
}

bool BuzzerController::tone(uint16_t frequency, uint16_t durationMs) {
    if (!_initialized) {
        return false;
    }
    
    if (frequency == 0) {
        noTone();
        return true;
    }
    
    // Set frequency
    ledcWriteTone(LEDC_CHANNEL, frequency);
    
    // Set duty cycle based on volume
    uint16_t duty = calculateDuty(_volume);
    ledcWrite(LEDC_CHANNEL, duty);
    
    // If duration specified, auto-stop after delay
    if (durationMs > 0) {
        delay(durationMs);
        noTone();
    }
    
    return true;
}

bool BuzzerController::noTone() {
    if (!_initialized) {
        return false;
    }
    
    ledcWrite(LEDC_CHANNEL, 0);
    return true;
}

bool BuzzerController::playMelody(const char* melodyName, uint16_t tempoBpm) {
    if (!_initialized) return false;
    if (!melodyName) return false;

    stopMelody();

    _tempoBpm = (tempoBpm == 0) ? 120 : tempoBpm;
    _mode = PlaybackMode::Melody;

    // Map name -> built-in melody
    if (strcasecmp(melodyName, "SCALE") == 0 || strcasecmp(melodyName, "HELLO") == 0) {
        _activeMelody = MELODY_SCALE;
        _activeMelodyLen = sizeof(MELODY_SCALE) / sizeof(MELODY_SCALE[0]);
    } else if (strcasecmp(melodyName, "SUCCESS") == 0 || strcasecmp(melodyName, "OK") == 0) {
        _activeMelody = MELODY_SUCCESS;
        _activeMelodyLen = sizeof(MELODY_SUCCESS) / sizeof(MELODY_SUCCESS[0]);
    } else if (strcasecmp(melodyName, "FAIL") == 0 || strcasecmp(melodyName, "ERROR") == 0) {
        _activeMelody = MELODY_FAIL;
        _activeMelodyLen = sizeof(MELODY_FAIL) / sizeof(MELODY_FAIL[0]);
    } else {
        // Default
        _activeMelody = MELODY_SCALE;
        _activeMelodyLen = sizeof(MELODY_SCALE) / sizeof(MELODY_SCALE[0]);
    }

    _isPlaying = true;
    const BaseType_t ok = xTaskCreate(melodyTaskFunc, "buz_mel", 2048, this, 1, &_melodyTaskHandle);
    if (ok != pdPASS) {
        _melodyTaskHandle = nullptr;
        _isPlaying = false;
        return false;
    }
    return true;
}

bool BuzzerController::playPattern(uint8_t count, uint16_t frequency, uint16_t durationMs, uint16_t intervalMs) {
    if (!_initialized) return false;
    if (count == 0) return true;

    stopMelody();

    _mode = PlaybackMode::Pattern;
    _patternCount = count;
    _patternFreq = frequency;
    _patternDurMs = durationMs;
    _patternIntervalMs = intervalMs;

    _isPlaying = true;
    const BaseType_t ok = xTaskCreate(melodyTaskFunc, "buz_pat", 2048, this, 1, &_melodyTaskHandle);
    if (ok != pdPASS) {
        _melodyTaskHandle = nullptr;
        _isPlaying = false;
        return false;
    }
    return true;
}

bool BuzzerController::stopMelody() {
    if (_melodyTaskHandle != nullptr) {
        vTaskDelete(_melodyTaskHandle);
        _melodyTaskHandle = nullptr;
    }
    
    noTone();
    _isPlaying = false;
    
    return true;
}

bool BuzzerController::setVolume(uint8_t volume) {
    _volume = constrain(volume, 0, 100);
    Serial.printf("[BUZZER] Volume set to %d%%\n", _volume);
    return true;
}

uint16_t BuzzerController::calculateDuty(uint8_t volume) {
    // Map volume (0-100) to duty cycle (0-1023)
    // Use exponential curve for better perception
    uint32_t duty = (1 << LEDC_RESOLUTION) - 1;  // Max: 1023
    duty = (duty * volume * volume) / 10000;  // Quadratic scaling
    return constrain(duty, 0, 1023);
}

// ============================================================================
// Melody Task (TODO: Implement)
// ============================================================================

void BuzzerController::melodyTaskFunc(void* param) {
    auto* self = static_cast<BuzzerController*>(param);
    if (!self) {
        vTaskDelete(nullptr);
        return;
    }

    if (self->_mode == PlaybackMode::Pattern) {
        for (uint8_t i = 0; i < self->_patternCount; i++) {
            // play tone
            if (self->_patternFreq > 0) {
                ledcWriteTone(LEDC_CHANNEL, self->_patternFreq);
                ledcWrite(LEDC_CHANNEL, self->calculateDuty(self->_volume));
            }
            vTaskDelay(pdMS_TO_TICKS(self->_patternDurMs));
            (void)self->noTone();

            if (i + 1 < self->_patternCount) {
                vTaskDelay(pdMS_TO_TICKS(self->_patternIntervalMs));
            }
        }
    } else if (self->_mode == PlaybackMode::Melody) {
        const float scale = (self->_tempoBpm > 0) ? (120.0f / (float)self->_tempoBpm) : 1.0f;
        for (size_t i = 0; i < self->_activeMelodyLen; i++) {
            const uint16_t f = self->_activeMelody[i].frequency;
            const uint16_t baseDur = self->_activeMelody[i].durationMs;
            const uint32_t dur = (uint32_t)max(1.0f, (float)baseDur * scale);

            if (f == 0) {
                (void)self->noTone();
            } else {
                ledcWriteTone(LEDC_CHANNEL, f);
                ledcWrite(LEDC_CHANNEL, self->calculateDuty(self->_volume));
            }

            vTaskDelay(pdMS_TO_TICKS(dur));
            (void)self->noTone();
            vTaskDelay(pdMS_TO_TICKS(20)); // tiny gap
        }
    }

    self->_isPlaying = false;
    self->_mode = PlaybackMode::None;
    self->_melodyTaskHandle = nullptr;
    vTaskDelete(nullptr);
}
