"""
ARIS Closed-Loop Optimization Experiment Engine.
Implements the closed-loop optimization experiment pipeline:
BASELINE
   ↓
OPTIMIZATION CANDIDATE
   ↓
BUILD
   ↓
FLASH
   ↓
RUN
   ↓
MEASURE
   ↓
COMPARE
   ↓
DECIDE
Retains both baseline and candidate data persistently.
"""

import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from backend.database.db_engine import DatabaseEngine
from backend.database.models import (
    ExperimentRecord,
    ValidationResultRecord,
    ValidationMetricDelta,
    RunRecord,
    OptimizationRecord
)
from backend.experiments.run_model import Run
from backend.experiments.validation_engine import ValidationEngine, ValidationReport
from backend.analysis.baseline_engine import BaselineEngine
from backend.telemetry.telemetry_schema import ArisException


class ExperimentEngine:
    """
    Coordinates closed-loop validation experiments comparing baseline benchmarks against candidate optimizations.
    """

    def __init__(self, db: DatabaseEngine, baseline_engine: BaselineEngine):
        self.db = db
        self.baseline_engine = baseline_engine

    def create_experiment(
        self,
        title: str,
        board_id: str,
        baseline_run_id: str,
        optimization_id: str
    ) -> ExperimentRecord:
        """
        Initializes an optimization experiment.
        Validates that baseline run and optimization candidate exist.
        """
        # Ensure baseline run exists
        base_run = self.db.get_run(baseline_run_id)
        if not base_run:
            raise ArisException(
                error_code="ARIS_VALIDATION_FAILED",
                message=f"Baseline run '{baseline_run_id}' does not exist.",
                details={"baseline_run_id": baseline_run_id},
                recoverable=False,
                status_code=404
            )

        # Ensure optimization candidate exists
        opt = self.db.get_optimization(optimization_id)
        if not opt:
            raise ArisException(
                error_code="ARIS_OPTIMIZATION_INVALID",
                message=f"Optimization candidate '{optimization_id}' does not exist.",
                details={"optimization_id": optimization_id},
                recoverable=False,
                status_code=404
            )

        exp_id = f"EXP-{uuid.uuid4().hex[:8].upper()}"
        exp = ExperimentRecord(
            experiment_id=exp_id,
            title=title,
            board_id=board_id,
            baseline_run_id=baseline_run_id,
            candidate_run_id=None,
            optimization_id=optimization_id,
            status="CREATED",
            validation_id=None,
            created_at=datetime.now(timezone.utc).isoformat()
        )
        self.db.save_experiment(exp)
        return exp

    def bind_candidate_run(
        self,
        experiment_id: str,
        candidate_run_id: str
    ) -> ExperimentRecord:
        """Associates the executed candidate benchmark run with this experiment."""
        exp = self.get_experiment(experiment_id)
        cand_run = self.db.get_run(candidate_run_id)
        if not cand_run:
            raise ArisException(
                error_code="ARIS_VALIDATION_FAILED",
                message=f"Candidate run '{candidate_run_id}' not found.",
                details={"candidate_run_id": candidate_run_id},
                recoverable=False,
                status_code=404
            )

        exp.candidate_run_id = candidate_run_id
        exp.status = "RUNNING"
        self.db.save_experiment(exp)
        return exp

    def validate_experiment(self, experiment_id: str) -> ValidationReport:
        """
        Computes baseline vs candidate statistical delta and decides validation status.
        DECIDE step:
        - Updates Optimization Candidate status (VALIDATED, REJECTED, etc.)
        - Stores ValidationResultRecord in database
        - Updates Experiment record
        """
        exp = self.get_experiment(experiment_id)
        if not exp.candidate_run_id:
            raise ArisException(
                error_code="ARIS_VALIDATION_FAILED",
                message="Cannot validate experiment: candidate run has not been bound or executed.",
                details={"experiment_id": experiment_id},
                recoverable=True,
                status_code=400
            )

        # Retrieve or compute baselines for both runs
        base_run = self.db.get_run(exp.baseline_run_id)
        cand_run = self.db.get_run(exp.candidate_run_id)

        # Fetch baseline objects
        base_record = None
        if base_run.baseline_id:
            base_record = self.db.get_baseline(base_run.baseline_id)
        if not base_record:
            base_record = self.baseline_engine.generate_baseline(base_run.run_id)

        cand_record = None
        if cand_run.baseline_id:
            cand_record = self.db.get_baseline(cand_run.baseline_id)
        if not cand_record:
            cand_record = self.baseline_engine.generate_baseline(cand_run.run_id)

        validation_id = f"VAL-{uuid.uuid4().hex[:8].upper()}"

        # Execute empirical validation comparison
        report = ValidationEngine.validate_benchmarks(
            baseline_record=base_record,
            candidate_record=cand_record,
            validation_id=validation_id,
            experiment_id=experiment_id
        )

        # Convert report deltas into ValidationMetricDelta models
        metric_deltas: Dict[str, ValidationMetricDelta] = {}
        for m, diff_val in report.difference.items():
            b_val = report.baseline.get(m, 0.0)
            c_val = report.candidate.get(m, 0.0)
            pct = report.percentage_change.get(m, 0.0)
            is_imp = pct < 0 if m != "loop_frequency" else pct > 0
            metric_deltas[m] = ValidationMetricDelta(
                metric=m,
                baseline_value=b_val,
                candidate_value=c_val,
                difference=diff_val,
                percentage_change=pct,
                is_improvement=is_imp
            )

        val_record = ValidationResultRecord(
            validation_id=validation_id,
            experiment_id=experiment_id,
            baseline_run_id=exp.baseline_run_id,
            candidate_run_id=exp.candidate_run_id,
            metrics=metric_deltas,
            validation_status=report.validation_status,
            reason=report.reason,
            created_at=datetime.now(timezone.utc).isoformat()
        )
        self.db.save_validation_result(val_record)

        # Update experiment record
        exp.validation_id = validation_id
        exp.status = "COMPLETED"
        self.db.save_experiment(exp)

        # Update candidate status
        opt = self.db.get_optimization(exp.optimization_id)
        if opt:
            if report.validation_status in ["VALIDATED", "PARTIALLY_VALIDATED"]:
                opt.status = "VALIDATED"
            elif report.validation_status == "REGRESSION":
                opt.status = "FAILED"
            elif report.validation_status == "REJECTED":
                opt.status = "REJECTED"
            self.db.save_optimization(opt)

        return report

    def get_experiment(self, experiment_id: str) -> ExperimentRecord:
        """Retrieves experiment record or raises 404."""
        exp = self.db.get_experiment(experiment_id)
        if not exp:
            raise ArisException(
                error_code="ARIS_VALIDATION_FAILED",
                message=f"Experiment '{experiment_id}' was not found.",
                details={"experiment_id": experiment_id},
                recoverable=False,
                status_code=404
            )
        return exp

    def list_experiments(self) -> List[ExperimentRecord]:
        """Lists all registered experiments."""
        return self.db.list_experiments()
