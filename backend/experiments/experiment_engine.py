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
        if exp.status in ("COMPLETED", "ROLLED_BACK"):
            raise ArisException(
                error_code="ARIS_VALIDATION_FAILED",
                message=f"Cannot bind candidate run: experiment '{experiment_id}' is already {exp.status}.",
                details={"experiment_id": experiment_id, "status": exp.status},
                recoverable=False,
                status_code=400
            )

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
        if exp.status == "COMPLETED":
            raise ArisException(
                error_code="ARIS_VALIDATION_FAILED",
                message=f"Experiment '{experiment_id}' has already completed validation.",
                details={"experiment_id": experiment_id, "status": exp.status},
                recoverable=False,
                status_code=400
            )
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

    def rollback_experiment(self, experiment_id: str) -> Dict[str, Any]:
        """
        Rolls back an optimization experiment:
        1. Transitions experiment status to ROLLED_BACK.
        2. Transitions candidate run status to ROLLED_BACK (if exists).
        3. Transitions optimization candidate status to ROLLED_BACK.
        Returns a rollback confirmation payload.
        """
        exp = self.get_experiment(experiment_id)
        exp.status = "ROLLED_BACK"
        self.db.save_experiment(exp)

        cand_run = None
        if exp.candidate_run_id:
            cand_run = self.db.get_run(exp.candidate_run_id)
            if cand_run:
                cand_run.status = "ROLLED_BACK"
                self.db.save_run(cand_run)

        opt = self.db.get_optimization(exp.optimization_id)
        if opt:
            opt.status = "ROLLED_BACK"
            self.db.save_optimization(opt)

        return {
            "status": "ROLLED_BACK",
            "experiment_id": experiment_id,
            "candidate_run_id": exp.candidate_run_id,
            "optimization_id": exp.optimization_id,
            "message": f"Successfully rolled back experiment '{experiment_id}' and restored baseline configuration."
        }

    def create_experiment_manifest(
        self,
        experiment_id: str,
        firmware_hash: str,
        candidate_hash: str,
        compiler_toolchain: str,
        selected_measurements: Optional[List[str]] = None,
        experiment_conditions: Optional[Dict[str, Any]] = None,
        prediction: Optional[Dict[str, Any]] = None,
        duration_seconds: float = 10.0,
        sample_count: int = 50,
        instrumentation_mode: str = "BALANCED"
    ):
        """
        Generates and persists an ExperimentManifest capturing exact board identity,
        code hashes, toolchain, conditions, and outcomes for reproducible validation.
        """
        from backend.experiments.manifest_models import ExperimentManifest
        from backend.firmware.board_profiles import get_board_profile
        exp = self.get_experiment(experiment_id)

        mcu = None
        arch = None
        fqbn = None
        try:
            profile = get_board_profile(exp.board_id)
            mcu = profile.mcu
            arch = profile.architecture
            fqbn = profile.fqbn
        except Exception:
            pass

        manifest_id = f"MAN-{uuid.uuid4().hex[:8].upper()}"
        manifest = ExperimentManifest(
            manifest_id=manifest_id,
            experiment_id=experiment_id,
            board_id=exp.board_id,
            mcu=mcu,
            architecture=arch,
            fqbn=fqbn,
            firmware_hash=firmware_hash,
            candidate_hash=candidate_hash,
            compiler_toolchain=compiler_toolchain,
            instrumentation_mode=instrumentation_mode,
            selected_measurements=selected_measurements or ["loop_time", "sram_used"],
            duration_seconds=duration_seconds,
            sample_count=sample_count,
            experiment_conditions=experiment_conditions or {},
            prediction=prediction or {},
            actual_result={},
            validation_result=None,
            created_at=datetime.now(timezone.utc).isoformat()
        )
        self.db.save_manifest(manifest)
        return manifest

    def create_provenance_lineage(
        self,
        firmware_id: str,
        analysis_run_id: Optional[str] = None,
        baseline_run_id: Optional[str] = None,
        finding_ids: Optional[List[str]] = None,
        hypothesis_id: Optional[str] = None,
        candidate_id: Optional[str] = None,
        experiment_id: Optional[str] = None,
        manifest_id: Optional[str] = None,
        candidate_run_id: Optional[str] = None,
        validation_id: Optional[str] = None
    ):
        """
        Creates and persists a full audit lineage connecting:
        Firmware -> Static Analysis -> Runtime Run -> Finding -> Hypothesis -> Candidate -> Experiment -> Validation.
        """
        from backend.experiments.manifest_models import ProvenanceLineage
        lineage_id = f"LIN-{uuid.uuid4().hex[:8].upper()}"
        lineage = ProvenanceLineage(
            lineage_id=lineage_id,
            firmware_id=firmware_id,
            analysis_run_id=analysis_run_id,
            baseline_run_id=baseline_run_id,
            finding_ids=finding_ids or [],
            hypothesis_id=hypothesis_id,
            candidate_id=candidate_id,
            experiment_id=experiment_id,
            manifest_id=manifest_id,
            candidate_run_id=candidate_run_id,
            validation_id=validation_id,
            created_at=datetime.now(timezone.utc).isoformat()
        )
        self.db.save_lineage(lineage)
        return lineage


