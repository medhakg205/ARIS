#ifndef ARIS_CONFIG_H
#define ARIS_CONFIG_H

#include "aris_types.h"

#define ARIS_DEFAULT_EPOCH_MS 100
#define ARIS_RUN_ID_MAX_LEN 32
#if defined(ARIS_LEAN_PROFILE)
  #if defined(ARDUINO) || defined(__AVR__)
    #define ARIS_BUFFER_SIZE 96
  #else
    #define ARIS_BUFFER_SIZE 128
  #endif
#else
  #if defined(ARDUINO) || defined(__AVR__)
    #define ARIS_BUFFER_SIZE 160
  #else
    #define ARIS_BUFFER_SIZE 256
  #endif
#endif

typedef struct {
    ArisInstrumentationMode mode;
    uint32_t epoch_interval_ms;
    uint32_t serial_baud_rate;
    bool enable_compact_framing;
    bool enable_json_stream;
} ArisConfig;

inline ArisConfig aris_default_config() {
    ArisConfig cfg;
    cfg.mode = ARIS_MODE_BALANCED;
    cfg.epoch_interval_ms = ARIS_DEFAULT_EPOCH_MS;
    cfg.serial_baud_rate = 115200UL;
    cfg.enable_compact_framing = true;
    cfg.enable_json_stream = false;
    return cfg;
}

#endif // ARIS_CONFIG_H
