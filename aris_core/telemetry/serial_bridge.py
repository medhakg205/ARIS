"""
Physical Hardware Serial Telemetry Bridge for ARIS.
Discovers and communicates with physical Arduino Uno, Mega, Nano, and other serial MCUs over USB.
Parses real $ARIS telemetry packets and converts them into real-time telemetry frames.
"""

from typing import List, Dict, Any, Callable
import threading
import time
import re
from aris_core.hardware_profiles import get_hardware_profile, HardwareProfile

try:
    import serial
    import serial.tools.list_ports
    HAS_PYSERIAL = True
except ImportError:
    HAS_PYSERIAL = False

class SerialBridge:
    def __init__(self):
        self.connected: bool = False
        self.current_port: str = ""
        self.baud_rate: int = 115200
        self._serial_conn = None
        self._read_thread: threading.Thread | None = None
        self._callbacks: List[Callable[[Dict[str, Any]], None]] = []
        self.last_packet_time: float = 0.0
        self.active_board_id: str = "arduino_uno"

    def set_board(self, board_id: str):
        self.active_board_id = board_id

    def list_ports(self) -> List[Dict[str, str]]:
        """List all physically available serial COM ports."""
        if not HAS_PYSERIAL:
            return []

        ports = serial.tools.list_ports.comports()
        res = []
        for p in ports:
            desc = p.description or ""
            # Identify common Arduino hardware
            is_arduino = any(k in desc.lower() for k in ["arduino", "ch340", "cp210", "ftdi", "usb serial"])
            res.append({
                "port": p.device,
                "desc": desc + (" [Detected Arduino]" if is_arduino else ""),
                "hwid": p.hwid or "",
                "is_arduino": is_arduino
            })
        return res

    def register_callback(self, cb: Callable[[Dict[str, Any]], None]):
        self._callbacks.append(cb)

    def connect(self, port: str, baud: int = 115200) -> bool:
        if not HAS_PYSERIAL:
            return False

        try:
            self.disconnect()
            self._serial_conn = serial.Serial(port, baud, timeout=0.2)
            self.connected = True
            self.current_port = port
            self.baud_rate = baud
            self.last_packet_time = time.time()
            self._read_thread = threading.Thread(target=self._read_loop, daemon=True)
            self._read_thread.start()
            print(f"[ARIS Serial Bridge] Connected to physical hardware on {port} @ {baud} baud.")
            return True
        except Exception as e:
            print(f"[ARIS Serial Bridge] Failed to connect to {port}: {e}")
            self.connected = False
            return False

    def disconnect(self):
        self.connected = False
        if self._serial_conn:
            try:
                if self._serial_conn.is_open:
                    self._serial_conn.close()
            except Exception:
                pass
        self._serial_conn = None
        self.current_port = ""

    def _read_loop(self):
        hw: HardwareProfile = get_hardware_profile(self.active_board_id)
        
        while self.connected and self._serial_conn and self._serial_conn.is_open:
            try:
                raw_bytes = self._serial_conn.readline()
                if not raw_bytes:
                    time.sleep(0.01)
                    continue

                line = raw_bytes.decode("utf-8", errors="ignore").strip()
                
                # Check for $ARIS framing packet from physical Arduino
                # Format: $ARIS,board,cpu,sram_free,stack_max,loop_us,isr_cnt,adc_cnt,gpio_cnt#
                if line.startswith("$ARIS") and "#" in line:
                    self.last_packet_time = time.time()
                    clean_line = line.replace("$ARIS,", "").replace("#", "").strip()
                    parts = clean_line.split(",")

                    if len(parts) >= 8:
                        try:
                            board_num = int(parts[0])
                            cpu_gross = float(parts[1])
                            free_sram = int(parts[2])
                            stack_max = int(parts[3])
                            loop_us = int(parts[4])
                            isr_cnt = int(parts[5])
                            adc_cnt = int(parts[6])
                            gpio_cnt = int(parts[7])

                            # Calculate derived physical metrics
                            loop_hz = round(1_000_000.0 / max(1, loop_us), 1)
                            used_sram = max(0, hw.sram_bytes - free_sram)
                            
                            # Observer compensation
                            observer_overhead = round(min(2.0, (32 * loop_hz) / 1_000_000 * 100), 2)
                            cpu_net = max(1.0, round(cpu_gross - observer_overhead, 1))

                            # Power calculation
                            active_ratio = cpu_net / 100.0
                            avg_current_ma = (hw.active_power_ma * active_ratio) + (hw.sleep_power_ma * (1.0 - active_ratio))
                            power_mw = round(hw.operating_voltage * avg_current_ma, 1)

                            frame_data = {
                                "timestamp_ms": int(time.time() * 1000),
                                "board_id": hw.id,
                                "board_name": hw.name,
                                "cpu_utilization_pct": cpu_gross,
                                "cpu_compensated_pct": cpu_net,
                                "free_sram_bytes": free_sram,
                                "used_sram_bytes": used_sram,
                                "stack_high_watermark_bytes": stack_max,
                                "loop_duration_us": loop_us,
                                "loop_frequency_hz": loop_hz,
                                "jitter_us": 8,
                                "isr_frequency_hz": isr_cnt * 10,
                                "adc_conversions_sec": adc_cnt * 10,
                                "gpio_toggles_sec": gpio_cnt * 10,
                                "power_consumption_mw": power_mw,
                                "active_current_ma": round(avg_current_ma, 2),
                                "observer_overhead_pct": observer_overhead,
                                "raw_packet": line,
                                "pin_states": {},
                                "is_physical_hardware": True
                            }

                            for cb in self._callbacks:
                                cb(frame_data)

                        except (ValueError, IndexError) as parse_err:
                            print(f"[ARIS Serial Bridge] Packet parse error: {parse_err}")

            except Exception as e:
                print(f"[ARIS Serial Bridge] Serial read error: {e}")
                break
            time.sleep(0.005)
