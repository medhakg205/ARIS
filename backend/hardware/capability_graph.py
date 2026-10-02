"""
ARIS Hardware Capability Graph & Provenance Specification.
Defines normalized, evidence-based hardware capabilities derived directly from dynamic board profiles.
Every capability maintains strict provenance:
- EXACT_PROFILE: Statically defined in verified hardware specs.
- TOOLCHAIN: Derived dynamically via arduino-cli board details.
- RUNTIME: Verified over serial handshake ($ARIS_ACK / $ARIS_BOOT).
- INFERRED: Safely deduced from architecture/compiler conventions.
- UNKNOWN: Property is unknown and left unspecified (zero guessing).
"""

from typing import Dict, Any, List, Optional, Set
from pydantic import BaseModel, Field
from enum import Enum


class CapabilityProvenance(str, Enum):
    EXACT_PROFILE = "EXACT_PROFILE"
    TOOLCHAIN = "TOOLCHAIN"
    RUNTIME = "RUNTIME"
    INFERRED = "INFERRED"
    UNKNOWN = "UNKNOWN"


class CapabilityItem(BaseModel):
    """Represents a specific hardware feature with truth provenance and availability."""
    name: str
    available: Optional[bool] = None # True, False, or None if unknown
    value: Any = None                # Quantitative or structured payload (e.g. 16000000, 32768, "avr-gcc")
    unit: Optional[str] = None       # e.g. "Hz", "bytes", "channels"
    provenance: CapabilityProvenance = CapabilityProvenance.UNKNOWN
    notes: Optional[str] = None


class HardwareCapabilityGraph(BaseModel):
    """
    Normalized capability graph derived strictly from dynamic board profile evidence.
    Represents physical MCU boundaries, peripheral resources, instrumentation limits,
    and toolchain characteristics without inventing hypothetical features.
    """
    board_id: str
    display_name: str
    fqbn: Optional[str] = None
    platform: Optional[str] = None
    mcu: Optional[str] = None
    architecture: Optional[str] = None

    # Provenance-tracked specifications
    clock: CapabilityItem = Field(default_factory=lambda: CapabilityItem(name="clock"))
    flash_memory: CapabilityItem = Field(default_factory=lambda: CapabilityItem(name="flash_memory", unit="bytes"))
    sram_memory: CapabilityItem = Field(default_factory=lambda: CapabilityItem(name="sram_memory", unit="bytes"))
    eeprom_memory: CapabilityItem = Field(default_factory=lambda: CapabilityItem(name="eeprom_memory", unit="bytes"))

    # Peripherals
    gpio: CapabilityItem = Field(default_factory=lambda: CapabilityItem(name="gpio", unit="pins"))
    adc: CapabilityItem = Field(default_factory=lambda: CapabilityItem(name="adc", unit="channels"))
    uart: CapabilityItem = Field(default_factory=lambda: CapabilityItem(name="uart", unit="peripherals"))
    spi: CapabilityItem = Field(default_factory=lambda: CapabilityItem(name="spi"))
    i2c: CapabilityItem = Field(default_factory=lambda: CapabilityItem(name="i2c"))
    timers: CapabilityItem = Field(default_factory=lambda: CapabilityItem(name="timers", unit="timers"))
    interrupts: CapabilityItem = Field(default_factory=lambda: CapabilityItem(name="interrupts"))
    watchdog: CapabilityItem = Field(default_factory=lambda: CapabilityItem(name="watchdog"))

    # Toolchain & Protocol
    compiler_toolchain: CapabilityItem = Field(default_factory=lambda: CapabilityItem(name="compiler_toolchain"))
    runtime_protocol: CapabilityItem = Field(default_factory=lambda: CapabilityItem(name="runtime_protocol"))

    # Instrumentation Capabilities
    available_instrumentation: List[str] = Field(default_factory=list)
    unavailable_instrumentation: List[str] = Field(default_factory=list)
    unknown_properties: List[str] = Field(default_factory=list)

    raw_properties_count: int = 0
