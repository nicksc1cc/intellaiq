#!/usr/bin/env python3
"""StickyRice Decision Engine — integrated into IntellaIQ.

Two-pass adaptive question planning, evidence graph, challenger analysis,
sensitivity analysis, and full decision report.
"""

import json
import re
import subprocess as sp
import os
from datetime import datetime
from collections import defaultdict

# Import AEO bridge
try:
    from core.aeo_bridge import AEO_QUESTIONS, fetch_and_score as fetch_aeo_scores, check_tracker_alive
    AEO_BRIDGE_AVAILABLE = True
except ImportError:
    AEO_QUESTIONS = []
    AEO_BRIDGE_AVAILABLE = False

    def fetch_aeo_scores(domain):
        return {"available": False, "reason": "AEO bridge not available", "scores": {}}

    def check_tracker_alive():
        return False

# Paths
STICKYRICE_DIR = os.path.expanduser("~/Projects/stickyrice")
JEV_ADAPTER = os.path.join(STICKYRICE_DIR, "scripts", "typesafe_jev_adapter.py")
DECISIONS_DIR = os.path.join(STICKYRICE_DIR, "decisions")

# ──────────────────────────────────────────────
# Pass 1 — Broad sweep questions
# ──────────────────────────────────────────────

PASS1_TEMPLATES = {
    "business_model": [
        {"id": "bm_value_prop", "dimension": "direct_evidence",
         "instructions": "Does the site clearly state what product or service they sell?",
         "why_it_matters": "Core business model clarity"},
        {"id": "bm_pricing", "dimension": "specificity",
         "instructions": "Does the site include specific pricing or pricing model information?",
         "why_it_matters": "Pricing transparency signals maturity"},
        {"id": "bm_target", "dimension": "direct_evidence",
         "instructions": "Does the site clearly define the customer or market they serve?",
         "why_it_matters": "Target definition determines market fit evaluation"},
        {"id": "bm_differentiation", "dimension": "inference",
         "instructions": "Does the site make a specific, verifiable claim about what makes them different?",
         "why_it_matters": "Differentiation claims show strategic clarity"},
        {"id": "bm_revenue_model", "dimension": "inference",
         "instructions": "Can their revenue model be inferred from the site?",
         "why_it_matters": "Revenue model shapes competitive dynamics"},
    ],
    "audience": [
        {"id": "aud_icp", "dimension": "specificity",
         "instructions": "Does the site describe a specific ideal customer profile?",
         "why_it_matters": "Vague targeting suggests poor GTM focus"},
        {"id": "aud_use_cases", "dimension": "direct_evidence",
         "instructions": "Does the site provide concrete use-case examples or customer stories?",
         "why_it_matters": "Use cases demonstrate real-world validation"},
        {"id": "aud_testimonials", "dimension": "corroboration",
         "instructions": "Does the site include named customer testimonials or case studies?",
         "why_it_matters": "Social proof is the strongest indirect evidence"},
    ],
    "credibility": [
        {"id": "cr_team", "dimension": "direct_evidence",
         "instructions": "Does the site list team members or founding story?",
         "why_it_matters": "Team transparency builds trust"},
        {"id": "cr_investors", "dimension": "direct_evidence",
         "instructions": "Does the site mention investors, funding, or revenue milestones?",
         "why_it_matters": "Funding signals business viability"},
        {"id": "cr_clients", "dimension": "corroboration",
         "instructions": "Does the site list named clients, logos, or usage metrics?",
         "why_it_matters": "Client logos are the strongest credibility signal"},
    ],
    "ai_visibility": [
        {"id": "aeo_vis_score", "dimension": "ai_visibility",
         "instructions": "Does this brand appear in AI-generated answers for relevant industry queries?",
         "why_it_matters": "AI visibility is the #1 leading indicator"},
        {"id": "aeo_vis_cross_model", "dimension": "ai_visibility",
         "instructions": "Is the brand cited across multiple AI models rather than just one?",
         "why_it_matters": "Cross-model citations indicate broad AI relevance"},
        {"id": "aeo_vis_sentiment", "dimension": "ai_visibility",
         "instructions": "Is the sentiment of AI citations about this brand predominantly positive?",
         "why_it_matters": "Negative AI citations damage brand perception"},
        {"id": "aeo_vis_gap", "dimension": "ai_visibility",
         "instructions": "Does this brand have an AI visibility gap versus its known competitors?",
         "why_it_matters": "Competitor gap reveals AI share trajectory"},
    ],
}
def generate_pass1_questions(analysis_type, pages):
    """Generate pass 1 broad-sweep questions based on analysis type."""
    templates = PASS1_TEMPLATES.get(analysis_type, {})
    if not analysis_type or analysis_type not in PASS1_TEMPLATES:
        templates = PASS1_TEMPLATES.get("business_model", [])
    else:
        templates = PASS1_TEMPLATES.get(analysis_type, [])
    
    questions = []
    for q in templates:
            questions.append({
                "id": q["id"],
                "type": "noul",
                "instructions": q["instructions"],
                "why_it_matters": q["why_it_matters"],
                "dimension": q["dimension"],
                "source_refs": [p["url"] for p in pages[:5]],
                "decision_links": ["overall_assessment"],
                "pass": 1,
            })
    return questions


