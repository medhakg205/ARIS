"""
ARIS Protocol Parser.
Parses both Canonical JSON telemetry samples and Fast Micro-Framing packets ($ARIS1,...#)
into validated TelemetrySample instances.
"""

import json
from typing import List, Dict, Any, Optional
from .protocol_schema import (
    TelemetrySample,
    CANONICAL_METRIC_NAMES,
    METRIC_METADATA,
    PROTOCOL_VERSION
)

class ProtocolParser:
    def __init__(self, run_id: str = "ARIS-2026-000001"):
        self.default_run_id = run_id

    def parse_json_sample(self, raw_json: str) -> TelemetrySample:
        """Parses a single canonical JSON telemetry sample."""
        data = json.loads(raw_json.strip())
        return TelemetrySample(**data)

    def parse_frame(self, line: str) -> List[TelemetrySample]:
        """
        Parses an incoming serial line.
        Supports:
        1. Canonical JSON line: {"protocol_version": "1.0", ...}
        2. Fast micro-frame: $ARIS1,run_id,board_id,mcu,timestamp,seq,cpu,loop_t,loop_f,jitter,s_used,s_free,stk_used,stk_max,isr_c,isr_r,gpio,adc,uart,spi,i2c,timer,reset,wdt,fault,overhead#
        3. Legacy micro-frame: $ARIS,board,cpu,sram_free,stack_max,loop_us,isr_cnt,adc_cnt,gpio_cnt#
        """
        line = line.strip()
        if not line:
            return []

        # Case 1: JSON payload
        if line.startswith("{") and line.endswith("}"):
            return [self.parse_json_sample(line)]

        # Case 2: ARIS1 Full Fast Framing Packet
        if line.startswith("$ARIS1,") and line.endswith("#"):
            return self._parse_aris1_frame(line)

        # Case 3: ARIS Legacy Framing Packet
        if line.startswith("$ARIS,") and line.endswith("#"):
            return self._parse_legacy_frame(line)

        return []

    def _parse_aris1_frame(self, line: str) -> List[TelemetrySample]:
        clean = line[len("$ARIS1,"):-1]
        parts = [p.strip() for p in clean.split(",")]
        if len(parts) < 25:
            return []

        run_id = parts[0]
        board_id = parts[1]
        mcu = parts[2]
        timestamp_ms = int(parts[3])
        sequence_base = int(parts[4])

        # Parse numeric values in canonical order
        raw_values = {
            "cpu_load": float(parts[5]),
            "loop_time": float(parts[6]),
            "loop_frequency": float(parts[7]),
            "loop_jitter": float(parts[8]),
            "sram_used": float(parts[9]),
            "sram_free": float(parts[10]),
            "stack_used": float(parts[11]),
            "stack_high_water_mark": float(parts[12]),
            "interrupt_count": float(parts[13]),
            "interrupt_rate": float(parts[14]),
            "gpio_activity": float(parts[15]),
            "adc_activity": float(parts[16]),
            "uart_activity": float(parts[17]),
            "spi_activity": float(parts[18]),
            "i2c_activity": float(parts[19]),
            "timer_activity": float(parts[20]),
            "reset_event": float(parts[21]),
            "watchdog_event": float(parts[22]),
            "runtime_fault": float(parts[23]),
            "instrumentation_overhead": float(parts[24])
        }

        samples = []
        seq = sequence_base
        for metric_name in CANONICAL_METRIC_NAMES:
            val = raw_values.get(metric_name, 0.0)
            meta = METRIC_METADATA[metric_name]
            sample = TelemetrySample(
                protocol_version=PROTOCOL_VERSION,
                run_id=run_id,
                board_id=board_id,
                mcu=mcu,
                timestamp_ms=timestamp_ms,
                sequence=seq,
                metric=metric_name,
                value=val,
                unit=meta["unit"],
                classification=meta["classification"],
                confidence=meta["confidence"]
            )
            samples.append(sample)
            seq += 1

        return samples

    def _parse_legacy_frame(self, line: str) -> List[TelemetrySample]:
        # Format: $ARIS,board_type_id,cpu,sram_free,stack_max,loop_us,isr_cnt,adc_cnt,gpio_cnt#
        clean = line[len("$ARIS,"):-1]
        parts = [p.strip() for p in clean.split(",")]
        if len(parts) < 8:
            return []

        board_type_id = int(parts[0])
        board_id = "arduino_uno"
        mcu = "atmega328p"
        if board_type_id == 2:
            board_id = "arduino_mega"
            mcu = "atmega2560"
        elif board_type_id == 3:
            board_id = "arduino_nano"
            mcu = "atmega328p"

        cpu_val = float(parts[1])
        sram_free_val = float(parts[2])
        stack_max_val = float(parts[3])
        loop_us = float(parts[4])
        loop_time_ms = loop_us / 1000.0
        isr_cnt = float(parts[5])
        adc_cnt = float(parts[6])
        gpio_cnt = float(parts[7])

        import time
        now_ms = int(time.time() * 1000)

        # Map to canonical samples
        samples = [
            TelemetrySample(
                protocol_version=PROTOCOL_VERSION,
                run_id=self.default_run_id,
                board_id=board_id,
                mcu=mcu,
                timestamp_ms=now_ms,
                sequence=1,
                metric="cpu_load",
                value=cpu_val,
                unit="%",
                classification="ESTIMATED",
                confidence=0.85
            ),
            TelemetrySample(
                protocol_version=PROTOCOL_VERSION,
                run_id=self.default_run_id,
                board_id=board_id,
                mcu=mcu,
                timestamp_ms=now_ms,
                sequence=2,
                metric="loop_time",
                value=loop_time_ms,
                unit="ms",
                classification="MEASURED",
                confidence=1.0
            ),
            TelemetrySample(
                protocol_version=PROTOCOL_VERSION,
                run_id=self.default_run_id,
                board_id=board_id,
                mcu=mcu,
                timestamp_ms=now_ms,
                sequence=3,
                metric="sram_free",
                value=sram_free_val,
                unit="bytes",
                classification="MEASURED",
                confidence=1.0
            ),
            TelemetrySample(
                protocol_version=PROTOCOL_VERSION,
                run_id=self.default_run_id,
                board_id=board_id,
                mcu=mcu,
                timestamp_ms=now_ms,
                sequence=4,
                metric="stack_high_water_mark",
                value=stack_max_val,
                unit="bytes",
                classification="ESTIMATED",
                confidence=0.95
            ),
            TelemetrySample(
                protocol_version=PROTOCOL_VERSION,
                run_id=self.default_run_id,
                board_id=board_id,
                mcu=mcu,
                timestamp_ms=now_ms,
                sequence=5,
                metric="interrupt_count",
                value=isr_cnt,
                unit="count",
                classification="MEASURED",
                confidence=1.0
            ),
            TelemetrySample(
                protocol_version=PROTOCOL_VERSION,
                run_id=self.default_run_id,
                board_id=board_id,
                mcu=mcu,
                timestamp_ms=now_ms,
                sequence=6,
                metric="adc_activity",
                value=adc_cnt,
                unit="conversions",
                classification="MEASURED",
                confidence=1.0
            ),
            TelemetrySample(
                protocol_version=PROTOCOL_VERSION,
                run_id=self.default_run_id,
                board_id=board_id,
                mcu=mcu,
                timestamp_ms=now_ms,
                sequence=7,
                metric="gpio_activity",
                value=gpio_cnt,
                unit="events",
                classification="MEASURED",
                confidence=1.0
            ),
            TelemetrySample(
                protocol_version=PROTOCOL_VERSION,
                run_id=self.default_run_id,
                board_id=board_id,
                mcu=mcu,
                timestamp_ms=now_ms,
                sequence=8,
                metric="instrumentation_overhead",
                value=2.0,
                unit="us",
                classification="MEASURED",
                confidence=1.0
            )
        ]
        return samples
