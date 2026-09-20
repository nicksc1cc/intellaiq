"""
Inflexion Intelligence Engine — Derived Intelligence
Phase 13: Derived Intelligence
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from collections import defaultdict
import itertools

try:
    from intelligence.core.models import (
        IntelligenceRun, Issue, Insight, Severity, IssueCategory,
        KnowledgeGraph, GraphNode, GraphEdge, NodeType, RelationshipType,
        PageState, QualityVector
    )
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from intelligence.core.models import (
        IntelligenceRun, Issue, Insight, Severity, IssueCategory,
        KnowledgeGraph, GraphNode, GraphEdge, NodeType, RelationshipType,
        PageState, QualityVector
    )


@dataclass
class DerivedFinding:
    finding_id: str
    type: str
    title: str
    description: str
    confidence: float
    severity: Severity
    affected_pages: list[str]
    affected_objectives: list[str]
    evidence: list[str]
    metadata: dict = field(default_factory=dict)


def derive_all_intelligence(run: IntelligenceRun) -> list[DerivedFinding]:
    """Run all derived intelligence analyses."""
    findings = []

    findings.extend(_detect_intellectual_ownership_gaps(run))
    findings.extend(_detect_duplication(run))
    findings.extend(_detect_evidence_gaps(run))
    findings.extend(_detect_knowledge_concentration(run))
    findings.extend(_detect_objective_coverage_gaps(run))
    findings.extend(_detect_quality_performance_anomalies(run))
    findings.extend(_detect_uncertainty_clusters(run))
    findings.extend(_detect_argument_overlap(run))
    findings.extend(_detect_concept_orphans(run))

    return findings


def _detect_intellectual_ownership_gaps(run: IntelligenceRun) -> list[DerivedFinding]:
    """Find concepts with no clear owner or multiple claimants."""
    findings = []

    # Build concept -> pages map from knowledge graph
    concept_pages = defaultdict(list)
    for node in run.knowledge_graph.nodes:
        if node.node_type == NodeType.CONCEPT:
            for edge in run.knowledge_graph.edges:
                if edge.target == node.node_id and edge.relationship == RelationshipType.COVERS:
                    # Find page
                    for n in run.knowledge_graph.nodes:
                        if n.node_id == edge.source and n.node_type == NodeType.PAGE:
                            concept_pages[node.label].append(n.label)
                            break

    for concept, pages in concept_pages.items():
        if len(pages) == 0:
            findings.append(DerivedFinding(
                finding_id=f"ownership_orphan_{concept}",
                type="ORPHANED_TERRITORY",
                title=f"Orphaned concept: {concept}",
                description=f"Concept '{concept}' appears in the knowledge graph but no page owns it.",
                confidence=0.8,
                severity=Severity.MEDIUM,
                affected_pages=[],
                affected_objectives=[],
                evidence=[f"concept:{concept}"],
                metadata={"concept": concept}
            ))
        elif len(pages) > 2:
            findings.append(DerivedFinding(
                finding_id=f"ownership_overclaimed_{concept}",
                type="OVERCLAIMED_TERRITORY",
                title=f"Overclaimed concept: {concept}",
                description=f"Concept '{concept}' is claimed by {len(pages)} pages: {', '.join(pages)}. Ownership is unclear.",
                confidence=0.85,
                severity=Severity.HIGH,
                affected_pages=pages,
                affected_objectives=[],
                evidence=[f"concept:{concept}"],
                metadata={"concept": concept, "claimant_pages": pages}
            ))
        elif len(pages) == 2:
            findings.append(DerivedFinding(
                finding_id=f"ownership_shared_{concept}",
                type="SHARED_TERRITORY",
                title=f"Shared concept: {concept}",
                description=f"Concept '{concept}' is shared between {pages[0]} and {pages[1]}. Check for differentiation.",
                confidence=0.75,
                severity=Severity.MEDIUM,
                affected_pages=pages,
                affected_objectives=[],
                evidence=[f"concept:{concept}"],
                metadata={"concept": concept, "pages": pages}
            ))

    return findings


def _detect_duplication(run: IntelligenceRun) -> list[DerivedFinding]:
    """Detect unnecessary duplication across pages."""
    findings = []

    # Check DUPLICATES edges
    for edge in run.knowledge_graph.edges:
        if edge.relationship == RelationshipType.DUPLICATES:
            source_page = edge.source.replace("page:", "")
            target_page = edge.target.replace("page:", "")
            stat = edge.properties.get("statistic", "unknown")

            findings.append(DerivedFinding(
                finding_id=f"dup_stat_{source_page}_{target_page}_{stat}",
                type="UNNECESSARY_DUPLICATION",
                title=f"Duplicate statistic: {stat}",
                description=f"Pages {source_page} and {target_page} both use statistic '{stat}' without recontextualization.",
                confidence=0.9,
                severity=Severity.MEDIUM,
                affected_pages=[source_page, target_page],
                affected_objectives=[],
                evidence=[f"statistic:{stat}"],
                metadata={"statistic": stat, "pages": [source_page, target_page]}
            ))

    # Check OVERLAPS edges with high weight
    for edge in run.knowledge_graph.edges:
        if edge.relationship == RelationshipType.OVERLAPS and edge.weight > 0.3:
            source_page = edge.source.replace("page:", "")
            target_page = edge.target.replace("page:", "")

            findings.append(DerivedFinding(
                finding_id=f"overlap_{source_page}_{target_page}",
                type="CONCEPTUAL_OVERLAP",
                title=f"High conceptual overlap: {source_page} ↔ {target_page}",
                description=f"Pages share {edge.weight:.0%} of their content. Consider specialisation or consolidation.",
                confidence=0.8,
                severity=Severity.HIGH if edge.weight > 0.4 else Severity.MEDIUM,
                affected_pages=[source_page, target_page],
                affected_objectives=[],
                evidence=[],
                metadata={"overlap_score": edge.weight, "pages": [source_page, target_page]}
            ))

    return findings


def _detect_evidence_gaps(run: IntelligenceRun) -> list[DerivedFinding]:
    """Detect claims without evidence, weak evidence, etc."""
    findings = []

    for page_id, page_state in run.page_states.items():
        central_claims = [c for c in page_state.claims if c.is_central]
        unevidenced_central = [c for c in central_claims if not c.evidence_refs]

        if unevidenced_central:
            findings.append(DerivedFinding(
                finding_id=f"evidence_gap_{page_id}",
                type="EVIDENCE_GAP",
                title=f"Central claims lack evidence: {page_id}",
                description=f"{len(unevidenced_central)} central claim(s) on {page_id} have no supporting evidence.",
                confidence=0.85,
                severity=Severity.HIGH,
                affected_pages=[page_id],
                affected_objectives=[],
                evidence=[c.claim_id for c in unevidenced_central],
                metadata={"unevidenced_count": len(unevidenced_central)}
            ))

        # Vendor claims without attribution
        vendor_claims = [c for c in page_state.claims if c.claim_type == "vendor_claim"]
        unattributed_vendor = [c for c in vendor_claims if not c.evidence_refs]

        if unattributed_vendor:
            findings.append(DerivedFinding(
                finding_id=f"vendor_unattributed_{page_id}",
                type="VENDOR_CLAIM_UNATTRIBUTED",
                title=f"Unattributed vendor claims: {page_id}",
                description=f"{len(unattributed_vendor)} vendor/platform claim(s) presented without source attribution.",
                confidence=0.9,
                severity=Severity.MEDIUM,
                affected_pages=[page_id],
                affected_objectives=[],
                evidence=[c.claim_id for c in unattributed_vendor],
                metadata={"unattributed_count": len(unattributed_vendor)}
            ))

    return findings


def _detect_knowledge_concentration(run: IntelligenceRun) -> list[DerivedFinding]:
    """Detect over-concentration of knowledge."""
    findings = []

    # One source supporting many claims
    source_claims = defaultdict(list)
    for page_state in run.page_states.values():
        for claim in page_state.claims:
            for ev_ref in claim.evidence_refs:
                source_claims[ev_ref].append(claim.claim_id)

    for source, claims in source_claims.items():
        if len(claims) > 10:
            findings.append(DerivedFinding(
                finding_id=f"concentration_source_{source}",
                type="KNOWLEDGE_CONCENTRATION",
                title=f"Single source overuse: {source}",
                description=f"Source '{source}' supports {len(claims)} claims across the site. Risk of single-point-of-failure.",
                confidence=0.8,
                severity=Severity.MEDIUM,
                affected_pages=list(set(c.split("_")[0] for c in claims if "_" in c)),
                affected_objectives=[],
                evidence=[source],
                metadata={"source": source, "claim_count": len(claims)}
            ))

    # One statistic used on many pages
    stat_pages = defaultdict(list)
    for page_state in run.page_states.values():
        for stat in page_state.statistics:
            stat_pages[stat.value].extend(stat.used_on_pages)

    for stat_value, pages in stat_pages.items():
        unique_pages = list(set(pages))
        if len(unique_pages) > 5:
            findings.append(DerivedFinding(
                finding_id=f"concentration_stat_{stat_value[:30]}",
                type="STATISTIC_OVERUSE",
                title=f"Overused statistic: {stat_value[:50]}...",
                description=f"Statistic '{stat_value[:50]}...' appears on {len(unique_pages)} pages. Consider if each usage adds new context.",
                confidence=0.85,
                severity=Severity.MEDIUM,
                affected_pages=unique_pages,
                affected_objectives=[],
                evidence=[stat_value],
                metadata={"statistic": stat_value, "page_count": len(unique_pages)}
            ))

    # One objective with no strong owner
    obj_owners = defaultdict(list)
    for page_id, page_objs in run.page_objectives.items():
        for po in page_objs:
            if po.quality > 0.7:
                obj_owners[po.objective_id].append(page_id)

    for obj_id, owners in obj_owners.items():
        if len(owners) == 0:
            obj = next((o for o in run.objectives if o.objective_id == obj_id), None)
            if obj:
                findings.append(DerivedFinding(
                    finding_id=f"objective_unowned_{obj_id}",
                    type="OBJECTIVE_GAP",
                    title=f"Objective has no strong owner: {obj.code}",
                    description=f"Objective '{obj.title}' has no page with quality > 0.7.",
                    confidence=0.75,
                    severity=Severity.HIGH,
                    affected_pages=[],
                    affected_objectives=[obj_id],
                    evidence=[],
                    metadata={"objective_id": obj_id}
                ))

    return findings


def _detect_objective_coverage_gaps(run: IntelligenceRun) -> list[DerivedFinding]:
    """Detect objectives with poor coverage."""
    findings = []

    for page_id, page_objs in run.page_objectives.items():
        for po in page_objs:
            if po.is_primary and po.coverage < 0.5:
                findings.append(DerivedFinding(
                    finding_id=f"obj_coverage_{page_id}_{po.objective_id}",
                    type="OBJECTIVE_COVERAGE_GAP",
                    title=f"Primary objective poorly covered: {page_id}",
                    description=f"Page {page_id} has primary objective {po.objective_id} with only {po.coverage:.0%} coverage.",
                    confidence=0.8,
                    severity=Severity.HIGH,
                    affected_pages=[page_id],
                    affected_objectives=[po.objective_id],
                    evidence=po.weak_questions,
                    metadata={"coverage": po.coverage, "question_count": po.question_count}
                ))

    return findings


def _detect_quality_performance_anomalies(run: IntelligenceRun) -> list[DerivedFinding]:
    """Detect quality/performance mismatches."""
    from intelligence.performance.performance_schema import calculate_quality_performance_anomalies

    # Convert quality vectors to dict format
    qv_dict = {}
    for page_id, qv in run.quality_vectors.items():
        if hasattr(qv, 'to_dict'):
            qv_dict[page_id] = qv.to_dict()
        else:
            qv_dict[page_id] = qv

    anomalies = calculate_quality_performance_anomalies(qv_dict, run.performance_data)

    findings = []
    for a in anomalies:
        findings.append(DerivedFinding(
            finding_id=f"qp_anomaly_{a['page_id']}_{a['type']}",
            type="QUALITY_PERFORMANCE_ANOMALY",
            title=f"Quality/Performance anomaly: {a['type']}",
            description=a["description"],
            confidence=0.75,
            severity=Severity.HIGH if a.get("severity") == "high" else Severity.MEDIUM,
            affected_pages=[a["page_id"]],
            affected_objectives=[],
            evidence=[],
            metadata=a
        ))

    return findings


def _detect_uncertainty_clusters(run: IntelligenceRun) -> list[DerivedFinding]:
    """Detect clusters of low-confidence judgements."""
    findings = []

    for page_id, jev_results in run.jev_results.items():
        low_conf = [r for r in jev_results if r.confidence < 0.4]
        if len(low_conf) > 5:
            findings.append(DerivedFinding(
                finding_id=f"uncertainty_{page_id}",
                type="UNCERTAINTY_CLUSTER",
                title=f"High uncertainty cluster: {page_id}",
                description=f"Page {page_id} has {len(low_conf)} low-confidence judgements (confidence < 0.4).",
                confidence=0.7,
                severity=Severity.MEDIUM,
                affected_pages=[page_id],
                affected_objectives=[],
                evidence=[r.question_id for r in low_conf],
                metadata={"low_confidence_count": len(low_conf)}
            ))

    return findings


def _detect_argument_overlap(run: IntelligenceRun) -> list[DerivedFinding]:
    """Detect arguments that substantially overlap."""
    findings = []

    arg_pages = defaultdict(list)
    for page_id, page_state in run.page_states.items():
        for arg in page_state.arguments:
            # Use first 100 chars as fingerprint
            fingerprint = arg.text[:100].lower().strip()
            arg_pages[fingerprint].append((page_id, arg.argument_id))

    for fingerprint, pages in arg_pages.items():
        if len(pages) > 1:
            page_ids = list(set(p[0] for p in pages))
            findings.append(DerivedFinding(
                finding_id=f"arg_overlap_{fingerprint[:30]}",
                type="ARGUMENT_OVERLAP",
                title=f"Overlapping arguments across {len(page_ids)} pages",
                description=f"Similar argument found on: {', '.join(page_ids)}. Fragment: {fingerprint[:80]}...",
                confidence=0.75,
                severity=Severity.MEDIUM,
                affected_pages=page_ids,
                affected_objectives=[],
                evidence=[p[1] for p in pages],
                metadata={"argument_fingerprint": fingerprint, "pages": page_ids}
            ))

    return findings


def _detect_concept_orphans(run: IntelligenceRun) -> list[DerivedFinding]:
    """Detect concepts that are central but poorly developed."""
    findings = []

    # Find concepts with many edges but low quality on owning pages
    concept_edges = defaultdict(list)
    for edge in run.knowledge_graph.edges:
        if edge.target.startswith("concept:") or edge.source.startswith("concept:"):
            concept_id = edge.target if edge.target.startswith("concept:") else edge.source
            concept_edges[concept_id].append(edge)

    for concept_id, edges in concept_edges.items():
        if len(edges) > 5:  # Central concept
            # Check if owning pages have low quality
            owning_pages = []
            for edge in edges:
                other = edge.source if edge.target == concept_id else edge.target
                if other.startswith("page:"):
                    owning_pages.append(other.replace("page:", ""))

            low_quality_owners = []
            for page_id in owning_pages:
                qv = run.quality_vectors.get(page_id)
                if qv and qv.subject_specificity.score < 0.5:
                    low_quality_owners.append(page_id)

            if low_quality_owners:
                concept_label = next((n.label for n in run.knowledge_graph.nodes if n.node_id == concept_id), concept_id)
                findings.append(DerivedFinding(
                    finding_id=f"orphan_concept_{concept_id}",
                    type="UNDERDEVELOPED_TERRITORY",
                    title=f"Central concept underdeveloped: {concept_label}",
                    description=f"Concept '{concept_label}' is highly connected ({len(edges)} edges) but owning pages have low specificity: {', '.join(low_quality_owners)}",
                    confidence=0.8,
                    severity=Severity.HIGH,
                    affected_pages=low_quality_owners,
                    affected_objectives=[],
                    evidence=[concept_id],
                    metadata={"concept": concept_label, "edge_count": len(edges), "low_quality_owners": low_quality_owners}
                ))

    return findings


def generate_issues_from_findings(findings: list[DerivedFinding]) -> list[Issue]:
    """Convert derived findings to actionable issues."""
    issues = []

    for f in findings:
        issue = Issue(
            issue_id=f.finding_id,
            category=_map_finding_type_to_category(f.type),
            severity=f.severity,
            confidence=f.confidence,
            affected_pages=f.affected_pages,
            affected_objectives=f.affected_objectives,
            root_cause=f.description,
            evidence=f.evidence,
            description=f.title,
            status="open"
        )
        issues.append(issue)

    return issues


def _map_finding_type_to_category(finding_type: str) -> IssueCategory:
    mapping = {
        "ORPHANED_TERRITORY": IssueCategory.KNOWLEDGE_GRAPH,
        "OVERCLAIMED_TERRITORY": IssueCategory.DIFFERENTIATION,
        "SHARED_TERRITORY": IssueCategory.DIFFERENTIATION,
        "UNNECESSARY_DUPLICATION": IssueCategory.DUPLICATION,
        "CONCEPTUAL_OVERLAP": IssueCategory.DIFFERENTIATION,
        "EVIDENCE_GAP": IssueCategory.EVIDENCE,
        "VENDOR_CLAIM_UNATTRIBUTED": IssueCategory.EVIDENCE,
        "KNOWLEDGE_CONCENTRATION": IssueCategory.KNOWLEDGE_GRAPH,
        "STATISTIC_OVERUSE": IssueCategory.DUPLICATION,
        "OBJECTIVE_GAP": IssueCategory.CONTENT,
        "OBJECTIVE_COVERAGE_GAP": IssueCategory.CONTENT,
        "QUALITY_PERFORMANCE_ANOMALY": IssueCategory.PERFORMANCE,
        "UNCERTAINTY_CLUSTER": IssueCategory.UNCERTAINTY,
        "ARGUMENT_OVERLAP": IssueCategory.DUPLICATION,
        "UNDERDEVELOPED_TERRITORY": IssueCategory.KNOWLEDGE_GRAPH,
    }
    return mapping.get(finding_type, IssueCategory.CONTENT)


def generate_insights_from_findings(findings: list[DerivedFinding]) -> list[Insight]:
    """Generate strategic insights from findings."""
    insights = []

    # Group findings by type
    by_type = defaultdict(list)
    for f in findings:
        by_type[f.type].append(f)

    # Create insight for each significant finding cluster
    for ftype, ffindings in by_type.items():
        if len(ffindings) >= 2:
            affected_pages = []
            for f in ffindings:
                affected_pages.extend(f.affected_pages)
            affected_pages = list(set(affected_pages))

            insight = Insight(
                insight_id=f"insight_{ftype.lower()}",
                type=ftype,
                title=f"Site-wide {ftype.replace('_', ' ').title()}",
                observation=f"{len(ffindings)} instances of {ftype.lower().replace('_', ' ')} detected across the site.",
                supporting_pages=affected_pages,
                supporting_objectives=list(set(o for f in ffindings for o in f.affected_objectives)),
                supporting_questions=list(set(e for f in ffindings for e in f.evidence)),
                supporting_evidence=list(set(e for f in ffindings for e in f.evidence)),
                confidence=sum(f.confidence for f in ffindings) / len(ffindings),
                severity=max((f.severity for f in ffindings), key=lambda s: s.value),
                scope="site_wide" if len(affected_pages) > 3 else "cluster",
                affected_relationships=[],
                historical_change=0.0,
                possible_action=_get_action_for_type(ftype),
                recommended_owner="Content Strategist",
                uncertainty=0.3
            )
            insights.append(insight)

    return insights


def _get_action_for_type(finding_type: str) -> str:
    actions = {
        "ORPHANED_TERRITORY": "Assign concept ownership to a specific page; create content if missing",
        "OVERCLAIMED_TERRITORY": "Clarify ownership boundaries; specialise each page's angle",
        "SHARED_TERRITORY": "Define clear differentiation between the two pages",
        "UNNECESSARY_DUPLICATION": "Remove or recontextualise duplicated statistic on one page",
        "CONCEPTUAL_OVERLAP": "Redesign page boundaries; specialise or consolidate",
        "EVIDENCE_GAP": "Add specific evidence (data, citations, case details) to central claims",
        "VENDOR_CLAIM_UNATTRIBUTED": "Attribute vendor claims with source, date, and context",
        "KNOWLEDGE_CONCENTRATION": "Diversify evidence sources; reduce single-source dependency",
        "STATISTIC_OVERUSE": "Retire statistic from some pages; replace with fresh data",
        "OBJECTIVE_GAP": "Create or strengthen page to own this objective",
        "OBJECTIVE_COVERAGE_GAP": "Add content addressing weak questions for this objective",
        "QUALITY_PERFORMANCE_ANOMALY": "Investigate why quality doesn't translate to performance",
        "UNCERTAINTY_CLUSTER": "Run targeted Jev questions with better state/context",
        "ARGUMENT_OVERLAP": "Differentiate arguments or assign ownership",
        "UNDERDEVELOPED_TERRITORY": "Invest in deepening content on owning pages",
    }
    return actions.get(finding_type, "Investigate and address root cause")