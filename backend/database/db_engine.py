"""
ARIS Relational Database Engine.
Provides clean SQLite relational storage with thread-safe access, transaction guarantees,
and CRUD utilities for all ARIS domain records:
- Boards
- Firmwares
- Runs
- Telemetry samples
- Findings
- Baselines
- Optimizations
- Experiments
- Validation results
Operates with standard library sqlite3 for zero-friction setup and zero external database dependencies.
"""

import sqlite3
import json
import threading
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from .models import (
    BoardRecord,
    FirmwareRecord,
    TelemetryRecord,
    FindingRecord,
    BaselineRecord,
    BaselineMetricStats,
    OptimizationRecord,
    RunRecord,
    ValidationResultRecord,
    ValidationMetricDelta,
    ExperimentRecord
)


class DatabaseEngine:
    """
    Manages persistent SQLite connection, table migrations, and domain operations.
    Thread-safe implementation with connection pooling / per-thread or locked execution.
    """

    def __init__(self, db_path: str = "aris.db"):
        # Store filesystem path to the database file (or ":memory:" for tests)
        self.db_path = db_path
        # Lock to synchronize write transactions across asynchronous worker threads
        self._lock = threading.Lock()
        # Ensure tables and indices are created immediately
        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        """
        Creates and configures a SQLite connection with WAL journaling and row factories.
        """
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        # Return rows as sqlite3.Row objects to access fields by column name
        conn.row_factory = sqlite3.Row
        # Enable foreign key constraints in SQLite
        conn.execute("PRAGMA foreign_keys = ON;")
        # Enable WAL mode for high concurrency read/write if writing to disk
        if self.db_path != ":memory:":
            conn.execute("PRAGMA journal_mode = WAL;")
        return conn

    def _init_database(self):
        """
        Initializes database schema with exact tables, foreign keys, and indexes.
        """
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()

                # 1. Boards Table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS boards (
                    board_id TEXT PRIMARY KEY,
                    display_name TEXT NOT NULL,
                    mcu TEXT NOT NULL,
                    architecture TEXT NOT NULL,
                    clock_hz INTEGER NOT NULL,
                    flash_bytes INTEGER NOT NULL,
                    sram_bytes INTEGER NOT NULL,
                    eeprom_bytes INTEGER NOT NULL,
                    gpio_count INTEGER NOT NULL,
                    adc_channels INTEGER NOT NULL,
                    uart_count INTEGER NOT NULL,
                    spi_available INTEGER NOT NULL,
                    i2c_available INTEGER NOT NULL,
                    timer_count INTEGER NOT NULL,
                    interrupt_capabilities TEXT NOT NULL
                );
                """)

                # 2. Firmwares Table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS firmwares (
                    firmware_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    source_code TEXT,
                    hex_content TEXT,
                    elf_path TEXT,
                    map_content TEXT,
                    created_at TEXT NOT NULL
                );
                """)

                # 3. Runs Table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    board_id TEXT NOT NULL,
                    firmware_id TEXT,
                    instrumentation_mode TEXT NOT NULL,
                    start_time TEXT,
                    end_time TEXT,
                    status TEXT NOT NULL,
                    is_simulated INTEGER NOT NULL DEFAULT 0,
                    is_demo INTEGER NOT NULL DEFAULT 0,
                    baseline_id TEXT,
                    FOREIGN KEY(board_id) REFERENCES boards(board_id) ON DELETE CASCADE,
                    FOREIGN KEY(firmware_id) REFERENCES firmwares(firmware_id) ON DELETE SET NULL
                );
                """)

                # 4. Telemetry Samples Table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS telemetry_samples (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    protocol_version TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    board_id TEXT NOT NULL,
                    mcu TEXT NOT NULL,
                    timestamp_ms INTEGER NOT NULL,
                    sequence INTEGER NOT NULL,
                    metric TEXT NOT NULL,
                    value REAL NOT NULL,
                    unit TEXT NOT NULL,
                    classification TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    is_demo INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY(run_id) REFERENCES runs(run_id) ON DELETE CASCADE
                );
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_run ON telemetry_samples(run_id);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_metric ON telemetry_samples(metric);")

                # 5. Findings Table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS findings (
                    finding_id TEXT PRIMARY KEY,
                    run_id TEXT,
                    rule_id TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    source_file TEXT NOT NULL,
                    source_line INTEGER NOT NULL,
                    runtime_correlation TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    evidence TEXT NOT NULL,
                    recommended_action TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES runs(run_id) ON DELETE CASCADE
                );
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_findings_run ON findings(run_id);")

                # 6. Baselines Table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS baselines (
                    baseline_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    board_id TEXT NOT NULL,
                    sample_window_ms INTEGER NOT NULL,
                    metrics_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES runs(run_id) ON DELETE CASCADE
                );
                """)

                # 7. Optimizations Table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS optimizations (
                    optimization_id TEXT PRIMARY KEY,
                    finding_id TEXT NOT NULL,
                    run_id TEXT,
                    title TEXT NOT NULL,
                    problem TEXT NOT NULL,
                    source_location TEXT NOT NULL,
                    before_code TEXT NOT NULL,
                    after_code TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    hardware_consideration TEXT NOT NULL,
                    expected_effect TEXT NOT NULL,
                    risk TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    validation_required INTEGER NOT NULL DEFAULT 1,
                    status TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES runs(run_id) ON DELETE SET NULL
                );
                """)

                # 8. Experiments Table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS experiments (
                    experiment_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    board_id TEXT NOT NULL,
                    baseline_run_id TEXT NOT NULL,
                    candidate_run_id TEXT,
                    optimization_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    validation_id TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(board_id) REFERENCES boards(board_id) ON DELETE CASCADE,
                    FOREIGN KEY(baseline_run_id) REFERENCES runs(run_id) ON DELETE CASCADE,
                    FOREIGN KEY(candidate_run_id) REFERENCES runs(run_id) ON DELETE SET NULL,
                    FOREIGN KEY(optimization_id) REFERENCES optimizations(optimization_id) ON DELETE CASCADE
                );
                """)

                # 9. Validation Results Table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS validation_results (
                    validation_id TEXT PRIMARY KEY,
                    experiment_id TEXT NOT NULL,
                    baseline_run_id TEXT NOT NULL,
                    candidate_run_id TEXT NOT NULL,
                    metrics_json TEXT NOT NULL,
                    validation_status TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(experiment_id) REFERENCES experiments(experiment_id) ON DELETE CASCADE
                );
                """)

                conn.commit()
            finally:
                conn.close()

    # -------------------------------------------------------------------------
    # Board Operations
    # -------------------------------------------------------------------------

    def save_board(self, board: BoardRecord) -> None:
        """Saves or updates a hardware board profile record."""
        with self._lock:
            conn = self._get_connection()
            try:
                conn.execute("""
                INSERT OR REPLACE INTO boards (
                    board_id, display_name, mcu, architecture, clock_hz,
                    flash_bytes, sram_bytes, eeprom_bytes, gpio_count,
                    adc_channels, uart_count, spi_available, i2c_available,
                    timer_count, interrupt_capabilities
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    board.board_id,
                    board.display_name,
                    board.mcu,
                    board.architecture,
                    board.clock_hz,
                    board.flash_bytes,
                    board.sram_bytes,
                    board.eeprom_bytes,
                    board.gpio_count,
                    board.adc_channels,
                    board.uart_count,
                    1 if board.spi_available else 0,
                    1 if board.i2c_available else 0,
                    board.timer_count,
                    json.dumps(board.interrupt_capabilities)
                ))
                conn.commit()
            finally:
                conn.close()

    def get_board(self, board_id: str) -> Optional[BoardRecord]:
        """Retrieves a board record by its canonical ID."""
        conn = self._get_connection()
        try:
            row = conn.execute("SELECT * FROM boards WHERE board_id = ?;", (board_id,)).fetchone()
            if not row:
                return None
            return BoardRecord(
                board_id=row["board_id"],
                display_name=row["display_name"],
                mcu=row["mcu"],
                architecture=row["architecture"],
                clock_hz=row["clock_hz"],
                flash_bytes=row["flash_bytes"],
                sram_bytes=row["sram_bytes"],
                eeprom_bytes=row["eeprom_bytes"],
                gpio_count=row["gpio_count"],
                adc_channels=row["adc_channels"],
                uart_count=row["uart_count"],
                spi_available=bool(row["spi_available"]),
                i2c_available=bool(row["i2c_available"]),
                timer_count=row["timer_count"],
                interrupt_capabilities=json.loads(row["interrupt_capabilities"])
            )
        finally:
            conn.close()

    def list_boards(self) -> List[BoardRecord]:
        """Returns all registered target board records."""
        conn = self._get_connection()
        try:
            rows = conn.execute("SELECT * FROM boards ORDER BY board_id ASC;").fetchall()
            return [
                BoardRecord(
                    board_id=row["board_id"],
                    display_name=row["display_name"],
                    mcu=row["mcu"],
                    architecture=row["architecture"],
                    clock_hz=row["clock_hz"],
                    flash_bytes=row["flash_bytes"],
                    sram_bytes=row["sram_bytes"],
                    eeprom_bytes=row["eeprom_bytes"],
                    gpio_count=row["gpio_count"],
                    adc_channels=row["adc_channels"],
                    uart_count=row["uart_count"],
                    spi_available=bool(row["spi_available"]),
                    i2c_available=bool(row["i2c_available"]),
                    timer_count=row["timer_count"],
                    interrupt_capabilities=json.loads(row["interrupt_capabilities"])
                )
                for row in rows
            ]
        finally:
            conn.close()

    # -------------------------------------------------------------------------
    # Firmware Operations
    # -------------------------------------------------------------------------

    def save_firmware(self, fw: FirmwareRecord) -> None:
        """Stores a firmware artifact in the database."""
        with self._lock:
            conn = self._get_connection()
            try:
                conn.execute("""
                INSERT OR REPLACE INTO firmwares (
                    firmware_id, name, source_code, hex_content, elf_path, map_content, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?);
                """, (
                    fw.firmware_id,
                    fw.name,
                    fw.source_code,
                    fw.hex_content,
                    fw.elf_path,
                    fw.map_content,
                    fw.created_at
                ))
                conn.commit()
            finally:
                conn.close()

    def get_firmware(self, firmware_id: str) -> Optional[FirmwareRecord]:
        """Retrieves a firmware record by ID."""
        conn = self._get_connection()
        try:
            row = conn.execute("SELECT * FROM firmwares WHERE firmware_id = ?;", (firmware_id,)).fetchone()
            if not row:
                return None
            return FirmwareRecord(
                firmware_id=row["firmware_id"],
                name=row["name"],
                source_code=row["source_code"],
                hex_content=row["hex_content"],
                elf_path=row["elf_path"],
                map_content=row["map_content"],
                created_at=row["created_at"]
            )
        finally:
            conn.close()

    def list_firmware(self) -> List[FirmwareRecord]:
        """Lists all stored firmware records."""
        conn = self._get_connection()
        try:
            rows = conn.execute("SELECT * FROM firmwares ORDER BY created_at DESC;").fetchall()
            return [
                FirmwareRecord(
                    firmware_id=row["firmware_id"],
                    name=row["name"],
                    source_code=row["source_code"],
                    hex_content=row["hex_content"],
                    elf_path=row["elf_path"],
                    map_content=row["map_content"],
                    created_at=row["created_at"]
                )
                for row in rows
            ]
        finally:
            conn.close()

    # -------------------------------------------------------------------------
    # Run Operations
    # -------------------------------------------------------------------------

    def save_run(self, run: RunRecord) -> None:
        """Saves or updates an execution run."""
        with self._lock:
            conn = self._get_connection()
            try:
                conn.execute("""
                INSERT INTO runs (
                    run_id, board_id, firmware_id, instrumentation_mode,
                    start_time, end_time, status, is_simulated, is_demo, baseline_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(run_id) DO UPDATE SET
                    board_id=excluded.board_id,
                    firmware_id=excluded.firmware_id,
                    instrumentation_mode=excluded.instrumentation_mode,
                    start_time=excluded.start_time,
                    end_time=excluded.end_time,
                    status=excluded.status,
                    is_simulated=excluded.is_simulated,
                    is_demo=excluded.is_demo,
                    baseline_id=excluded.baseline_id;
                """, (
                    run.run_id,
                    run.board_id,
                    run.firmware_id,
                    run.instrumentation_mode,
                    run.start_time,
                    run.end_time,
                    run.status,
                    1 if run.is_simulated else 0,
                    1 if run.is_demo else 0,
                    run.baseline_id
                ))
                conn.commit()
            finally:
                conn.close()

    def get_run(self, run_id: str) -> Optional[RunRecord]:
        """Fetches a run record by its unique run_id."""
        conn = self._get_connection()
        try:
            row = conn.execute("SELECT * FROM runs WHERE run_id = ?;", (run_id,)).fetchone()
            if not row:
                return None
            return RunRecord(
                run_id=row["run_id"],
                board_id=row["board_id"],
                firmware_id=row["firmware_id"],
                instrumentation_mode=row["instrumentation_mode"],
                start_time=row["start_time"],
                end_time=row["end_time"],
                status=row["status"],
                is_simulated=bool(row["is_simulated"]),
                is_demo=bool(row["is_demo"]),
                baseline_id=row["baseline_id"]
            )
        finally:
            conn.close()

    def list_runs(self) -> List[RunRecord]:
        """Lists all execution runs."""
        conn = self._get_connection()
        try:
            rows = conn.execute("SELECT * FROM runs ORDER BY run_id DESC;").fetchall()
            return [
                RunRecord(
                    run_id=row["run_id"],
                    board_id=row["board_id"],
                    firmware_id=row["firmware_id"],
                    instrumentation_mode=row["instrumentation_mode"],
                    start_time=row["start_time"],
                    end_time=row["end_time"],
                    status=row["status"],
                    is_simulated=bool(row["is_simulated"]),
                    is_demo=bool(row["is_demo"]),
                    baseline_id=row["baseline_id"]
                )
                for row in rows
            ]
        finally:
            conn.close()

    # -------------------------------------------------------------------------
    # Telemetry Operations
    # -------------------------------------------------------------------------

    def save_telemetry_sample(self, sample: TelemetryRecord) -> None:
        """Saves a single validated telemetry sample."""
        with self._lock:
            conn = self._get_connection()
            try:
                conn.execute("""
                INSERT INTO telemetry_samples (
                    protocol_version, run_id, board_id, mcu, timestamp_ms,
                    sequence, metric, value, unit, classification, confidence, is_demo
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    sample.protocol_version,
                    sample.run_id,
                    sample.board_id,
                    sample.mcu,
                    sample.timestamp_ms,
                    sample.sequence,
                    sample.metric,
                    sample.value,
                    sample.unit,
                    sample.classification,
                    sample.confidence,
                    1 if sample.is_demo else 0
                ))
                conn.commit()
            finally:
                conn.close()

    def save_telemetry_batch(self, samples: List[TelemetryRecord]) -> None:
        """Efficient batch insertion for telemetry samples."""
        if not samples:
            return
        with self._lock:
            conn = self._get_connection()
            try:
                conn.executemany("""
                INSERT INTO telemetry_samples (
                    protocol_version, run_id, board_id, mcu, timestamp_ms,
                    sequence, metric, value, unit, classification, confidence, is_demo
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, [
                    (
                        s.protocol_version,
                        s.run_id,
                        s.board_id,
                        s.mcu,
                        s.timestamp_ms,
                        s.sequence,
                        s.metric,
                        s.value,
                        s.unit,
                        s.classification,
                        s.confidence,
                        1 if s.is_demo else 0
                    )
                    for s in samples
                ])
                conn.commit()
            finally:
                conn.close()

    def get_telemetry_by_run(self, run_id: str, limit: int = 1000) -> List[TelemetryRecord]:
        """Retrieves stored telemetry samples for a given run ID."""
        conn = self._get_connection()
        try:
            rows = conn.execute("""
            SELECT * FROM telemetry_samples
            WHERE run_id = ?
            ORDER BY timestamp_ms ASC, sequence ASC
            LIMIT ?;
            """, (run_id, limit)).fetchall()
            return [
                TelemetryRecord(
                    id=row["id"],
                    protocol_version=row["protocol_version"],
                    run_id=row["run_id"],
                    board_id=row["board_id"],
                    mcu=row["mcu"],
                    timestamp_ms=row["timestamp_ms"],
                    sequence=row["sequence"],
                    metric=row["metric"],
                    value=row["value"],
                    unit=row["unit"],
                    classification=row["classification"],
                    confidence=row["confidence"],
                    is_demo=bool(row["is_demo"])
                )
                for row in rows
            ]
        finally:
            conn.close()

    # -------------------------------------------------------------------------
    # Finding Operations
    # -------------------------------------------------------------------------

    def save_finding(self, finding: FindingRecord) -> None:
        """Stores a static or correlated analysis finding."""
        with self._lock:
            conn = self._get_connection()
            try:
                conn.execute("""
                INSERT OR REPLACE INTO findings (
                    finding_id, run_id, rule_id, severity, title, description,
                    source_file, source_line, runtime_correlation, confidence,
                    evidence, recommended_action
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    finding.finding_id,
                    finding.run_id,
                    finding.rule_id,
                    finding.severity,
                    finding.title,
                    finding.description,
                    finding.source_file,
                    finding.source_line,
                    finding.runtime_correlation,
                    finding.confidence,
                    json.dumps(finding.evidence),
                    finding.recommended_action
                ))
                conn.commit()
            finally:
                conn.close()

    def get_findings_by_run(self, run_id: str) -> List[FindingRecord]:
        """Retrieves all findings recorded for a specific run ID."""
        conn = self._get_connection()
        try:
            rows = conn.execute("SELECT * FROM findings WHERE run_id = ?;", (run_id,)).fetchall()
            return [
                FindingRecord(
                    finding_id=row["finding_id"],
                    run_id=row["run_id"],
                    rule_id=row["rule_id"],
                    severity=row["severity"],
                    title=row["title"],
                    description=row["description"],
                    source_file=row["source_file"],
                    source_line=row["source_line"],
                    runtime_correlation=row["runtime_correlation"],
                    confidence=row["confidence"],
                    evidence=json.loads(row["evidence"]),
                    recommended_action=row["recommended_action"]
                )
                for row in rows
            ]
        finally:
            conn.close()

    # -------------------------------------------------------------------------
    # Baseline Operations
    # -------------------------------------------------------------------------

    def save_baseline(self, baseline: BaselineRecord) -> None:
        """Stores a calculated baseline profile."""
        with self._lock:
            conn = self._get_connection()
            try:
                # Serialize metrics stats mapping into JSON string
                metrics_dump = {
                    k: v.model_dump() for k, v in baseline.metrics.items()
                }
                conn.execute("""
                INSERT OR REPLACE INTO baselines (
                    baseline_id, run_id, board_id, sample_window_ms, metrics_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?);
                """, (
                    baseline.baseline_id,
                    baseline.run_id,
                    baseline.board_id,
                    baseline.sample_window_ms,
                    json.dumps(metrics_dump),
                    baseline.created_at
                ))
                conn.commit()
            finally:
                conn.close()

    def get_baseline(self, baseline_id: str) -> Optional[BaselineRecord]:
        """Retrieves a baseline record by its unique ID."""
        conn = self._get_connection()
        try:
            row = conn.execute("SELECT * FROM baselines WHERE baseline_id = ?;", (baseline_id,)).fetchone()
            if not row:
                return None
            raw_metrics = json.loads(row["metrics_json"])
            metrics = {
                k: BaselineMetricStats(**v) for k, v in raw_metrics.items()
            }
            return BaselineRecord(
                baseline_id=row["baseline_id"],
                run_id=row["run_id"],
                board_id=row["board_id"],
                sample_window_ms=row["sample_window_ms"],
                metrics=metrics,
                created_at=row["created_at"]
            )
        finally:
            conn.close()

    # -------------------------------------------------------------------------
    # Optimization Candidate Operations
    # -------------------------------------------------------------------------

    def save_optimization(self, opt: OptimizationRecord) -> None:
        """Stores an optimization candidate."""
        with self._lock:
            conn = self._get_connection()
            try:
                conn.execute("""
                INSERT INTO optimizations (
                    optimization_id, finding_id, run_id, title, problem,
                    source_location, before_code, after_code, reason,
                    hardware_consideration, expected_effect, risk, confidence,
                    validation_required, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(optimization_id) DO UPDATE SET
                    finding_id=excluded.finding_id,
                    run_id=excluded.run_id,
                    title=excluded.title,
                    problem=excluded.problem,
                    source_location=excluded.source_location,
                    before_code=excluded.before_code,
                    after_code=excluded.after_code,
                    reason=excluded.reason,
                    hardware_consideration=excluded.hardware_consideration,
                    expected_effect=excluded.expected_effect,
                    risk=excluded.risk,
                    confidence=excluded.confidence,
                    validation_required=excluded.validation_required,
                    status=excluded.status;
                """, (
                    opt.optimization_id,
                    opt.finding_id,
                    opt.run_id,
                    opt.title,
                    opt.problem,
                    json.dumps(opt.source_location),
                    opt.before_code,
                    opt.after_code,
                    opt.reason,
                    opt.hardware_consideration,
                    json.dumps(opt.expected_effect),
                    opt.risk,
                    opt.confidence,
                    1 if opt.validation_required else 0,
                    opt.status
                ))
                conn.commit()
            finally:
                conn.close()

    def get_optimization(self, optimization_id: str) -> Optional[OptimizationRecord]:
        """Retrieves an optimization candidate by ID."""
        conn = self._get_connection()
        try:
            row = conn.execute("SELECT * FROM optimizations WHERE optimization_id = ?;", (optimization_id,)).fetchone()
            if not row:
                return None
            return OptimizationRecord(
                optimization_id=row["optimization_id"],
                finding_id=row["finding_id"],
                run_id=row["run_id"],
                title=row["title"],
                problem=row["problem"],
                source_location=json.loads(row["source_location"]),
                before_code=row["before_code"],
                after_code=row["after_code"],
                reason=row["reason"],
                hardware_consideration=row["hardware_consideration"],
                expected_effect=json.loads(row["expected_effect"]),
                risk=row["risk"],
                confidence=row["confidence"],
                validation_required=bool(row["validation_required"]),
                status=row["status"]
            )
        finally:
            conn.close()

    def get_optimizations_by_run(self, run_id: str) -> List[OptimizationRecord]:
        """Retrieves optimization candidates associated with a run."""
        conn = self._get_connection()
        try:
            rows = conn.execute("SELECT * FROM optimizations WHERE run_id = ?;", (run_id,)).fetchall()
            return [
                OptimizationRecord(
                    optimization_id=row["optimization_id"],
                    finding_id=row["finding_id"],
                    run_id=row["run_id"],
                    title=row["title"],
                    problem=row["problem"],
                    source_location=json.loads(row["source_location"]),
                    before_code=row["before_code"],
                    after_code=row["after_code"],
                    reason=row["reason"],
                    hardware_consideration=row["hardware_consideration"],
                    expected_effect=json.loads(row["expected_effect"]),
                    risk=row["risk"],
                    confidence=row["confidence"],
                    validation_required=bool(row["validation_required"]),
                    status=row["status"]
                )
                for row in rows
            ]
        finally:
            conn.close()

    # -------------------------------------------------------------------------
    # Experiment & Validation Operations
    # -------------------------------------------------------------------------

    def save_experiment(self, exp: ExperimentRecord) -> None:
        """Stores or updates an experiment record."""
        with self._lock:
            conn = self._get_connection()
            try:
                conn.execute("""
                INSERT INTO experiments (
                    experiment_id, title, board_id, baseline_run_id,
                    candidate_run_id, optimization_id, status, validation_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(experiment_id) DO UPDATE SET
                    title=excluded.title,
                    board_id=excluded.board_id,
                    baseline_run_id=excluded.baseline_run_id,
                    candidate_run_id=excluded.candidate_run_id,
                    optimization_id=excluded.optimization_id,
                    status=excluded.status,
                    validation_id=excluded.validation_id,
                    created_at=excluded.created_at;
                """, (
                    exp.experiment_id,
                    exp.title,
                    exp.board_id,
                    exp.baseline_run_id,
                    exp.candidate_run_id,
                    exp.optimization_id,
                    exp.status,
                    exp.validation_id,
                    exp.created_at
                ))
                conn.commit()
            finally:
                conn.close()

    def get_experiment(self, experiment_id: str) -> Optional[ExperimentRecord]:
        """Retrieves an experiment by ID."""
        conn = self._get_connection()
        try:
            row = conn.execute("SELECT * FROM experiments WHERE experiment_id = ?;", (experiment_id,)).fetchone()
            if not row:
                return None
            return ExperimentRecord(
                experiment_id=row["experiment_id"],
                title=row["title"],
                board_id=row["board_id"],
                baseline_run_id=row["baseline_run_id"],
                candidate_run_id=row["candidate_run_id"],
                optimization_id=row["optimization_id"],
                status=row["status"],
                validation_id=row["validation_id"],
                created_at=row["created_at"]
            )
        finally:
            conn.close()

    def list_experiments(self) -> List[ExperimentRecord]:
        """Lists all optimization experiments."""
        conn = self._get_connection()
        try:
            rows = conn.execute("SELECT * FROM experiments ORDER BY created_at DESC;").fetchall()
            return [
                ExperimentRecord(
                    experiment_id=row["experiment_id"],
                    title=row["title"],
                    board_id=row["board_id"],
                    baseline_run_id=row["baseline_run_id"],
                    candidate_run_id=row["candidate_run_id"],
                    optimization_id=row["optimization_id"],
                    status=row["status"],
                    validation_id=row["validation_id"],
                    created_at=row["created_at"]
                )
                for row in rows
            ]
        finally:
            conn.close()

    def save_validation_result(self, val: ValidationResultRecord) -> None:
        """Stores a validation result."""
        with self._lock:
            conn = self._get_connection()
            try:
                metrics_dump = {
                    k: v.model_dump() for k, v in val.metrics.items()
                }
                conn.execute("""
                INSERT OR REPLACE INTO validation_results (
                    validation_id, experiment_id, baseline_run_id, candidate_run_id,
                    metrics_json, validation_status, reason, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    val.validation_id,
                    val.experiment_id,
                    val.baseline_run_id,
                    val.candidate_run_id,
                    json.dumps(metrics_dump),
                    val.validation_status,
                    val.reason,
                    val.created_at
                ))
                conn.commit()
            finally:
                conn.close()

    def get_validation_result(self, validation_id: str) -> Optional[ValidationResultRecord]:
        """Retrieves a validation result by ID."""
        conn = self._get_connection()
        try:
            row = conn.execute("SELECT * FROM validation_results WHERE validation_id = ?;", (validation_id,)).fetchone()
            if not row:
                return None
            raw_metrics = json.loads(row["metrics_json"])
            metrics = {
                k: ValidationMetricDelta(**v) for k, v in raw_metrics.items()
            }
            return ValidationResultRecord(
                validation_id=row["validation_id"],
                experiment_id=row["experiment_id"],
                baseline_run_id=row["baseline_run_id"],
                candidate_run_id=row["candidate_run_id"],
                metrics=metrics,
                validation_status=row["validation_status"],
                reason=row["reason"],
                created_at=row["created_at"]
            )
        finally:
            conn.close()
