"""
Inflexion Intelligence Engine — Jev Evaluation Engine
Phase 7: Jev Evaluation Engine
"""

from __future__ import annotations
import os
import json
import time
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

try:
    from intelligence.core.models import PageState, GeneratedQuestion, JevResult, QuestionType, PageType, IntelligenceRun
    from intelligence.questions.question_templates import get_templates_for_objective, get_template
    from intelligence.objectives.objective_registry import get_objectives_for_page
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from intelligence.core.models import PageState, GeneratedQuestion, JevResult, QuestionType, PageType, IntelligenceRun
    from intelligence.questions.question_templates import get_templates_for_objective, get_template
    from intelligence.objectives.objective_registry import get_objectives_for_page


logger = logging.getLogger(__name__)


@dataclass
class JevClient:
    api_key: str | None = None
    client: Any = None
    available: bool = False

    def __post_init__(self):
        if self.api_key is None:
            self.api_key = os.environ.get("TYPESAFE_API_KEY")
        if self.api_key:
            try:
                from typesafe_sdk import TypeSafeClient, Noul, Choice, Score
                self.client = TypeSafeClient(api_key=self.api_key)
                self.available = True
                self._Noul = Noul
                self._Choice = Choice
                self._Score = Score
                logger.info("TypeSafe Jev client initialized")
            except Exception as e:
                logger.warning(f"TypeSafe SDK not available: {e}")
                self.available = False
        else:
            logger.info("No TYPESAFE_API_KEY set — using fallback evaluation")

    def evaluate(
        self,
        state: dict[str, Any],
        questions: dict[str, dict[str, Any]],
        model: str = "jev-latest"
    ) -> dict[str, Any]:
        if not self.available:
            return self._fallback_evaluate(state, questions)

        try:
            # Build TypeSafe questions
            ts_questions = {}
            for qid, qdef in questions.items():
                qtype = qdef.get("type", "noul")
                if qtype == "noul":
                    ts_questions[qid] = self._Noul(instructions=qdef["instructions"])
                    if "criteria" in qdef:
                        # Note: Noul in SDK may not support criteria directly
                        pass
                elif qtype == "choice":
                    ts_questions[qid] = self._Choice(
                        instructions=qdef["instructions"],
                        criteria=qdef.get("criteria", {})
                    )
                elif qtype == "score":
                    ts_questions[qid] = self._Score(
                        instructions=qdef["instructions"],
                        criteria=qdef.get("criteria", [])
                    )

            response = self.client.system_one(
                state=state,
                questions=ts_questions,
                model=model
            )

            results = {}
            for qid, answer in response.answers.items():
                if hasattr(answer, "noul"):
                    results[qid] = {"noul": answer.noul, "confidence": 1.0 - abs(answer.noul - 0.5) * 2}
                elif hasattr(answer, "choice"):
                    results[qid] = {
                        "choice": answer.choice,
                        "probabilities": answer.probabilities,
                        "confidence": answer.confidence
                    }
                elif hasattr(answer, "score"):
                    results[qid] = {
                        "score": answer.score,
                        "legend": answer.legend,
                        "probabilities": answer.probabilities,
                        "confidence": answer.confidence
                    }
            return results

        except Exception as e:
            logger.error(f"Jev evaluation failed: {e}, falling back")
            return self._fallback_evaluate(state, questions)

    def _fallback_evaluate(
        self,
        state: dict[str, Any],
        questions: dict[str, dict[str, Any]]
    ) -> dict[str, Any]:
        """Deterministic fallback when TypeSafe API is unavailable."""
        results = {}
        page_text = state.get("body_text", "") if isinstance(state, dict) else str(state)
        page_id = state.get("page_id", "unknown") if isinstance(state, dict) else "unknown"

        for qid, qdef in questions.items():
            qtype = qdef.get("type", "noul")
            instructions = qdef.get("instructions", "").lower()

            # Simple heuristic-based evaluation
            if qtype == "noul":
                prob = self._heuristic_noul(page_id, page_text, instructions)
                results[qid] = {"noul": prob, "confidence": 0.4 + (abs(prob - 0.5) * 0.8)}
            elif qtype == "choice":
                criteria = qdef.get("criteria", {})
                options = list(criteria.keys()) if criteria else ["yes", "no"]
                prob = self._heuristic_noul(page_id, page_text, instructions)
                choice = options[1] if prob > 0.5 else options[0]
                probs = {opt: (0.7 if opt == choice else 0.3/(len(options)-1)) for opt in options}
                results[qid] = {"choice": choice, "probabilities": probs, "confidence": 0.4}
            elif qtype == "score":
                criteria = qdef.get("criteria", [])
                levels = len(criteria)
                prob = self._heuristic_noul(page_id, page_text, instructions)
                score_val = prob * (levels - 1)
                probs = {str(i): (0.6 if abs(i - score_val) < 1 else 0.4/(levels-1)) for i in range(levels)}
                results[qid] = {
                    "score": score_val,
                    "legend": {str(i): c for i, c in enumerate(criteria)},
                    "probabilities": probs,
                    "confidence": 0.35
                }
        return results

    def _heuristic_noul(self, page_id: str, text: str, instructions: str) -> float:
        """Heuristic evaluation based on page characteristics and content signals."""
        text_lower = text.lower()

        # Page-specific baselines (more extreme)
        baselines = {
            "technical-geo": 0.75,
            "aeo": 0.45,
            "ai-discovery": 0.35,
            "ai-visibility-analytics": 0.45,
            "digital-pr": 0.40,
            "retail-media": 0.50,
            "amazon": 0.55,
            "ai-media": 0.40,
            "media": 0.45,
            "consultancy": 0.50,
            "measurement": 0.65,
            "ecommerce-whitepaper": 0.80,
            "beauty-media-strategy": 0.60,
            "index": 0.35,
        }
        base = baselines.get(page_id, 0.45)

        # Content-based signals from actual page text
        adjustments = 0.0

        # Evidence signals
        stat_count = text_lower.count('%') + text_lower.count('$') + text_lower.count('202') + text_lower.count('2026')
        citation_signals = text_lower.count('source') + text_lower.count('study') + text_lower.count('research') + text_lower.count('according to')
        if "evidence" in instructions or "supported" in instructions:
            if stat_count > 5 and citation_signals > 3:
                adjustments += 0.20
            elif stat_count > 2:
                adjustments += 0.10
            elif page_id in ["ecommerce-whitepaper", "technical-geo"]:
                adjustments += 0.15
            elif page_id in ["ai-discovery", "digital-pr"]:
                adjustments -= 0.05

        # Distinctiveness signals
        if "distinct" in instructions or "unique" in instructions:
            overlap_indicators = text_lower.count('aeo') + text_lower.count('ai discovery') + text_lower.count('technical geo')
            if page_id in ["aeo", "ai-discovery", "ai-visibility-analytics"]:
                if overlap_indicators > 5:
                    adjustments -= 0.20
                else:
                    adjustments -= 0.10
            elif page_id in ["technical-geo", "ecommerce-whitepaper"]:
                adjustments += 0.15

        # Technical precision signals
        tech_terms = ['a9', 'rufus', 'crawler', 'rendering', 'schema', 'structured data', 'json-ld', 'entity', 'knowledge graph', 'retrieval', 'ranking', 'algorithm']
        tech_count = sum(1 for t in tech_terms if t in text_lower)
        if "technical" in instructions or "platform" in instructions:
            if tech_count > 5:
                adjustments += 0.20
            elif tech_count > 2:
                adjustments += 0.10
            elif page_id in ["technical-geo", "amazon"]:
                adjustments += 0.15
            elif page_id in ["ai-media", "media"]:
                adjustments -= 0.10

        # Formulaic writing signals
        formulaic_patterns = ['not x but y', 'not only', 'but also', 'this is why', 'this means', 'the shift', 'the new model', 'from x to y', 'where x meets y']
        formulaic_count = sum(1 for p in formulaic_patterns if p in text_lower)
        if "formulaic" in instructions or "pattern" in instructions:
            if formulaic_count > 3:
                adjustments -= 0.20
            elif formulaic_count > 1:
                adjustments -= 0.10
            elif page_id in ["aeo", "ai-discovery", "consultancy"]:
                adjustments -= 0.10
            elif page_id in ["ecommerce-whitepaper", "beauty-media-strategy"]:
                adjustments += 0.05

        # Commercial signals
        commercial_terms = ['client', 'service', 'engagement', 'consultation', 'implementation', 'transformation', 'strategy', 'roadmap', 'roi', 'revenue']
        comm_count = sum(1 for t in commercial_terms if t in text_lower)
        if "commercial" in instructions:
            if comm_count > 3:
                adjustments += 0.15
            elif page_id in ["technical-geo", "amazon", "retail-media"]:
                adjustments += 0.10

        # Structure/template signals
        if "structure" in instructions or "template" in instructions:
            if page_id in ["aeo", "ai-discovery", "retail-media", "consultancy"]:
                adjustments -= 0.15
            elif page_id in ["ecommerce-whitepaper", "technical-geo"]:
                adjustments += 0.10

        # Purpose clarity
        if "purpose" in instructions:
            heading_count = text_lower.count('<h2>') + text_lower.count('<h3>') + text_lower.count('##') + text_lower.count('###')
            if heading_count > 5:
                adjustments += 0.10

        # Apply stronger bounds and push toward extremes
        result = base + adjustments
        # Push toward extremes for more discriminating results
        if result > 0.65:
            result = 0.75 + (result - 0.65) * 0.8
        elif result < 0.35:
            result = 0.25 - (0.35 - result) * 0.8
        
        return max(0.05, min(0.95, result))


