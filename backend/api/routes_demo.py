"""
ARIS Demo Projects REST API Routes.
Returns curated example Arduino sketches for demo/simulation mode.
Each project contains realistic code with deliberate antipatterns
so the ARIS AI engine can identify issues and generate optimizations.

Endpoints:
- GET /api/demo/projects   - list all demo projects
- GET /api/demo/boards     - list demo-supported boards
- POST /api/demo/setup     - create a demo firmware record from chosen project+board
"""

from typing import List, Dict, Any
from fastapi import APIRouter
from backend.api.dependencies import get_db, get_firmware_mgr
from backend.database.models import FirmwareRecord

router = APIRouter(tags=["Demo"])

# ─────────────────────────────────────────────
# Demo Board Profiles (subset, all ATmega-class)
# ─────────────────────────────────────────────
DEMO_BOARDS = [
    {
        "board_id": "arduino_uno",
        "display_name": "Arduino Uno",
        "mcu": "ATmega328P",
        "clock_mhz": 16,
        "sram_kb": 2,
        "flash_kb": 32,
    },
    {
        "board_id": "arduino_nano",
        "display_name": "Arduino Nano",
        "mcu": "ATmega328P",
        "clock_mhz": 16,
        "sram_kb": 2,
        "flash_kb": 32,
    },
    {
        "board_id": "arduino_mega",
        "display_name": "Arduino Mega 2560",
        "mcu": "ATmega2560",
        "clock_mhz": 16,
        "sram_kb": 8,
        "flash_kb": 256,
    },
]

