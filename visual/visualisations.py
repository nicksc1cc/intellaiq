"""
Inflexion Intelligence Engine — Visualisations
Phases 15-20: Core Visualisations
"""

from __future__ import annotations
import json
from dataclasses import dataclass
from typing import Any
from pathlib import Path

try:
    from intelligence.core.models import IntelligenceRun, QualityVector, KnowledgeGraph, GraphNode, GraphEdge, NodeType, RelationshipType
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from intelligence.core.models import IntelligenceRun, QualityVector, KnowledgeGraph, GraphNode, GraphEdge, NodeType, RelationshipType


@dataclass
class VisualizationData:
    """Container for all visualization data."""
    objective_matrix: dict
    knowledge_graph: dict
    intellectual_territory: dict
    quality_performance: dict
    evidence_graph: dict
    change_graph: dict
    question_explorer: dict
    issue_map: dict
    ownership_map: dict


def prepare_objective_matrix(run: IntelligenceRun) -> dict:
    """Prepare data for Objective Matrix visualization."""
    pages = run.pages_analyzed
    objectives = [o.objective_id for o in run.objectives]

    matrix = []
    for page_id in pages:
        row = {"page_id": page_id, "cells": []}
        page_objs = run.page_objectives.get(page_id, [])
        obj_map = {po.objective_id: po for po in page_objs}

        for obj_id in objectives:
            po = obj_map.get(obj_id)
            if po:
                row["cells"].append({
                    "objective_id": obj_id,
                    "coverage": po.coverage,
                    "quality": po.quality,
                    "confidence": po.confidence,
                    "question_count": po.question_count,
                    "is_primary": po.is_primary,
                    "ownership": po.ownership,
                    "has_issue": len(po.weak_questions) > 0
                })
            else:
                row["cells"].append({
                    "objective_id": obj_id,
                    "coverage": 0,
                    "quality": 0,
                    "confidence": 0,
                    "question_count": 0,
                    "is_primary": False,
                    "ownership": None,
                    "has_issue": False
                })
        matrix.append(row)

    return {
        "pages": pages,
        "objectives": objectives,
        "matrix": matrix,
        "objective_details": {o.objective_id: o.to_dict() for o in run.objectives}
    }


def prepare_knowledge_graph_viz(run: IntelligenceRun, view: str = "site") -> dict:
    """Prepare knowledge graph for visualization."""
    nodes = []
    edges = []

    # Filter nodes based on view
    if view == "site":
        # All nodes
        nodes = [n.to_dict() for n in run.knowledge_graph.nodes]
        edges = [e.to_dict() for e in run.knowledge_graph.edges]
    elif view.startswith("page:"):
        page_id = view.replace("page:", "")
        # Subgraph around page
        from intelligence.graph.knowledge_graph import get_page_subgraph
        subgraph = get_page_subgraph(run.knowledge_graph, page_id)
        nodes = [n.to_dict() for n in subgraph.nodes]
        edges = [e.to_dict() for e in subgraph.edges]
    elif view.startswith("cluster:"):
        community_id = int(view.replace("cluster:", ""))
        from intelligence.graph.knowledge_graph import get_cluster_subgraph
        subgraph = get_cluster_subgraph(run.knowledge_graph, community_id)
        nodes = [n.to_dict() for n in subgraph.nodes]
        edges = [e.to_dict() for e in subgraph.edges]

    return {
        "nodes": nodes,
        "edges": edges,
        "view": view,
        "stats": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "node_types": _count_node_types(nodes),
            "relationship_types": _count_relationship_types(edges)
        }
    }


def _count_node_types(nodes: list) -> dict:
    counts = {}
    for n in nodes:
        nt = n.get("node_type", "unknown")
        counts[nt] = counts.get(nt, 0) + 1
    return counts


def _count_relationship_types(edges: list) -> dict:
    counts = {}
    for e in edges:
        rt = e.get("relationship", "unknown")
        counts[rt] = counts.get(rt, 0) + 1
    return counts


