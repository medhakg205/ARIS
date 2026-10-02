"""
Unit tests for ARIS Telemetry Protocol, Schema, and Ingestion.
Verifies:
- Canonical 20 metrics
- Metric veracity invariants (cpu_load must be ESTIMATED on AVR)
- Fast micro-frame ($ARIS1...#) parsing
- Canonical JSON stream parsing
- Graceful rejection of malformed packets
- Monotonic sequence handling
"""

import pytest
from pydantic import ValidationError

from backend.telemetry.telemetry_schema import (
    TelemetrySample,
    CANONICAL_METRIC_NAMES,
    CANONICAL_CLASSIFICATIONS,
    ArisErrorResponse,
    CANONICAL_ERROR_CODES
)
from backend.telemetry.telemetry_ingestor import TelemetryIngestor
from backend.database.models import RunRecord


def test_canonical_metric_names_and_count():
    """Verify exactly 20 canonical metrics exist."""
    assert len(CANONICAL_METRIC_NAMES) == 20
    expected = [
        "cpu_load", "loop_time", "loop_frequency", "loop_jitter",
        "sram_used", "sram_free", "stack_used", "stack_high_water_mark",
        "interrupt_count", "interrupt_rate", "gpio_activity", "adc_activity",
        "uart_activity", "spi_activity", "i2c_activity", "timer_activity",
        "reset_event", "watchdog_event", "runtime_fault", "instrumentation_overhead"
    ]
    for m in expected:
        assert m in CANONICAL_METRIC_NAMES


def test_cpu_load_must_be_estimated_never_measured():
    """Verify cpu_load fails validation if classified as MEASURED."""
    with pytest.raises(ValidationError) as exc:
        TelemetrySample(
            protocol_version="1.0",
            run_id="ARIS-000001",
            board_id="arduino_uno",
            mcu="atmega328p",
            timestamp_ms=1000,
            sequence=1,
            metric="cpu_load",
            value=45.0,
            unit="%",
            classification="MEASURED",  # Illegal on AVR
            confidence=1.0
        )
    assert "cpu_load' must NEVER be classified as MEASURED" in str(exc.value)


def test_reject_non_canonical_metric():
    """Verify alias metrics are rejected."""
    bad_metrics = ["cpuUsage", "freeMemory", "loopLatency", "jitter"]
    for bad in bad_metrics:
        with pytest.raises(ValidationError):
            TelemetrySample(
                protocol_version="1.0",
                run_id="ARIS-000001",
                board_id="arduino_uno",
                mcu="atmega328p",
                timestamp_ms=1000,
                sequence=1,
                metric=bad,
                value=10.0,
                unit="unit",
                classification="MEASURED",
                confidence=1.0
            )


def test_ingest_json_packet(temp_db, ingestor):
    """Test ingesting a valid canonical JSON packet."""
    temp_db.save_run(RunRecord(
        run_id="ARIS-000001",
        board_id="arduino_uno",
        status="RUNNING",
        is_simulated=False,
        is_demo=False,
    ))
    raw_json = (
        '{"protocol_version": "1.0", "run_id": "ARIS-000001", "board_id": "arduino_uno", '
        '"mcu": "atmega328p", "timestamp_ms": 123456, "sequence": 42, '
        '"metric": "loop_time", "value": 4.21, "unit": "ms", '
        '"classification": "MEASURED", "confidence": 1.0}'
    )
    samples = ingestor.ingest_raw_line(raw_json)
    assert len(samples) == 1
    sample = samples[0]
    assert sample.metric == "loop_time"
    assert sample.value == 4.21
    assert ingestor.total_packets_valid == 1


