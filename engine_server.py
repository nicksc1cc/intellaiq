#!/usr/bin/env python3
"""IntellaIQ Engine - Website Intelligence Analysis Server.

A lightweight HTTP server that provides:
  - POST /api/scan    - Crawl a URL, extract pages, return top 10 decision-relevant pages
  - POST /api/analyze - Run JEV atomic question analysis on page data
  - GET  /            - Serve the engine.html frontend

Usage:
  /Volumes/My\ Passport/sloptotal/venv/bin/python engine_server.py [--port PORT]

Requires: requests, beautifulsoup4
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.parse
import os
import sys
import re
import subprocess
import traceback
from urllib.parse import urlparse, urljoin
from datetime import datetime

import requests
from bs4 import BeautifulSoup

# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────

SERVER_PORT = int(os.environ.get("PORT", os.environ.get("ENGINE_PORT", "8338")))
UI_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui")
ENGINE_HTML = os.path.join(UI_DIR, "engine.html")

# JEV adapter paths (use sys.executable for cross-platform)
PYTHON_BIN = sys.executable
ADAPTER_DIR = os.path.dirname(os.path.abspath(__file__))
JEV_ADAPTER = os.path.join(ADAPTER_DIR, "typesafe_jev_adapter.py")

# Priority scoring for URLs
URL_PRIORITY_KEYWORDS = {
    # High priority (positive score)
    "home": 5, "index": 5, "product": 5, "solutions": 5, "pricing": 5,
    "about": 4, "platform": 4, "features": 4, "how-it-works": 4,
    "case-studies": 4, "case-study": 4, "industries": 3,
    "resources": 3, "blog": 3, "news": 3, "docs": 3,
    "documentation": 3, "contact": 2, "demo": 4, "why": 3,
    "benefits": 4, "capabilities": 4, "integrations": 3,
    "customers": 4, "testimonials": 3, "reviews": 3,
}
URL_PRIORITY_BLOCKLIST = {
    "privacy", "privacy-policy", "terms", "terms-of-service",
    "tos", "login", "signin", "sign-in", "register", "signup",
    "sign-up", "careers", "jobs", "legal", "cookie",
    "tag/", "author/", "category/", "page/", "wp-",
    ".css", ".js", ".png", ".jpg", ".gif", ".svg", ".ico",
    "mailto:", "tel:", "#", "javascript:",
}

# ──────────────────────────────────────────────
# Question library (12 questions, 4 categories)
# ──────────────────────────────────────────────

DECISION_QUESTIONS = [
    # ── BUSINESS ──
    {
        "id": "what_company_sells",
        "category": "business",
        "analysis_type": "business_model",
        "question": "What does this company actually sell?",
        "instructions": (
            "Based on the page content, identify the specific products, services, "
            "or offerings this company provides. Be concrete — name the exact "
            "product names, service tiers, or solution categories mentioned."
        ),
    },
    {
        "id": "who_is_targeting",
        "category": "business",
        "analysis_type": "audience",
        "question": "Who is this company really targeting?",
        "instructions": (
            "Identify the specific customer segments, industries, roles, or "
            "use cases this company addresses. Look for explicit targeting "
            "language as well as implicit signals (examples, testimonials, case studies)."
        ),
    },
    {
        "id": "what_problem",
        "category": "business",
        "analysis_type": "problem",
        "question": "What problem is this company solving?",
        "instructions": (
            "Identify the core problem(s) this company claims to solve. "
            "Distinguish between the stated problem (marketing language) and "
            "the actual operational problem the product addresses."
        ),
    },
    # ── POSITIONING ──
    {
        "id": "how_positioning",
        "category": "positioning",
        "analysis_type": "positioning",
        "question": "How is this company positioning itself?",
        "instructions": (
            "Analyse the company's positioning strategy — the market category "
            "they claim, the competitors they compare to, the value proposition "
            "they emphasize. Is this market leader, innovator, challenger, "
            "cost-effective alternative, or enterprise-grade?"
        ),
    },
    {
        "id": "what_makes_different",
        "category": "positioning",
        "analysis_type": "differentiation",
        "question": "What makes this company different?",
        "instructions": (
            "Identify explicit differentiation claims — what the company says "
            "sets them apart from alternatives. Also identify implicit "
            "differentiators (features, capabilities, approach) that "
            "distinguish them from competitors."
        ),
    },
    {
        "id": "what_believe",
        "category": "positioning",
        "analysis_type": "narrative",
        "question": "What does the company want customers to believe?",
        "instructions": (
            "Identify the core narrative and belief system the company wants "
            "to implant. This is the 'belief transfer' — the emotional or "
            "rational conviction a visitor should leave with. Look beyond "
            "features to the underlying story."
        ),
    },
    # ── EVIDENCE ──
    {
        "id": "how_substantiate",
        "category": "evidence",
        "analysis_type": "evidence",
        "question": "How well does the company substantiate its claims?",
        "instructions": (
            "Evaluate the overall quality and quantity of evidence supporting "
            "the company's key claims. Consider: data citations, case studies, "
            "testimonials, certifications, published research, statistics, "
            "social proof, or third-party validations."
        ),
    },
    {
        "id": "strongest_claims",
        "category": "evidence",
        "analysis_type": "strongest_claims",
        "question": "Which claims are strongest?",
        "instructions": (
            "Identify the specific claims on this site that are best supported "
            "by evidence. A strong claim has: specific data, named sources, "
            "verifiable references, or detailed case examples. Name the claims "
            "and why they are strong."
        ),
    },
    {
        "id": "evidence_gaps",
        "category": "evidence",
        "analysis_type": "evidence_gaps",
        "question": "Which important claims lack evidence?",
        "instructions": (
            "Identify important claims that lack supporting evidence. These are "
            "claims a sceptical buyer would want verified but the site provides "
            "only assertion without substantiation. Focus on claims that matter "
            "for purchase decisions."
        ),
    },
    # ── OPPORTUNITY ──
    {
        "id": "biggest_gaps",
        "category": "opportunity",
        "analysis_type": "gaps",
        "question": "Where are the biggest gaps?",
        "instructions": (
            "Identify the biggest gaps between what the company promises and "
            "what it demonstrates. Also consider gaps in their offering, "
            "positioning, or evidence compared to what a sophisticated buyer "
            "would need to make a decision."
        ),
    },
    {
        "id": "where_opportunities",
        "category": "opportunity",
        "analysis_type": "opportunities",
        "question": "Where might there be opportunities?",
        "instructions": (
            "Identify strategic opportunities: underserved customer segments, "
            "weak competitor positioning, gaps in their narrative, features "
            "they could emphasise more, or market angles they are missing."
        ),
    },
    {
        "id": "investigate_next",
        "category": "opportunity",
        "analysis_type": "investigation",
        "question": "What should we investigate next?",
        "instructions": (
            "Based on the evidence so far, recommend the next areas to investigate "
            "— specific questions to research, claims to verify, competitors to "
            "compare, or customers to interview. Prioritise by decision impact."
        ),
    },
]


def make_atomic_questions(decision_question, page_content):
    """Generate atomic questions with StickyRice-level specificity.

    Produces 10-12 atomic (noul) questions across multiple dimensions:
    - Direct evidence (does the page explicitly say X)
    - Signal consistency (is X repeated across sections)
    - Specificity (is X specific or vague)
    - Corroboration (is X supported by other claims)
    - Contradiction (is there counter-evidence)
    - Inference (what can be reasonably inferred)
    """
    atomic = []
    text = page_content[:8000]
    analysis_type = decision_question.get("analysis_type", "")
    concepts_map = {
        "business_model": [
            ("what they sell", "core product offering"),
            ("their pricing model", "revenue structure"),
            ("their target market", "market definition"),
            ("their value chain", "delivery approach"),
            ("their business model", "commercial logic"),
        ],
        "audience": [
            ("who they target", "customer definition"),
            ("their ideal customer profile", "buyer persona"),
            ("their use cases", "application scenarios"),
            ("their industry focus", "sector specificity"),
            ("their customer segments", "segment clarity"),
        ],
        "problem": [
            ("the problem they solve", "problem definition"),
            ("the customer pain point", "pain clarity"),
            ("the root cause they address", "causal claim"),
            ("the outcome they deliver", "result promise"),
            ("why this matters now", "timeliness claim"),
        ],
        "positioning": [
            ("their market category", "category claim"),
            ("their value proposition", "value definition"),
            ("their competitive frame", "competition framing"),
            ("their positioning language", "messaging consistency"),
            ("their market claim", "market assertion"),
        ],
        "differentiation": [
            ("what makes them different", "differentiation claim"),
            ("their unique advantage", "uniqueness"),
            ("their competitive moat", "defensibility"),
            ("their comparative claim", "comparison"),
            ("their proprietary capability", "proprietary claim"),
        ],
        "narrative": [
            ("their core narrative", "story"),
            ("their mission statement", "mission"),
            ("their brand promise", "promise"),
            ("their emotional appeal", "emotion"),
            ("their vision", "vision"),
        ],
        "evidence": [
            ("supporting data they provide", "data evidence"),
            ("customer proof they show", "social proof"),
            ("third-party validation", "external proof"),
            ("case study specificity", "case depth"),
            ("quantitative claims", "metrics"),
        ],
        "strongest_claims": [
            ("their best-supported claim", "top claim"),
            ("their most specific evidence", "specific evidence"),
            ("their most convincing proof", "convincing proof"),
            ("their most verifiable assertion", "verifiable"),
            ("their most frequently repeated claim", "repeated claim"),
        ],
        "evidence_gaps": [
            ("a claim without supporting evidence", "unsupported claim"),
            ("an assertion that needs proof", "needs proof"),
            ("a promise without specifics", "vague promise"),
            ("a gap in their evidence chain", "evidence gap"),
            ("an area lacking detail", "missing detail"),
        ],
        "gaps": [
            ("a gap in their offering", "offering gap"),
            ("a missing element", "missing element"),
            ("an unaddressed need", "unaddressed need"),
            ("a weakness in positioning", "positioning weakness"),
            ("an area of ambiguity", "ambiguity"),
        ],
        "opportunities": [
            ("an unmet customer need", "unmet need"),
            ("an underdeveloped market angle", "market angle"),
            ("a potential growth area", "growth area"),
            ("a positioning whitespace", "whitespace"),
            ("an adjacent possibility", "adjacent"),
        ],
        "investigation": [
            ("the most important unknown", "key unknown"),
            ("a critical question unanswered", "critical question"),
            ("what to verify externally", "verify need"),
            ("a competitor vulnerability", "competitor weak point"),
            ("a customer insight gap", "insight gap"),
        ],
    }
    concepts = concepts_map.get(analysis_type, [
        ("the core offering", "offering"),
        ("the value claim", "value"),
        ("the key message", "message"),
        ("the supporting detail", "detail"),
        ("the underlying assumption", "assumption"),
    ])

    # Dimension 1: Direct evidence (questions 1-5)
    for i in range(5):
        concept, dimension = concepts[i % len(concepts)]
        templates = [
            f"Does the page explicitly state what {concept} is?",
            f"Is there direct evidence supporting their claim about {concept}?",
            f"Does the page provide specific details about {concept}?",
            f"Is {concept} described with clarity and precision?",
            f"Would a reader understand {concept} from the page alone?",
        ]
        atomic.append({
            "id": f"{decision_question['id']}_direct_{i+1}",
            "type": "noul",
            "instructions": templates[i],
            "criteria": {"true": "Yes, the page clearly supports this", "false": "No, the page does not"},
            "source_refs": [decision_question["id"], f"page_evidence_{dimension}"],
            "why_it_matters": f"Direct evidence for {concept} is the foundation of the '{decision_question['question']}' assessment",
            "decision_links": [decision_question["id"]],
        })

    # Dimension 2: Signal consistency (questions 6-8)
    consistency_templates = [
        f"Is the claim about '{concepts[0][0]}' consistent across the page?",
        f"Are there contradictions in how '{concepts[1][0]}' is presented?",
        f"Does the evidence for '{concepts[2][0]}' reinforce or undermine the main claim?",
    ]
    for i, t in enumerate(consistency_templates):
        atomic.append({
            "id": f"{decision_question['id']}_consist_{i+1}",
            "type": "noul",
            "instructions": t,
            "criteria": {"true": "Yes, consistent", "false": "No, contradictory"},
            "source_refs": [decision_question["id"], "consistency_check"],
            "why_it_matters": "Signal consistency separates genuine positioning from scattered messaging",
            "decision_links": [decision_question["id"]],
        })

    # Dimension 3: Specificity (questions 9-10)
    atomic.append({
        "id": f"{decision_question['id']}_specificity",
        "type": "noul",
        "instructions": f"Are the claims about '{concepts[0][0]}' specific rather than generic?",
        "criteria": {"true": "Specific and detailed", "false": "Generic or vague"},
        "source_refs": [decision_question["id"], "specificity_check"],
        "why_it_matters": "Specificity is a reliable signal of genuine capability vs marketing language",
        "decision_links": [decision_question["id"]],
    })
    atomic.append({
        "id": f"{decision_question['id']}_inference",
        "type": "noul",
        "instructions": f"Can a reasonable inference about '{concepts[0][0]}' be drawn even if not explicitly stated?",
        "criteria": {"true": "Yes, inferable", "false": "No, cannot infer"},
        "source_refs": [decision_question["id"], "inference_check"],
        "why_it_matters": "What can be inferred is as important as what is stated",
        "decision_links": [decision_question["id"]],
    })

    # Dimension 4: Evidence quality (questions 11-12)
    if len(text) > 500:
        atomic.append({
            "id": f"{decision_question['id']}_quality",
            "type": "noul",
            "instructions": f"Does the page provide quantitative or independently verifiable support for '{concepts[0][0]}'?",
            "criteria": {"true": "Quantifiable or verifiable", "false": "Qualitative only"},
            "source_refs": [decision_question["id"], "quality_check"],
            "why_it_matters": "Verifiable evidence carries more weight than unsupported assertions",
            "decision_links": [decision_question["id"]],
        })

    return atomic


def build_evidence_state(pages, analysis_type):
    """Build a consolidated evidence state from page content for a given analysis type."""
    parts = []
    parts.append(f"=== ANALYSIS TYPE: {analysis_type} ===")
    parts.append(f"Analysis date: {datetime.now().isoformat()}")
    parts.append(f"Pages analysed: {len(pages)}")
    parts.append("")

    for i, page in enumerate(pages):
        parts.append(f"--- Page {i+1}: {page.get('title', 'Untitled')} ---")
        parts.append(f"URL: {page.get('url', '')}")
        text = page.get("clean_text", "")
        if text:
            # Include first 3000 chars per page for evidence state
            parts.append(text[:3000])
        parts.append("")

    return "\n".join(parts)


def call_jev(evidence_state, questions):
    """Call the JEV adapter with evidence state and questions."""
    adapter_input = {
        "state": evidence_state,
        "questions": {}
    }
    for q in questions:
        qid = q["id"]
        adapter_input["questions"][qid] = {
            "type": q.get("type", "noul"),
            "instructions": q["instructions"],
        }
        if q.get("criteria") is not None:
            adapter_input["questions"][qid]["criteria"] = q["criteria"]

    env = os.environ.copy()
    env["TYPESAFE_API_KEY"] = os.environ.get("TYPESAFE_API_KEY", "")

    try:
        result = subprocess.run(
            [PYTHON_BIN, JEV_ADAPTER],
            input=json.dumps(adapter_input),
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
        )

        if result.returncode != 0:
            return {
                "error": f"JEV adapter failed (exit {result.returncode})",
                "stderr": result.stderr[:2000] if result.stderr else "",
            }

        output = json.loads(result.stdout)
        return output

    except FileNotFoundError:
        return {"error": f"Python binary not found: {PYTHON_BIN}"}
    except json.JSONDecodeError as e:
        return {"error": f"JEV returned invalid JSON: {e}"}
    except subprocess.TimeoutExpired:
        return {"error": "JEV evaluation timed out after 120 seconds"}
    except Exception as e:
        return {"error": f"JEV call failed: {e}"}


def generate_narrative(decision_question, assessment, question_text_map, pages):
    """Generate an LLM narrative synthesis of JEV results using OpenAI."""
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        return {"narrative": "LLM synthesis unavailable (no API key configured).", "available": False}

    # Build a compact summary of the evidence for the LLM
    signals_summary = []
    top_sigs = assessment.get("top_signals", [])
    bot_sigs = assessment.get("bottom_signals", [])
    for s in top_sigs:
        qinfo = question_text_map.get(s["id"], {})
        signals_summary.append(f"STRONG: {qinfo.get('text', s['id'])} (score: {s['score']:.2f})")
    for s in bot_sigs:
        qinfo = question_text_map.get(s["id"], {})
        signals_summary.append(f"WEAK: {qinfo.get('text', s['id'])} (score: {s['score']:.2f})")

    contradictions = assessment.get("contradictions", [])
    unknowns = assessment.get("critical_unknowns", [])
    ev_strength = assessment.get("evidence_strength", {})
    dip = assessment.get("decision_impact_probability", 0.5)
    challenger = assessment.get("challenger", {})

    prompt = f"""You are an intelligence analyst reviewing a website evidence assessment.

