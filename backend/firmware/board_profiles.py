"""
ARIS Board Profiles & Universal Architecture Specifications.
Provides canonical cached hardware profiles and dynamic toolchain/handshake resolution:
- Universal BoardProfile representation supporting AVR, ARM, ESP, SAMD, RISC-V, etc.
- BoardProfileResolver: dynamically constructs profiles from arduino-cli toolchain metadata,
  runtime handshake frames, or marks partially resolved devices with explicit unavailable_properties.
- Detects and flags BOARD_IDENTITY_MISMATCH when discovery and handshake disagree.
- Maintains zero generic guessing: if an MCU or memory limit is unknown, it remains None
  with unavailable_properties recorded, NEVER default-filling ATmega328P.
"""

import os
import sys
import json
import logging
import subprocess
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from backend.database.models import BoardRecord

logger = logging.getLogger("aris.firmware.board_profiles")


@dataclass
class BoardProfile:
    """
    Board Profile representation for ARIS.
    Supports canonical known targets as well as dynamically derived / partially resolved boards.
    """
    board_id: str                                  # Unique board identifier (canonical or derived)
    display_name: str                              # Human-readable display name
    mcu: Optional[str] = None                      # Microcontroller chip part name (e.g. "atmega328p", "ra4m1")
    architecture: Optional[str] = None             # Core architecture ("avr8", "arm_cortex_m4", "esp32", etc.)
    clock_hz: Optional[int] = None                 # System clock frequency in Hz
    flash_bytes: Optional[int] = None              # Total non-volatile Flash memory
    sram_bytes: Optional[int] = None               # Total static RAM
    eeprom_bytes: Optional[int] = None             # Total EEPROM or data flash
    gpio_count: Optional[int] = None               # Accessible digital GPIO lines
    adc_channels: Optional[int] = None             # Analog ADC channels
    uart_count: Optional[int] = None               # Hardware UART count
    spi_available: Optional[bool] = None           # SPI bus support
    i2c_available: Optional[bool] = None           # I2C (Two-Wire Interface) support
    timer_count: Optional[int] = None              # Hardware timers count
    interrupt_capabilities: List[str] = field(default_factory=list) # Hardware interrupt vector list
    fqbn: Optional[str] = ""                       # Fully Qualified Board Name (e.g. "arduino:avr:uno")
    build_toolchain: str = "avr-gcc"               # Toolchain identifier
    supported: bool = True                         # Supported for automated ARIS build & analysis
    # Resolution metadata
    profile_source: str = "EXACT_PROFILE"          # EXACT_PROFILE, TOOLCHAIN_DERIVED, RUNTIME_VERIFIED, PARTIALLY_RESOLVED, UNKNOWN
    confidence: str = "HIGH"                       # CONFIRMED, HIGH, MEDIUM, LOW, UNKNOWN, MISMATCH
    unavailable_properties: List[str] = field(default_factory=list)
    platform: Optional[str] = None
    capabilities: Dict[str, Any] = field(default_factory=dict)

    @property
    def arch(self) -> Optional[str]:
        return self.architecture

    def is_avr(self) -> bool:
        """Returns True if the board architecture is AVR8."""
        return bool(self.architecture and "avr" in self.architecture.lower())

    def is_arm(self) -> bool:
        """Returns True if the board architecture is ARM Cortex."""
        return bool(self.architecture and "arm" in self.architecture.lower())

    def is_esp(self) -> bool:
        """Returns True if the board is ESP8266 or ESP32."""
        return bool(self.architecture and "esp" in self.architecture.lower())

    def to_record(self) -> BoardRecord:
        """Converts profile to persistent database BoardRecord."""
        return BoardRecord(
            board_id=self.board_id,
            display_name=self.display_name,
            mcu=self.mcu,
            architecture=self.architecture,
            clock_hz=self.clock_hz,
            flash_bytes=self.flash_bytes,
            sram_bytes=self.sram_bytes,
            eeprom_bytes=self.eeprom_bytes,
            gpio_count=self.gpio_count,
            adc_channels=self.adc_channels,
            uart_count=self.uart_count,
            spi_available=self.spi_available,
            i2c_available=self.i2c_available,
            timer_count=self.timer_count,
            interrupt_capabilities=list(self.interrupt_capabilities),
            fqbn=self.fqbn or "",
            build_toolchain=self.build_toolchain,
            supported=self.supported,
            profile_source=self.profile_source,
            confidence=self.confidence,
            unavailable_properties=list(self.unavailable_properties),
            platform=self.platform,
            capabilities=dict(self.capabilities)
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serializes to dictionary representation."""
        return asdict(self)


# Canonical registry of known Arduino boards (serves as authoritative cache, NOT a closed whitelist)
CANONICAL_BOARD_PROFILES: Dict[str, BoardProfile] = {
    # -------------------------------------------------------------------------
    # 1. Arduino Uno R3 (ATmega328P, AVR8)
    # -------------------------------------------------------------------------
    "arduino_uno": BoardProfile(
        board_id="arduino_uno",
        display_name="Arduino Uno",
        mcu="atmega328p",
        architecture="avr8",
        clock_hz=16_000_000,
        flash_bytes=32_768,      # 32 KB Flash
        sram_bytes=2_048,        # 2 KB SRAM
        eeprom_bytes=1_024,      # 1 KB EEPROM
        gpio_count=14,           # D0 - D13
        adc_channels=6,          # A0 - A5
        uart_count=1,            # 1 hardware UART (Serial on pins 0, 1)
        spi_available=True,      # MOSI 11, MISO 12, SCK 13
        i2c_available=True,      # SDA A4, SCL A5
        timer_count=3,           # Timer0 (8-bit), Timer1 (16-bit), Timer2 (8-bit)
        interrupt_capabilities=[
            "INT0", "INT1",
            "PCINT0", "PCINT1", "PCINT2",
            "TIMER0_OVF", "TIMER1_OVF", "TIMER2_OVF"
        ],
        fqbn="arduino:avr:uno",
        build_toolchain="avr-gcc",
        supported=True,
        profile_source="EXACT_PROFILE",
        confidence="CONFIRMED",
        platform="arduino:avr"
    ),

    # -------------------------------------------------------------------------
    # 2. Arduino Nano (ATmega328P, AVR8)
    # -------------------------------------------------------------------------
    "arduino_nano": BoardProfile(
        board_id="arduino_nano",
        display_name="Arduino Nano",
        mcu="atmega328p",
        architecture="avr8",
        clock_hz=16_000_000,
        flash_bytes=32_768,      # 32 KB Flash
        sram_bytes=2_048,        # 2 KB SRAM
        eeprom_bytes=1_024,      # 1 KB EEPROM
        gpio_count=14,           # D0 - D13
        adc_channels=8,          # A0 - A7
        uart_count=1,            # 1 hardware UART
        spi_available=True,
        i2c_available=True,
        timer_count=3,
        interrupt_capabilities=[
            "INT0", "INT1",
            "PCINT0", "PCINT1", "PCINT2",
            "TIMER0_OVF", "TIMER1_OVF", "TIMER2_OVF"
        ],
        fqbn="arduino:avr:nano",
        build_toolchain="avr-gcc",
        supported=True,
        profile_source="EXACT_PROFILE",
        confidence="CONFIRMED",
        platform="arduino:avr"
    ),

    # -------------------------------------------------------------------------
    # 3. Arduino Mega 2560 R3 (ATmega2560, AVR8)
    # -------------------------------------------------------------------------
    "arduino_mega": BoardProfile(
        board_id="arduino_mega",
        display_name="Arduino Mega 2560",
        mcu="atmega2560",
        architecture="avr8",
        clock_hz=16_000_000,
        flash_bytes=262_144,     # 256 KB Flash
        sram_bytes=8_192,        # 8 KB SRAM
        eeprom_bytes=4_096,      # 4 KB EEPROM
        gpio_count=54,           # D0 - D53
        adc_channels=16,         # A0 - A15
        uart_count=4,            # 4 hardware UARTs
        spi_available=True,
        i2c_available=True,
        timer_count=6,
        interrupt_capabilities=[
            "INT0", "INT1", "INT2", "INT3", "INT4", "INT5",
            "PCINT0", "PCINT1", "PCINT2",
            "TIMER0_OVF", "TIMER1_OVF", "TIMER2_OVF",
            "TIMER3_OVF", "TIMER4_OVF", "TIMER5_OVF"
        ],
        fqbn="arduino:avr:mega",
        build_toolchain="avr-gcc",
        supported=True,
        profile_source="EXACT_PROFILE",
        confidence="CONFIRMED",
        platform="arduino:avr"
    )
}

# Extended known modern architectures cataloged in cache
EXTENDED_BOARD_PROFILES: Dict[str, BoardProfile] = {
    # -------------------------------------------------------------------------
    # 4. Arduino Leonardo (ATmega32U4, AVR8 with Native USB)
    # -------------------------------------------------------------------------
    "arduino_leonardo": BoardProfile(
        board_id="arduino_leonardo",
        display_name="Arduino Leonardo",
        mcu="atmega32u4",
        architecture="avr8",
        clock_hz=16_000_000,
        flash_bytes=32_768,
        sram_bytes=2_560,        # 2.5 KB SRAM
        eeprom_bytes=1_024,
        gpio_count=20,
        adc_channels=12,
        uart_count=1,
        spi_available=True,
        i2c_available=True,
        timer_count=4,
        interrupt_capabilities=["INT0", "INT1", "INT2", "INT3", "INT6"],
        fqbn="arduino:avr:leonardo",
        build_toolchain="avr-gcc",
        supported=True,
        profile_source="EXACT_PROFILE",
        confidence="CONFIRMED",
        platform="arduino:avr"
    ),

    # -------------------------------------------------------------------------
    # 5. Arduino Uno R4 WiFi (Renesas RA4M1, ARM Cortex-M4)
    # -------------------------------------------------------------------------
    "arduino_uno_r4_wifi": BoardProfile(
        board_id="arduino_uno_r4_wifi",
        display_name="Arduino Uno R4 WiFi",
        mcu="ra4m1",
        architecture="arm_cortex_m4",
        clock_hz=48_000_000,
        flash_bytes=262_144,     # 256 KB Flash
        sram_bytes=32_768,       # 32 KB SRAM
        eeprom_bytes=8_192,      # 8 KB Data Flash
        gpio_count=14,
        adc_channels=6,
        uart_count=2,
        spi_available=True,
        i2c_available=True,
        timer_count=8,
        interrupt_capabilities=["NVIC_ARM_CORTEX_M4"],
        fqbn="arduino:renesas_uno:unor4wifi",
        build_toolchain="arm-none-eabi-gcc",
        supported=True,
        profile_source="EXACT_PROFILE",
        confidence="CONFIRMED",
        platform="arduino:renesas_uno"
    ),

    # -------------------------------------------------------------------------
    # 6. Arduino Uno R4 Minima (Renesas RA4M1, ARM Cortex-M4)
    # -------------------------------------------------------------------------
    "arduino_uno_r4_minima": BoardProfile(
        board_id="arduino_uno_r4_minima",
        display_name="Arduino Uno R4 Minima",
        mcu="ra4m1",
        architecture="arm_cortex_m4",
        clock_hz=48_000_000,
        flash_bytes=262_144,
        sram_bytes=32_768,
        eeprom_bytes=8_192,
        gpio_count=14,
        adc_channels=6,
        uart_count=2,
        spi_available=True,
        i2c_available=True,
        timer_count=8,
        interrupt_capabilities=["NVIC_ARM_CORTEX_M4"],
        fqbn="arduino:renesas_uno:minima",
        build_toolchain="arm-none-eabi-gcc",
        supported=True,
        profile_source="EXACT_PROFILE",
        confidence="CONFIRMED",
        platform="arduino:renesas_uno"
    ),

    # -------------------------------------------------------------------------
    # 7. Arduino Due (SAM3X8E, ARM Cortex-M3)
    # -------------------------------------------------------------------------
    "arduino_due": BoardProfile(
        board_id="arduino_due",
        display_name="Arduino Due",
        mcu="sam3x8e",
        architecture="arm_cortex_m3",
        clock_hz=84_000_000,
        flash_bytes=524_288,     # 512 KB Flash
        sram_bytes=98_304,       # 96 KB SRAM
        eeprom_bytes=0,
        gpio_count=54,
        adc_channels=12,
        uart_count=4,
        spi_available=True,
        i2c_available=True,
        timer_count=9,
        interrupt_capabilities=["NVIC_ARM_CORTEX_M3"],
        fqbn="arduino:sam:arduino_due_x",
        build_toolchain="arm-none-eabi-gcc",
        supported=True,
        profile_source="EXACT_PROFILE",
        confidence="CONFIRMED",
        platform="arduino:sam"
    ),

    # -------------------------------------------------------------------------
    # 8. Raspberry Pi Pico (RP2040, Dual ARM Cortex-M0+)
    # -------------------------------------------------------------------------
    "rp2040_pico": BoardProfile(
        board_id="rp2040_pico",
        display_name="Raspberry Pi Pico",
        mcu="rp2040",
        architecture="arm_cortex_m0plus",
        clock_hz=133_000_000,
        flash_bytes=2_097_152,   # 2 MB Flash
        sram_bytes=266_240,      # 264 KB SRAM
        eeprom_bytes=0,
        gpio_count=30,
        adc_channels=4,
        uart_count=2,
        spi_available=True,
        i2c_available=True,
        timer_count=4,
        interrupt_capabilities=["NVIC_ARM_CORTEX_M0PLUS"],
        fqbn="rp2040:rp2040:rpipico",
        build_toolchain="arm-none-eabi-gcc",
        supported=True,
        profile_source="EXACT_PROFILE",
        confidence="CONFIRMED",
        platform="rp2040:rp2040"
    )
}

ALL_BOARD_PROFILES: Dict[str, BoardProfile] = {**CANONICAL_BOARD_PROFILES, **EXTENDED_BOARD_PROFILES}


class BoardProfileResolver:
    """
    Universal Hardware Profile Resolver.
    Resolves board configurations from:
    1. Authoritative exact cache (Uno, Mega, Nano, Leonardo, Uno R4, Due, etc.)
    2. Arduino CLI toolchain metadata ('arduino-cli board details --fqbn <fqbn> --format json')
    3. Runtime Handshake frame ($ARIS_ACK / $ARIS_BOOT)
    4. Partially resolved / uncertain devices with explicit unavailable_properties.
    Never fabricates or assumes hardware characteristics.
    """

    @classmethod
    def resolve_from_toolchain(cls, fqbn: str, cli_path: Optional[str] = None) -> Optional[BoardProfile]:
        """
        Executes 'arduino-cli board details --fqbn <fqbn> --format json'
        and parses platform and target properties dynamically into a BoardProfile.
        """
        if not fqbn:
            return None

        # Check exact known profile cache first
        for prof in ALL_BOARD_PROFILES.values():
            if prof.fqbn and prof.fqbn.strip().lower() == fqbn.strip().lower():
                return prof

        # If cli_path not provided, locate it
        if not cli_path:
            from backend.serial.serial_discovery import find_arduino_cli_path
            cli_path = find_arduino_cli_path()

        if not cli_path:
            logger.debug(f"Toolchain unavailable to resolve FQBN: {fqbn}")
            return None

        try:
            res = subprocess.run(
                [cli_path, "board", "details", "--fqbn", fqbn, "--format", "json"],
                capture_output=True,
                text=True,
                timeout=5.0
            )
            if res.returncode != 0 or not res.stdout.strip():
                logger.debug(f"board details failed for FQBN {fqbn}: {res.stderr}")
                return None

            data = json.loads(res.stdout)
            return cls.parse_toolchain_json(data, fqbn)
        except Exception as e:
            logger.warning(f"Error resolving board details for {fqbn}: {e}")
            return None

    @classmethod
    def parse_toolchain_json(cls, data: Dict[str, Any], fqbn: str) -> BoardProfile:
        """
        Parses JSON output from 'arduino-cli board details --format json'
        into a dynamic BoardProfile.
        """
        display_name = data.get("name") or fqbn
        board_id = fqbn.replace(":", "_").replace("-", "_").lower()

        # Extract properties list (e.g. "build.mcu=atmega328p")
        raw_props = data.get("properties", [])
        props_map: Dict[str, str] = {}
        if isinstance(raw_props, list):
            for item in raw_props:
                if isinstance(item, str) and "=" in item:
                    k, v = item.split("=", 1)
                    props_map[k.strip()] = v.strip()
                elif isinstance(item, dict):
                    k = item.get("key", "")
                    v = item.get("value", "")
                    if k:
                        props_map[k] = v
        elif isinstance(raw_props, dict):
            props_map = {str(k): str(v) for k, v in raw_props.items()}

        # MCU identification
        mcu = props_map.get("build.mcu")
        if not mcu and "build.board" in props_map:
            mcu = props_map.get("build.board")

        # Architecture determination
        arch_raw = (
            props_map.get("build.arch")
            or props_map.get("build.architecture")
            or ""
        ).lower()
        if not arch_raw:
            # Infer from FQBN package/arch (e.g. arduino:avr:uno -> avr8)
            fqbn_parts = fqbn.split(":")
            if len(fqbn_parts) >= 2:
                arch_raw = fqbn_parts[1].lower()

        architecture = "unknown"
        if "avr" in arch_raw:
            architecture = "avr8"
        elif "cortex-m4" in arch_raw or "cortex_m4" in arch_raw:
            architecture = "arm_cortex_m4"
        elif "cortex-m0" in arch_raw:
            architecture = "arm_cortex_m0plus"
        elif "cortex-m3" in arch_raw:
            architecture = "arm_cortex_m3"
        elif "cortex" in arch_raw or "arm" in arch_raw or "sam" in arch_raw:
            architecture = "arm"
        elif "esp32" in arch_raw or "esp32" in fqbn.lower():
            architecture = "esp32"
        elif "esp8266" in arch_raw or "esp8266" in fqbn.lower():
            architecture = "esp8266"
        elif arch_raw:
            architecture = arch_raw

        # Clock frequency
        clock_hz = None
        f_cpu_str = props_map.get("build.f_cpu", "")
        if f_cpu_str:
            clean_fcpu = "".join([c for c in f_cpu_str if c.isdigit()])
            if clean_fcpu:
                clock_hz = int(clean_fcpu)

        # Memory limits from upload parameters
        flash_bytes = None
        if "upload.maximum_size" in props_map:
            val_str = "".join([c for c in props_map["upload.maximum_size"] if c.isdigit()])
            if val_str:
                flash_bytes = int(val_str)

        sram_bytes = None
        if "upload.maximum_data_size" in props_map:
            val_str = "".join([c for c in props_map["upload.maximum_data_size"] if c.isdigit()])
            if val_str:
                sram_bytes = int(val_str)

        # Toolchain determination
        toolchain = "unknown"
        if architecture == "avr8":
            toolchain = "avr-gcc"
        elif "arm" in architecture:
            toolchain = "arm-none-eabi-gcc"
        elif "esp" in architecture:
            toolchain = "xtensa-esp32-elf-gcc"

        # Platform package
        fqbn_parts = fqbn.split(":")
        platform = f"{fqbn_parts[0]}:{fqbn_parts[1]}" if len(fqbn_parts) >= 2 else None

        unavailable: List[str] = []
        if not mcu:
            unavailable.append("mcu")
        if not architecture or architecture == "unknown":
            unavailable.append("architecture")
        if not clock_hz:
            unavailable.append("clock_hz")
        if not flash_bytes:
            unavailable.append("flash_bytes")
        if not sram_bytes:
            unavailable.append("sram_bytes")
        unavailable.extend(["eeprom_bytes", "gpio_count", "adc_channels", "timer_count"])

        return BoardProfile(
            board_id=board_id,
            display_name=display_name,
            mcu=mcu,
            architecture=architecture if architecture != "unknown" else None,
            clock_hz=clock_hz,
            flash_bytes=flash_bytes,
            sram_bytes=sram_bytes,
            eeprom_bytes=None,
            gpio_count=None,
            adc_channels=None,
            uart_count=None,
            spi_available=None,
            i2c_available=None,
            timer_count=None,
            interrupt_capabilities=[],
            fqbn=fqbn,
            build_toolchain=toolchain,
            supported=True,
            profile_source="TOOLCHAIN_DERIVED",
            confidence="HIGH",
            unavailable_properties=unavailable,
            platform=platform,
            capabilities={"derived_from_toolchain": True, "properties_count": len(props_map)}
        )

    @classmethod
    def resolve_from_handshake(cls, handshake_data: Dict[str, Any]) -> BoardProfile:
        """
        Builds or refines a BoardProfile based on an authoritative hardware handshake frame.
        Handshake format contains:
        board_id, mcu, architecture, clock_hz, runtime_version, protocol_version.
        """
        board_id = handshake_data.get("board_id") or "runtime_target"
        mcu = handshake_data.get("mcu")
        arch = handshake_data.get("architecture")
        clock_hz = handshake_data.get("clock_hz")

        # Check if known canonical profile exists
        if board_id in ALL_BOARD_PROFILES:
            base = ALL_BOARD_PROFILES[board_id]
            # Clone with confirmed confidence
            prof = BoardProfile(**asdict(base))
            prof.profile_source = "RUNTIME_VERIFIED"
            prof.confidence = "CONFIRMED"
            return prof

        display_name = f"Hardware Target ({mcu or board_id})"
        unavailable: List[str] = []
        if not mcu:
            unavailable.append("mcu")
        if not arch:
            unavailable.append("architecture")
        if not clock_hz:
            unavailable.append("clock_hz")
        unavailable.extend(["flash_bytes", "sram_bytes", "eeprom_bytes", "gpio_count", "timer_count"])

        return BoardProfile(
            board_id=board_id,
            display_name=display_name,
            mcu=mcu,
            architecture=arch,
            clock_hz=clock_hz,
            flash_bytes=None,
            sram_bytes=None,
            eeprom_bytes=None,
            gpio_count=None,
            adc_channels=None,
            uart_count=1,
            spi_available=None,
            i2c_available=None,
            timer_count=None,
            interrupt_capabilities=[],
            fqbn="",
            build_toolchain="avr-gcc" if arch == "avr8" else "toolchain-gcc",
            supported=True,
            profile_source="RUNTIME_VERIFIED",
            confidence="CONFIRMED",
            unavailable_properties=unavailable,
            platform=None,
            capabilities={
                "runtime_version": handshake_data.get("runtime_version"),
                "protocol_version": handshake_data.get("protocol_version"),
                "instrumentation_mode": handshake_data.get("instrumentation_mode")
            }
        )

    @classmethod
    def create_partially_resolved(
        cls,
        board_id: str,
        display_name: str,
        description: str = "",
        fqbn: Optional[str] = None
    ) -> BoardProfile:
        """
        Constructs a partially resolved profile for unrecognized devices (e.g. bare CH340).
        Guarantees that missing metrics are NOT assumed or defaulted to Uno R3.
        """
        unavailable = [
            "mcu",
            "architecture",
            "clock_hz",
            "flash_bytes",
            "sram_bytes",
            "eeprom_bytes",
            "gpio_count",
            "adc_channels",
            "timer_count",
            "fqbn"
        ]
        return BoardProfile(
            board_id=board_id,
            display_name=display_name,
            mcu=None,
            architecture=None,
            clock_hz=None,
            flash_bytes=None,
            sram_bytes=None,
            eeprom_bytes=None,
            gpio_count=None,
            adc_channels=None,
            uart_count=None,
            spi_available=None,
            i2c_available=None,
            timer_count=None,
            interrupt_capabilities=[],
            fqbn=fqbn or "",
            build_toolchain="unknown",
            supported=False,
            profile_source="PARTIALLY_RESOLVED",
            confidence="UNCERTAIN",
            unavailable_properties=unavailable,
            platform=None,
            capabilities={"description": description, "resolution_pending": True}
        )

    @classmethod
    def verify_identity_match(
        cls,
        discovered: Optional[BoardProfile],
        handshake: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Compares toolchain/discovery profile with actual runtime handshake frame.
        Detects conflicts (e.g. Discovery inferred Uno R3, but Handshake reports ATmega2560 or RA4M1).
        Returns (is_match, mismatch_reason).
        """
        if not discovered or not handshake or not handshake.get("handshake_success"):
            return (True, None)

        hs_mcu = (handshake.get("mcu") or "").strip().lower()
        hs_arch = (handshake.get("architecture") or "").strip().lower()
        disc_mcu = (discovered.mcu or "").strip().lower()
        disc_arch = (discovered.architecture or "").strip().lower()

        # If both define MCU, check compatibility
        if hs_mcu and disc_mcu and hs_mcu != disc_mcu:
            reason = (
                f"BOARD_IDENTITY_MISMATCH: Discovery detected {disc_mcu} ({discovered.display_name}) "
                f"but runtime handshake confirmed {hs_mcu}."
            )
            return (False, reason)

        # If both define Architecture, check compatibility
        if hs_arch and disc_arch and hs_arch != disc_arch:
            reason = (
                f"BOARD_IDENTITY_MISMATCH: Discovery inferred architecture '{disc_arch}' "
                f"but runtime handshake confirmed '{hs_arch}'."
            )
            return (False, reason)

        return (True, None)


def get_board_profile(board_id: str, allow_unresolved: bool = False) -> BoardProfile:
    """
    Retrieves the board profile by ID.
    Checks:
    1. In-memory known profiles cache (canonical and extended)
    2. Database engine (if initialized)
    3. If board_id looks like an FQBN, resolves dynamically via toolchain.
    4. If allow_unresolved is True, returns partially resolved profile.
       Otherwise raises KeyError with supported canonical boards list.
    """
    if board_id in ALL_BOARD_PROFILES:
        return ALL_BOARD_PROFILES[board_id]

    # Attempt dynamic toolchain resolution if it looks like an FQBN
    if ":" in board_id:
        profile = BoardProfileResolver.resolve_from_toolchain(board_id)
        if profile:
            return profile

    # Attempt lookup in DB
    try:
        from backend.database.db_engine import DatabaseEngine
        db = DatabaseEngine()
        record = db.get_board(board_id)
        if record:
            return BoardProfile(
                board_id=record.board_id,
                display_name=record.display_name,
                mcu=record.mcu,
                architecture=record.architecture,
                clock_hz=record.clock_hz,
                flash_bytes=record.flash_bytes,
                sram_bytes=record.sram_bytes,
                eeprom_bytes=record.eeprom_bytes,
                gpio_count=record.gpio_count,
                adc_channels=record.adc_channels,
                uart_count=record.uart_count,
                spi_available=record.spi_available,
                i2c_available=record.i2c_available,
                timer_count=record.timer_count,
                interrupt_capabilities=record.interrupt_capabilities,
                fqbn=record.fqbn,
                build_toolchain=record.build_toolchain,
                supported=record.supported,
                profile_source=record.profile_source,
                confidence=record.confidence,
                unavailable_properties=record.unavailable_properties,
                platform=record.platform,
                capabilities=record.capabilities
            )
    except Exception as e:
        logger.debug(f"DB lookup for board {board_id} skipped: {e}")

    if allow_unresolved:
        return BoardProfileResolver.create_partially_resolved(
            board_id=board_id,
            display_name=f"Unknown Target ({board_id})"
        )

    raise KeyError(
        f"Unsupported ARIS board_id '{board_id}'. "
        f"Supported boards: {list(CANONICAL_BOARD_PROFILES.keys())}"
    )


def get_board_profile_by_fqbn(fqbn: str) -> Optional[BoardProfile]:
    """
    Locates board profile by matching FQBN against cache, or deriving dynamically.
    """
    if not fqbn:
        return None

    fqbn_clean = fqbn.strip().lower()
    # 1. Match against known cache
    for profile in ALL_BOARD_PROFILES.values():
        if profile.fqbn and (profile.fqbn.lower() == fqbn_clean or fqbn_clean.startswith(profile.fqbn.lower())):
            return profile

    # 2. Derive dynamically from toolchain
    derived = BoardProfileResolver.resolve_from_toolchain(fqbn)
    if derived:
        return derived

    return None


def list_board_profiles() -> List[BoardProfile]:
    """Returns a list of all registered canonical and cached board profiles."""
    return list(ALL_BOARD_PROFILES.values())
