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
        self._mem_conn = sqlite3.connect(":memory:", check_same_thread=False) if db_path == ":memory:" else None
        # Ensure tables and indices are created immediately
        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        """
        Creates and configures a SQLite connection with WAL journaling and row factories.
        """
        if self._mem_conn is not None:
            conn = self._mem_conn
        else:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
        # Return rows as sqlite3.Row objects to access fields by column name
        conn.row_factory = sqlite3.Row
        # Enable foreign key constraints in SQLite
        conn.execute("PRAGMA foreign_keys = ON;")
        # Enable WAL mode for high concurrency read/write if writing to disk
        if self.db_path != ":memory:":
            conn.execute("PRAGMA journal_mode = WAL;")
        return conn

    def _close_connection(self, conn: sqlite3.Connection) -> None:
        """Closes connection only if not using shared in-memory connection."""
        if self._mem_conn is None:
            conn.close()

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
                    mcu TEXT,
                    architecture TEXT,
                    clock_hz INTEGER,
                    flash_bytes INTEGER,
                    sram_bytes INTEGER,
                    eeprom_bytes INTEGER,
                    gpio_count INTEGER,
                    adc_channels INTEGER,
                    uart_count INTEGER,
                    spi_available INTEGER,
                    i2c_available INTEGER,
                    timer_count INTEGER,
                    interrupt_capabilities TEXT NOT NULL,
                    fqbn TEXT,
                    build_toolchain TEXT,
                    supported INTEGER NOT NULL DEFAULT 1,
                    profile_source TEXT NOT NULL DEFAULT 'EXACT_PROFILE',
                    confidence TEXT NOT NULL DEFAULT 'HIGH',
                    unavailable_properties TEXT NOT NULL DEFAULT '[]',
                    platform TEXT,
                    capabilities TEXT NOT NULL DEFAULT '{}'
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

                # 10. Hypotheses Table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS hypotheses (
                    hypothesis_id TEXT PRIMARY KEY,
                    target_metric TEXT NOT NULL,
                    predicted_effect TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    evidence_references TEXT NOT NULL,
                    supporting_static_evidence TEXT NOT NULL,
                    supporting_runtime_evidence TEXT NOT NULL,
                    hardware_constraints TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """)

                # 11. Experiment Manifests Table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS experiment_manifests (
                    manifest_id TEXT PRIMARY KEY,
                    experiment_id TEXT NOT NULL,
                    board_id TEXT NOT NULL,
                    mcu TEXT,
                    architecture TEXT,
                    fqbn TEXT,
                    firmware_hash TEXT NOT NULL,
                    candidate_hash TEXT NOT NULL,
                    compiler_toolchain TEXT NOT NULL,
                    runtime_version TEXT NOT NULL,
                    instrumentation_mode TEXT NOT NULL,
                    selected_measurements TEXT NOT NULL,
                    duration_seconds REAL NOT NULL,
                    sample_count INTEGER NOT NULL,
                    experiment_conditions TEXT NOT NULL,
                    prediction TEXT NOT NULL,
                    actual_result TEXT NOT NULL,
                    validation_result TEXT,
                    created_at TEXT NOT NULL
                );
                """)

                # 12. Provenance Lineage Table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS provenance_lineages (
                    lineage_id TEXT PRIMARY KEY,
                    firmware_id TEXT NOT NULL,
                    analysis_run_id TEXT,
                    baseline_run_id TEXT,
                    finding_ids TEXT NOT NULL,
                    hypothesis_id TEXT,
                    candidate_id TEXT,
                    experiment_id TEXT,
                    manifest_id TEXT,
                    candidate_run_id TEXT,
                    validation_id TEXT,
                    created_at TEXT NOT NULL
                );
                """)

                # 13. Predictions Table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS predictions (
                    prediction_id TEXT PRIMARY KEY,
                    experiment_id TEXT NOT NULL,
                    candidate_id TEXT NOT NULL,
                    firmware_id TEXT NOT NULL,
                    baseline_id TEXT,
                    board_id TEXT NOT NULL,
                    mcu TEXT,
                    architecture TEXT,
                    fqbn TEXT,
                    hardware_profile_hash TEXT,
                    optimization_category TEXT NOT NULL,
                    target_metric TEXT NOT NULL,
                    predicted_value REAL,
                    predicted_delta_pct REAL NOT NULL,
                    lower_bound_pct REAL NOT NULL,
                    upper_bound_pct REAL NOT NULL,
                    confidence REAL NOT NULL,
                    prediction_source TEXT NOT NULL,
                    evidence_references TEXT NOT NULL,
                    calibration_state TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """)

                # 14. Measurement Outcomes Table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS measurement_outcomes (
                    outcome_id TEXT PRIMARY KEY,
                    prediction_id TEXT NOT NULL,
                    experiment_id TEXT NOT NULL,
                    target_metric TEXT NOT NULL,
                    actual_value REAL NOT NULL,
                    actual_delta_pct REAL NOT NULL,
                    confidence_interval TEXT,
                    sample_count INTEGER NOT NULL,
                    variance REAL NOT NULL,
                    measurement_method TEXT NOT NULL,
                    instrumentation_config TEXT NOT NULL,
                    measurement_overhead_us REAL,
                    telemetry_provenance TEXT NOT NULL,
                    validation_status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """)

                # 15. Prediction Errors Table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS prediction_errors (
                    error_id TEXT PRIMARY KEY,
                    prediction_id TEXT NOT NULL,
                    outcome_id TEXT NOT NULL,
                    target_metric TEXT NOT NULL,
                    predicted_delta_pct REAL NOT NULL,
                    actual_delta_pct REAL NOT NULL,
                    signed_error_pp REAL NOT NULL,
                    absolute_error_pp REAL NOT NULL,
                    relative_error_pct REAL,
                    directional_match INTEGER NOT NULL,
                    is_outlier INTEGER NOT NULL,
                    outlier_reason TEXT,
                    created_at TEXT NOT NULL
                );
                """)

                # 16. Experiment Memory Table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS experiment_memories (
                    memory_id TEXT PRIMARY KEY,
                    experiment_id TEXT NOT NULL,
                    candidate_id TEXT NOT NULL,
                    board_id TEXT NOT NULL,
                    mcu TEXT NOT NULL,
                    architecture TEXT NOT NULL,
                    fqbn TEXT,
                    compiler_toolchain TEXT NOT NULL,
                    optimization_category TEXT NOT NULL,
                    target_metric TEXT NOT NULL,
                    predicted_delta_pct REAL NOT NULL,
                    actual_delta_pct REAL NOT NULL,
                    signed_error_pp REAL NOT NULL,
                    telemetry_provenance TEXT NOT NULL,
                    validation_status TEXT NOT NULL,
                    trade_off_metrics TEXT NOT NULL,
                    is_outlier INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                );
                """)

                # Migration / column checks for dynamic board discovery
                cursor.execute("PRAGMA table_info(boards);")
                existing_cols = {col["name"] for col in cursor.fetchall()}
                new_columns = [
                    ("fqbn", "TEXT"),
                    ("build_toolchain", "TEXT DEFAULT 'avr-gcc'"),
                    ("supported", "INTEGER DEFAULT 1"),
                    ("profile_source", "TEXT DEFAULT 'EXACT_PROFILE'"),
                    ("confidence", "TEXT DEFAULT 'HIGH'"),
                    ("unavailable_properties", "TEXT DEFAULT '[]'"),
                    ("platform", "TEXT"),
                    ("capabilities", "TEXT DEFAULT '{}'")
                ]
                for col_name, col_def in new_columns:
                    if col_name not in existing_cols:
                        cursor.execute(f"ALTER TABLE boards ADD COLUMN {col_name} {col_def};")

                conn.commit()
            finally:
                self._close_connection(conn)

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
                    timer_count, interrupt_capabilities, fqbn, build_toolchain,
                    supported, profile_source, confidence, unavailable_properties,
                    platform, capabilities
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
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
                    1 if board.spi_available is True else (0 if board.spi_available is False else None),
                    1 if board.i2c_available is True else (0 if board.i2c_available is False else None),
                    board.timer_count,
                    json.dumps(board.interrupt_capabilities),
                    board.fqbn,
                    board.build_toolchain,
                    1 if board.supported else 0,
                    board.profile_source,
                    board.confidence,
                    json.dumps(board.unavailable_properties),
                    board.platform,
                    json.dumps(board.capabilities)
                ))
                conn.commit()
            finally:
                self._close_connection(conn)

    def _row_to_board_record(self, row: sqlite3.Row) -> BoardRecord:
        """Helper to safely construct BoardRecord from sqlite3.Row."""
        row_keys = set(row.keys())
        interrupts = []
        if "interrupt_capabilities" in row_keys and row["interrupt_capabilities"]:
            try:
                interrupts = json.loads(row["interrupt_capabilities"])
            except Exception:
                interrupts = []

        unavail = []
        if "unavailable_properties" in row_keys and row["unavailable_properties"]:
            try:
                unavail = json.loads(row["unavailable_properties"])
            except Exception:
                unavail = []

        caps = {}
        if "capabilities" in row_keys and row["capabilities"]:
            try:
                caps = json.loads(row["capabilities"])
            except Exception:
                caps = {}

        spi_val = row["spi_available"]
        spi_available = bool(spi_val) if spi_val is not None else None
        i2c_val = row["i2c_available"]
        i2c_available = bool(i2c_val) if i2c_val is not None else None

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
            spi_available=spi_available,
            i2c_available=i2c_available,
            timer_count=row["timer_count"],
            interrupt_capabilities=interrupts,
            fqbn=row["fqbn"] if "fqbn" in row_keys else "",
            build_toolchain=row["build_toolchain"] if "build_toolchain" in row_keys and row["build_toolchain"] else "avr-gcc",
            supported=bool(row["supported"]) if "supported" in row_keys and row["supported"] is not None else True,
            profile_source=row["profile_source"] if "profile_source" in row_keys and row["profile_source"] else "EXACT_PROFILE",
            confidence=row["confidence"] if "confidence" in row_keys and row["confidence"] else "HIGH",
            unavailable_properties=unavail,
            platform=row["platform"] if "platform" in row_keys else None,
            capabilities=caps
        )

    def get_board(self, board_id: str) -> Optional[BoardRecord]:
        """Retrieves a board record by its canonical or dynamic ID."""
        conn = self._get_connection()
        try:
            row = conn.execute("SELECT * FROM boards WHERE board_id = ?;", (board_id,)).fetchone()
            if not row:
                return None
            return self._row_to_board_record(row)
        finally:
            self._close_connection(conn)

    def list_boards(self) -> List[BoardRecord]:
        """Returns all registered target board records."""
        conn = self._get_connection()
        try:
            rows = conn.execute("SELECT * FROM boards ORDER BY board_id ASC;").fetchall()
            return [self._row_to_board_record(row) for row in rows]
        finally:
            self._close_connection(conn)

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
                self._close_connection(conn)

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
            self._close_connection(conn)

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
            self._close_connection(conn)

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
                self._close_connection(conn)

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
            self._close_connection(conn)

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
            self._close_connection(conn)

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
                self._close_connection(conn)

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
                self._close_connection(conn)

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
            self._close_connection(conn)

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
                self._close_connection(conn)

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
            self._close_connection(conn)

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
                self._close_connection(conn)

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
            self._close_connection(conn)

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
                self._close_connection(conn)

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
            self._close_connection(conn)

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
            self._close_connection(conn)

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
                self._close_connection(conn)

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
            self._close_connection(conn)

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
            self._close_connection(conn)

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
                self._close_connection(conn)

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
            self._close_connection(conn)

    # -------------------------------------------------------------------------
    # Hardware Experiment Manifest, Hypothesis & Lineage Operations
    # -------------------------------------------------------------------------

    def save_hypothesis(self, hyp: Any) -> None:
        """Stores or updates a performance hypothesis."""
        with self._lock:
            conn = self._get_connection()
            try:
                conn.execute("""
                INSERT OR REPLACE INTO hypotheses (
                    hypothesis_id, target_metric, predicted_effect, confidence,
                    evidence_references, supporting_static_evidence,
                    supporting_runtime_evidence, hardware_constraints, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    hyp.hypothesis_id,
                    hyp.target_metric,
                    hyp.predicted_effect,
                    hyp.confidence,
                    json.dumps(hyp.evidence_references),
                    json.dumps(hyp.supporting_static_evidence),
                    json.dumps(hyp.supporting_runtime_evidence),
                    json.dumps(hyp.hardware_constraints),
                    hyp.status,
                    hyp.created_at
                ))
                conn.commit()
            finally:
                self._close_connection(conn)

    def get_hypothesis(self, hypothesis_id: str) -> Optional[Any]:
        """Retrieves a performance hypothesis by ID."""
        conn = self._get_connection()
        try:
            row = conn.execute("SELECT * FROM hypotheses WHERE hypothesis_id = ?;", (hypothesis_id,)).fetchone()
            if not row:
                return None
            from backend.experiments.manifest_models import PerformanceHypothesis
            return PerformanceHypothesis(
                hypothesis_id=row["hypothesis_id"],
                target_metric=row["target_metric"],
                predicted_effect=row["predicted_effect"],
                confidence=row["confidence"],
                evidence_references=json.loads(row["evidence_references"]),
                supporting_static_evidence=json.loads(row["supporting_static_evidence"]),
                supporting_runtime_evidence=json.loads(row["supporting_runtime_evidence"]),
                hardware_constraints=json.loads(row["hardware_constraints"]),
                status=row["status"],
                created_at=row["created_at"]
            )
        finally:
            self._close_connection(conn)

    def save_manifest(self, manifest: Any) -> None:
        """Stores or updates a reproducible experiment manifest."""
        with self._lock:
            conn = self._get_connection()
            try:
                conn.execute("""
                INSERT OR REPLACE INTO experiment_manifests (
                    manifest_id, experiment_id, board_id, mcu, architecture, fqbn,
                    firmware_hash, candidate_hash, compiler_toolchain, runtime_version,
                    instrumentation_mode, selected_measurements, duration_seconds,
                    sample_count, experiment_conditions, prediction, actual_result,
                    validation_result, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    manifest.manifest_id,
                    manifest.experiment_id,
                    manifest.board_id,
                    manifest.mcu,
                    manifest.architecture,
                    manifest.fqbn,
                    manifest.firmware_hash,
                    manifest.candidate_hash,
                    manifest.compiler_toolchain,
                    manifest.runtime_version,
                    manifest.instrumentation_mode,
                    json.dumps(manifest.selected_measurements),
                    manifest.duration_seconds,
                    manifest.sample_count,
                    json.dumps(manifest.experiment_conditions),
                    json.dumps(manifest.prediction),
                    json.dumps(manifest.actual_result),
                    manifest.validation_result,
                    manifest.created_at
                ))
                conn.commit()
            finally:
                self._close_connection(conn)

    def get_manifest(self, manifest_id: str) -> Optional[Any]:
        """Retrieves an experiment manifest by manifest ID."""
        conn = self._get_connection()
        try:
            row = conn.execute("SELECT * FROM experiment_manifests WHERE manifest_id = ?;", (manifest_id,)).fetchone()
            if not row:
                return None
            from backend.experiments.manifest_models import ExperimentManifest
            return ExperimentManifest(
                manifest_id=row["manifest_id"],
                experiment_id=row["experiment_id"],
                board_id=row["board_id"],
                mcu=row["mcu"],
                architecture=row["architecture"],
                fqbn=row["fqbn"],
                firmware_hash=row["firmware_hash"],
                candidate_hash=row["candidate_hash"],
                compiler_toolchain=row["compiler_toolchain"],
                runtime_version=row["runtime_version"],
                instrumentation_mode=row["instrumentation_mode"],
                selected_measurements=json.loads(row["selected_measurements"]),
                duration_seconds=row["duration_seconds"],
                sample_count=row["sample_count"],
                experiment_conditions=json.loads(row["experiment_conditions"]),
                prediction=json.loads(row["prediction"]),
                actual_result=json.loads(row["actual_result"]),
                validation_result=row["validation_result"],
                created_at=row["created_at"]
            )
        finally:
            self._close_connection(conn)

    def get_manifest_by_experiment(self, experiment_id: str) -> Optional[Any]:
        """Retrieves an experiment manifest associated with an experiment ID."""
        conn = self._get_connection()
        try:
            row = conn.execute("SELECT * FROM experiment_manifests WHERE experiment_id = ?;", (experiment_id,)).fetchone()
            if not row:
                return None
            from backend.experiments.manifest_models import ExperimentManifest
            return ExperimentManifest(
                manifest_id=row["manifest_id"],
                experiment_id=row["experiment_id"],
                board_id=row["board_id"],
                mcu=row["mcu"],
                architecture=row["architecture"],
                fqbn=row["fqbn"],
                firmware_hash=row["firmware_hash"],
                candidate_hash=row["candidate_hash"],
                compiler_toolchain=row["compiler_toolchain"],
                runtime_version=row["runtime_version"],
                instrumentation_mode=row["instrumentation_mode"],
                selected_measurements=json.loads(row["selected_measurements"]),
                duration_seconds=row["duration_seconds"],
                sample_count=row["sample_count"],
                experiment_conditions=json.loads(row["experiment_conditions"]),
                prediction=json.loads(row["prediction"]),
                actual_result=json.loads(row["actual_result"]),
                validation_result=row["validation_result"],
                created_at=row["created_at"]
            )
        finally:
            self._close_connection(conn)

    def save_lineage(self, lineage: Any) -> None:
        """Stores or updates provenance audit lineage."""
        with self._lock:
            conn = self._get_connection()
            try:
                conn.execute("""
                INSERT OR REPLACE INTO provenance_lineages (
                    lineage_id, firmware_id, analysis_run_id, baseline_run_id,
                    finding_ids, hypothesis_id, candidate_id, experiment_id,
                    manifest_id, candidate_run_id, validation_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    lineage.lineage_id,
                    lineage.firmware_id,
                    lineage.analysis_run_id,
                    lineage.baseline_run_id,
                    json.dumps(lineage.finding_ids),
                    lineage.hypothesis_id,
                    lineage.candidate_id,
                    lineage.experiment_id,
                    lineage.manifest_id,
                    lineage.candidate_run_id,
                    lineage.validation_id,
                    lineage.created_at
                ))
                conn.commit()
            finally:
                self._close_connection(conn)

    def get_lineage(self, lineage_id: str) -> Optional[Any]:
        """Retrieves provenance lineage by lineage ID."""
        conn = self._get_connection()
        try:
            row = conn.execute("SELECT * FROM provenance_lineages WHERE lineage_id = ?;", (lineage_id,)).fetchone()
            if not row:
                return None
            from backend.experiments.manifest_models import ProvenanceLineage
            return ProvenanceLineage(
                lineage_id=row["lineage_id"],
                firmware_id=row["firmware_id"],
                analysis_run_id=row["analysis_run_id"],
                baseline_run_id=row["baseline_run_id"],
                finding_ids=json.loads(row["finding_ids"]),
                hypothesis_id=row["hypothesis_id"],
                candidate_id=row["candidate_id"],
                experiment_id=row["experiment_id"],
                manifest_id=row["manifest_id"],
                candidate_run_id=row["candidate_run_id"],
                validation_id=row["validation_id"],
                created_at=row["created_at"]
            )
        finally:
            self._close_connection(conn)

    # -------------------------------------------------------------------------
    # Prediction, Outcome, Error & Experiment Memory Operations
    # -------------------------------------------------------------------------

    def save_prediction(self, pred: Any) -> None:
        """Stores or updates a PredictionRecord."""
        with self._lock:
            conn = self._get_connection()
            try:
                conn.execute("""
                INSERT OR REPLACE INTO predictions (
                    prediction_id, experiment_id, candidate_id, firmware_id,
                    baseline_id, board_id, mcu, architecture, fqbn,
                    hardware_profile_hash, optimization_category, target_metric,
                    predicted_value, predicted_delta_pct, lower_bound_pct,
                    upper_bound_pct, confidence, prediction_source,
                    evidence_references, calibration_state, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    pred.prediction_id, pred.experiment_id, pred.candidate_id, pred.firmware_id,
                    pred.baseline_id, pred.board_id, pred.mcu, pred.architecture, pred.fqbn,
                    pred.hardware_profile_hash, pred.optimization_category, pred.target_metric,
                    pred.predicted_value, pred.predicted_delta_pct, pred.lower_bound_pct,
                    pred.upper_bound_pct, pred.confidence, pred.prediction_source,
                    json.dumps(pred.evidence_references), pred.calibration_state, pred.created_at
                ))
                conn.commit()
            finally:
                self._close_connection(conn)

    def get_prediction(self, prediction_id: str) -> Optional[Any]:
        """Retrieves a PredictionRecord by ID."""
        conn = self._get_connection()
        try:
            row = conn.execute("SELECT * FROM predictions WHERE prediction_id = ?;", (prediction_id,)).fetchone()
            if not row:
                return None
            from backend.experiments.calibration_models import PredictionRecord
            return PredictionRecord(
                prediction_id=row["prediction_id"],
                experiment_id=row["experiment_id"],
                candidate_id=row["candidate_id"],
                firmware_id=row["firmware_id"],
                baseline_id=row["baseline_id"],
                board_id=row["board_id"],
                mcu=row["mcu"],
                architecture=row["architecture"],
                fqbn=row["fqbn"],
                hardware_profile_hash=row["hardware_profile_hash"],
                optimization_category=row["optimization_category"],
                target_metric=row["target_metric"],
                predicted_value=row["predicted_value"],
                predicted_delta_pct=row["predicted_delta_pct"],
                lower_bound_pct=row["lower_bound_pct"],
                upper_bound_pct=row["upper_bound_pct"],
                confidence=row["confidence"],
                prediction_source=row["prediction_source"],
                evidence_references=json.loads(row["evidence_references"]),
                calibration_state=row["calibration_state"],
                created_at=row["created_at"]
            )
        finally:
            self._close_connection(conn)

    def save_outcome(self, outcome: Any) -> None:
        """Stores a MeasurementOutcome."""
        with self._lock:
            conn = self._get_connection()
            try:
                conn.execute("""
                INSERT OR REPLACE INTO measurement_outcomes (
                    outcome_id, prediction_id, experiment_id, target_metric,
                    actual_value, actual_delta_pct, confidence_interval,
                    sample_count, variance, measurement_method,
                    instrumentation_config, measurement_overhead_us,
                    telemetry_provenance, validation_status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    outcome.outcome_id, outcome.prediction_id, outcome.experiment_id, outcome.target_metric,
                    outcome.actual_value, outcome.actual_delta_pct,
                    json.dumps(outcome.confidence_interval) if outcome.confidence_interval else None,
                    outcome.sample_count, outcome.variance, outcome.measurement_method,
                    outcome.instrumentation_config, outcome.measurement_overhead_us,
                    outcome.telemetry_provenance, outcome.validation_status, outcome.created_at
                ))
                conn.commit()
            finally:
                self._close_connection(conn)

    def get_outcome(self, outcome_id: str) -> Optional[Any]:
        """Retrieves a MeasurementOutcome by ID."""
        conn = self._get_connection()
        try:
            row = conn.execute("SELECT * FROM measurement_outcomes WHERE outcome_id = ?;", (outcome_id,)).fetchone()
            if not row:
                return None
            from backend.experiments.calibration_models import MeasurementOutcome
            return MeasurementOutcome(
                outcome_id=row["outcome_id"],
                prediction_id=row["prediction_id"],
                experiment_id=row["experiment_id"],
                target_metric=row["target_metric"],
                actual_value=row["actual_value"],
                actual_delta_pct=row["actual_delta_pct"],
                confidence_interval=json.loads(row["confidence_interval"]) if row["confidence_interval"] else None,
                sample_count=row["sample_count"],
                variance=row["variance"],
                measurement_method=row["measurement_method"],
                instrumentation_config=row["instrumentation_config"],
                measurement_overhead_us=row["measurement_overhead_us"],
                telemetry_provenance=row["telemetry_provenance"],
                validation_status=row["validation_status"],
                created_at=row["created_at"]
            )
        finally:
            self._close_connection(conn)

    def save_prediction_error(self, err: Any) -> None:
        """Stores a PredictionError record."""
        with self._lock:
            conn = self._get_connection()
            try:
                conn.execute("""
                INSERT OR REPLACE INTO prediction_errors (
                    error_id, prediction_id, outcome_id, target_metric,
                    predicted_delta_pct, actual_delta_pct, signed_error_pp,
                    absolute_error_pp, relative_error_pct, directional_match,
                    is_outlier, outlier_reason, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    err.error_id, err.prediction_id, err.outcome_id, err.target_metric,
                    err.predicted_delta_pct, err.actual_delta_pct, err.signed_error_pp,
                    err.absolute_error_pp, err.relative_error_pct,
                    1 if err.directional_match else 0,
                    1 if err.is_outlier else 0,
                    err.outlier_reason, err.created_at
                ))
                conn.commit()
            finally:
                self._close_connection(conn)

    def save_memory_record(self, mem: Any) -> None:
        """Stores or updates an ExperimentMemoryRecord."""
        with self._lock:
            conn = self._get_connection()
            try:
                conn.execute("""
                INSERT OR REPLACE INTO experiment_memories (
                    memory_id, experiment_id, candidate_id, board_id, mcu,
                    architecture, fqbn, compiler_toolchain, optimization_category,
                    target_metric, predicted_delta_pct, actual_delta_pct,
                    signed_error_pp, telemetry_provenance, validation_status,
                    trade_off_metrics, is_outlier, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    mem.memory_id, mem.experiment_id, mem.candidate_id, mem.board_id, mem.mcu,
                    mem.architecture, mem.fqbn, mem.compiler_toolchain, mem.optimization_category,
                    mem.target_metric, mem.predicted_delta_pct, mem.actual_delta_pct,
                    mem.signed_error_pp, mem.telemetry_provenance, mem.validation_status,
                    json.dumps(mem.trade_off_metrics), 1 if mem.is_outlier else 0, mem.created_at
                ))
                conn.commit()
            finally:
                self._close_connection(conn)

    def list_memory_records(self) -> List[Any]:
        """Lists all stored ExperimentMemoryRecord items."""
        conn = self._get_connection()
        try:
            rows = conn.execute("SELECT * FROM experiment_memories ORDER BY created_at DESC;").fetchall()
            from backend.experiments.calibration_models import ExperimentMemoryRecord
            return [
                ExperimentMemoryRecord(
                    memory_id=r["memory_id"],
                    experiment_id=r["experiment_id"],
                    candidate_id=r["candidate_id"],
                    board_id=r["board_id"],
                    mcu=r["mcu"],
                    architecture=r["architecture"],
                    fqbn=r["fqbn"],
                    compiler_toolchain=r["compiler_toolchain"],
                    optimization_category=r["optimization_category"],
                    target_metric=r["target_metric"],
                    predicted_delta_pct=r["predicted_delta_pct"],
                    actual_delta_pct=r["actual_delta_pct"],
                    signed_error_pp=r["signed_error_pp"],
                    telemetry_provenance=r["telemetry_provenance"],
                    validation_status=r["validation_status"],
                    trade_off_metrics=json.loads(r["trade_off_metrics"]),
                    is_outlier=bool(r["is_outlier"]),
                    created_at=r["created_at"]
                )
                for r in rows
            ]
        finally:
            self._close_connection(conn)