# ─────────────────────────────────────────────
# Demo Project Catalogue
# ─────────────────────────────────────────────
DEMO_PROJECTS: List[Dict[str, Any]] = [
    {
        "project_id": "led_blink",
        "title": "LED Blink (Blocking Delay)",
        "icon": "💡",
        "category": "GPIO & Timing",
        "description": "Classic LED blink using blocking delay(). Causes 100% CPU stall during wait periods — ARIS detects this as a critical antipattern and suggests a millis() state machine.",
        "antipatterns": ["Blocking delay()", "No non-blocking state machine", "CPU stall during idle"],
        "source_code": """\
/**
 * LED Blink — Common beginner implementation.
 * Antipatterns:
 *  1. delay() blocks the entire CPU — no other code runs during the wait.
 *  2. No millis()-based state machine for non-blocking behaviour.
 *  3. LED state is managed with blocking logic instead of toggling.
 */

#include "../../runtime/aris_runtime.h"

const int LED_PIN = 13;

void setup() {
    Serial.begin(115200);
    pinMode(LED_PIN, OUTPUT);
    ARIS.init("arduino_uno", 115200, "ARIS-DEMO-LED", ARIS_MODE_BALANCED);
}

void loop() {
    ARIS.loop_enter();

    // Antipattern 1: Heavy blocking delay — CPU is stalled for 1 full second.
    // No ISR, timer, or other task can execute during this time.
    digitalWrite(LED_PIN, HIGH);
    ARIS.record_gpio(1);
    delay(1000);  // 1000 ms block — CRITICAL ANTIPATTERN

    digitalWrite(LED_PIN, LOW);
    ARIS.record_gpio(1);
    delay(1000);  // Another 1000 ms block — CPU 100% idle

    // Antipattern 2: Verbose serial in hot loop wastes UART bandwidth
    Serial.println("LED toggled — delay complete");

    ARIS.loop_exit();
}
""",
    },
    {
        "project_id": "ultrasonic_sensor",
        "title": "Ultrasonic Distance Sensor (HC-SR04)",
        "icon": "📡",
        "category": "Sensor & Measurement",
        "description": "HC-SR04 distance measurement using pulseIn() — a blocking call that freezes the CPU waiting for the echo pin. ARIS finds blocking calls, raw float division, and spammy serial logging.",
        "antipatterns": ["Blocking pulseIn()", "Repeated float division on 8-bit MCU", "Serial spam in hot loop"],
        "source_code": """\
/**
 * Ultrasonic Distance Measurement (HC-SR04)
 * Antipatterns:
 *  1. pulseIn() is a blocking busy-wait — CPU is stalled waiting for echo.
 *  2. Distance is calculated using software floating-point (expensive on AVR).
 *  3. Serial.print() inside every loop iteration floods the UART buffer.
 */

#include "../../runtime/aris_runtime.h"

const int TRIG_PIN = 9;
const int ECHO_PIN = 10;

void setup() {
    Serial.begin(115200);
    pinMode(TRIG_PIN, OUTPUT);
    pinMode(ECHO_PIN, INPUT);
    ARIS.init("arduino_uno", 115200, "ARIS-DEMO-ULTRASONIC", ARIS_MODE_BALANCED);
}

void loop() {
    ARIS.loop_enter();

    // Trigger pulse
    digitalWrite(TRIG_PIN, LOW);
    delayMicroseconds(2);
    digitalWrite(TRIG_PIN, HIGH);
    delayMicroseconds(10);  // Blocking 10µs stall
    digitalWrite(TRIG_PIN, LOW);
    ARIS.record_gpio(3);

    // Antipattern 1: pulseIn() blocks until echo returns — worst case 30ms stall
    long duration = pulseIn(ECHO_PIN, HIGH);  // BLOCKING — up to 30ms wait

    // Antipattern 2: Float arithmetic on an 8-bit MCU (no FPU) — ~200 cycles each
    float distance_cm = duration * 0.034 / 2.0;
    float distance_in = distance_cm / 2.54;

    ARIS.record_adc(1);

    // Antipattern 3: Serial.print every loop iteration — floods UART buffer
    Serial.print("Distance: ");
    Serial.print(distance_cm);
    Serial.print(" cm / ");
    Serial.print(distance_in);
    Serial.println(" in");

    delay(50);  // Another blocking delay
    ARIS.loop_exit();
}
""",
    },
    {
        "project_id": "temperature_monitor",
        "title": "Temperature Monitor (NTC Thermistor)",
        "icon": "🌡️",
        "category": "Analog & Math",
        "description": "NTC thermistor temperature reading using the Steinhart-Hart equation — packed with expensive float math, log(), and repeated ADC reads. ARIS recommends integer LUT (lookup table) approximation.",
        "antipatterns": ["Repeated log() float math in loop", "Redundant ADC reads", "No averaging or oversampling"],
        "source_code": """\
/**
 * NTC Thermistor Temperature Monitor
 * Antipatterns:
 *  1. Steinhart-Hart equation uses log() — software float, ~500 cycles per call.
 *  2. Multiple analogRead() calls without averaging — noisy readings.
 *  3. No low-pass filter or sample averaging — value jumps around.
 *  4. Repeated Serial.print every loop wastes UART time.
 */

#include "../../runtime/aris_runtime.h"
#include <math.h>

const int THERMISTOR_PIN = A0;
const float SERIES_R = 10000.0;
const float NOMINAL_R = 10000.0;
const float NOMINAL_TEMP = 25.0;
const float B_COEFFICIENT = 3950.0;

void setup() {
    Serial.begin(115200);
    ARIS.init("arduino_uno", 115200, "ARIS-DEMO-TEMP", ARIS_MODE_BALANCED);
}

void loop() {
    ARIS.loop_enter();

    // Antipattern 1: Single ADC read — no averaging, high noise
    int raw = analogRead(THERMISTOR_PIN);
    ARIS.record_adc(1);

    // Antipattern 2: Software floating-point division — expensive on AVR
    float resistance = SERIES_R / (1023.0 / (float)raw - 1.0);

    // Antipattern 3: log() function — extremely expensive software float (~500 cycles)
    float steinhart = log(resistance / NOMINAL_R);
    steinhart /= B_COEFFICIENT;
    steinhart += 1.0 / (NOMINAL_TEMP + 273.15);
    steinhart = 1.0 / steinhart;
    float celsius = steinhart - 273.15;
    float fahrenheit = celsius * 9.0 / 5.0 + 32.0;

    // Antipattern 4: Serial spam every loop iteration
    Serial.print("Temp: ");
    Serial.print(celsius);
    Serial.print(" C / ");
    Serial.print(fahrenheit);
    Serial.println(" F");

    delay(100);  // Blocking delay
    ARIS.loop_exit();
}
""",
    },
    {
        "project_id": "pir_motion_sensor",
        "title": "PIR Motion Detector (Polling)",
        "icon": "👁️",
        "category": "Sensor & Events",
        "description": "PIR motion sensor polled in a tight loop — without hardware interrupts. ARIS identifies the busy-wait polling, blocking LED delay, and recommends an attachInterrupt() ISR approach.",
        "antipatterns": ["Busy-wait polling without interrupt", "Blocking LED delay", "No debounce logic"],
        "source_code": """\
/**
 * PIR Motion Sensor — Polling-Based Detection
 * Antipatterns:
 *  1. digitalRead() in tight loop instead of hardware interrupt (ISR).
 *  2. delay() inside if-block freezes CPU during the ON period.
 *  3. No debounce — rapid false triggers are possible.
 *  4. Serial.println every single detection event — floods UART.
 */

#include "../../runtime/aris_runtime.h"

const int PIR_PIN = 2;
const int LED_PIN = 13;
const int BUZZER_PIN = 8;

bool motionDetected = false;

void setup() {
    Serial.begin(115200);
    pinMode(PIR_PIN, INPUT);
    pinMode(LED_PIN, OUTPUT);
    pinMode(BUZZER_PIN, OUTPUT);
    ARIS.init("arduino_uno", 115200, "ARIS-DEMO-PIR", ARIS_MODE_BALANCED);
}

void loop() {
    ARIS.loop_enter();

    // Antipattern 1: Polling digitalRead() in a tight loop instead of using
    // attachInterrupt() which would allow CPU to sleep between events.
    int state = digitalRead(PIR_PIN);
    ARIS.record_gpio(1);

    if (state == HIGH) {
        if (!motionDetected) {
            motionDetected = true;
            Serial.println("MOTION DETECTED!");  // Antipattern 4

            // Antipattern 2: Blocking delay inside event handler
            digitalWrite(LED_PIN, HIGH);
            digitalWrite(BUZZER_PIN, HIGH);
            ARIS.record_gpio(2);
            delay(5000);  // CPU completely stalled for 5 seconds — CRITICAL
            digitalWrite(LED_PIN, LOW);
            digitalWrite(BUZZER_PIN, LOW);
            ARIS.record_gpio(2);
        }
    } else {
        motionDetected = false;
    }

    ARIS.loop_exit();
}
""",
    },
    {
        "project_id": "servo_motor_control",
        "title": "Servo Motor Sweep (Blocking)",
        "icon": "🦾",
        "category": "Actuator & PWM",
        "description": "Standard servo sweep using a for-loop and delay(). Every step blocks the CPU. ARIS recommends a timer-driven non-blocking approach using millis() and a position state machine.",
        "antipatterns": ["Blocking sweep with delay() inside for-loop", "No state machine", "CPU stall during motion"],
        "source_code": """\
/**
 * Servo Motor Sweep — Common Blocking Implementation
 * Antipatterns:
 *  1. for-loop + delay() inside loop() — blocks CPU during entire sweep.
 *  2. No position state machine — can't do anything else during motion.
 *  3. Direct write on every iteration without change detection.
 *  4. Verbose serial printing during motion — floods UART.
 */

#include "../../runtime/aris_runtime.h"
#include <Servo.h>

Servo myServo;
const int SERVO_PIN = 9;

void setup() {
    Serial.begin(115200);
    myServo.attach(SERVO_PIN);
    ARIS.init("arduino_uno", 115200, "ARIS-DEMO-SERVO", ARIS_MODE_BALANCED);
}

void loop() {
    ARIS.loop_enter();

    // Antipattern 1: Blocking forward sweep — CPU locked for entire duration
    for (int pos = 0; pos <= 180; pos++) {
        myServo.write(pos);
        ARIS.record_gpio(1);
        delay(15);  // 15ms block per degree = 2.7 seconds total stall FORWARD
        Serial.print("Pos: "); Serial.println(pos);  // Antipattern 4
    }

    // Antipattern 1: Blocking reverse sweep — another 2.7 seconds stall
    for (int pos = 180; pos >= 0; pos--) {
        myServo.write(pos);
        ARIS.record_gpio(1);
        delay(15);  // CRITICAL: CPU completely unavailable during sweep
        Serial.print("Pos: "); Serial.println(pos);
    }

    ARIS.loop_exit();
}
""",
    },
    {
        "project_id": "button_debounce",
        "title": "Button Counter (No Debounce)",
        "icon": "🔘",
        "category": "GPIO & Debounce",
        "description": "Button press counter without software debounce — causes multiple counts per physical press. ARIS detects the missing debounce, busy-wait polling, and float counter displayed via serial.",
        "antipatterns": ["No debounce logic", "Busy-wait polling", "Float arithmetic for integer counter"],
        "source_code": """\
/**
 * Button Press Counter — No Debounce
 * Antipatterns:
 *  1. No debounce — mechanical bounce causes multiple counts per press.
 *  2. Polling in tight loop without sleep or interrupt.
 *  3. float used for an integer counter (wasteful on 8-bit AVR).
 *  4. Serial.print on every loop iteration even when nothing changed.
 */

#include "../../runtime/aris_runtime.h"

const int BUTTON_PIN = 4;
const int LED_PIN = 13;

float pressCount = 0.0;  // Antipattern 3: float for integer counter
int lastState = HIGH;

void setup() {
    Serial.begin(115200);
    pinMode(BUTTON_PIN, INPUT_PULLUP);
    pinMode(LED_PIN, OUTPUT);
    ARIS.init("arduino_uno", 115200, "ARIS-DEMO-BUTTON", ARIS_MODE_BALANCED);
}

void loop() {
    ARIS.loop_enter();

    // Antipattern 2: Polling every loop iteration with no sleep
    int currentState = digitalRead(BUTTON_PIN);
    ARIS.record_gpio(1);

    if (currentState == LOW && lastState == HIGH) {
        // Antipattern 1: No debounce — bouncing contact causes multiple triggers
        pressCount += 1.0;  // Antipattern 3: float addition for integer increment
        digitalWrite(LED_PIN, !digitalRead(LED_PIN));
        ARIS.record_gpio(1);
    }

    lastState = currentState;

    // Antipattern 4: Serial print every loop — ~200µs overhead per print
    Serial.print("Button presses: ");
    Serial.println((int)pressCount);  // Cast back to int — float was pointless

    delay(10);  // Short delay doesn't fully debounce — still 50-100 counts per press
    ARIS.loop_exit();
}
""",
    },
]

