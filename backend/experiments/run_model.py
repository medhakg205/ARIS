"""
ARIS Run Model and Execution Lifecycle State Machine.
Defines the canonical Run lifecycle states:
CREATED -> BUILDING -> FLASHING -> RUNNING -> COLLECTING -> COMPLETED (or FAILED / ROLLED_BACK).
Tracks runtime execution context, board binding, and baseline references.
"""

from typing import Set, Optional, List, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from backend.telemetry.telemetry_schema import ArisException


# Canonical Run Statuses
CANONICAL_RUN_STATUSES: Set[str] = {
    "CREATED",
    "BUILDING",
    "FLASHING",
    "RUNNING",
    "COLLECTING",
    "COMPLETED",
    "FAILED",
    "ROLLED_BACK"
}

# Canonical Instrumentation Modes
CANONICAL_INSTRUMENTATION_MODES: Set[str] = {"LOW", "BALANCED", "FULL"}


class Run(BaseModel):
    """
    In-memory representation of an active or historical execution Run.
    """
    run_id: str
    board_id: str
    firmware_id: Optional[str] = None
    instrumentation_mode: str = "BALANCED"
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    status: str = "CREATED"
    is_simulated: bool = False
    is_demo: bool = False
    baseline_reference: Optional[str] = None
    analysis_reference: Optional[str] = None

    def transition_to(self, new_status: str) -> None:
        """
        Transitions run to a new lifecycle status. Validates allowed state names.
        """
        if new_status not in CANONICAL_RUN_STATUSES:
            raise ArisException(
                error_code="ARIS_VALIDATION_FAILED",
                message=f"Invalid run status '{new_status}'. Allowed: {CANONICAL_RUN_STATUSES}",
                details={"run_id": self.run_id, "attempted_status": new_status},
                recoverable=False,
                status_code=400
            )

        self.status = new_status
        if new_status in ["RUNNING", "COLLECTING"] and not self.start_time:
            self.start_time = datetime.now(timezone.utc).isoformat()
        elif new_status in ["COMPLETED", "FAILED", "ROLLED_BACK"]:
            self.end_time = datetime.now(timezone.utc).isoformat()
