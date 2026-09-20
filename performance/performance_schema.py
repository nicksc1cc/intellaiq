"""
Inflexion Intelligence Engine — Performance Data Schema
Phase 12: Performance Data Schema
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from pathlib import Path
import json

try:
    from intelligence.core.models import PerformanceSnapshot
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from intelligence.core.models import PerformanceSnapshot


PERFORMANCE_DIR = Path(__file__).parent.parent / "data" / "performance"
PERFORMANCE_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class DataSource:
    source_id: str
    name: str
    type: str  # gsc, ga4, ahrefs, semrush, typesafe, custom
    credentials: dict = field(default_factory=dict)
    enabled: bool = True
    last_sync: datetime | None = None
    config: dict = field(default_factory=dict)


# Predefined data sources for Inflexion
DATA_SOURCES = {
    "gsc": DataSource(
        source_id="gsc",
        name="Google Search Console",
        type="gsc",
        config={"site_url": "https://nicksc1cc.github.io/inflexion-website/"}
    ),
    "ga4": DataSource(
        source_id="ga4",
        name="Google Analytics 4",
        type="ga4",
        config={"property_id": "G-XXXXXXXXXX"}
    ),
    "ahrefs": DataSource(
        source_id="ahrefs",
        name="Ahrefs",
        type="ahrefs",
        config={"target": "nicksc1cc.github.io/inflexion-website/"}
    ),
    "semrush": DataSource(
        source_id="semrush",
        name="SEMrush",
        type="semrush",
        config={"domain": "nicksc1cc.github.io"}
    ),
    "typesafe_ai_visibility": DataSource(
        source_id="typesafe_ai_visibility",
        name="TypeSafe AI Visibility",
        type="typesafe",
        config={"endpoint": "https://api.typesafe.ai/v1/visibility"}
    ),
}


def save_performance_snapshot(snapshot: PerformanceSnapshot) -> Path:
    """Save a performance snapshot."""
    filename = f"perf_{snapshot.page_id}_{snapshot.timestamp.strftime('%Y%m%d_%H%M%S')}.json"
    filepath = PERFORMANCE_DIR / filename
    filepath.write_text(json.dumps(snapshot.to_dict(), indent=2))
    return filepath


def load_performance_snapshots(page_id: str, limit: int = 10) -> list[PerformanceSnapshot]:
    """Load recent performance snapshots for a page."""
    snapshots = []
    for filepath in sorted(PERFORMANCE_DIR.glob(f"perf_{page_id}_*.json"))[-limit:]:
        try:
            data = json.loads(filepath.read_text())
            snapshots.append(PerformanceSnapshot(**data))
        except:
            pass
    return snapshots


def get_latest_performance(page_id: str) -> PerformanceSnapshot | None:
    """Get the most recent performance snapshot for a page."""
    snapshots = load_performance_snapshots(page_id, limit=1)
    return snapshots[0] if snapshots else None


def calculate_quality_performance_anomalies(
    quality_vectors: dict[str, Any],
    performance_data: dict[str, PerformanceSnapshot]
) -> list[dict]:
    """Identify quality/performance anomalies."""
    anomalies = []

    for page_id, qv in quality_vectors.items():
        perf = performance_data.get(page_id)
        if not perf:
            continue

        overall_quality = qv.get("overall", 0) if isinstance(qv, dict) else qv.overall

        # Normalize traffic metrics (simple heuristic)
        traffic_score = 0.0
        if perf.organic_clicks:
            traffic_score += min(perf.organic_clicks / 1000, 1.0) * 0.4
        if perf.sessions:
            traffic_score += min(perf.sessions / 500, 1.0) * 0.3
        if perf.ai_citations:
            traffic_score += min(perf.ai_citations / 100, 1.0) * 0.3

        # Anomaly detection
        if overall_quality > 0.7 and traffic_score < 0.3:
            anomalies.append({
                "page_id": page_id,
                "type": "HIGH_QUALITY_LOW_TRAFFIC",
                "quality_score": overall_quality,
                "traffic_score": traffic_score,
                "severity": "high" if overall_quality > 0.8 else "medium",
                "description": f"High quality ({overall_quality:.0%}) but low traffic ({traffic_score:.0%})"
            })
        elif overall_quality < 0.4 and traffic_score > 0.5:
            anomalies.append({
                "page_id": page_id,
                "type": "LOW_QUALITY_HIGH_TRAFFIC",
                "quality_score": overall_quality,
                "traffic_score": traffic_score,
                "severity": "high" if traffic_score > 0.7 else "medium",
                "description": f"Low quality ({overall_quality:.0%}) but high traffic ({traffic_score:.0%})"
            })
        elif overall_quality > 0.7 and perf.ai_citations and perf.ai_citations < 5:
            anomalies.append({
                "page_id": page_id,
                "type": "HIGH_QUALITY_LOW_AI_VISIBILITY",
                "quality_score": overall_quality,
                "ai_citations": perf.ai_citations,
                "severity": "medium",
                "description": f"High quality but few AI citations ({perf.ai_citations})"
            })
        elif overall_quality < 0.4 and perf.ai_citations and perf.ai_citations > 20:
            anomalies.append({
                "page_id": page_id,
                "type": "LOW_QUALITY_HIGH_AI_VISIBILITY",
                "quality_score": overall_quality,
                "ai_citations": perf.ai_citations,
                "severity": "medium",
                "description": f"Low quality but high AI citations ({perf.ai_citations})"
            })
        elif overall_quality > 0.7 and perf.leads and perf.leads == 0:
            anomalies.append({
                "page_id": page_id,
                "type": "HIGH_QUALITY_NO_LEADS",
                "quality_score": overall_quality,
                "leads": perf.leads,
                "severity": "medium",
                "description": f"High quality but no leads generated"
            })

    return anomalies


def get_performance_summary(performance_data: dict[str, PerformanceSnapshot]) -> dict:
    """Generate site-wide performance summary."""
    if not performance_data:
        return {"error": "No performance data available"}

    total_pages = len(performance_data)
    pages_with_traffic = sum(1 for p in performance_data.values() if p.sessions and p.sessions > 0)
    pages_with_ai_citations = sum(1 for p in performance_data.values() if p.ai_citations and p.ai_citations > 0)
    pages_with_leads = sum(1 for p in performance_data.values() if p.leads and p.leads > 0)

    total_sessions = sum(p.sessions or 0 for p in performance_data.values())
    total_ai_citations = sum(p.ai_citations or 0 for p in performance_data.values())
    total_leads = sum(p.leads or 0 for p in performance_data.values())

    return {
        "total_pages_tracked": total_pages,
        "pages_with_organic_traffic": pages_with_traffic,
        "pages_with_ai_citations": pages_with_ai_citations,
        "pages_generating_leads": pages_with_leads,
        "total_sessions": total_sessions,
        "total_ai_citations": total_ai_citations,
        "total_leads": total_leads,
        "avg_sessions_per_page": total_sessions / max(total_pages, 1),
        "avg_ai_citations_per_page": total_ai_citations / max(total_pages, 1),
    }