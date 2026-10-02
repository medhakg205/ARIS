"""
ARIS Optimization Transformation Taxonomy & Transformation Registry.
Defines formal optimization transformations, architecture boundaries,
required hardware peripherals, trade-offs, and risk models.
"""

from typing import Dict, Any, List, Optional, Set
from pydantic import BaseModel, Field
from enum import Enum


class TransformationCategory(str, Enum):
    LOOP_OPTIMIZATION = "LOOP_OPTIMIZATION"
    REDUNDANT_COMPUTATION_REMOVAL = "REDUNDANT_COMPUTATION_REMOVAL"
    CONSTANT_PRECOMPUTATION = "CONSTANT_PRECOMPUTATION"
    DEAD_CODE_REMOVAL = "DEAD_CODE_REMOVAL"
    MEMORY_ACCESS_REDUCTION = "MEMORY_ACCESS_REDUCTION"
    DATA_STRUCTURE_REPLACEMENT = "DATA_STRUCTURE_REPLACEMENT"
    SERIAL_IO_REDUCTION = "SERIAL_IO_REDUCTION"
    INTERRUPT_HANDLING_OPTIMIZATION = "INTERRUPT_HANDLING_OPTIMIZATION"
    TIMING_OPTIMIZATION = "TIMING_OPTIMIZATION"
    MEMORY_LAYOUT_OPTIMIZATION = "MEMORY_LAYOUT_OPTIMIZATION"


class ResourceImpactType(str, Enum):
    DECREASE = "DECREASE"
    INCREASE = "INCREASE"
    NEUTRAL = "NEUTRAL"
    UNCERTAIN = "UNCERTAIN"


class OptimizationTransformation(BaseModel):
    """
    Formal representation of an optimization transformation definition.
    Specifies exact capability prerequisites, architecture limits, and trade-offs.
    """
    transformation_id: str
    name: str
    category: TransformationCategory
    description: str
    supported_architectures: List[str] = Field(default_factory=lambda: ["*"])  # ["*"] or ["avr8", "arm_cortex_m4", etc.]
    required_capabilities: List[str] = Field(default_factory=list)             # e.g. ["gpio"], ["timers"], ["uart"]
    incompatible_capabilities: List[str] = Field(default_factory=list)         # e.g. features that conflict
    min_clock_hz: Optional[int] = None
    min_flash_bytes: Optional[int] = None
    min_sram_bytes: Optional[int] = None

    # Expected metric directional impacts
    expected_loop_time_impact: ResourceImpactType = ResourceImpactType.DECREASE
    expected_sram_impact: ResourceImpactType = ResourceImpactType.NEUTRAL
    expected_flash_impact: ResourceImpactType = ResourceImpactType.NEUTRAL
    expected_jitter_impact: ResourceImpactType = ResourceImpactType.DECREASE

    # Safety & Requirements
    safety_risk: str = "LOW"  # LOW, MEDIUM, HIGH
    reversibility: str = "FULLY_REVERSIBLE"  # FULLY_REVERSIBLE, MANUAL_INTERVENTION
    static_prerequisites: List[str] = Field(default_factory=list)
    runtime_prerequisites: List[str] = Field(default_factory=list)
    code_pattern_tag: str = ""
    rationale_template: str = ""