QUESTION: {decision_question['question']}
CONFIDENCE: {assessment['confidence']:.0%} ({assessment.get('confidence_band', 'MODERATE')})
VERDICT: {assessment['verdict']}
EVIDENCE STRENGTH: {ev_strength.get('strong_signals', 0)} strong, {ev_strength.get('weak_signals', 0)} weak out of {ev_strength.get('total_signals', 0)} signals
DECISION IMPACT PROBABILITY: {dip:.2f}

KEY SIGNALS:
{chr(10).join(signals_summary)}

CONTRADICTIONS: {len(contradictions)}
{chr(10).join([f"- Gap {c['gap']:.2f} between '{c.get('signal_a','')}' and '{c.get('signal_b','')}'" for c in contradictions[:2]]) if contradictions else 'None detected'}

CRITICAL UNKNOWNS: {len(unknowns)}
{chr(10).join([f"- {u['id'].replace('_',' ')} (score: {u['score']:.2f})" for u in unknowns[:2]]) if unknowns else 'None'}

PAGES ANALYSED: {len(pages)}

Write a concise intelligence assessment (3-4 paragraphs) that:
1. States the bottom-line finding in one sentence
2. Explains what evidence supports this conclusion
3. Notes what is uncertain or contradictory
4. Gives a clear implication for decision-making