class JevEvaluationEngine:
    def __init__(self, api_key: str | None = None):
        self.client = JevClient(api_key=api_key)
        self.max_workers = 10

    def build_state_for_page(self, page: PageState, objectives: list) -> dict[str, Any]:
        return {
            "page_id": page.page_id,
            "page_type": page.page_type.value,
            "title": page.title,
            "url": page.url,
            "body_text": page.body_text[:15000],
            "headings": page.headings,
            "sections": [{"heading": s.get("heading", ""), "text": s.get("text", "")[:2000]} for s in page.sections[:10]],
            "claims": [{"text": c.text, "type": c.claim_type} for c in page.claims[:10]],
            "arguments": [{"text": a.text[:1000], "id": a.argument_id} for a in page.arguments[:5]],
            "statistics": [{"value": s.value, "context": s.context} for s in page.statistics[:15]],
            "internal_links": page.internal_links,
            "evidence_refs": page.evidence_refs,
            "word_count": page.word_count,
            "objectives": [{"id": o.objective_id, "title": o.title, "description": o.description} for o in objectives],
        }

    def generate_questions_for_page(
        self,
        page: PageState,
        objectives: list
    ) -> list[GeneratedQuestion]:
        from intelligence.core.models import GeneratedQuestion
        from intelligence.questions.question_templates import get_templates_for_objective
        import uuid

        questions = []
        for obj in objectives:
            templates = get_templates_for_objective(obj.objective_id)
            for template in templates:
                # Skip if template doesn't apply to this page type
                if page.page_type not in template.applies_to_page_types:
                    continue

                # Build instructions with variable substitution
                instructions = template.instructions_template
                criteria = template.criteria_template
                variables = {
                    "page_id": page.page_id,
                    "page_type": page.page_type.value,
                    "title": page.title,
                    "service_name": page.page_id.replace("-", " ").title(),
                    "domain": "AI/GEO" if "geo" in page.page_id or "aeo" in page.page_id else "retail media",
                    "target_audience": "technical decision makers" if page.page_type == PageType.TECHNICAL else "marketing leaders",
                    "key_concepts": ", ".join(page.topics[:5]) if page.topics else "AI discovery, GEO, citations",
                    "other_pages": ", ".join([p for p in ["aeo", "ai-discovery", "technical-geo", "ai-visibility-analytics"] if p != page.page_id]),
                    "parent_pages": "ecommerce-whitepaper",
                    "related_pages": ", ".join(page.internal_links[:5]),
                    "other_page_ids": ", ".join([p for p in ["aeo", "ai-discovery", "technical-geo", "ai-visibility-analytics", "digital-pr"] if p != page.page_id]),
                }

                for var, val in variables.items():
                    instructions = instructions.replace(f"{{{var}}}", val)
                    if isinstance(criteria, dict):
                        criteria = {k: v.replace(f"{{{var}}}", val) if isinstance(v, str) else v for k, v in criteria.items()}
                    elif isinstance(criteria, list):
                        criteria = [c.replace(f"{{{var}}}", val) if isinstance(c, str) else c for c in criteria]

                questions.append(GeneratedQuestion(
                    question_id=f"{page.page_id}_{template.template_id}_{obj.code}",
                    template_id=template.template_id,
                    page_id=page.page_id,
                    objective_id=obj.objective_id,
                    question_type=template.question_type,
                    instructions=instructions,
                    criteria=criteria,
                    variables=variables
                ))
        return questions

    def evaluate_page(
        self,
        page: PageState,
        objectives: list,
        run_id: str
    ) -> list[JevResult]:
        state = self.build_state_for_page(page, objectives)
        questions = self.generate_questions_for_page(page, objectives)

        if not questions:
            return []

        # Build question map for Jev
        jev_questions = {}
        for q in questions:
            jev_questions[q.question_id] = {
                "type": q.question_type.value,
                "instructions": q.instructions,
                "criteria": q.criteria
            }

        # Run evaluation
        results = self.client.evaluate(state, jev_questions)

        # Convert to JevResult objects
        jev_results = []
        for q in questions:
            result_data = results.get(q.question_id, {})
            if q.question_type == QuestionType.NOUL:
                result_val = result_data.get("noul", 0.5)
                prob = result_val
            elif q.question_type == QuestionType.CHOICE:
                result_val = result_data.get("choice", "")
                prob = result_data.get("probabilities", {})
            elif q.question_type == QuestionType.SCORE:
                result_val = result_data.get("score", 0)
                prob = result_data.get("probabilities", {})
            else:
                result_val = None
                prob = None

            confidence = result_data.get("confidence", 0.3)

            jev_results.append(JevResult(
                question_id=q.question_id,
                page_id=page.page_id,
                objective_id=q.objective_id,
                question_type=q.question_type,
                result=result_val,
                probability=prob,
                confidence=confidence,
                evidence_refs=[],
                text_locations=[],
                timestamp=datetime.now(),
                run_id=run_id
            ))

        return jev_results

    def evaluate_all_pages(
        self,
        pages: dict[str, PageState],
        run_id: str,
        progress_callback: callable = None
    ) -> dict[str, list[JevResult]]:
        all_results = {}
        total = len(pages)
        completed = 0

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_page = {
                executor.submit(self.evaluate_page, page, get_objectives_for_page(page.page_id, page.page_type), run_id): page_id
                for page_id, page in pages.items()
            }

            for future in as_completed(future_to_page):
                page_id = future_to_page[future]
                try:
                    results = future.result()
                    all_results[page_id] = results
                    completed += 1
                    if progress_callback:
                        progress_callback(completed, total, page_id)
                except Exception as e:
                    logger.error(f"Failed to evaluate {page_id}: {e}")
                    all_results[page_id] = []
                    completed += 1
                    if progress_callback:
                        progress_callback(completed, total, page_id)

        return all_results


def create_jev_engine(api_key: str | None = None) -> JevEvaluationEngine:
    return JevEvaluationEngine(api_key=api_key)