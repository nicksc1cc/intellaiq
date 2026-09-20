"""
Inflexion Intelligence Engine — Quality Vectors
Phase 8: Quality Vectors
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

try:
    from intelligence.core.models import QualityVector, QualityDimension, JevResult, PageState, PageObjective
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from intelligence.core.models import QualityVector, QualityDimension, JevResult, PageState, PageObjective


# Mapping from question primitives to quality dimensions
PRIMITIVE_TO_DIMENSION = {
    "purpose": "subject_specificity",
    "distinctiveness": "intellectual_distinctiveness",
    "evidence": "evidence_quality",
    "specificity": "subject_specificity",
    "differentiation": "site_differentiation",
    "technical_precision": "technical_accuracy",
    "commercial_relevance": "commercial_usefulness",
    "human_writing": "human_writing",
    "structural_coherence": "structural_quality",
    "argument": "argument_quality",
    "citation": "evidence_quality",
    "repetition": "site_differentiation",
    "knowledge": "knowledge_contribution",
    "internal_relationship": "structural_quality",
    "topical_authority": "subject_specificity",
    "ai_discovery": "technical_accuracy",
    "technical_geo": "technical_accuracy",
    "commercial": "commercial_usefulness",
    "outcome": "commercial_usefulness",
}


def calculate_quality_vector(
    page: PageState,
    jev_results: list[JevResult],
    page_objectives: list[PageObjective]
) -> QualityVector:
    # Group results by primitive
    primitive_scores = {}
    primitive_confidences = {}
    primitive_evidence = {}
    primitive_weak = {}
    primitive_strong = {}

    for result in jev_results:
        # Determine primitive from question_id or template
        primitive = _infer_primitive(result.question_id)

        if primitive not in primitive_scores:
            primitive_scores[primitive] = []
            primitive_confidences[primitive] = []
            primitive_evidence[primitive] = []
            primitive_weak[primitive] = []
            primitive_strong[primitive] = []

        score = _extract_score(result)
        conf = result.confidence

        primitive_scores[primitive].append(score)
        primitive_confidences[primitive].append(conf)
        primitive_evidence[primitive].extend(result.evidence_refs)
        if score < 0.4:
            primitive_weak[primitive].append(result.question_id)
        elif score > 0.7:
            primitive_strong[primitive].append(result.question_id)

    # Calculate dimension scores
    dims = {}
    dimension_names = [
        "intellectual_distinctiveness",
        "evidence_quality",
        "subject_specificity",
        "argument_quality",
        "human_writing",
        "structural_quality",
        "site_differentiation",
        "technical_accuracy",
        "commercial_usefulness",
        "editorial_quality",
        "knowledge_contribution",
        "objective_coverage",
        "confidence",
    ]

    for dim_name in dimension_names:
        # Find primitives that map to this dimension
        relevant_primitives = [p for p, d in PRIMITIVE_TO_DIMENSION.items() if d == dim_name]

        if relevant_primitives:
            scores = []
            confs = []
            evidence = []
            weak_qs = []
            strong_qs = []
            for p in relevant_primitives:
                if p in primitive_scores:
                    scores.extend(primitive_scores[p])
                    confs.extend(primitive_confidences[p])
                    evidence.extend(primitive_evidence[p])
                    weak_qs.extend(primitive_weak[p])
                    strong_qs.extend(primitive_strong[p])

            if scores:
                # Weighted average by confidence
                weighted_sum = sum(s * c for s, c in zip(scores, confs))
                total_conf = sum(confs)
                avg_score = weighted_sum / total_conf if total_conf > 0 else sum(scores) / len(scores)
                avg_conf = sum(confs) / len(confs) if confs else 0.3
            else:
                avg_score = 0.5
                avg_conf = 0.2
        else:
            avg_score = 0.5
            avg_conf = 0.2
            evidence = []
            weak_qs = []
            strong_qs = []

        # Special handling for certain dimensions
        if dim_name == "objective_coverage":
            avg_score = _calculate_objective_coverage(page_objectives)
            avg_conf = 0.7
        elif dim_name == "editorial_quality":
            avg_score = _calculate_editorial_quality(page, jev_results)
            avg_conf = 0.5
        elif dim_name == "confidence":
            avg_score = sum(r.confidence for r in jev_results) / len(jev_results) if jev_results else 0.3
            avg_conf = 0.8

        dims[dim_name] = QualityDimension(
            score=avg_score,
            confidence=avg_conf,
            evidence_refs=list(set(evidence)),
            weak_questions=weak_qs,
            strong_questions=strong_qs
        )

    return QualityVector(
        intellectual_distinctiveness=dims["intellectual_distinctiveness"],
        evidence_quality=dims["evidence_quality"],
        subject_specificity=dims["subject_specificity"],
        argument_quality=dims["argument_quality"],
        human_writing=dims["human_writing"],
        structural_quality=dims["structural_quality"],
        site_differentiation=dims["site_differentiation"],
        technical_accuracy=dims["technical_accuracy"],
        commercial_usefulness=dims["commercial_usefulness"],
        editorial_quality=dims["editorial_quality"],
        knowledge_contribution=dims["knowledge_contribution"],
        objective_coverage=dims["objective_coverage"],
        confidence=dims["confidence"],
    )


def _infer_primitive(question_id: str) -> str:
    """Infer the question primitive from the question ID."""
    for primitive in PRIMITIVE_TO_DIMENSION.keys():
        if primitive.upper() in question_id.upper():
            return primitive
    # Check template mappings
    template_primitives = {
        "PURPOSE": "purpose",
        "DISTINCT": "distinctiveness",
        "EVIDENCE": "evidence",
        "SPECIFICITY": "specificity",
        "DIFF": "differentiation",
        "TECH_PRECISION": "technical_precision",
        "COMMERCIAL": "commercial_relevance",
        "WRITING": "human_writing",
        "STRUCTURE": "structural_coherence",
        "ARGUMENT": "argument",
        "CITATION": "citation",
        "REPETITION": "repetition",
        "KNOWLEDGE": "knowledge",
        "INTERNAL": "internal_relationship",
        "AUTHORITY": "topical_authority",
        "AI_DISCOVERY": "ai_discovery",
        "TECH_GEO": "technical_geo",
        "OUTCOME": "outcome",
    }
    for key, prim in template_primitives.items():
        if key in question_id.upper():
            return prim
    return "unknown"


def _extract_score(result: JevResult) -> float:
    """Extract a normalized 0-1 score from a JevResult."""
    if result.question_type.value == "noul":
        return float(result.result) if isinstance(result.result, (int, float)) else 0.5
    elif result.question_type.value == "choice":
        # For choice, use confidence as proxy for score
        return float(result.confidence)
    elif result.question_type.value == "score":
        # Normalize score to 0-1 based on number of levels
        if isinstance(result.probability, dict):
            levels = len(result.probability)
            if levels > 1:
                return float(result.result) / (levels - 1) if isinstance(result.result, (int, float)) else 0.5
        return 0.5
    return 0.5


def _calculate_objective_coverage(page_objectives: list[PageObjective]) -> float:
    if not page_objectives:
        return 0.3
    total_coverage = sum(obj.coverage for obj in page_objectives)
    return min(1.0, total_coverage / len(page_objectives))


def _calculate_editorial_quality(page: PageState, jev_results: list[JevResult]) -> float:
    """Calculate editorial quality from structural and writing signals."""
    score = 0.5

    # Heading structure
    if page.headings:
        h2_count = sum(1 for h in page.headings if not h.startswith("0"))  # non-kicker headings
        if h2_count >= 5:
            score += 0.1
        elif h2_count >= 3:
            score += 0.05

    # Section count
    if len(page.sections) >= 8:
        score += 0.1
    elif len(page.sections) >= 5:
        score += 0.05

    # Evidence presence
    if page.claims:
        evidenced_claims = sum(1 for c in page.claims if c.evidence_refs)
        if evidenced_claims / len(page.claims) > 0.5:
            score += 0.1

    # Visual elements
    if page.images:
        score += 0.05

    # Statistics
    if len(page.statistics) >= 5:
        score += 0.05

    # Penalize formulaic writing patterns
    writing_results = [r for r in jev_results if "WRITING" in r.question_id.upper() or "FORMULAIC" in r.question_id.upper()]
    for r in writing_results:
        if hasattr(r, 'result') and isinstance(r.result, (int, float)):
            if r.result > 0.6:  # High formulaic score
                score -= 0.1

    return max(0.0, min(1.0, score))


def calculate_all_quality_vectors(
    pages: dict[str, PageState],
    all_jev_results: dict[str, list[JevResult]],
    all_page_objectives: dict[str, list[PageObjective]]
) -> dict[str, QualityVector]:
    vectors = {}
    for page_id, page in pages.items():
        jev_results = all_jev_results.get(page_id, [])
        page_objs = all_page_objectives.get(page_id, [])
        vectors[page_id] = calculate_quality_vector(page, jev_results, page_objs)
    return vectors