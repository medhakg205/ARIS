#ifndef ARIS_BOARD_FACTORY_H
#define ARIS_BOARD_FACTORY_H

#include "board_adapter.h"
#include "board_uno.h"
#include "board_nano.h"
#include "board_mega.h"
#include <string.h>

inline BoardAdapter* aris_create_board_adapter(const char* board_id) {
    if (!board_id) return new UnoBoardAdapter();
    if (strcmp(board_id, "arduino_uno") == 0) return new UnoBoardAdapter();
    if (strcmp(board_id, "arduino_nano") == 0) return new NanoBoardAdapter();
    if (strcmp(board_id, "arduino_mega") == 0) return new MegaBoardAdapter();
    return new UnoBoardAdapter();
}

#endif // ARIS_BOARD_FACTORY_H
