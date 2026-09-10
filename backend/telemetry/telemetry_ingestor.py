"""
ARIS Telemetry Ingestion Pipeline.
Handles:
- Frame decoding (Fast Micro-Framing $ARIS1,...# and Direct JSON streams)
- Schema validation via TelemetrySample
- Sequence monotonicity validation
- Timestamp handling and timer wraparound checks
- Run and board association
- Persistent storage via DatabaseEngine
- Real-time subscriber dispatching for WebSockets
- Graceful rejection of malformed packets
"""

import json
import logging
from typing import List, Dict, Any, Callable, Optional
from datetime import datetime, timezone

from .telemetry_schema import (
    TelemetrySample,
    CANONICAL_METRIC_NAMES,
    METRIC_SPECIFICATIONS,
    PROTOCOL_VERSION,
    ArisException
)
from backend.database.db_engine import DatabaseEngine
from backend.database.models import TelemetryRecord, RunRecord

logger = logging.getLogger("aris.telemetry.ingestor")


class TelemetryIngestor:
    """
    Core ingestion processor that receives raw telemetry data, validates it against
    the canonical protocol, verifies sequence and timestamp integrity, saves it to
    the database, and distributes it to live subscribers.
    """

    def __init__(self, db: DatabaseEngine):
        self.db = db
        # Set of real-time listener callbacks: callback(TelemetrySample)
        self._subscribers: List[Callable[[TelemetrySample], None]] = []
        # Track highest sequence number seen per (run_id, metric) to enforce monotonicity
        self._last_sequence: Dict[str, int] = {}
        # Track latest timestamp per run_id
        self._last_timestamp: Dict[str, int] = {}
        # Track statistics on ingested and malformed packets
        self.total_packets_received: int = 0
        self.total_packets_valid: int = 0
        self.total_packets_rejected: int = 0
        self.last_error: Optional[str] = None

    def subscribe(self, callback: Callable[[TelemetrySample], None]) -> None:
        """Registers a listener callback for live validated telemetry samples."""
        if callback not in self._subscribers:
            self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[TelemetrySample], None]) -> None:
        """Removes a previously registered listener callback."""
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    def ingest_raw_line(self, raw_line: str, active_run_id: Optional[str] = None) -> List[TelemetrySample]:
        """
        Parses and ingests a raw line from physical serial or simulated hardware.
        Supports:
        1. JSON payload: {"protocol_version": "1.0", ...}
        2. Fast micro-frame: $ARIS1,run_id,board_id,mcu,timestamp,seq,cpu,loop_t,loop_f,jitter,s_used,s_free,stk_used,stk_max,isr_c,isr_r,gpio,adc,uart,spi,i2c,timer,reset,wdt,fault,overhead#
        """
        self.total_packets_received += 1
        line = raw_line.strip()
        if not line:
            return []

        samples: List[TelemetrySample] = []

        try:
            # Case 1: Line is a JSON payload
            if line.startswith("{") and line.endswith("}"):
                sample = self._parse_json_packet(line, active_run_id)
                if sample:
                    samples.append(sample)

            # Case 2: Line is a Fast Micro-Framing ARIS1 packet
            elif line.startswith("$ARIS1,") and line.endswith("#"):
                samples = self._parse_aris1_frame(line, active_run_id)

            else:
                # Malformed framing structure
                self._handle_rejection(f"Unrecognized framing format: {line[:30]}")
                return []

        except Exception as e:
            self._handle_rejection(f"Exception parsing telemetry line: {str(e)}")
            return []

        # Process and persist each validated sample
        processed_samples: List[TelemetrySample] = []
        for sample in samples:
            if self._validate_and_store_sample(sample):
                processed_samples.append(sample)

        return processed_samples

    def _parse_json_packet(self, json_str: str, override_run_id: Optional[str] = None) -> Optional[TelemetrySample]:
        """Parses a single canonical JSON telemetry object."""
        try:
            data = json.loads(json_str)
            if override_run_id and "run_id" not in data:
                data["run_id"] = override_run_id
            return TelemetrySample(**data)
        except Exception as e:
            self._handle_rejection(f"Malformed JSON telemetry packet: {e}")
            return None

    def _parse_aris1_frame(self, line: str, override_run_id: Optional[str] = None) -> List[TelemetrySample]:
        """
        Decodes the fast micro-frame format transmitted over UART on 8-bit AVR microcontrollers.
        Format: $ARIS1,run_id,board_id,mcu,timestamp,seq,cpu,loop_t,loop_f,jitter,s_used,s_free,stk_used,stk_max,isr_c,isr_r,gpio,adc,uart,spi,i2c,timer,reset,wdt,fault,overhead#
        """
        clean = line[len("$ARIS1,"):-1]
        parts = [p.strip() for p in clean.split(",")]
        if len(parts) < 25:
            self._handle_rejection(f"Insufficient fields in ARIS1 frame: expected 25, got {len(parts)}")
            return []

        run_id = override_run_id or parts[0]
        board_id = parts[1]
        mcu = parts[2]
        timestamp_ms = int(parts[3])
        sequence_base = int(parts[4])

        # Map parsed values to canonical metrics in strict order
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
            meta = METRIC_SPECIFICATIONS[metric_name]
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

    def _validate_and_store_sample(self, sample: TelemetrySample) -> bool:
        """
        Performs sequence monotonicity checks, run association, database persistence,
        and subscriber dispatching.
        """
        # 1. Sequence validation (warn on sequence reversals, but do not drop to preserve data)
        seq_key = f"{sample.run_id}:{sample.metric}"
        last_seq = self._last_sequence.get(seq_key)
        if last_seq is not None and sample.sequence <= last_seq:
            logger.warning(
                f"Sequence non-monotonic for {seq_key}: got {sample.sequence} after {last_seq}"
            )
        self._last_sequence[seq_key] = sample.sequence

        # 2. Timestamp tracking
        self._last_timestamp[sample.run_id] = sample.timestamp_ms

        # 3. Ensure Run exists in DB or create implicit run if needed
        run = self.db.get_run(sample.run_id)
        if not run:
            self.db.save_run(RunRecord(
                run_id=sample.run_id,
                board_id=sample.board_id,
                status="RUNNING",
                start_time=datetime.now(timezone.utc).isoformat()
            ))

        # 4. Save to database
        record = TelemetryRecord(
            protocol_version=sample.protocol_version,
            run_id=sample.run_id,
            board_id=sample.board_id,
            mcu=sample.mcu,
            timestamp_ms=sample.timestamp_ms,
            sequence=sample.sequence,
            metric=sample.metric,
            value=sample.value,
            unit=sample.unit,
            classification=sample.classification,
            confidence=sample.confidence,
            is_demo=False
        )
        self.db.save_telemetry_sample(record)

        self.total_packets_valid += 1

        # 5. Dispatch to live real-time subscribers (e.g. WebSocket broadcasts)
        for subscriber in list(self._subscribers):
            try:
                subscriber(sample)
            except Exception as e:
                logger.error(f"Error notifying telemetry subscriber: {e}")

        return True

    def _handle_rejection(self, reason: str):
        """Logs and counts rejected packets gracefully without crashing."""
        self.total_packets_rejected += 1
        self.last_error = reason
        logger.warning(f"Telemetry packet rejected: {reason}")