Write as an analyst, not a marketer. Use plain language. Do not use bullet points."""

    try:
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 600,
                "temperature": 0.3,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        narrative = data["choices"][0]["message"]["content"].strip()
        return {"narrative": narrative, "model": data["model"], "available": True}
    except Exception as e:
        return {"narrative": f"Narrative synthesis unavailable: {e}", "available": False}


def synthesize_assessment(decision_question, jev_result, pages):
    """Synthesize JEV results into a structured, StickyRice-level assessment.

    Produces:
    - Verdict with confidence and evidence strength breakdown
    - Evidence coverage across pages and dimensions
    - Strongest and weakest signals identified
    - Contradictions flagged
    - What is observed vs inferred
    - Critical unknowns
    - Challenger / counter-case
    - Decision impact probability
    - Implications
    """
    atomic_results = jev_result.get("answers", jev_result.get("results", {}))
    noul_answers = {}
    for qid, answer in atomic_results.items():
        if isinstance(answer, dict):
            noul_answers[qid] = answer.get("noul", answer.get("answer", 0.5))
        elif isinstance(answer, (int, float)):
            noul_answers[qid] = answer
        else:
            noul_answers[qid] = 0.5

    values = list(noul_answers.values())
    mean_score = sum(values) / len(values) if values else 0.5
    variance = sum((v - mean_score) ** 2 for v in values) / len(values) if values else 0
    std_dev = variance ** 0.5

    # Evidence strength classification (StickyRice model)
    def classify_strength(score):
        if score >= 0.85:
            return {"label": "VERY STRONG", "score": score, "description": "Direct, specific and independently supported"}
        elif score >= 0.65:
            return {"label": "STRONG", "score": score, "description": "Direct and specific evidence"}
        elif score >= 0.45:
            return {"label": "MODERATE", "score": score, "description": "Reasonable evidence with limited specificity"}
        elif score >= 0.25:
            return {"label": "WEAK", "score": score, "description": "Indirect evidence or plausible interpretation"}
        else:
            return {"label": "UNKNOWN", "score": score, "description": "Insufficient evidence to determine"}

    # Classify each atomic answer
    classified_signals = {}
    for qid, score in noul_answers.items():
        classified_signals[qid] = classify_strength(score)

    # Confidence calculation (StickyRice: evidence strength + coverage + consistency - contradictions)
    strong_count = sum(1 for v in values if v >= 0.65)
    weak_count = sum(1 for v in values if v < 0.35)
    total = len(values) if values else 1
    evidence_strength_ratio = strong_count / total
    coverage_ratio = len(pages) / 10.0 if pages else 0.5
    consistency_factor = 1.0 - (std_dev * 2)  # High variance = low consistency
    contradiction_penalty = weak_count / total * 0.2  # Weak signals reduce confidence

    raw_confidence = (
        evidence_strength_ratio * 0.35 +
        min(coverage_ratio, 1.0) * 0.25 +
        max(consistency_factor, 0) * 0.25 +
        0.15  # Base confidence
    ) - contradiction_penalty

    confidence = max(0.0, min(1.0, round(raw_confidence, 3)))

    # Confidence band
    if confidence >= 0.80:
        confidence_band = "HIGH"
    elif confidence >= 0.55:
        confidence_band = "MODERATE"
    elif confidence >= 0.30:
        confidence_band = "LOW"
    else:
        confidence_band = "VERY LOW"

    # Verdict based on mean and distribution shape
    if mean_score > 0.65 and std_dev < 0.25:
        verdict = "Clearly evidenced with strong agreement across signals"
    elif mean_score > 0.55 and std_dev < 0.3:
        verdict = "Evidence leans positive but with notable variation"
    elif mean_score > 0.45:
        verdict = "Uncertain — evidence is mixed or inconclusive"
    elif mean_score > 0.35:
        verdict = "Evidence leans negative with some supporting signals"
    else:
        verdict = "Evidence is weak or absent"

    # Identify strongest and weakest signals
    sorted_signals = sorted(noul_answers.items(), key=lambda x: x[1], reverse=True)
    top_signals = [{"id": qid, "score": score, "strength": classify_strength(score)}
                   for qid, score in sorted_signals[:3]]
    bottom_signals = [{"id": qid, "score": score, "strength": classify_strength(score)}
                      for qid, score in sorted_signals[-3:]]

    # Contradiction detection (signals that diverge significantly)
    contradictions = []
    for i in range(len(sorted_signals) - 1):
        for j in range(i + 1, len(sorted_signals)):
            diff = abs(sorted_signals[i][1] - sorted_signals[j][1])
            if diff > 0.5:
                contradictions.append({
                    "signal_a": sorted_signals[i][0],
                    "score_a": sorted_signals[i][1],
                    "signal_b": sorted_signals[j][0],
                    "score_b": sorted_signals[j][1],
                    "gap": round(diff, 2),
                })

    # Critical unknowns (signals below threshold)
    critical_unknowns = [
        {"id": qid, "score": score}
        for qid, score in noul_answers.items()
        if score < 0.30
    ]

    # Decision Impact Probability
    # Based on: signal strength + coverage + materiality
    dip_base = evidence_strength_ratio * 0.4 + min(coverage_ratio, 1.0) * 0.3 + (1.0 - contradiction_penalty * 3) * 0.3
    dip = min(0.95, max(0.05, round(dip_base, 2)))

    return {
        "decision_question_id": decision_question["id"],
        "question": decision_question["question"],
        "category": decision_question["category"],
        "analysis_type": decision_question["analysis_type"],
        "verdict": verdict,
        "confidence": confidence,
        "confidence_band": confidence_band,
        "evidence_strength": {
            "mean_score": round(mean_score, 3),
            "std_deviation": round(std_dev, 3),
            "strong_signals": strong_count,
            "weak_signals": weak_count,
            "total_signals": total,
        },
        "atomic_questions_answered": total,
        "high_confidence_signals": strong_count,
        "classified_signals": classified_signals,
        "top_signals": top_signals,
        "bottom_signals": bottom_signals,
        "contradictions": contradictions[:3],  # Top 3 contradictions
        "critical_unknowns": critical_unknowns[:3],  # Top 3 unknowns
        "decision_impact_probability": dip,
        "challenger": _generate_challenger(decision_question, mean_score, confidence, dip),
        "model_version": jev_result.get("model", jev_result.get("model_version", "unknown")),
        "pages_analysed": len(pages),
        "raw_results": atomic_results,
    }


def _generate_challenger(decision_question, mean_score, confidence, dip):
    """Generate a challenger/counter-case analysis (StickyRice challenger pass)."""
    # Only generate meaningful challenger when confidence is high enough
    if confidence < 0.3:
        return {
            "summary": "Confidence is too low for a meaningful challenger analysis",
            "challenger_assessment": "More evidence needed before counter-case can be evaluated",
        }

    # Build counter-case based on evidence direction
    if mean_score > 0.55:
        direction = "positive"
        counter = "The positive assessment may overstate the strength of available evidence"
        reverse_case = "The page evidence could be read as marketing language rather than substantiated claims"
    elif mean_score > 0.35:
        direction = "mixed"
        counter = "The mixed assessment may underweight signals that individually are meaningful"
        reverse_case = "A different reading of the evidence could produce a more decisive assessment"
    else:
        direction = "negative"
        counter = "The negative assessment may miss signals that are present but not explicit"
        reverse_case = "What appears absent from the page may exist elsewhere on the site"

    return {
        "summary": counter,
        "direction": direction,
        "challenger_assessment": reverse_case,
        "would_change_at": f"Decision would change if: {(1.0 - mean_score) * 100:.0f}% of signals reversed direction",
        "cheapest_research": "Verify the highest-confidence finding against an independent source",
    }


# ──────────────────────────────────────────────
# Crawling logic
# ──────────────────────────────────────────────

def url_priority_score(url):
    """Score a URL by its relevance for decision analysis."""
    path = urlparse(url).path.lower()
    parts = path.strip("/").split("/")
    last_part = parts[-1] if parts else ""

    if not path or path == "/":
        return 100  # Homepage: highest priority

    # Check blocklist
    for blocked in URL_PRIORITY_BLOCKLIST:
        if blocked in path:
            return -10

    # Score by keyword matches in path
    score = 0
    for segment in path.strip("/").split("/"):
        for keyword, kw_score in URL_PRIORITY_KEYWORDS.items():
            if keyword in segment:
                score += kw_score

    # Bonus for shorter paths (top-level pages)
    depth = len(parts)
    score += max(0, 5 - depth)

    # Penalty for very deep paths
    if depth > 3:
        score -= depth - 3

    return score


def extract_clean_text(soup):
    """Extract clean text from a BeautifulSoup object, removing boilerplate."""
    # Remove unwanted elements
    for tag in soup(["script", "style", "nav", "footer", "header",
                      "noscript", "iframe", "svg", "form"]):
        tag.decompose()

    # Remove hidden elements
    for tag in soup.find_all(style=re.compile(r"display\s*:\s*none", re.I)):
        tag.decompose()

    text = soup.get_text(separator=" ", strip=True)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def fetch_page_text(url, timeout=15):
    """Fetch a URL and return (title, clean_text, error)."""
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        resp.raise_for_status()

        content_type = resp.headers.get("Content-Type", "").lower()
        if "text/html" not in content_type and "html" not in content_type:
            return url, "Non-HTML content", ""

        soup = BeautifulSoup(resp.text, "html.parser")
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else url
        clean_text = extract_clean_text(soup)

        return title, clean_text, None

    except requests.exceptions.Timeout:
        return None, None, f"Timeout fetching {url}"
    except requests.exceptions.HTTPError as e:
        return None, None, f"HTTP {e.response.status_code} for {url}"
    except requests.exceptions.ConnectionError:
        return None, None, f"Connection error for {url}"
    except Exception as e:
        return None, None, f"Error fetching {url}: {e}"


def discover_links(homepage_url, html_text):
    """Discover same-domain internal links from HTML content."""
    base_domain = urlparse(homepage_url).netloc.lower()
    soup = BeautifulSoup(html_text, "html.parser")
    discovered = set()

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"].strip()
        if not href or href.startswith("#") or href.startswith("javascript:"):
            continue

        absolute = urljoin(homepage_url, href)
        parsed = urllib.parse.urlparse(absolute)

        # Filter to same domain only
        if parsed.netloc.lower() != base_domain:
            continue

        # Remove fragment
        clean_url = urllib.parse.urlunparse((
            parsed.scheme, parsed.netloc, parsed.path,
            parsed.params, parsed.query, ""
        ))
        discovered.add(clean_url)

    return list(discovered)


def run_scan(target_url):
    """Full scan pipeline: fetch homepage, discover pages, rank and extract top 10."""
    if not target_url.startswith(("http://", "https://")):
        target_url = "https://" + target_url

    parsed = urlparse(target_url)
    if not parsed.netloc:
        return {"error": f"Invalid URL: {target_url}"}

    # 1. Fetch homepage
    title, clean_text, error = fetch_page_text(target_url)
    if error:
        return {"error": error}

    # 2. Discover internal links
    try:
        resp = requests.get(
            target_url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=15,
            allow_redirects=True,
        )
        resp.raise_for_status()
        all_links = discover_links(target_url, resp.text)
    except Exception as e:
        all_links = []

    # 3. Deduplicate and filter
    unique_links = list(set(all_links))
    base_domain = parsed.netloc.lower()
    same_domain = [
        url for url in unique_links
        if urlparse(url).netloc.lower() == base_domain
    ]

    # 4. Score and rank
    scored = []
    for url in same_domain:
        if url == target_url:
            continue  # Skip homepage (already fetched)
        priority = url_priority_score(url)
        scored.append({"url": url, "priority": priority})

    scored.sort(key=lambda x: x["priority"], reverse=True)

    # 5. Take top candidates (up to 20, then fetch)
    candidates = scored[:20]
    fetched_pages = []

    # Include the homepage
    fetched_pages.append({
        "url": target_url,
        "title": title or target_url,
        "clean_text": clean_text,
        "priority": 100,
        "source": "homepage",
    })

    for candidate in candidates:
        u = candidate["url"]
        if u == target_url:
            continue
        p_title, p_text, p_error = fetch_page_text(u)
        if p_text and not p_error:
            fetched_pages.append({
                "url": u,
                "title": p_title or u,
                "clean_text": p_text,
                "priority": candidate["priority"],
                "source": "crawl",
            })

    # 6. Sort by priority, return top 10
    fetched_pages.sort(key=lambda x: x["priority"], reverse=True)
    top_10 = fetched_pages[:10]

    return {
        "target_url": target_url,
        "domain": base_domain,
        "pages_discovered": len(unique_links),
        "pages_fetched": len(fetched_pages),
        "top_pages": [
            {
                "url": p["url"],
                "title": p["title"],
                "priority": p["priority"],
                "source": p["source"],
                "word_count": len(p.get("clean_text", "").split()),
                "preview": p.get("clean_text", "")[:500],
                "content": p.get("clean_text", "")[:3000],
            }
            for p in top_10
        ],
        "timestamp": datetime.now().isoformat(),
    }


def run_analysis(question_id, pages):
    """Run full analysis pipeline for a decision question against page data."""
    # Find the decision question
    decision_q = None
    for q in DECISION_QUESTIONS:
        if q["id"] == question_id:
            decision_q = q
            break
    if not decision_q:
        return {"error": f"Unknown question_id: {question_id}"}

    # Build evidence state from page content
    evidence_state = build_evidence_state(pages, decision_q["analysis_type"])

    # Generate atomic questions
    combined_text = " ".join(p.get("clean_text", "") for p in pages[:3])
    atomic_questions = make_atomic_questions(decision_q, combined_text)

    # Call JEV
    jev_result = call_jev(evidence_state, atomic_questions)

    if "error" in jev_result:
        return {
            "decision_question_id": question_id,
            "error": jev_result["error"],
            "atomic_questions_generated": len(atomic_questions),
            "evidence_state_length": len(evidence_state),
        }

    # Synthesize assessment
    assessment = synthesize_assessment(decision_q, jev_result, pages)

    # Build question text map for rich display
    question_text_map = {}
    for q in atomic_questions:
        question_text_map[q["id"]] = {
            "text": q["instructions"],
            "why": q.get("why_it_matters", ""),
        }

    # Generate LLM narrative
    narrative = generate_narrative(decision_q, assessment, question_text_map, pages)

    return {
        "assessment": assessment,
        "narrative": narrative,
        "questions": question_text_map,
        "meta": {
            "decision_question_id": question_id,
            "atomic_questions_count": len(atomic_questions),
            "evidence_state_length": len(evidence_state),
            "pages_analysed": len(pages),
            "timestamp": datetime.now().isoformat(),
        },
        "jev_raw": jev_result,
    }


# ──────────────────────────────────────────────
# HTTP request handler
# ──────────────────────────────────────────────

class EngineHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the IntellaIQ Engine API."""

    def _set_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Max-Age", "86400")

    def _send_json(self, data, status=200):
        body = json.dumps(data, indent=2, default=str).encode("utf-8")
        self.send_response(status)
        self._set_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html, status=200):
        body = html.encode("utf-8")
        self.send_response(status)
        self._set_cors_headers()
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, status, message):
        self._send_json({"error": message, "status": status}, status)

    def _read_body(self):
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length > 0:
            raw = self.rfile.read(content_length)
            return raw.decode("utf-8")
        return ""

    def do_OPTIONS(self):
        """Handle preflight CORS requests."""
        self.send_response(200)
        self._set_cors_headers()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        """Handle GET requests - serve the engine frontend."""
        parsed_path = urllib.parse.urlparse(self.path)

        if parsed_path.path == "/":
            if os.path.exists(ENGINE_HTML):
                with open(ENGINE_HTML, "r") as f:
                    html = f.read()
                self._send_html(html)
            else:
                self._send_json({
                    "service": "IntellaIQ Engine",
                    "version": "1.0.0",
                    "endpoints": {
                        "GET /": "This status page or the engine HTML frontend",
                        "GET /health": "Health check",
                        "POST /api/scan": "Scan a URL and return top decision-relevant pages",
                        "POST /api/analyze": "Run JEV atomic question analysis on page data",
                    },
                    "questions_available": [
                        {"id": q["id"], "category": q["category"], "question": q["question"]}
                        for q in DECISION_QUESTIONS
                    ],
                })
        elif parsed_path.path == "/health":
            self._send_json({
                "status": "ok",
                "service": "IntellaIQ Engine",
                "timestamp": datetime.now().isoformat(),
                "jev_adapter_available": os.path.exists(JEV_ADAPTER),
                "python_bin": PYTHON_BIN,
            })
        else:
            self._send_error(404, f"Not found: {self.path}")

    def do_POST(self):
        """Handle POST requests - scan and analyze endpoints."""
        parsed_path = urllib.parse.urlparse(self.path)
        body_text = self._read_body()

        if not body_text:
            self._send_error(400, "Request body is required")
            return

        try:
            data = json.loads(body_text)
        except json.JSONDecodeError as e:
            self._send_error(400, f"Invalid JSON: {e}")
            return

        if parsed_path.path == "/api/scan":
            self._handle_scan(data)
        elif parsed_path.path == "/api/analyze":
            self._handle_analyze(data)
        else:
            self._send_error(404, f"Not found: {self.path}")

    def _handle_scan(self, data):
        """Handle POST /api/scan."""
        url = data.get("url", "").strip()
        if not url:
            self._send_error(400, "Missing required field: 'url'")
            return

        try:
            result = run_scan(url)
            if "error" in result:
                self._send_error(400, result["error"])
            else:
                self._send_json(result)
        except Exception as e:
            self._send_error(500, f"Scan failed: {e}\n{traceback.format_exc()}")

    def _handle_analyze(self, data):
        """Handle POST /api/analyze."""
        question_id = data.get("question_id", "").strip()
        pages = data.get("pages", data.get("page_data", []))

        if not question_id:
            self._send_error(400, "Missing required field: 'question_id'")
            return

        if not pages:
            self._send_error(400, "Missing required field: 'pages' (or 'page_data')")
            return

        # Normalize pages: if a single page dict is provided, wrap in list
        if isinstance(pages, dict):
            pages = [pages]

        try:
            result = run_analysis(question_id, pages)
            if "error" in result:
                self._send_error(400, result["error"])
            else:
                self._send_json(result)
        except Exception as e:
            self._send_error(500, f"Analysis failed: {e}\n{traceback.format_exc()}")

    def log_message(self, format, *args):
        """Override to use stderr for cleaner output."""
        sys.stderr.write(f"[{datetime.now().isoformat()}] {format % args}\n")
        sys.stderr.flush()


# ──────────────────────────────────────────────
# Main entry point
# ──────────────────────────────────────────────

def main():
    port = SERVER_PORT
    if "--port" in sys.argv:
        idx = sys.argv.index("--port")
        if idx + 1 < len(sys.argv):
            port = int(sys.argv[idx + 1])

    server = HTTPServer(("0.0.0.0", port), EngineHandler)
    print(f"IntellaIQ Engine Server running on http://0.0.0.0:{port}", flush=True)
    print(f"  API endpoints:", flush=True)
    print(f"    POST /api/scan    - Analyse a website", flush=True)
    print(f"    POST /api/analyze - Run atomic question analysis", flush=True)
    print(f"    GET  /health      - Health check", flush=True)
    print(f"    GET  /            - Frontend (if engine.html exists)", flush=True)
    print(f"  JEV adapter: {JEV_ADAPTER}", flush=True)
    print(f"  UI dir: {UI_DIR}", flush=True)
    print(f"  Engine HTML: {ENGINE_HTML} (exists: {os.path.exists(ENGINE_HTML)})", flush=True)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...", flush=True)
        server.server_close()


if __name__ == "__main__":
    main()