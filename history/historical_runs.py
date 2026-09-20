"""
Inflexion Intelligence Engine — Historical Runs
Phase 11: Historical Runs & Change Intelligence
"""

from __future__ import annotations
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from collections import defaultdict

try:
    from intelligence.core.models import IntelligenceRun, QualityVector, PageState, JevResult
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from intelligence.core.models import IntelligenceRun, QualityVector, PageState, JevResult


RUNS_DIR = Path(__file__).parent.parent / "data" / "runs"
RUNS_DIR.mkdir(parents=True, exist_ok=True)


def save_run(run: IntelligenceRun) -> Path:
    """Save an intelligence run to disk."""
    filename = f"run_{run.run_id}.json"
    filepath = RUNS_DIR / filename
    filepath.write_text(run.to_json())
    return filepath


def load_run(run_id: str) -> IntelligenceRun | None:
    """Load a specific run by ID."""
    filepath = RUNS_DIR / f"run_{run_id}.json"
    if filepath.exists():
        data = json.loads(filepath.read_text())
        # Reconstruction would be needed for full objects
        return data
    return None


def load_latest_run() -> IntelligenceRun | None:
    """Load the most recent run."""
    runs = sorted(RUNS_DIR.glob("run_*.json"))
    if runs:
        return json.loads(runs[-1].read_text())
    return None


def list_runs() -> list[dict]:
    """List all available runs with metadata."""
    runs = []
    for filepath in sorted(RUNS_DIR.glob("run_*.json")):
        try:
            data = json.loads(filepath.read_text())
            runs.append({
                "run_id": data.get("run_id"),
                "timestamp": data.get("timestamp"),
                "git_commit": data.get("git_commit"),
                "pages_analyzed": len(data.get("pages_analyzed", [])),
                "filepath": str(filepath)
            })
        except:
            pass
    return runs


@dataclass
class ChangeEvent:
    change_id: str
    run_a_id: str
    run_b_id: str
    page_id: str
    change_type: str  # NEW, REMOVED, IMPROVED, WEAKENED, UNCHANGED, CONFLICT, NEW_UNCERTAINTY
    dimension: str | None = None
    old_value: float | None = None
    new_value: float | None = None
    confidence: float = 0.0
    details: dict = field(default_factory=dict)


def compare_runs(run_a: IntelligenceRun, run_b: IntelligenceRun) -> list[ChangeEvent]:
    """Compare two runs and generate change events."""
    changes = []

    pages_a = set(run_a.pages_analyzed)
    pages_b = set(run_b.pages_analyzed)

    # Page-level changes
    for page_id in pages_a - pages_b:
        changes.append(ChangeEvent(
            change_id=f"page_removed_{page_id}",
            run_a_id=run_a.run_id,
            run_b_id=run_b.run_id,
            page_id=page_id,
            change_type="REMOVED",
            confidence=1.0
        ))

    for page_id in pages_b - pages_a:
        changes.append(ChangeEvent(
            change_id=f"page_new_{page_id}",
            run_a_id=run_a.run_id,
            run_b_id=run_b.run_id,
            page_id=page_id,
            change_type="NEW",
            confidence=1.0
        ))

    # Quality vector changes
    common_pages = pages_a & pages_b
    for page_id in common_pages:
        qv_a = run_a.quality_vectors.get(page_id)
        qv_b = run_b.quality_vectors.get(page_id)

        if qv_a and qv_b:
            for dim_name in [
                "intellectual_distinctiveness", "evidence_quality", "subject_specificity",
                "argument_quality", "human_writing", "structural_quality",
                "site_differentiation", "technical_accuracy", "commercial_usefulness",
                "editorial_quality", "knowledge_contribution", "objective_coverage"
            ]:
                dim_a = getattr(qv_a, dim_name)
                dim_b = getattr(qv_b, dim_name)

                delta = dim_b.score - dim_a.score
                if abs(delta) > 0.05:  # 5% threshold
                    change_type = "IMPROVED" if delta > 0 else "WEAKENED"
                    changes.append(ChangeEvent(
                        change_id=f"qv_{dim_name}_{page_id}",
                        run_a_id=run_a.run_id,
                        run_b_id=run_b.run_id,
                        page_id=page_id,
                        change_type=change_type,
                        dimension=dim_name,
                        old_value=dim_a.score,
                        new_value=dim_b.score,
                        confidence=min(dim_a.confidence, dim_b.confidence),
                        details={"delta": delta}
                    ))

        # Jev result changes
        jev_a = run_a.jev_results.get(page_id, [])
        jev_b = run_b.jev_results.get(page_id, [])

        jev_a_map = {r.question_id: r for r in jev_a}
        jev_b_map = {r.question_id: r for r in jev_b}

        for qid in set(jev_a_map.keys()) | set(jev_b_map.keys()):
            r_a = jev_a_map.get(qid)
            r_b = jev_b_map.get(qid)

            if r_a and not r_b:
                changes.append(ChangeEvent(
                    change_id=f"jev_removed_{qid}",
                    run_a_id=run_a.run_id,
                    run_b_id=run_b.run_id,
                    page_id=page_id,
                    change_type="REMOVED",
                    dimension=qid,
                    confidence=0.8
                ))
            elif r_b and not r_a:
                changes.append(ChangeEvent(
                    change_id=f"jev_new_{qid}",
                    run_a_id=run_a.run_id,
                    run_b_id=run_b.run_id,
                    page_id=page_id,
                    change_type="NEW",
                    dimension=qid,
                    confidence=0.8
                ))
            elif r_a and r_b:
                score_a = _extract_jev_score(r_a)
                score_b = _extract_jev_score(r_b)
                delta = score_b - score_a
                if abs(delta) > 0.15:
                    changes.append(ChangeEvent(
                        change_id=f"jev_changed_{qid}",
                        run_a_id=run_a.run_id,
                        run_b_id=run_b.run_id,
                        page_id=page_id,
                        change_type="IMPROVED" if delta > 0 else "WEAKENED",
                        dimension=qid,
                        old_value=score_a,
                        new_value=score_b,
                        confidence=min(r_a.confidence, r_b.confidence),
                        details={"delta": delta}
                    ))

    return changes