def prepare_intellectual_territory(run: IntelligenceRun) -> dict:
    """Prepare intellectual territory map."""
    # Build concept -> pages map (using CONCEPT nodes and USES relationships)
    concept_pages = {}
    concept_edges = []

    for node in run.knowledge_graph.nodes:
        if node.node_type == NodeType.CONCEPT:
            owning_pages = []
            for edge in run.knowledge_graph.edges:
                if edge.target == node.node_id and edge.relationship == RelationshipType.USES:
                    for n in run.knowledge_graph.nodes:
                        if n.node_id == edge.source and n.node_type == NodeType.PAGE:
                            owning_pages.append(n.label)
                            break
            if owning_pages:
                concept_pages[node.label] = owning_pages
                concept_edges.extend([{"source": p, "target": node.label, "relationship": "OWNS"} for p in owning_pages])

    # Also check TOPIC nodes with COVERS relationships (for backwards compatibility)
    for node in run.knowledge_graph.nodes:
        if node.node_type == NodeType.TOPIC:
            owning_pages = []
            for edge in run.knowledge_graph.edges:
                if edge.target == node.node_id and edge.relationship == RelationshipType.COVERS:
                    for n in run.knowledge_graph.nodes:
                        if n.node_id == edge.source and n.node_type == NodeType.PAGE:
                            owning_pages.append(n.label)
                            break
            if owning_pages:
                if node.label not in concept_pages:
                    concept_pages[node.label] = owning_pages
                else:
                    # Merge pages
                    for p in owning_pages:
                        if p not in concept_pages[node.label]:
                            concept_pages[node.label].append(p)
                concept_edges.extend([{"source": p, "target": node.label, "relationship": "OWNS"} for p in owning_pages])

    # Identify territories
    territories = {
        "core_territories": [],
        "emerging_territories": [],
        "underdeveloped_territories": [],
        "overlapping_territories": [],
        "orphaned_territories": [],
        "overclaimed_territories": [],
        "unowned_territories": []
    }

    for concept, pages in concept_pages.items():
        qv_scores = [run.quality_vectors.get(p, {}).subject_specificity.score if hasattr(run.quality_vectors.get(p, {}), 'subject_specificity') else 0 for p in pages]
        avg_quality = sum(qv_scores) / len(qv_scores) if qv_scores else 0

        if len(pages) == 0:
            territories["orphaned_territories"].append({"concept": concept, "pages": []})
        elif len(pages) >= 3:
            territories["overclaimed_territories"].append({"concept": concept, "pages": pages, "avg_quality": avg_quality})
        elif len(pages) == 2:
            territories["overlapping_territories"].append({"concept": concept, "pages": pages, "avg_quality": avg_quality})
        elif avg_quality < 0.5:
            territories["underdeveloped_territories"].append({"concept": concept, "pages": pages, "avg_quality": avg_quality})
        elif avg_quality > 0.7:
            territories["core_territories"].append({"concept": concept, "pages": pages, "avg_quality": avg_quality})
        else:
            territories["emerging_territories"].append({"concept": concept, "pages": pages, "avg_quality": avg_quality})

    return {
        "territories": territories,
        "concept_pages": concept_pages,
        "concept_edges": concept_edges,
        "summary": {k: len(v) for k, v in territories.items()}
    }


def prepare_quality_performance(run: IntelligenceRun) -> dict:
    """Prepare Quality x Performance scatter data."""
    from intelligence.performance.performance_schema import calculate_quality_performance_anomalies

    qv_dict = {}
    for page_id, qv in run.quality_vectors.items():
        qv_dict[page_id] = qv.to_dict() if hasattr(qv, 'to_dict') else qv

    anomalies = calculate_quality_performance_anomalies(qv_dict, run.performance_data)

    points = []
    for page_id in run.pages_analyzed:
        qv = run.quality_vectors.get(page_id)
        perf = run.performance_data.get(page_id)

        quality = qv.overall if hasattr(qv, 'overall') else qv.get('overall', 0) if qv else 0

        traffic_score = 0
        if perf:
            if perf.sessions:
                traffic_score += min(perf.sessions / 500, 1.0) * 0.5
            if perf.ai_citations:
                traffic_score += min(perf.ai_citations / 50, 1.0) * 0.3
            if perf.organic_clicks:
                traffic_score += min(perf.organic_clicks / 200, 1.0) * 0.2

        commercial_score = 0
        if perf and perf.leads:
            commercial_score = min(perf.leads / 10, 1.0)

        confidence = qv.confidence.score if hasattr(qv, 'confidence') else qv.get('confidence', {}).get('score', 0.5)

        points.append({
            "page_id": page_id,
            "x": quality,
            "y": traffic_score,
            "size": commercial_score * 20 + 5,
            "confidence": confidence,
            "commercial": commercial_score,
            "anomaly": any(a["page_id"] == page_id for a in anomalies),
            "anomaly_type": next((a["type"] for a in anomalies if a["page_id"] == page_id), None),
            "page_type": run.page_states[page_id].page_type.value if page_id in run.page_states else "unknown"
        })

    return {
        "points": points,
        "anomalies": anomalies,
        "quadrants": {
            "high_quality_high_traffic": [p for p in points if p["x"] > 0.6 and p["y"] > 0.5],
            "high_quality_low_traffic": [p for p in points if p["x"] > 0.6 and p["y"] <= 0.5],
            "low_quality_high_traffic": [p for p in points if p["x"] <= 0.6 and p["y"] > 0.5],
            "low_quality_low_traffic": [p for p in points if p["x"] <= 0.6 and p["y"] <= 0.5]
        }
    }


