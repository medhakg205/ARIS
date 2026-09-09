/**
 * ARIS Example: Memory Stress & Watermark Instrumentation
 * Demonstrates SRAM heap allocation tracking and stack high-water mark detection.
 */

#include "../../runtime/aris_runtime.h"

char* dynamic_buffer = nullptr;
size_t buffer_size = 64;

// Recursive function to push stack depth
int recursive_stack_burner(int depth) {
    volatile char local_frame[16];
    for (int i = 0; i < 16; i++) {
        local_frame[i] = (char)(depth + i);
    }
    if (depth <= 0) {
        return local_frame[0];
    }
    return local_frame[0] + recursive_stack_burner(depth - 1);
}

void setup() {
    // Initialize ARIS in FULL mode to track memory dynamics
    ARIS.init("arduino_uno", 115200, "ARIS-MEM-001", ARIS_MODE_FULL);

    // Initial dynamic allocation
    dynamic_buffer = (char*)malloc(buffer_size);
    if (dynamic_buffer) {
        memset(dynamic_buffer, 0x42, buffer_size);
    }
}

void loop() {
    ARIS.loop_enter();

    // Burn stack to depth 8 to observe watermark expansion
    volatile int res = recursive_stack_burner(8);
    (void)res;

    delay(50);

    ARIS.loop_exit();
}
