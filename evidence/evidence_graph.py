"""
Inflexion Intelligence Engine — Evidence Graph
Phase 10: Evidence Graph
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from collections import defaultdict

try:
    from intelligence.core.models import PageState, Claim, Evidence, Statistic
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from intelligence.core.models import PageState, Claim, Evidence, Statistic


@dataclass
class EvidenceNode:
    evidence_id: str
    text: str
    source: str
    source_type: str
    date: str | None
    strength: float
    claims_supported: list[str] = field(default_factory=list)
    pages_using: list[str] = field(default_factory=list)
    statistics_supported: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass
class ClaimNode:
    claim_id: str
    text: str
    page_id: str
    claim_type: str
    confidence: float
    evidence_refs: list[str] = field(default_factory=list)
    supporting_evidence: list[str] = field(default_factory=list)


@dataclass
class StatisticNode:
    statistic_id: str
    value: str
    context: str
    page_id: str
    source: str | None
    date: str | None
    used_on_pages: list[str] = field(default_factory=list)
    evidence_supporting: list[str] = field(default_factory=list)


class EvidenceGraph:
    def __init__(self):
        self.evidence: dict[str, EvidenceNode] = {}
        self.claims: dict[str, ClaimNode] = {}
        self.statistics: dict[str, StatisticNode] = {}
        self.source_to_evidence: dict[str, list[str]] = defaultdict(list)
        self.page_to_evidence: dict[str, list[str]] = defaultdict(list)

    def add_evidence(self, evidence: EvidenceNode) -> None:
        self.evidence[evidence.evidence_id] = evidence
        self.source_to_evidence[evidence.source].append(evidence.evidence_id)
        for page_id in evidence.pages_using:
            self.page_to_evidence[page_id].append(evidence.evidence_id)

    def add_claim(self, claim: ClaimNode) -> None:
        self.claims[claim.claim_id] = claim

    def add_statistic(self, statistic: StatisticNode) -> None:
        self.statistics[statistic.statistic_id] = statistic

    def get_claims_without_evidence(self) -> list[ClaimNode]:
        return [c for c in self.claims.values() if not c.evidence_refs]

    def get_evidence_supporting_multiple_pages(self) -> list[EvidenceNode]:
        return [e for e in self.evidence.values() if len(e.pages_using) > 1]

    def get_overused_statistics(self, threshold: int = 3) -> list[StatisticNode]:
        return [s for s in self.statistics.values() if len(s.used_on_pages) >= threshold]

    def get_stale_sources(self, max_age_days: int = 365) -> list[EvidenceNode]:
        from datetime import datetime, timedelta
        cutoff = datetime.now() - timedelta(days=max_age_days)
        stale = []
        for ev in self.evidence.values():
            if ev.date:
                try:
                    ev_date = datetime.fromisoformat(ev.date.replace("Z", "+00:00"))
                    if ev_date < cutoff:
                        stale.append(ev)
                except:
                    pass
        return stale

    def get_weak_evidence_claims(self, strength_threshold: float = 0.4) -> list[ClaimNode]:
        weak = []
        for claim in self.claims.values():
            if claim.evidence_refs:
                avg_strength = sum(
                    self.evidence[eid].strength
                    for eid in claim.evidence_refs
                    if eid in self.evidence
                ) / len(claim.evidence_refs)
                if avg_strength < strength_threshold:
                    weak.append(claim)
        return weak

    def get_first_party_evidence_claims(self) -> list[ClaimNode]:
        first_party = []
        for claim in self.claims.values():
            for eid in claim.evidence_refs:
                if eid in self.evidence and self.evidence[eid].source_type == "first_party":
                    first_party.append(claim)
                    break
        return first_party

    def get_conflicting_evidence(self) -> list[tuple[str, str, str]]:
        """Returns tuples of (claim_id, evidence_id_1, evidence_id_2) where evidence conflicts."""
        conflicts = []
        # This is a simplified check - real implementation would need semantic analysis
        return conflicts

    def to_dict(self) -> dict:
        return {
            "evidence": {k: v.__dict__ for k, v in self.evidence.items()},
            "claims": {k: v.__dict__ for k, v in self.claims.items()},
            "statistics": {k: v.__dict__ for k, v in self.statistics.items()},
        }


def build_evidence_graph(pages: dict[str, PageState]) -> EvidenceGraph:
    graph = EvidenceGraph()

    # Extract evidence from pages
    evidence_id_counter = 0

    for page_id, page in pages.items():
        # From claims
        for claim in page.claims:
            claim_node = ClaimNode(
                claim_id=claim.claim_id,
                text=claim.text,
                page_id=page_id,
                claim_type=claim.claim_type,
                confidence=claim.confidence,
                evidence_refs=claim.evidence_refs.copy()
            )
            graph.add_claim(claim_node)

        # From statistics
        for stat in page.statistics:
            # Create evidence node for each statistic source
            if stat.source:
                ev_id = f"ev_{stat.statistic_id}"
                evidence_node = EvidenceNode(
                    evidence_id=ev_id,
                    text=f"{stat.value} - {stat.context}",
                    source=stat.source,
                    source_type="third_party" if "http" in (stat.source or "") else "vendor",
                    date=stat.date,
                    strength=0.6,
                    claims_supported=[],
                    pages_using=[page_id] + stat.used_on_pages,
                    statistics_supported=[stat.statistic_id]
                )
                graph.add_evidence(evidence_node)

                # Link claim to this evidence if relevant
                for claim in page.claims:
                    if stat.value.lower() in claim.text.lower() or any(w in claim.text.lower() for w in stat.context.lower().split()[:5]):
                        claim_node = graph.claims.get(claim.claim_id)
                        if claim_node and ev_id not in claim_node.evidence_refs:
                            claim_node.evidence_refs.append(ev_id)
                            claim_node.supporting_evidence.append(ev_id)

            stat_node = StatisticNode(
                statistic_id=stat.statistic_id,
                value=stat.value,
                context=stat.context,
                page_id=page_id,
                source=stat.source,
                date=stat.date,
                used_on_pages=stat.used_on_pages.copy()
            )
            graph.add_statistic(stat_node)

        # From explicit evidence refs
        for ev_ref in page.evidence_refs:
            ev_id = f"ev_{page_id}_{evidence_id_counter}"
            evidence_id_counter += 1
            evidence_node = EvidenceNode(
                evidence_id=ev_id,
                text=ev_ref,
                source=ev_ref,
                source_type="external",
                date=None,
                strength=0.5,
                claims_supported=[],
                pages_using=[page_id]
            )
            graph.add_evidence(evidence_node)

    return graph


def analyze_evidence_health(graph: EvidenceGraph) -> dict[str, Any]:
    return {
        "total_evidence": len(graph.evidence),
        "total_claims": len(graph.claims),
        "total_statistics": len(graph.statistics),
        "claims_without_evidence": len(graph.get_claims_without_evidence()),
        "evidence_supporting_multiple_pages": len(graph.get_evidence_supporting_multiple_pages()),
        "overused_statistics": len(graph.get_overused_statistics()),
        "stale_sources": len(graph.get_stale_sources()),
        "weak_evidence_claims": len(graph.get_weak_evidence_claims()),
        "first_party_evidence_claims": len(graph.get_first_party_evidence_claims()),
        "unique_sources": len(graph.source_to_evidence),
        "source_diversity": len(graph.source_to_evidence) / max(len(graph.evidence), 1),
    }