def prepare_question_explorer(run: IntelligenceRun, page_id: str = None) -> dict:
    """Prepare Question Explorer data."""
    if page_id:
        pages = [page_id]
    else:
        pages = run.pages_analyzed

    explorer = {}
    for pid in pages:
        jev_results = run.jev_results.get(pid, [])
        page_objs = run.page_objectives.get(pid, [])

        by_objective = {}
        for po in page_objs:
            obj_results = [r for r in jev_results if r.objective_id == po.objective_id]
            by_objective[po.objective_id] = {
                "objective_title": next((o.title for o in run.objectives if o.objective_id == po.objective_id), po.objective_id),
                "coverage": po.coverage,
                "quality": po.quality,
                "questions": [
                    {
                        "question_id": r.question_id,
                        "type": r.question_type.value,
                        "result": r.result,
                        "probability": r.probability,
                        "confidence": r.confidence,
                        "evidence_refs": r.evidence_refs,
                        "text_locations": r.text_locations
                    }
                    for r in obj_results
                ]
            }

        explorer[pid] = {
            "page_id": pid,
            "objectives": by_objective,
            "total_questions": len(jev_results),
            "avg_confidence": sum(r.confidence for r in jev_results) / len(jev_results) if jev_results else 0
        }

    return explorer


def prepare_issue_map(run: IntelligenceRun) -> dict:
    """Prepare Issue Map visualization."""
    issues_by_category = {}
    issues_by_severity = {}
    issues_by_page = {}

    for issue in run.issues:
        cat = issue.category.value
        sev = issue.severity.value

        if cat not in issues_by_category:
            issues_by_category[cat] = []
        issues_by_category[cat].append(issue.to_dict())

        if sev not in issues_by_severity:
            issues_by_severity[sev] = []
        issues_by_severity[sev].append(issue.to_dict())

        for page in issue.affected_pages:
            if page not in issues_by_page:
                issues_by_page[page] = []
            issues_by_page[page].append(issue.to_dict())

    return {
        "by_category": issues_by_category,
        "by_severity": issues_by_severity,
        "by_page": issues_by_page,
        "total": len(run.issues),
        "high_confidence": [i.to_dict() for i in run.issues if i.confidence > 0.7]
    }


def prepare_ownership_map(run: IntelligenceRun) -> dict:
    """Prepare Objective Ownership Map."""
    ownership = {}

    for obj in run.objectives:
        owners = []
        for page_id, page_objs in run.page_objectives.items():
            po = next((p for p in page_objs if p.objective_id == obj.objective_id), None)
            if po and po.quality > 0.5:
                owners.append({
                    "page_id": page_id,
                    "quality": po.quality,
                    "coverage": po.coverage,
                    "is_primary": po.is_primary,
                    "ownership": po.ownership
                })

        ownership[obj.objective_id] = {
            "objective": obj.to_dict(),
            "owners": sorted(owners, key=lambda o: o["quality"], reverse=True),
            "has_clear_owner": len([o for o in owners if o["quality"] > 0.7]) == 1,
            "contested": len([o for o in owners if o["quality"] > 0.5]) > 1,
            "unowned": len(owners) == 0
        }

    return ownership


def prepare_all_visualizations(run: IntelligenceRun) -> VisualizationData:
    """Prepare all visualization data for a run."""
    return VisualizationData(
        objective_matrix=prepare_objective_matrix(run),
        knowledge_graph=prepare_knowledge_graph_viz(run),
        intellectual_territory=prepare_intellectual_territory(run),
        quality_performance=prepare_quality_performance(run),
        evidence_graph=run.evidence_graph,  # Already a dict
        change_graph={},  # Would need two runs
        question_explorer=prepare_question_explorer(run),
        issue_map=prepare_issue_map(run),
        ownership_map=prepare_ownership_map(run)
    )


def export_visualizations(viz: VisualizationData, output_dir: Path) -> None:
    """Export all visualizations as JSON files."""
    output_dir.mkdir(parents=True, exist_ok=True)

    for attr_name in [
        "objective_matrix", "knowledge_graph", "intellectual_territory",
        "quality_performance", "evidence_graph", "change_graph",
        "question_explorer", "issue_map", "ownership_map"
    ]:
        data = getattr(viz, attr_name)
        filepath = output_dir / f"{attr_name}.json"
        filepath.write_text(json.dumps(data, indent=2, default=str))