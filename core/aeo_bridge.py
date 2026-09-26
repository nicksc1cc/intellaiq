#!/usr/bin/env python3
"""GEO/AEO Tracker bridge for IntellaIQ.

Queries the local GEO/AEO Tracker instance for brand visibility data
and feeds it into the StickyRice decision model as a new dimension.
"""

import json
import urllib.request
import urllib.error

AEO_TRACKER_URL = "http://localhost:3001"

# ──────────────────────────────────────────────
# AEO Visibility Question Templates
# ──────────────────────────────────────────────

AEO_QUESTIONS = [
    {
        "id": "aeo_visibility_score",
        "type": "score",
        "dimension": "ai_visibility",
        "instructions": "What is the brand's overall AI visibility score across major models (0 = invisible, 1 = dominant)?",
        "why_it_matters": "AI visibility is a leading indicator of whether the brand will be discovered by AI-first users.",
        "decision_links": ["overall_assessment"],
        "source_refs": ["geo_aeo_tracker"],
    },
    {
        "id": "aeo_citation_diversity",
        "type": "noul",
        "dimension": "ai_visibility",
        "instructions": "Is the brand cited across multiple AI models (ChatGPT, Perplexity, Gemini, etc.) rather than just one?",
        "why_it_matters": "Cross-model citation indicates broad AI discoverability, not platform-specific luck.",
        "decision_links": ["overall_assessment"],
        "source_refs": ["geo_aeo_tracker"],
    },
    {
        "id": "aeo_citation_sources",
        "type": "noul",
        "dimension": "ai_visibility",
        "instructions": "Are the brand's AI citations coming from authoritative sources the brand controls (own site, PR, partnerships) vs uncontrolled sources (forums, reviews, social)?",
        "why_it_matters": "Controlled citations are strategic; uncontrolled ones are reactive and may carry negative framing.",
        "decision_links": ["overall_assessment"],
        "source_refs": ["geo_aeo_tracker"],
    },
    {
        "id": "aeo_sentiment",
        "type": "noul",
        "dimension": "ai_visibility",
        "instructions": "Is the brand's AI citation sentiment predominantly positive, neutral, or mixed?",
        "why_it_matters": "Sentiment in AI answers shapes brand perception more than any owned channel.",
        "decision_links": ["overall_assessment"],
        "source_refs": ["geo_aeo_tracker"],
    },
    {
        "id": "aeo_competitor_gap",
        "type": "score",
        "dimension": "ai_visibility",
        "instructions": "How large is the visibility gap between this brand and its top AI-cited competitor (0 = huge gap, 1 = leading)?",
        "why_it_matters": "The competitor gap reveals whether the brand is gaining or losing AI share.",
        "decision_links": ["overall_assessment"],
        "source_refs": ["geo_aeo_tracker"],
    },
    {
        "id": "aeo_trend",
        "type": "noul",
        "dimension": "ai_visibility",
        "instructions": "Has the brand's AI visibility been improving over recent weeks?",
        "why_it_matters": "Trend direction matters more than absolute score — improving brands are investing correctly.",
        "decision_links": ["overall_assessment"],
        "source_refs": ["geo_aeo_tracker"],
    },
]


def check_tracker_alive():
    """Check if the GEO/AEO Tracker is running."""
    try:
        req = urllib.request.Request(f"{AEO_TRACKER_URL}/api/state", method="GET")
        with urllib.request.urlopen(req, timeout=3) as resp:
            return True
    except Exception:
        return False


def fetch_visibility_data(domain):
    """Fetch AI visibility data for a domain from the AEO tracker.

    Returns a dict with visibility scores or None if unavailable.
    """
    # The tracker doesn't have a direct domain-lookup API,
    # but we can try to query its scrape/analyze endpoints.

    # For now, check if tracker is alive and report status
    alive = check_tracker_alive()
    return {
        "tracker_alive": alive,
        "tracker_url": AEO_TRACKER_URL if alive else None,
        "bright_data_configured": False,  # Would need BRIGHT_DATA_KEY
        "domain": domain,
        "note": "AEO tracker is alive but needs Bright Data key for live results"
    }


def run_aeo_scan(domain, prompt=None):
    """Run an AEO scan for a domain using the tracker's scrape endpoint.

    Queries all available AI models for brand mentions.
    Returns structured results or error dict.
    """
    if not prompt:
        prompt = f"What do you know about {domain}?"

    results = {}
    providers = ["chatgpt", "perplexity", "gemini", "copilot"]

    for provider in providers:
        try:
            body = json.dumps({"prompt": prompt, "provider": provider}).encode()
            req = urllib.request.Request(
                f"{AEO_TRACKER_URL}/api/scrape",
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read())
                results[provider] = data
        except urllib.error.HTTPError as e:
            results[provider] = {"error": f"HTTP {e.code}: {e.read().decode()[:200]}"}
        except Exception as e:
            results[provider] = {"error": str(e)[:200]}

    return results


def synthesize_aeo_scores(visibility_data, prompt_results):
    """Convert raw AEO data into StickyRice atomic scores.

    Returns a dict mapping question_ids to {answer, confidence}.
    """
    scores = {}

    # If tracker isn't running or no results, return neutral scores with low confidence
    if not visibility_data.get("tracker_alive"):
        for q in AEO_QUESTIONS:
            scores[q["id"]] = {"answer": 0.5, "confidence": 0.1}
        return scores

    # Check if any provider returned real data (not demo)
    has_real_data = any(
        isinstance(prompt_results.get(p), dict)
        and "error" not in prompt_results.get(p, {})
        and prompt_results.get(p, {}) != {}
        for p in prompt_results
    )

    if not has_real_data:
        # No Bright Data key — return low-confidence neutral
        for q in AEO_QUESTIONS:
            scores[q["id"]] = {"answer": 0.5, "confidence": 0.15}
        return scores

    # With real data, extract signals and score
    # This would parse actual AI response data
    # For now, placeholder logic
    for q in AEO_QUESTIONS:
        if q["id"] == "aeo_trend":
            scores[q["id"]] = {"answer": 0.5, "confidence": 0.3}
        else:
            scores[q["id"]] = {"answer": 0.5, "confidence": 0.3}

    return scores


def fetch_and_score(domain):
    """Full pipeline: check tracker, scan, synthesize scores.

    Returns AEO atomic scores ready for merging into the decision model.
    """
    visibility = fetch_visibility_data(domain)
    if not visibility.get("tracker_alive"):
        return {
            "available": False,
            "reason": "GEO/AEO Tracker is not running",
            "scores": synthesize_aeo_scores(visibility, {}),
        }

    # Run quick scan
    prompt = f"Tell me about {domain} and what they do"
    prompt_results = run_aeo_scan(domain, prompt)
    aeo_scores = synthesize_aeo_scores(visibility, prompt_results)

    return {
        "available": True,
        "tracker_url": AEO_TRACKER_URL,
        "has_bright_data": False,
        "domain": domain,
        "prompts_sent": len(prompt_results),
        "scores": aeo_scores,
        "raw_results": prompt_results,
    }