# ──────────────────────────────────────────────
# Pass 2 — Adaptive follow-up questions
# ──────────────────────────────────────────────

UNCERTAINTY_THRESHOLD = 0.40  # Questions with confidence below this get follow-ups

FOLLOW_UP_TEMPLATES = {
    "bm_value_prop": [
        {"id": "bm_value_prop_f1", "instructions": "Does the site use specific, measurable language to describe their offering, not vague marketing terms?",
         "why_it_matters": "Vague language often hides an undefined product."},
        {"id": "bm_value_prop_f2", "instructions": "Can the product or service category be inferred from site navigation, headings, or CTAs?",
         "why_it_matters": "Category placement shapes which competitive set they belong to."},
    ],
    "bm_pricing": [
        {"id": "bm_pricing_f1", "instructions": "Does the site include a pricing page, even if it requires contacting sales?",
         "why_it_matters": "A pricing page (even hidden) signals a defined commercial model."},
        {"id": "bm_pricing_f2", "instructions": "Does the site mention free trials, demos, or freemium tiers?",
         "why_it_matters": "Acquisition model is a key part of go-to-market strategy."},
    ],
    "aud_icp": [
        {"id": "aud_icp_f1", "instructions": "Does the site's case studies or testimonials describe specific customer titles, industries, or outcomes?",
         "why_it_matters": "Named outcomes validate that the ICP is real, not aspirational."},
    ],
    "pr_feature_detail": [
        {"id": "pr_feature_f1", "instructions": "Does the site include a features page, comparison matrix, or specification sheet?",
         "why_it_matters": "Feature pages are the strongest indicator of product substance."},
    ],
    "cr_clients": [
        {"id": "cr_clients_f1", "instructions": "Are the client logos or testimonials verifiable (named companies, not 'Fortune 500' or logos without names)?",
         "why_it_matters": "Unnamed clients are often fabricated or aspirational."},
    ],
    "cp_moat": [
        {"id": "cp_moat_f1", "instructions": "Does the site mention patents, proprietary technology, exclusive data, or regulatory approvals?",
         "why_it_matters": "Patents and regulatory approvals are the strongest defensibility signals."},
    ],
}


def generate_pass2_questions(pass1_results):
    """Generate adaptive follow-up questions for low-confidence areas."""
    questions = []
    for qid, result in pass1_results.items():
        confidence = result.get("confidence", 0)
        answer = result.get("answer", 0.5)
        if confidence < UNCERTAINTY_THRESHOLD or (0.35 <= answer <= 0.65):
            follow_ups = FOLLOW_UP_TEMPLATES.get(qid, [])
            for fq in follow_ups:
                questions.append({
                    "id": fq["id"],
                    "type": "noul",
                    "instructions": fq["instructions"],
                    "why_it_matters": fq["why_it_matters"],
                    "dimension": "follow_up",
                    "source_refs": result.get("source_refs", []),
                    "decision_links": result.get("decision_links", ["overall_assessment"]),
                    "follows_up": qid,
                    "pass": 2,
                })
    return questions


# ──────────────────────────────────────────────
# Evidence Graph
# ──────────────────────────────────────────────