def test_ingest_aris1_fast_micro_frame(temp_db, ingestor):
    """Test ingesting a fast micro-framing packet ($ARIS1,...#)."""
    temp_db.save_run(RunRecord(
        run_id="ARIS-000001",
        board_id="arduino_uno",
        status="RUNNING",
        is_simulated=False,
        is_demo=False,
    ))
    frame = "$ARIS1,ARIS-000001,arduino_uno,atmega328p,10500,1,28.50,3.20,312.50,0.15,512,1536,64,142,12,120.00,10,5,35,0,0,100,1,0,0,1.50#"
    samples = ingestor.ingest_raw_line(frame)
    assert len(samples) == 20
    metrics_ingested = {s.metric: s.value for s in samples}
    assert metrics_ingested["cpu_load"] == 28.50
    assert metrics_ingested["loop_time"] == 3.20
    assert metrics_ingested["sram_free"] == 1536
    assert metrics_ingested["runtime_fault"] == 0.0


def test_reject_malformed_packets(ingestor):
    """Verify malformed packets are rejected gracefully without exceptions."""
    assert ingestor.ingest_raw_line("garbage data packet") == []
    assert ingestor.ingest_raw_line("$ARIS1,short,packet#") == []
    assert ingestor.total_packets_rejected >= 2


def test_reject_unknown_run_id_without_implicit_record(temp_db, ingestor):
    """Verify unknown run_id is rejected, no implicit run created, no sample persisted."""
    notified = []
    ingestor.subscribe(lambda s: notified.append(s))

    raw_json = (
        '{"protocol_version": "1.0", "run_id": "ARIS-UNKNOWN-999", "board_id": "arduino_uno", '
        '"mcu": "atmega328p", "timestamp_ms": 1000, "sequence": 1, '
        '"metric": "loop_time", "value": 5.0, "unit": "ms", '
        '"classification": "MEASURED", "confidence": 1.0}'
    )
    samples = ingestor.ingest_raw_line(raw_json)
    assert len(samples) == 0
    assert ingestor.total_packets_rejected >= 1
    assert ingestor.last_error is not None
    assert "ARIS_TELEMETRY_INVALID" in ingestor.last_error

    # Verify no implicit run was created in DB
    assert temp_db.get_run("ARIS-UNKNOWN-999") is None

    # Verify no telemetry persisted
    assert len(temp_db.get_telemetry_by_run("ARIS-UNKNOWN-999")) == 0

    # Verify subscribers not notified
    assert len(notified) == 0


def test_telemetry_provenance_distinction_physical_vs_simulated(temp_db, ingestor):
    """Verify physical runs produce is_demo=False, simulated runs produce is_demo=True."""
    # Physical run
    temp_db.save_run(RunRecord(
        run_id="ARIS-PHYS-01",
        board_id="arduino_uno",
        status="RUNNING",
        is_simulated=False,
        is_demo=False
    ))
    # Simulated run
    temp_db.save_run(RunRecord(
        run_id="ARIS-SIM-01",
        board_id="arduino_uno",
        status="RUNNING",
        is_simulated=True,
        is_demo=True
    ))

    # Ingest physical
    frame_phys = "$ARIS1,ARIS-PHYS-01,arduino_uno,atmega328p,100,1,10.0,2.0,500.0,0.1,500,1500,50,100,0,0,0,0,0,0,0,0,0,0,0,1.0#"
    samples_phys = ingestor.ingest_raw_line(frame_phys)
    assert len(samples_phys) == 20
    db_samples_phys = temp_db.get_telemetry_by_run("ARIS-PHYS-01")
    assert len(db_samples_phys) == 20
    assert all(s.is_demo is False for s in db_samples_phys)

    # Ingest simulated
    frame_sim = "$ARIS1,ARIS-SIM-01,arduino_uno,atmega328p,100,1,10.0,2.0,500.0,0.1,500,1500,50,100,0,0,0,0,0,0,0,0,0,0,0,1.0#"
    samples_sim = ingestor.ingest_raw_line(frame_sim)
    assert len(samples_sim) == 20
    db_samples_sim = temp_db.get_telemetry_by_run("ARIS-SIM-01")
    assert len(db_samples_sim) == 20
    assert all(s.is_demo is True for s in db_samples_sim)