def _extract_jev_score(result: JevResult) -> float:
    if result.question_type.value == "noul":
        return float(result.result) if isinstance(result.result, (int, float)) else 0.5
    elif result.question_type.value == "score":
        if isinstance(result.probability, dict) and result.probability:
            levels = len(result.probability)
            if levels > 1 and isinstance(result.result, (int, float)):
                return float(result.result) / (levels - 1)
        return 0.5
    return 0.5


def get_change_summary(changes: list[ChangeEvent]) -> dict[str, Any]:
    """Generate a summary of changes between runs."""
    summary = {
        "total_changes": len(changes),
        "by_type": defaultdict(int),
        "by_page": defaultdict(int),
        "by_dimension": defaultdict(int),
        "improved_pages": set(),
        "weakened_pages": set(),
        "new_pages": set(),
        "removed_pages": set(),
    }

    for c in changes:
        summary["by_type"][c.change_type] += 1
        summary["by_page"][c.page_id] += 1
        if c.dimension:
            summary["by_dimension"][c.dimension] += 1

        if c.change_type == "IMPROVED":
            summary["improved_pages"].add(c.page_id)
        elif c.change_type == "WEAKENED":
            summary["weakened_pages"].add(c.page_id)
        elif c.change_type == "NEW":
            summary["new_pages"].add(c.page_id)
        elif c.change_type == "REMOVED":
            summary["removed_pages"].add(c.page_id)

    # Convert sets to lists for JSON serialization
    summary["improved_pages"] = list(summary["improved_pages"])
    summary["weakened_pages"] = list(summary["weakened_pages"])
    summary["new_pages"] = list(summary["new_pages"])
    summary["removed_pages"] = list(summary["removed_pages"])
    summary["by_type"] = dict(summary["by_type"])
    summary["by_page"] = dict(summary["by_page"])
    summary["by_dimension"] = dict(summary["by_dimension"])

    return summary


def get_page_history(page_id: str, limit: int = 10) -> list[dict]:
    """Get historical quality data for a specific page."""
    runs = list_runs()
    history = []

    for run_meta in runs[-limit:]:
        run_data = load_run(run_meta["run_id"])
        if run_data:
            qv = run_data.get("quality_vectors", {}).get(page_id)
            if qv:
                history.append({
                    "run_id": run_meta["run_id"],
                    "timestamp": run_meta["timestamp"],
                    "git_commit": run_meta["git_commit"],
                    "overall_score": qv.get("overall", 0),
                    "dimensions": {k: v.get("score", 0) for k, v in qv.items() if isinstance(v, dict)}
                })

    return history


def detect_regression(run_a: IntelligenceRun, run_b: IntelligenceRun, page_id: str) -> list[str]:
    """Detect if changes to a page caused regressions in other areas."""
    regressions = []

    qv_a = run_a.quality_vectors.get(page_id)
    qv_b = run_b.quality_vectors.get(page_id)

    if qv_a and qv_b:
        # Check if overall improved but specific critical dimensions weakened
        critical_dims = ["intellectual_distinctiveness", "evidence_quality", "site_differentiation", "technical_accuracy"]
        overall_delta = qv_b.overall - qv_a.overall

        for dim in critical_dims:
            dim_a = getattr(qv_a, dim)
            dim_b = getattr(qv_b, dim)
            if dim_b.score < dim_a.score - 0.05 and overall_delta > 0:
                regressions.append(f"{dim} regressed while overall improved")

    return regressions