# Build a lookup dict for quick access
_PROJECT_MAP: Dict[str, Dict[str, Any]] = {p["project_id"]: p for p in DEMO_PROJECTS}


@router.get("/api/demo/projects")
def list_demo_projects() -> List[Dict[str, Any]]:
    """Returns all available demo project templates."""
    return [
        {
            "project_id": p["project_id"],
            "title": p["title"],
            "icon": p["icon"],
            "category": p["category"],
            "description": p["description"],
            "antipatterns": p["antipatterns"],
        }
        for p in DEMO_PROJECTS
    ]


@router.get("/api/demo/boards")
def list_demo_boards() -> List[Dict[str, Any]]:
    """Returns boards supported in demo mode."""
    return DEMO_BOARDS


class DemoSetupRequest:
    pass


from pydantic import BaseModel


class DemoSetupBody(BaseModel):
    board_id: str = "arduino_uno"
    project_id: str = "led_blink"


@router.post("/api/demo/setup")
def setup_demo(req: DemoSetupBody) -> Dict[str, Any]:
    """
    Creates or retrieves the firmware record for a chosen demo project.
    Returns the firmware_id to use when creating the run.
    """
    project = _PROJECT_MAP.get(req.project_id)
    if not project:
        from backend.telemetry.telemetry_schema import ArisException
        raise ArisException(
            error_code="ARIS_VALIDATION_FAILED",
            message=f"Unknown demo project '{req.project_id}'.",
            details={"project_id": req.project_id},
            recoverable=True,
            status_code=400,
        )

    firmware_id = f"ARIS-DEMO-{req.board_id.upper()}-{req.project_id.upper()}"
    db = get_db()
    existing = db.get_firmware(firmware_id)
    if not existing:
        mgr = get_firmware_mgr()
        record = mgr.upload_firmware(
            name=f"{project['title']} — {req.board_id}",
            source_code=project["source_code"],
        )
        # Override firmware_id to our stable key
        import sqlite3
        conn = sqlite3.connect(db.db_path)
        conn.execute(
            "UPDATE firmwares SET firmware_id=? WHERE firmware_id=?",
            (firmware_id, record.firmware_id),
        )
        conn.commit()
        conn.close()

    return {
        "firmware_id": firmware_id,
        "project": {
            "project_id": project["project_id"],
            "title": project["title"],
            "icon": project["icon"],
            "antipatterns": project["antipatterns"],
        },
        "board_id": req.board_id,
        "source_code": project["source_code"],
    }