class EvidenceGraph:
    """Links JEV results to specific pages, excerpts, and claims."""
    
    def __init__(self):
        self.nodes = []   # {id, type, label, detail}
        self.edges = []   # {source, target, relationship}
    
    def add_evidence(self, question_id, question_text, score, confidence,
                     url, excerpt, dimension):
        nid = f"ev_{question_id}"
        self.nodes.append({
            "id": nid,
            "type": "jev_result",
            "label": question_text[:60],
            "detail": {
                "question_id": question_id,
                "question": question_text,
                "score": score,
                "confidence": confidence,
                "dimension": dimension,
                "url": url,
                "excerpt": excerpt[:200],
            }
        })
        return nid
    
    def add_page(self, url, title):
        nid = f"pg_{url[:40]}"
        self.nodes.append({
            "id": nid,
            "type": "page",
            "label": title or url,
            "detail": {"url": url, "title": title},
        })
        return nid
    
    def add_claim(self, claim_text, page_url):
        nid = f"cl_{hash(claim_text) % 10000}"
        self.nodes.append({
            "id": nid,
            "type": "claim",
            "label": claim_text[:80],
            "detail": {"text": claim_text, "source_url": page_url},
        })
        return nid
    
    def link(self, source, target, relationship):
        self.edges.append({"source": source, "target": target, "relationship": relationship})
    
    def to_dict(self):
        return {"nodes": self.nodes, "edges": self.edges}


# ──────────────────────────────────────────────
# JEV Adapter Call
# ──────────────────────────────────────────────

