# ARIS AI Architecture

**Adaptive Runtime Intelligence System for Embedded Devices**
**Subsystem Owner:** Engineer 3 (AI + Frontend)
**Version:** 1.0.0

---

## 1. Overview

The ARIS AI Engine is a modular, architecture-aware optimization layer that analyzes embedded firmware running on real Arduino-class microcontrollers (ATmega328P, ATmega2560, AVR8 architecture). It does NOT operate as a generic AI code assistant—it understands the physical hardware constraints, observes actual runtime behavior, and generates optimization candidates validated against real-world telemetry.

### Core Principles
- **Zero Hardware Hallucination**: Never references non-existent MCU features (CPU perf counters, caches, FPU, branch predictors).
- **Veracity Separation**: Strictly distinguishes MEASURED, ESTIMATED, DERIVED, and PREDICTED values.
- **Human Approval Required**: AI-generated code is NEVER automatically flashed. Users must explicitly approve.
- **Provider Abstraction**: Not locked to a single AI provider—supports Gemini, OpenAI, and deterministic rule synthesis.
- **Graceful Degradation**: Reports `ARIS_AI_UNAVAILABLE` when no provider is configured; never fabricates output.

---

## 2. Module Architecture

```
backend/ai/
├── __init__.py                 # Package exports
├── provider.py                 # AIProvider abstraction + Gemini/OpenAI/RuleSynthesizer
├── context_builder.py          # Assembles AIContextInput from all data sources
├── firmware_analyzer.py        # Static structural analysis of AVR Arduino sketches
├── optimization_reasoner.py    # 7-step architecture-aware reasoning pipeline
├── candidate_generator.py      # Orchestrates provider dispatch and validation
├── risk_evaluator.py           # Risk classification (LOW/MEDIUM/HIGH)
├── prediction_engine.py        # Quantitative performance forecasting + accuracy tracking
└── output_validator.py         # Canonical schema enforcement
```

---

## 3. AI Provider Abstraction

### 3.1 Abstract Base: `AIProvider`

```python
class AIProvider(ABC):
    provider_id: str          # "gemini", "openai", "rule_synthesizer"
    display_name: str         # Human-readable label
    is_available() -> bool    # Configuration check
    generate_candidate(context, finding) -> OptimizationCandidate
```

### 3.2 Providers

| Provider | Key | Availability | Mode |
|---|---|---|---|
| `GeminiProvider` | `GEMINI_API_KEY` env var | Online when key set | LLM-based optimization via Gemini API |
| `OpenAIProvider` | `OPENAI_API_KEY` env var | Online when key set | LLM-based optimization via OpenAI API |
| `RuleSynthesizerProvider` | None (built-in) | **Always available** | Deterministic, architecture-aware AVR transforms |

### 3.3 Provider Selection

`get_ai_provider(type)`:
- `"auto"` (default): Gemini → OpenAI → RuleSynthesizer fallback chain.
- `"gemini"` / `"openai"` / `"rule_synthesizer"`: Specific provider.
- Unknown provider → `ARIS_AI_UNAVAILABLE` error.

---

## 4. AI Input Contract: `AIContextInput`

The AI receives a comprehensive diagnostic package:

```python
class AIContextInput:
    board_profile: Dict         # MCU specs, clock, SRAM, Flash, architecture
    firmware_source: str        # Arduino C/C++ sketch source code
    static_findings: List       # Code antipatterns from static analysis
    runtime_metrics: Dict       # Measured/estimated runtime values
    baseline_metrics: Dict      # Statistical baseline (mean, median, variance, jitter)
    runtime_static_correlations: List   # Correlated static + runtime findings
    optimization_history: List  # Previously attempted optimizations
```

### Board Profile Enrichment
- `has_hardware_perf_counters: false` — ATmega328P/ATmega2560 have NO performance counters
- `instruction_cycle_ns: 62.5` — 16 MHz = 62.5 ns per clock cycle
- `architecture_class: "avr8"` — 8-bit Harvard RISC architecture

---

## 5. AI Output Contract: `OptimizationCandidate`

