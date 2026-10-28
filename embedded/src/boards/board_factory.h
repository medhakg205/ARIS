#ifndef ARIS_BOARD_FACTORY_H
#define ARIS_BOARD_FACTORY_H

#include "board_adapter.h"
#include "board_uno.h"
#include "board_nano.h"
#include "board_mega.h"
#include <string.h>

inline BoardAdapter* aris_create_board_adapter(const char* board_id) {
#if defined(__AVR_ATmega328P__)
    if (board_id && strcmp(board_id, "arduino_nano") == 0) return new NanoBoardAdapter();
    return new UnoBoardAdapter();
#elif defined(__AVR_ATmega2560__)
    return new MegaBoardAdapter();
#else
    if (!board_id) return new UnoBoardAdapter();
    if (strcmp(board_id, "arduino_uno") == 0) return new UnoBoardAdapter();
    if (strcmp(board_id, "arduino_nano") == 0) return new NanoBoardAdapter();
    if (strcmp(board_id, "arduino_mega") == 0) return new MegaBoardAdapter();
    return new UnoBoardAdapter();
#endif
}

#endif // ARIS_BOARD_FACTORY_H
