"""
ARIS Serial Communication Manager.
Manages serial hardware connections, background ingestion loops,
and graceful disconnection handling.
Enforces the canonical error contract: on serial connection failure or drop,
issues the ARIS_SERIAL_DISCONNECTED canonical error.
"""

import time
import threading
import logging
from typing import Optional, Dict, Any

from backend.telemetry.telemetry_ingestor import TelemetryIngestor
from backend.telemetry.telemetry_schema import ArisException

logger = logging.getLogger("aris.serial.manager")


class SerialManager:
    """
    Controls physical serial port connection lifecycle.
    Reads lines in a background daemon thread and pushes them into TelemetryIngestor.
    """

    def __init__(self, ingestor: TelemetryIngestor):
        self.ingestor = ingestor
        self.connected: bool = False
        self.current_port: Optional[str] = None
        self.current_baud: int = 115200
        self.active_run_id: Optional[str] = None
        self.handshake_data: Optional[Dict[str, Any]] = None
        self._serial_handle = None
        self._read_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

    def set_active_run(self, run_id: Optional[str]) -> None:
        """Sets or updates the active run_id associated with incoming telemetry."""
        with self._lock:
            self.active_run_id = run_id

    def connect(self, port: str, baud_rate: int = 115200, run_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Establishes a serial connection to the specified hardware COM/TTY port.
        Raises ArisException(ARIS_SERIAL_DISCONNECTED) on failure.
        """
        with self._lock:
            if self.connected:
                self.disconnect()

            try:
                import serial
            except ImportError:
                raise ArisException(
                    error_code="ARIS_BACKEND_UNAVAILABLE",
                    message="pyserial package is not available on host system.",
                    details={"port": port},
                    recoverable=False,
                    status_code=503
                )

            try:
                # Open serial port with 0.5s timeout
                self._serial_handle = serial.Serial(
                    port=port,
                    baudrate=baud_rate,
                    timeout=0.5,
                    write_timeout=1.0
                )
                self.connected = True
                self.current_port = port
                self.current_baud = baud_rate
                self.active_run_id = run_id
                self._stop_event.clear()

                # Launch background reader thread
                self._read_thread = threading.Thread(
                    target=self._reader_loop,
                    name=f"ARIS-Serial-{port}",
                    daemon=True
                )
                self._read_thread.start()

                logger.info(f"Connected to physical microcontroller on {port} @ {baud_rate} baud.")
                return {
                    "connected": True,
                    "port": self.current_port,
                    "baud_rate": self.current_baud,
                    "run_id": self.active_run_id
                }

            except Exception as e:
                self.connected = False
                self.current_port = None
                self._serial_handle = None
                logger.error(f"Failed to open serial port {port}: {e}")
                raise ArisException(
                    error_code="ARIS_SERIAL_DISCONNECTED",
                    message=f"Failed to connect to serial port {port}: {str(e)}",
                    details={"port": port, "baud_rate": baud_rate},
                    recoverable=True,
                    status_code=400
                )

    def disconnect(self) -> Dict[str, Any]:
        """
        Closes the active serial connection safely.
        """
        with self._lock:
            self.connected = False
            self._stop_event.set()

            if self._serial_handle:
                try:
                    if self._serial_handle.is_open:
                        self._serial_handle.close()
                except Exception as e:
                    logger.warning(f"Error closing serial handle: {e}")
                finally:
                    self._serial_handle = None

            previous_port = self.current_port
            self.current_port = None

            logger.info(f"Disconnected serial port {previous_port}.")
            return {
                "connected": False,
                "previous_port": previous_port
            }

    def get_status(self) -> Dict[str, Any]:
        """Returns the current connection status and telemetry ingestion counts."""
        with self._lock:
            return {
                "connected": self.connected,
                "port": self.current_port,
                "baud_rate": self.current_baud if self.connected else None,
                "active_run_id": self.active_run_id,
                "packets_received": self.ingestor.total_packets_received,
                "packets_valid": self.ingestor.total_packets_valid,
                "packets_rejected": self.ingestor.total_packets_rejected,
                "last_error": self.ingestor.last_error,
                "handshake": self.handshake_data,
                "is_hardware": True if self.connected else False
            }

    def perform_handshake(self, timeout_sec: float = 2.0) -> Dict[str, Any]:
        """
        Sends $ARIS_HELLO# to target hardware and awaits $ARIS_ACK confirmation.
        Distinguishes real instrumented ARIS hardware from un-instrumented serial devices.
        """
        if not self.connected or not self._serial_handle:
            return {
                "handshake_success": False,
                "is_hardware": False,
                "message": "Not connected to any physical serial port."
            }

        try:
            self.handshake_data = None
            with self._lock:
                if self._serial_handle and self._serial_handle.is_open:
                    self._serial_handle.write(b"$ARIS_HELLO#\n")
                    self._serial_handle.flush()

            start_t = time.time()
            while time.time() - start_t < timeout_sec:
                if self.handshake_data:
                    return self.handshake_data
                time.sleep(0.05)

            return {
                "handshake_success": False,
                "is_hardware": True,
                "message": f"Connected to {self.current_port}, but target did not respond to ARIS runtime handshake."
            }
        except Exception as e:
            logger.warning(f"Error performing serial handshake on {self.current_port}: {e}")
            return {
                "handshake_success": False,
                "is_hardware": True,
                "error": str(e)
            }

    def _parse_handshake_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Parses $ARIS_ACK,...# or $ARIS_BOOT,...# handshake frame."""
        clean = line.strip()
        if not ((clean.startswith("$ARIS_ACK,") or clean.startswith("$ARIS_BOOT,")) and clean.endswith("#")):
            return None

        # Format: $ARIS_ACK,runtime_version,protocol_version,board_id,mcu,arch,clock_hz,mode#
        payload = clean[clean.index(",") + 1 : -1]
        parts = [p.strip() for p in payload.split(",")]
        if len(parts) < 6:
            return None

        data = {
            "handshake_success": True,
            "is_hardware": True,
            "runtime_version": parts[0],
            "protocol_version": parts[1],
            "board_id": parts[2],
            "mcu": parts[3],
            "architecture": parts[4],
            "clock_hz": int(parts[5]) if parts[5].isdigit() else 16000000,
            "instrumentation_mode": parts[6] if len(parts) > 6 else "BALANCED",
            "frame_type": "ACK" if clean.startswith("$ARIS_ACK") else "BOOT"
        }
        return data

    def _reader_loop(self) -> None:
        """
        Continuous background thread that reads lines from the active serial interface.
        Feeds raw lines into the TelemetryIngestor.
        Detects physical cable disconnects or buffer corruption.
        """
        while not self._stop_event.is_set():
            if not self._serial_handle or not self._serial_handle.is_open:
                break

            try:
                raw_bytes = self._serial_handle.readline()
                if not raw_bytes:
                    # Timeout reached with no data; sleep briefly and retry
                    time.sleep(0.01)
                    continue

                line_str = raw_bytes.decode("utf-8", errors="ignore").strip()
                if line_str:
                    # Check for handshake packet
                    if line_str.startswith("$ARIS_ACK,") or line_str.startswith("$ARIS_BOOT,"):
                        hs = self._parse_handshake_line(line_str)
                        if hs:
                            with self._lock:
                                self.handshake_data = hs
                            logger.info(f"Received ARIS runtime handshake from {self.current_port}: {hs}")
                            continue

                    # Ingest line into the telemetry ingestion pipeline
                    self.ingestor.ingest_raw_line(line_str, active_run_id=self.active_run_id)

            except Exception as e:
                # Disconnection or hardware I/O error occurred
                logger.error(f"Serial read error on {self.current_port}: {e}")
                self.connected = False
                break

        # If loop terminated unexpectedly, ensure cleanup
        with self._lock:
            if self._serial_handle:
                try:
                    self._serial_handle.close()
                except Exception:
                    pass
                self._serial_handle = None
            self.connected = False