def call_jev(evidence_state, questions):
    """Call the JEV adapter for atomic question evaluation."""
    try:
        result = sp.run(
            ["python3", JEV_ADAPTER],
            input=json.dumps({
                "state": evidence_state[:8000],
                "questions": {q["id"]: q for q in questions},
            }),
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            return {"error": f"JEV adapter failed: {result.stderr[:200]}"}
        return json.loads(result.stdout)
    except FileNotFoundError:
        return {"error": f"JEV adapter not found at {JEV_ADAPTER}"}
    except sp.TimeoutExpired:
        return {"error": "JEV adapter timed out after 120s"}
    except Exception as e:
        return {"error": f"JEV adapter call failed: {str(e)}"}


# ──────────────────────────────────────────────
# Decision Report Builder
# ──────────────────────────────────────────────

def build_decision_report(decision_question, pass1_questions, pass1_results,
                          pass2_questions, pass2_results, evidence_graph,
                          pages):
    """Build the full StickyRice decision report."""
    
    # Score aggregation
    all_scores = []
    dimension_scores = defaultdict(list)
    for qid, result in {**pass1_results, **pass2_results}.items():
        score = result.get("answer", 0.5) if isinstance(result, dict) else 0.5
        conf = result.get("confidence", 0.5) if isinstance(result, dict) else 0.5
        all_scores.append((score, conf))
        # Find dimension
        for q in pass1_questions + pass2_questions:
            if q["id"] == qid:
                dim = q.get("dimension", "unknown")
                dimension_scores[dim].append((score, conf))
                break
    
    if not all_scores:
        return {"error": "No results to synthesize"}
    
    weighted_sum = sum(s * c for s, c in all_scores)
    total_weight = sum(c for _, c in all_scores)
    mean_score = weighted_sum / total_weight if total_weight > 0 else 0.5
    mean_confidence = total_weight / len(all_scores) if all_scores else 0.5
    
    # Dimension breakdown
    dimension_summary = {}
    for dim, scores in dimension_scores.items():
        if scores:
            dim_weighted = sum(s * c for s, c in scores)
            dim_weight = sum(c for _, c in scores)
            dimension_summary[dim] = round(dim_weighted / dim_weight, 2) if dim_weight > 0 else 0.5
    
    # Identify strongest and weakest signals
    scored_questions = []
    for q in pass1_questions + pass2_questions:
        result = pass1_results.get(q["id"]) or pass2_results.get(q["id"], {})
        score = result.get("answer", 0.5)
        confidence = result.get("confidence", 0.5)
        scored_questions.append({**q, "score": score, "confidence": confidence})
    
    strongest = sorted(scored_questions, key=lambda x: x["score"], reverse=True)[:3]
    weakest = sorted(scored_questions, key=lambda x: x["score"])[:3]
    most_uncertain = sorted(scored_questions, key=lambda x: x["confidence"])[:3]
    
    # Contradictions
    contradictions = []
    for dim, scores in dimension_scores.items():
        values = [s for s, _ in scores]
        if values and (max(values) - min(values)) > 0.5:
            contradictions.append({
                "dimension": dim,
                "range": round(max(values) - min(values), 2),
                "high": max(values),
                "low": min(values),
            })
    
    # Critical unknowns (high-impact, low-confidence)
    critical_unknowns = []
    for q in most_uncertain:
        result = pass1_results.get(q["id"]) or pass2_results.get(q["id"], {})
        score = q.get("score", 0.5)
        is_high_impact = any(k in q.get("id", "") for k in ["pricing", "revenue", "differentiation", "client", "product"])
        if is_high_impact or score < 0.4:
            critical_unknowns.append({
                "question": q["instructions"],
                "score": q["score"],
                "confidence": q["confidence"],
                "why_it_matters": q.get("why_it_matters", ""),
            })
    
    # Sensitivity: how much would the score change if each unknown was resolved
    sensitivities = []
    for q in critical_unknowns[:5]:
        base = mean_score
        optimistic = (mean_score * total_weight + 1.0 * 0.9) / (total_weight + 0.9)
        pessimistic = (mean_score * total_weight + 0.0 * 0.9) / (total_weight + 0.9)
        sensitivities.append({
            "factor": q["question"][:60] + "...",
            "base": round(mean_score, 2),
            "optimistic": round(optimistic, 2),
            "pessimistic": round(pessimistic, 2),
        })
    
    # Decision band
    if mean_score >= 0.7:
        verdict = "FAVOURABLE"
    elif mean_score >= 0.45:
        verdict = "NEUTRAL"
    else:
        verdict = "UNFAVOURABLE"
    
    confidence_band = "HIGH" if mean_confidence >= 0.7 else "MEDIUM" if mean_confidence >= 0.4 else "LOW"
    
    return {
        "verdict": verdict,
        "score": round(mean_score, 2),
        "confidence": round(mean_confidence, 2),
        "confidence_interval": [
            round(max(0, mean_score - (1 - mean_confidence) * 0.5), 2),
            round(min(1, mean_score + (1 - mean_confidence) * 0.5), 2),
        ],
        "dimension_scores": dimension_summary,
        "strongest_signals": [
            {"question": q["instructions"][:80], "score": round(q["score"], 2)}
            for q in strongest
        ],
        "weakest_signals": [
            {"question": q["instructions"][:80], "score": round(q["score"], 2)}
            for q in weakest
        ],
        "most_uncertain": [
            {"question": q["instructions"][:80], "confidence": round(q["confidence"], 2)}
            for q in most_uncertain[:5]
        ],
        "contradictions": contradictions[:5],
        "critical_unknowns": critical_unknowns[:5],
        "sensitivity": sensitivities[:5],
        "evidence_graph": evidence_graph.to_dict(),
        "total_questions": len(pass1_questions) + len(pass2_questions),
        "pass1_count": len(pass1_questions),
        "pass2_count": len(pass2_questions),
        "timestamp": datetime.now().isoformat(),
    }


# ──────────────────────────────────────────────
# Challenger Pass
# ──────────────────────────────────────────────

def run_challenger_pass(report, pages):
    """Generate a rigorous counter-case to stress-test the assessment."""
    
    scenarios = []
    
    # 1. The "hollow company" scenario
    if report["score"] > 0.5:
        scenarios.append({
            "scenario": "The company appears credible but has no real product",
            "trigger": "Only marketing claims, no technical detail, no named clients, no verifiable team",
            "what_would_prove_it": "Inability to demo, no public API, employees untraceable on LinkedIn",
            "impact": f"Score drops from {report['score']:.0%} to ~15%",
        })
    
    # 2. The "small team" scenario
    scenarios.append({
        "scenario": "The company is a small team without enterprise capability",
        "trigger": "No enterprise clients, no compliance pages, no SLAs mentioned",
        "what_would_prove_it": "No SOC2/ISO, no enterprise pricing, support page shows limited hours",
        "impact": f"Score drops from {report['score']:.0%} to ~30%",
    })
    
    # 3. The "vaporware" scenario
    for sig in report.get("weakest_signals", []):
        if "screenshot" in sig.get("question", "").lower() or "demo" in sig.get("question", "").lower():
            scenarios.append({
                "scenario": "Product may not exist in marketable form",
                "trigger": "No product screenshots or demo despite claims",
                "what_would_prove_it": "No working product, no public roadmap, no independent reviews",
                "impact": f"Score drops from {report['score']:.0%} to ~10%",
            })
            break
    
    # 4. The "market mismatch" scenario
    if report.get("critical_unknowns"):
        scenarios.append({
            "scenario": "Undefined market fit",
            "trigger": "Confused or contradictory market positioning on site",
            "what_would_prove_it": "No repeatable sales motion, no named reference customers",
            "impact": f"Score drops from {report['score']:.0%} to ~25%",
        })
    
    return {
        "challenger_scenarios": scenarios[:5],
        "strongest_counter_case": scenarios[0] if scenarios else None,
        "assumption_that_would_reverse": (
            "The strongest assumption this assessment makes is that "
            "the website accurately reflects the company's actual capabilities. "
            "If the site is purely marketing with no product behind it, "
            "the assessment would be materially wrong."
        ),
    }


# ──────────────────────────────────────────────
# Main Pipeline
# ──────────────────────────────────────────────

def run_sticky_analysis(decision_question, pages):
    """Full StickyRice analysis pipeline."""
    
    evidence_graph = EvidenceGraph()
    
    # Build evidence state
    combined_text = " ".join(p.get("clean_text", "") or "" for p in pages[:5])
    evidence_state = f"Analysis Type: {decision_question.get('analysis_type', 'general')}\n\n"
    evidence_state += f"Decision Question: {decision_question.get('text', '')}\n\n"
    for p in pages[:5]:
        text = (p.get("clean_text", "") or "")[:3000]
        evidence_state += f"\n--- Page: {p.get('url', '')} ---\n{text}\n"
    
    # Pass 1: Broad sweep
    pass1_questions = generate_pass1_questions(decision_question.get("analysis_type", ""), pages)
    pass1_result = call_jev(evidence_state, pass1_questions)
    
    if "error" in pass1_result:
        return {"error": pass1_result["error"],
                "pass1_questions": len(pass1_questions)}
    
    pass1_raw = pass1_result.get("answers", pass1_result.get("results", {}))
    pass1_results = {}
    for q in pass1_questions:
        raw = pass1_raw.get(q["id"], {})
        if isinstance(raw, dict):
            pass1_results[q["id"]] = {
                "answer": raw.get("noul", raw.get("answer", 0.5)),
                "confidence": raw.get("confidence", 0.5),
            }
        else:
            pass1_results[q["id"]] = {"answer": float(raw), "confidence": 0.5}
    
    # Build evidence graph from pass 1
    for p in pages[:5]:
        pg_id = evidence_graph.add_page(p.get("url", ""), p.get("title", ""))
        for q in pass1_questions:
            result = pass1_results.get(q["id"], {})
            if isinstance(result, dict):
                ev_id = evidence_graph.add_evidence(
                    q["id"], q["instructions"],
                    result.get("answer", 0.5), result.get("confidence", 0.5),
                    p.get("url", ""), p.get("clean_text", "")[:200],
                    q.get("dimension", "general"),
                )
                evidence_graph.link(pg_id, ev_id, "contains_evidence")
    
    # Pass 2: Adaptive follow-ups
    pass2_questions = generate_pass2_questions(pass1_results)
    pass2_results = {}
    if pass2_questions:
        pass2_result = call_jev(evidence_state, pass2_questions)
        if "error" not in pass2_result:
            pass2_raw = pass2_result.get("answers", pass2_result.get("results", {}))
            for q in pass2_questions:
                raw = pass2_raw.get(q["id"], {})
                if isinstance(raw, dict):
                    pass2_results[q["id"]] = {
                        "answer": raw.get("noul", raw.get("answer", 0.5)),
                        "confidence": raw.get("confidence", 0.5),
                    }
                else:
                    pass2_results[q["id"]] = {"answer": float(raw), "confidence": 0.5}
    
    # Build decision report
    report = build_decision_report(decision_question, pass1_questions, pass1_results,
                                    pass2_questions, pass2_results, evidence_graph, pages)

    if "error" in report:
        return report

    # Run challenger
    challenger = run_challenger_pass(report, pages)

    # AEO bridge: check if tracker is alive
    aeo_data = {"available": False, "reason": "Not checked"}
    if AEO_BRIDGE_AVAILABLE:
        try:
            domain = ""
            for p in pages:
                from urllib.parse import urlparse
                parsed = urlparse(p.get("url", ""))
                if parsed.netloc:
                    domain = parsed.netloc
                    break
            if domain:
                aeo_data = fetch_aeo_scores(domain)
        except Exception as e:
            aeo_data = {"available": False, "error": str(e)[:100]}

    return {
            "report": report,
            "challenger": challenger,
            "aeo_visibility": aeo_data,
    "pass1_questions": [
        {"id": q["id"], "text": q["instructions"], "dimension": q.get("dimension", "")}
        for q in pass1_questions
    ],
    "pass2_questions": [
        {"id": q["id"], "text": q["instructions"], "follows_up": q.get("follows_up", "")}
        for q in pass2_questions
    ],
    "pass1_results": pass1_results,
    "pass2_results": pass2_results,
    "meta": {
        "total_questions": len(pass1_questions) + len(pass2_questions),
        "pass1_count": len(pass1_questions),
        "pass2_count": len(pass2_questions),
        "evidence_state_length": len(evidence_state),
        "pages_analysed": len(pages),
        "timestamp": datetime.now().isoformat(),
        "depth": "adaptive_two_pass",
    },
    }