class TransformationRegistry:
    """
    Registry of canonical, evidence-based embedded firmware transformations.
    Enforces hardware and capability checking to prevent illegal/unsupported candidates.
    """
    _registry: Dict[str, OptimizationTransformation] = {}

    @classmethod
    def register(cls, transform: OptimizationTransformation) -> None:
        cls._registry[transform.transformation_id] = transform

    @classmethod
    def get(cls, transformation_id: str) -> Optional[OptimizationTransformation]:
        cls._ensure_initialized()
        return cls._registry.get(transformation_id)

    @classmethod
    def list_all(cls) -> List[OptimizationTransformation]:
        cls._ensure_initialized()
        return list(cls._registry.values())

    @classmethod
    def get_by_category(cls, category: TransformationCategory) -> List[OptimizationTransformation]:
        cls._ensure_initialized()
        return [t for t in cls._registry.values() if t.category == category]

    @classmethod
    def _ensure_initialized(cls) -> None:
        if cls._registry:
            return

        # 1. Non-blocking timing transformation (delay to millis state machine)
        cls.register(OptimizationTransformation(
            transformation_id="TR-TIME-001",
            name="Convert blocking delay to non-blocking millis() state machine",
            category=TransformationCategory.TIMING_OPTIMIZATION,
            description="Replaces synchronous delay() busy-wait with non-blocking timer interval checks.",
            supported_architectures=["*"],
            required_capabilities=["timers"],
            incompatible_capabilities=[],
            expected_loop_time_impact=ResourceImpactType.DECREASE,
            expected_sram_impact=ResourceImpactType.INCREASE,  # Requires static timestamp var (4 bytes)
            expected_flash_impact=ResourceImpactType.INCREASE,  # Slight code expansion
            expected_jitter_impact=ResourceImpactType.DECREASE,
            safety_risk="LOW",
            reversibility="FULLY_REVERSIBLE",
            code_pattern_tag="delay_call",
            rationale_template="Replaces CPU busy-wait stall ({duration}ms) with non-blocking state machine yielding execution cycles to concurrent loop iterations."
        ))

        # 2. UART Serial throttling
        cls.register(OptimizationTransformation(
            transformation_id="TR-SERIAL-001",
            name="Throttle UART Serial output & stream buffering",
            category=TransformationCategory.SERIAL_IO_REDUCTION,
            description="Rates limits repetitive serial print calls to prevent UART ring buffer saturation.",
            supported_architectures=["*"],
            required_capabilities=["uart"],
            expected_loop_time_impact=ResourceImpactType.DECREASE,
            expected_sram_impact=ResourceImpactType.INCREASE,  # Requires timestamp tracker
            expected_flash_impact=ResourceImpactType.INCREASE,
            expected_jitter_impact=ResourceImpactType.DECREASE,
            safety_risk="LOW",
            reversibility="FULLY_REVERSIBLE",
            code_pattern_tag="serial_print_loop",
            rationale_template="Limits serial transmission cadence, mitigating UART TX buffer saturation stalls."
        ))

        # 3. Flash ROM string placement (F() macro / PROGMEM)
        cls.register(OptimizationTransformation(
            transformation_id="TR-MEM-001",
            name="Store string literals in Flash ROM via F() macro",
            category=TransformationCategory.MEMORY_LAYOUT_OPTIMIZATION,
            description="Positions immutable string constants into Flash ROM instead of copying into dynamic SRAM at boot.",
            supported_architectures=["avr8"],  # Highly specific to Harvard AVR architecture where RAM is tiny
            required_capabilities=["flash_memory", "sram_memory"],
            expected_loop_time_impact=ResourceImpactType.NEUTRAL,
            expected_sram_impact=ResourceImpactType.DECREASE,
            expected_flash_impact=ResourceImpactType.NEUTRAL,
            expected_jitter_impact=ResourceImpactType.NEUTRAL,
            safety_risk="LOW",
            reversibility="FULLY_REVERSIBLE",
            code_pattern_tag="raw_string_literal",
            rationale_template="Migrates constant string literals from precious SRAM to Flash ROM, guarding against stack/heap collision."
        ))

        # 4. Direct Register GPIO manipulation
        cls.register(OptimizationTransformation(
            transformation_id="TR-GPIO-001",
            name="Direct Port Register GPIO access",
            category=TransformationCategory.LOOP_OPTIMIZATION,
            description="Replaces high-overhead digitalWrite/digitalRead with atomic direct port register manipulation.",
            supported_architectures=["avr8"],
            required_capabilities=["gpio"],
            expected_loop_time_impact=ResourceImpactType.DECREASE,
            expected_sram_impact=ResourceImpactType.NEUTRAL,
            expected_flash_impact=ResourceImpactType.DECREASE,
            expected_jitter_impact=ResourceImpactType.DECREASE,
            safety_risk="MEDIUM",  # Port pin mapping must match exact hardware wiring
            reversibility="FULLY_REVERSIBLE",
            code_pattern_tag="digital_io_call",
            rationale_template="Bypasses Arduino core pin lookup tables (~50 clock cycles) with single-cycle atomic port register writes."
        ))

        # 5. Fixed-Point Arithmetic (Float to Integer/Fixed-Point)
        cls.register(OptimizationTransformation(
            transformation_id="TR-COMP-001",
            name="Fixed-point integer arithmetic substitution",
            category=TransformationCategory.REDUNDANT_COMPUTATION_REMOVAL,
            description="Converts software-emulated floating-point math into fixed-point or scaled integer arithmetic.",
            supported_architectures=["*"],
            incompatible_capabilities=["hardware_fpu"],  # Not needed if hardware FPU exists
            expected_loop_time_impact=ResourceImpactType.DECREASE,
            expected_sram_impact=ResourceImpactType.NEUTRAL,
            expected_flash_impact=ResourceImpactType.DECREASE,
            expected_jitter_impact=ResourceImpactType.DECREASE,
            safety_risk="MEDIUM",  # Loss of precision if scale factor is improperly chosen
            reversibility="FULLY_REVERSIBLE",
            code_pattern_tag="software_float_math",
            rationale_template="Eliminates multi-cycle IEEE 754 software emulation on MCU cores lacking hardware floating point units."
        ))

        # 6. Flash Look-Up Table (LUT) for Transcendental Math
        cls.register(OptimizationTransformation(
            transformation_id="TR-LUT-001",
            name="Precomputed Look-Up Table for transcendental functions",
            category=TransformationCategory.CONSTANT_PRECOMPUTATION,
            description="Replaces runtime sin/cos/exp/log math calls with a precomputed lookup table stored in Flash memory.",
            supported_architectures=["*"],
            required_capabilities=["flash_memory"],
            min_flash_bytes=4096,
            expected_loop_time_impact=ResourceImpactType.DECREASE,
            expected_sram_impact=ResourceImpactType.NEUTRAL,
            expected_flash_impact=ResourceImpactType.INCREASE,  # Consumes Flash for the table
            expected_jitter_impact=ResourceImpactType.DECREASE,
            safety_risk="LOW",
            reversibility="FULLY_REVERSIBLE",
            code_pattern_tag="transcendental_math",
            rationale_template="Substitutes expensive runtime iterative calculations with instantaneous O(1) table lookups in ROM."
        ))

        # 7. Hardware Interrupt Pin-Change capture
        cls.register(OptimizationTransformation(
            transformation_id="TR-ISR-001",
            name="Hardware Interrupt Input Capture over synchronous polling",
            category=TransformationCategory.INTERRUPT_HANDLING_OPTIMIZATION,
            description="Replaces blocking pulseIn() or tight pin polling loops with an asynchronous ISR event listener.",
            supported_architectures=["*"],
            required_capabilities=["interrupts", "gpio"],
            expected_loop_time_impact=ResourceImpactType.DECREASE,
            expected_sram_impact=ResourceImpactType.INCREASE,  # ISR volatile shared state
            expected_flash_impact=ResourceImpactType.INCREASE,
            expected_jitter_impact=ResourceImpactType.DECREASE,
            safety_risk="MEDIUM",  # Concurrency/volatile semantics required
            reversibility="FULLY_REVERSIBLE",
            code_pattern_tag="blocking_io_poll",
            rationale_template="Frees MCU core from synchronous pin-state polling by triggering asynchronous hardware interrupt handlers."
        ))

        # 8. Dead Code & Unused Library Elimination
        cls.register(OptimizationTransformation(
            transformation_id="TR-DEAD-001",
            name="Dead code and unreferenced symbol elimination",
            category=TransformationCategory.DEAD_CODE_REMOVAL,
            description="Removes unused static functions, constants, or redundant debug routines.",
            supported_architectures=["*"],
            expected_loop_time_impact=ResourceImpactType.NEUTRAL,
            expected_sram_impact=ResourceImpactType.DECREASE,
            expected_flash_impact=ResourceImpactType.DECREASE,
            expected_jitter_impact=ResourceImpactType.NEUTRAL,
            safety_risk="LOW",
            reversibility="FULLY_REVERSIBLE",
            code_pattern_tag="dead_code",
            rationale_template="Removes unreachable instructions and buffers, reclaiming ROM and RAM headroom."
        ))