```python
class OptimizationCandidate:
    optimization_id: str                # "OPT-XXXXXXXX"
    finding_id: str                     # Reference to triggering finding
    title: str                          # Concise optimization title
    problem: str                        # Description of the performance issue
    source_location: {file, line}       # Source code location
    before_code: str                    # Original code snippet
    after_code: str                     # Proposed optimized code
    reason: str                         # Architectural rationale
    hardware_consideration: str         # MCU-specific hardware implications
    expected_effect: Dict               # Quantitative predictions (PREDICTED classification)
    risk: "LOW" | "MEDIUM" | "HIGH"     # Risk assessment
    confidence: float                   # 0.0 to 1.0
    validation_required: bool           # Always true
    status: str                         # PROPOSED → APPROVED → BUILDING → TESTING → VALIDATED
```

### Status Transitions
```
PROPOSED → APPROVED → BUILDING → TESTING → VALIDATED
    ↓                                        ↓
  REJECTED                               ROLLED_BACK
                                             ↓
                                          FAILED
```

---

## 6. Reasoning Pipeline (7 Steps)

The `OptimizationReasoner` implements the following pipeline:

```
BOARD PROFILE + FIRMWARE + STATIC FINDINGS + RUNTIME TELEMETRY + BASELINE + CORRELATION
  ↓
Step 1: PROBLEM IDENTIFICATION
  ↓
Step 2: POSSIBLE OPTIMIZATIONS (rule-based code transforms)
  ↓
Step 3: HARDWARE CONSTRAINT CHECK (AVR8 specific)
  ↓
Step 4: RISK ASSESSMENT (via RiskEvaluator)
  ↓
Step 5: EXPECTED EFFECT (via PredictionEngine — PREDICTED classification)
  ↓
Step 6: OPTIMIZATION CANDIDATE ASSEMBLY
  ↓
Step 7: OUTPUT VALIDATION (via OutputValidator)
```

### Canonical Rules
| Rule | Antipattern | Transform |
|---|---|---|
| ARIS-001 | `delay()` blocking | Non-blocking `millis()` state machine |
| ARIS-002 | Unthrottled `Serial.print` | Rate-limited transmission + `F()` macro |
| ARIS-003/005 | RAM string literals | `F()` / `PROGMEM` Flash storage |
| ARIS-004 | Software `float` math | Fixed-point integer arithmetic |
| ARIS-007 | Slow `digitalWrite()` | Direct port register (SBI/CBI) |

---

## 7. Zero Hardware Hallucination Guarantee

The `_verify_zero_hardware_hallucinations()` method scans all AI reasoning text for forbidden references:

**Forbidden on ATmega328P / ATmega2560:**
- CPU performance counters
- L1/L2 cache
- Branch predictors
- Hardware FPU
- Out-of-order execution
- Instruction cache

If detected, raises `ValueError` immediately—no hallucinated hardware features reach the user.

---

## 8. Prediction Engine

### Pre-Test Forecasting
`PredictionEngine.forecast_effect()` generates quantitative hardware predictions before flash:
- `loop_time_delta_ms` (always classified PREDICTED)
- `cpu_load_delta_pct` (always classified PREDICTED)
- `sram_recovery_bytes`
- `jitter_reduction_pct`

### Post-Test Comparison
`PredictionEngine.calculate_prediction_accuracy()` compares predicted vs actual:
- Absolute error per metric
- Relative error percentage
- Directional match (did it improve in the predicted direction?)
- Composite accuracy score
- Scientific caveat: "Single closed-loop trial. Multi-run benchmark required for statistical significance."

---

## 9. Risk Assessment

The `RiskEvaluator` classifies risk based on:

| Risk Level | Triggers |
|---|---|
| **HIGH** | Modifying ISR, `cli()`/`sei()`, inline assembly, pointer casting |
| **MEDIUM** | Direct port register writes, float-to-integer conversion |
| **LOW** | Non-blocking millis(), PROGMEM strings, serial throttling |

---

## 10. REST API Integration

### Endpoints (Contract with Engineer 2 Backend)
- `POST /api/ai/analyze` — Assembles `AIContextInput` for the AI engine
- `POST /api/ai/generate-candidate` — Generates and validates an `OptimizationCandidate`
- `GET /api/ai/providers` — Lists available AI providers and their status

### Error Handling
All errors use canonical ARIS error schema:
```json
{
  "error_code": "ARIS_AI_UNAVAILABLE",
  "message": "AI service unavailable: GEMINI_API_KEY is not configured.",
  "details": {"provider": "gemini"},
  "recoverable": true
}
```
