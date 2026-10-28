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
        self._lock = threading.RLock()
        self._deployment_in_progress: bool = False
        self._deployment_port: Optional[str] = None
        self._deployment_lock = threading.Lock()

    def set_active_run(self, run_id: Optional[str]) -> None:
        """Sets or updates the active run_id associated with incoming telemetry."""
        with self._lock:
            self.active_run_id = run_id

    def connect(self, port: str, baud_rate: int = 115200, run_id: Optional[str] = None, force: bool = False) -> Dict[str, Any]:
        """
        Establishes a serial connection to the specified hardware COM/TTY port.
        Raises ArisException(ARIS_SERIAL_DISCONNECTED) on failure.
        """
        if not force and self.is_deployment_active() and (not port or (self._deployment_port and self._deployment_port.upper() == port.upper())):
            raise ArisException(
                error_code="ARIS_SERIAL_BUSY",
                message=f"Cannot connect to {port}: firmware deployment is actively in progress.",
                details={"port": port},
                recoverable=True,
                status_code=409
            )

        with self._lock:
            if self.connected or self._serial_handle:
                self.release_serial(wait_ms=200)

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

    def is_serial_open(self, port: Optional[str] = None) -> bool:
        """
        Returns whether the serial port is currently open.
        If port is specified, checks if the connection matches that specific port.
        """
        with self._lock:
            if not self.connected and not self._serial_handle:
                return False
            if port and self.current_port and self.current_port.upper() != port.upper():
                return False
            if self._serial_handle:
                try:
                    return bool(self._serial_handle.is_open)
                except Exception:
                    return False
            return bool(self.connected)

    def release_serial(self, port: Optional[str] = None, wait_ms: int = 500) -> Dict[str, Any]:
        """
        Safely and idempotently releases any active serial port handle.
        1. Signals background telemetry reader thread to stop.
        2. Cancels pending I/O via cancel_read/cancel_write.
        3. Closes serial handle completely and sets to None.
        4. Joins the background reader thread to guarantee no lingering access.
        5. Waits for Windows OS to release COM port device lock (wait_ms).
        6. Verifies handle is closed.
        Guarantees that avrdude / arduino-cli can open the COM port without 'Access is denied'.
        """
        with self._lock:
            if port and self.current_port and self.current_port.upper() != port.upper():
                if not self.connected and not self._serial_handle:
                    return {
                        "released": True,
                        "port": port,
                        "current_port": self.current_port,
                        "status": "different_port_not_open"
                    }

            logger.info(f"Releasing serial handle for port {self.current_port or port or 'ALL'}.")
            self.connected = False
            self._stop_event.set()

            # Cancel any pending read/write in background thread to unblock ReadFile immediately
            if self._serial_handle:
                try:
                    if hasattr(self._serial_handle, "cancel_read"):
                        self._serial_handle.cancel_read()
                except Exception as e:
                    logger.debug(f"cancel_read exception: {e}")

                try:
                    if hasattr(self._serial_handle, "cancel_write"):
                        self._serial_handle.cancel_write()
                except Exception as e:
                    logger.debug(f"cancel_write exception: {e}")

                try:
                    if hasattr(self._serial_handle, "is_open") and self._serial_handle.is_open:
                        self._serial_handle.close()
                except Exception as e:
                    logger.warning(f"Error closing serial handle: {e}")
                finally:
                    self._serial_handle = None

            thread_to_join = None
            if self._read_thread and self._read_thread.is_alive():
                if threading.current_thread() != self._read_thread:
                    thread_to_join = self._read_thread
                self._read_thread = None

            released_port = self.current_port
            self.current_port = None

        # Join reader thread OUTSIDE the lock to prevent deadlock with reader loop cleanup
        if thread_to_join:
            try:
                thread_to_join.join(timeout=1.5)
            except Exception as e:
                logger.warning(f"Error joining serial reader thread: {e}")

        # Give Windows OS kernel time to flush and release COM port device lock
        if wait_ms > 0:
            time.sleep(wait_ms / 1000.0)

        # Verify handle is closed
        is_open = self.is_serial_open(port)
        if is_open:
            logger.error(f"Serial port {port or released_port} reported still open after release!")
        else:
            logger.info(f"Serial port {port or released_port} successfully released and confirmed closed.")

        return {
            "released": not is_open,
            "port": released_port or port,
            "is_open": is_open
        }

    def is_deployment_active(self) -> bool:
        """Returns True if a firmware deployment/flashing operation is actively in progress."""
        with self._lock:
            return bool(self._deployment_in_progress)

    def begin_deployment(self, port: str) -> None:
        """
        Enters deployment mode:
        1. Prevents concurrent deployments by acquiring deployment lock.
        2. Releases active serial port handle and stops background reader.
        3. Marks deployment active to block auto-detection and connection attempts.
        """
        acquired = self._deployment_lock.acquire(blocking=False)
        if not acquired:
            raise ArisException(
                error_code="ARIS_CONCURRENT_DEPLOYMENT",
                message=f"A firmware deployment is already in progress on port {self._deployment_port or 'target'}.",
                details={"port": port, "active_deployment_port": self._deployment_port},
                recoverable=False,
                status_code=409
            )
        try:
            with self._lock:
                self._deployment_in_progress = True
                self._deployment_port = port
            # Completely release the port
            self.release_serial(port=port, wait_ms=600)
            logger.info(f"Deployment mode active for port {port}. Serial released and auto-detection locked.")
        except Exception:
            self.end_deployment(port)
            raise

    def end_deployment(self, port: Optional[str] = None) -> None:
        """Exits deployment mode and unlocks port for normal detection/connection."""
        with self._lock:
            self._deployment_in_progress = False
            self._deployment_port = None
        if self._deployment_lock.locked():
            try:
                self._deployment_lock.release()
            except RuntimeError:
                pass
        logger.info(f"Deployment mode exited for port {port}. Normal detection resumed.")

    def acquire_serial(self, port: str, baud_rate: int = 115200, run_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Explicitly acquires serial port for telemetry streaming.
        Alias / wrapper around connect() for symmetry with release_serial().
        """
        return self.connect(port=port, baud_rate=baud_rate, run_id=run_id)

    def disconnect(self) -> Dict[str, Any]:
        """
        Closes the active serial connection safely.
        """
        res = self.release_serial(wait_ms=0)
        return {
            "connected": False,
            "previous_port": res.get("port")
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

    def perform_handshake(self, timeout_sec: float = 5.0) -> Dict[str, Any]:
        """
        Actively queries the MCU target with $ARIS_HELLO# and waits for $ARIS_ACK response.
        Retries periodically (every 350ms) to ensure handshake is received even if the MCU
        is undergoing bootloader delay (Optiboot 1-1.5s), setup() execution, or baud rate settling.
        """
        if not self.connected or not self._serial_handle:
            return {
                "handshake_success": False,
                "is_hardware": False,
                "message": "Not connected to any physical serial port."
            }

        try:
            # If a valid handshake was already captured (e.g. from boot announcement upon connect), return it
            with self._lock:
                if self.handshake_data and self.handshake_data.get("handshake_success"):
                    return dict(self.handshake_data)
                self.handshake_data = None

            start_t = time.time()
            last_probe_t = 0.0
            probe_interval = 0.35  # send $ARIS_HELLO# every 350ms

            while time.time() - start_t < timeout_sec:
                with self._lock:
                    if self.handshake_data and self.handshake_data.get("handshake_success"):
                        return dict(self.handshake_data)

                    now = time.time()
                    if now - last_probe_t >= probe_interval:
                        if self._serial_handle and self._serial_handle.is_open:
                            try:
                                # Ensure newline boundary before and after to ensure clean framing in MCU UART buffer
                                self._serial_handle.write(b"\r\n$ARIS_HELLO#\n")
                                self._serial_handle.flush()
                                last_probe_t = now
                            except Exception as write_err:
                                logger.debug(f"Handshake probe write error: {write_err}")

                time.sleep(0.04)

            # Final check under lock before timing out
            with self._lock:
                if self.handshake_data and self.handshake_data.get("handshake_success"):
                    return dict(self.handshake_data)

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
        """Parses $ARIS_ACK,...# or $ARIS_BOOT,...# handshake frame from arbitrary serial stream line."""
        if not line:
            return None

        clean = line.strip()
        idx = clean.find("$ARIS_ACK,")
        frame_type = "ACK"
        if idx == -1:
            idx = clean.find("$ARIS_BOOT,")
            frame_type = "BOOT"
        if idx == -1:
            return None

        hash_idx = clean.find("#", idx)
        if hash_idx == -1:
            return None

        frame = clean[idx : hash_idx + 1]

        # Format: $ARIS_ACK,runtime_version,protocol_version,board_id,mcu,arch,clock_hz,mode#
        try:
            payload = frame[frame.index(",") + 1 : -1]
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
                "frame_type": frame_type
            }
            return data
        except Exception as e:
            logger.debug(f"Failed to parse handshake frame '{frame}': {e}")
            return None

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
                    # Check for handshake packet anywhere in the line
                    if "$ARIS_ACK," in line_str or "$ARIS_BOOT," in line_str:
                        hs = self._parse_handshake_line(line_str)
                        if hs:
                            with self._lock:
                                self.handshake_data = hs
                            logger.info(f"Received ARIS runtime handshake from {self.current_port}: {hs}")

                            # Extract any non-handshake text that may have arrived on the same line
                            # so user sketch prints (or telemetry JSON) are preserved
                            start_tok = "$ARIS_ACK," if "$ARIS_ACK," in line_str else "$ARIS_BOOT,"
                            s_idx = line_str.find(start_tok)
                            e_idx = line_str.find("#", s_idx)
                            if e_idx != -1:
                                prefix = line_str[:s_idx].strip()
                                suffix = line_str[e_idx + 1:].strip()
                                if prefix:
                                    self.ingestor.ingest_raw_line(prefix, active_run_id=self.active_run_id)
                                if suffix:
                                    self.ingestor.ingest_raw_line(suffix, active_run_id=self.active_run_id)
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
