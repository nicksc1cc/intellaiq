"""Jev integration - TypeSafe System One client for atomic page judgements"""

import os
import re
import json
from typing import Any
from dataclasses import asdict

try:
    from .models import JevResult, QuestionTheme, Severity, Ownership
except ImportError:
    from core.models import JevResult, QuestionTheme, Severity, Ownership

# Try to import TypeSafe SDK
try:
    from typesafe_sdk import TypeSafeClient, Choice, Noul, Score
    TYPESAFE_AVAILABLE = True
except ImportError:
    TYPESAFE_AVAILABLE = False


class JevClient:
    """Client for TypeSafe Jev atomic question evaluations"""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("TYPESAFE_API_KEY")
        self.client = None
        self._is_available = TYPESAFE_AVAILABLE and bool(self.api_key)
        
        if self._is_available:
            self.client = TypeSafeClient(api_key=self.api_key)
        else:
            print("[Jev] TypeSafe not available - will use fallback inferences")

    def evaluate_text(self, body_text: str, heading: str, page_title: str) -> list[JevResult]:
        """Run a bundled Jev evaluation on a text segment"""
        state = {
            "body_text": body_text[:32000],
            "heading": heading,
            "page_title": page_title,
        }
        
        return self._run_evaluation(state)

    def _run_evaluation(self, state: dict) -> list[JevResult]:
        """Execute the complete question battery against a page state"""
        
        if self.client and self._is_available:
            return self._run_typesafe(state)
        else:
            return self._run_fallback(state)

    def _run_typesafe(self, state: dict) -> list[JevResult]:
        """Execute using TypeSafe Jev API - returns structured results"""
        try:
            with TypeSafeClient() as client:
                response = client.system_one(
                    state=state,
                    questions={
                        # A01-A02: Page purpose
                        "page_has_purpose": Noul(
                            instructions="Based on 'body_text', 'heading', and 'page_title': Does this page have one clearly identifiable primary intellectual job?"
                        ),
                        "purpose_statable": Noul(
                            instructions="Based on 'body_text' and 'heading': Can that primary job be stated in one sentence?"
                        ),
                        "purpose_distinct": Noul(
                            instructions="Based on 'body_text': Is this page's primary purpose materially different from standard industry content?"
                        ),
                        # C01: Distinctiveness
                        "could_be_any_consultancy": Noul(
                            instructions="Based on 'body_text': Could another competent consultancy publish substantially the same page?"
                        ),
                        "has_specific_observation": Noul(
                            instructions="Based on 'body_text': Does this page contain an Inflexion-specific observation rather than generic industry commentary?"
                        ),
                        "uses_specific_mechanics": Noul(
                            instructions="Based on 'body_text': Does this page use specific mechanics rather than broad industry language?"
                        ),
                        # E01-E03: Human writing
                        "uses_not_x_but_y": Noul(
                            instructions="Based on 'body_text': Does this page use unnecessary 'not X, but Y' contrasts?"
                        ),
                        "uses_rhetorical_questions": Noul(
                            instructions="Based on 'body_text': Does this page contain rhetorical questions?"
                        ),
                        "excessive_explanation": Noul(
                            instructions="Based on 'body_text': Does this page over-explain obvious implications?"
                        ),
                        "contains_slogans": Noul(
                            instructions="Based on 'body_text': Does this page use slogans where observations would be better?"
                        ),
                        # H01-H02: Technical precision
                        "names_technology_correctly": Noul(
                            instructions="Based on 'body_text': Are technologies named correctly (not conflated)?"
                        ),
                        "distinguishes_platforms": Noul(
                            instructions="Based on 'body_text': Does the page distinguish between different platforms appropriately (e.g., ChatGPT vs Gemini vs Google AI Mode)?"
                        ),
                        "avoids_overgeneralizing": Noul(
                            instructions="Based on 'body_text': Does the page avoid generalizing one platform's behavior to all AI systems?"
                        ),
                        # G01: Evidence quality
                        "claims_supported": Noul(
                            instructions="Based on 'body_text': Are major factual claims supported by evidence?"
                        ),
                        "vendor_claim_misrepresented": Noul(
                            instructions="Based on 'body_text': Is any vendor claim presented as independent evidence?"
                        ),
                        # D01-D02: Site differentiation
                        "duplicates_central_argument": Noul(
                            instructions="Based on 'body_text': Does this page seem to duplicate arguments that would be owned by another page?"
                        ),
                        # L01-L03: Writer's eye
                        "writer_noticed_something": Noul(
                            instructions="Based on 'body_text': Does the writer appear to have selectively noticed something?"
                        ),
                        "has_concrete_detail": Noul(
                            instructions="Based on 'body_text': Is there a concrete detail carrying meaning?"
                        ),
                        "leaves_interpretive_space": Noul(
                            instructions="Based on 'body_text': Does the writing leave interpretive space rather than explaining every implication?"
                        ),
                    }
                )
        except Exception as e:
            print(f"[Jev] TypeSafe call failed: {e}")
            return self._run_fallback(state)
        
        results = []
        nouls_map = response.nouls if hasattr(response, 'nouls') else {}
        
        for qid, answer in nouls_map.items():
            if hasattr(answer, 'noul'):
                probability = answer.noul
                result_str = "YES" if probability > 0.6 else ("NO" if probability < 0.4 else "UNCLEAR")
                
                # Map question IDs to themes
                theme_map = {
                    "page_has_purpose": QuestionTheme.PAGE_PURPOSE,
                    "purpose_statable": QuestionTheme.PAGE_PURPOSE,
                    "purpose_distinct": QuestionTheme.DISTINCTIVENESS,
                    "could_be_any_consultancy": QuestionTheme.DISTINCTIVENESS,
                    "has_specific_observation": QuestionTheme.DISTINCTIVENESS,
                    "uses_specific_mechanics": QuestionTheme.DISTINCTIVENESS,
                    "uses_not_x_but_y": QuestionTheme.HUMAN_WRITING,
                    "uses_rhetorical_questions": QuestionTheme.HUMAN_WRITING,
                    "excessive_explanation": QuestionTheme.HUMAN_WRITING,
                    "contains_slogans": QuestionTheme.HUMAN_WRITING,
                    "names_technology_correctly": QuestionTheme.TECHNICAL_PRECISION,
                    "distinguishes_platforms": QuestionTheme.TECHNICAL_PRECISION,
                    "avoids_overgeneralizing": QuestionTheme.TECHNICAL_PRECISION,
                    "claims_supported": QuestionTheme.EVIDENCE,
                    "vendor_claim_misrepresented": QuestionTheme.EVIDENCE,
                    "duplicates_central_argument": QuestionTheme.SITE_DIFFERENTIATION,
                    "writer_noticed_something": QuestionTheme.WRITERS_EYE,
                    "has_concrete_detail": QuestionTheme.WRITERS_EYE,
                    "leaves_interpretive_space": QuestionTheme.WRITERS_EYE,
                }
                
                results.append(JevResult(
                    question_id=qid,
                    theme=theme_map.get(qid, QuestionTheme.PAGE_PURPOSE),
                    result=result_str,
                    confidence=probability,
                    evidence=[],
                ))
        
        return results or self._run_fallback(state)

    def _run_fallback(self, state: dict) -> list[JevResult]:
        """Fallback analysis when TypeSafe is unavailable - uses deterministic heuristics"""
        body_text = state.get("body_text", "")
        heading = state.get("heading", "")
        page_title = state.get("page_title", "")
        
        results = []
        
        # A01-A08: Page purpose
        has_purpose_prob = 0.7 if heading else 0.4
        results.append(JevResult("page_has_purpose", QuestionTheme.PAGE_PURPOSE, 
                                "YES" if has_purpose_prob > 0.6 else "UNCLEAR", has_purpose_prob, []))
        
        # C01-C02: Distinctiveness
        generic_indicators = ["optimize", "transform", "evolve", "landscape", "navigate", "unlock", "holistic"]
        generic_buzz_count = sum(1 for w in generic_indicators if w.lower() in body_text.lower())
        could_be_any = generic_buzz_count > 5
        results.append(JevResult("could_be_any_consultancy", QuestionTheme.DISTINCTIVENESS,
                                "YES" if could_be_any else "NO", 
                                0.7 if could_be_any else 0.5, []))
        
        # E01-E15: Human writing patterns
        not_x_but_y_count = len(re.findall(r'not\s+\w+,\s*but', body_text, re.IGNORECASE))
        results.append(JevResult("uses_not_x_but_y", QuestionTheme.HUMAN_WRITING,
                                "YES" if not_x_but_y_count > 1 else "NO",
                                min(0.5 + not_x_but_y_count * 0.1, 0.95), []))
        
        rhetorical_questions = len(re.findall(r'(The question is|What does this mean|The real question)', body_text))
        results.append(JevResult("uses_rhetorical_questions", QuestionTheme.HUMAN_WRITING,
                                "YES" if rhetorical_questions > 0 else "NO",
                                0.6 if rhetorical_questions > 0 else 0.8, []))
        
        this_is_why = len(re.findall(r'This is why', body_text))
        results.append(JevResult("uses_this_is_why", QuestionTheme.HUMAN_WRITING,
                                "YES" if this_is_why > 0 else "NO", 0.6, []))
        
        # H01-H04: Technical precision
        platform_confusions = ["AI says", "the algorithm", "AI systems"]
        confusion_count = sum(1 for p in platform_confusions if p.lower() in body_text.lower())
        
        # D01-D15: Site differentiation detection
        an_answer_engine_patterns = [
            "share of answer", "share of shelf", "AI citation", "zero-click",
            "Google AI", "ChatGPT", "Perplexity", "Gemini", "Claude", "Rufus"
        ]
        pattern_count = sum(1 for p in an_answer_engine_patterns if p.lower() in body_text.lower())
        
        return results
    
    def evaluate_pair(self, page_a_text: str, page_b_text: str, page_a_name: str, page_b_name: str) -> JevResult:
        """Compare two pages for duplication"""
        state = {
            "page_a_text": page_a_text[:10000],
            "page_b_text": page_b_text[:10000],
            "page_a_name": page_a_name,
            "page_b_name": page_b_name,
        }
        
        if self.client and self._is_available:
            try:
                with TypeSafeClient() as client:
                    response = client.system_one(
                        state=state,
                        questions={
                            "same_central_argument": Noul(
                                instructions=f"Based on 'page_a_text' and 'page_b_text': Do page '{page_a_name}' and page '{page_b_name}' make the same central argument?"
                            ),
                            "same_evidence": Noul(
                                instructions=f"Do these two pages use the same evidence for the same purpose?"
                            ),
                            "same_framework": Noul(
                                instructions=f"Do these two pages use the same framework or rhetorical structure?"
                            ),
                            "same_conclusion": Noul(
                                instructions=f"Do these two pages reach substantially the same conclusion?"
                            ),
                        }
                    )
                    
                    nouls = response.nouls if hasattr(response, 'nouls') else {}
                    results = []
                    for qid, answer in nouls.items():
                        prob = answer.noul if hasattr(answer, 'noul') else 0.5
                        results.append(JevResult(
                            question_id=f"{page_a_name}_vs_{page_b_name}_{qid}",
                            theme=QuestionTheme.SITE_DIFFERENTIATION,
                            result="YES" if prob > 0.6 else ("NO" if prob < 0.4 else "UNCLEAR"),
                            confidence=prob,
                            evidence=[{"page_a": page_a_name, "page_b": page_b_name}]
                        ))
                    return results
            except Exception as e:
                print(f"[Jev] Pair eval failed: {e}")
        
        # Fallback: simple text overlap
        words_a = set(page_a_text.lower().split()[:200])
        words_b = set(page_b_text.lower().split()[:200])
        overlap = len(words_a & words_b) / max(len(words_a | words_b), 1)
        
        return [JevResult(
            question_id=f"{page_a_name}_vs_{page_b_name}_same",
            theme=QuestionTheme.SITE_DIFFERENTIATION,
            result="YES" if overlap > 0.4 else ("NO" if overlap < 0.2 else "UNCLEAR"),
            confidence=overlap,
            evidence=[{"page_a": page_a_name, "page_b": page_b_name}]
        )]


import re