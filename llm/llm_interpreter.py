"""
Inflexion Intelligence Engine — LLM Interpretation Layer
Phase 14: LLM Interpretation
"""

from __future__ import annotations
import os
import json
from dataclasses import dataclass, field
from typing import Any
from pathlib import Path

try:
    from intelligence.core.models import IntelligenceRun, Insight, Issue, Severity
    from intelligence.derived.derived_intelligence import DerivedFinding
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from intelligence.core.models import IntelligenceRun, Insight, Issue, Severity
    from intelligence.derived.derived_intelligence import DerivedFinding


@dataclass
class InterpretationResult:
    run_id: str
    page_interpretations: dict[str, str]
    site_interpretation: str
    strategic_insights: list[dict]
    hermes_tasks: list[dict]
    confidence: float


class LLMInterpreter:
    def __init__(self, api_key: str | None = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model
        self.client = None

        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
            except ImportError:
                pass

    def interpret_page(
        self,
        page_id: str,
        run: IntelligenceRun,
        quality_vector: Any,
        jev_results: list,
        findings: list[DerivedFinding],
        issues: list[Issue]
    ) -> str:
        """Generate LLM interpretation for a single page."""
        if not self.client:
            return self._fallback_page_interpretation(page_id, run, quality_vector, jev_results, findings, issues)

        # Build context
        context = self._build_page_context(page_id, run, quality_vector, jev_results, findings, issues)

        prompt = f"""You are a senior media strategist analysing the Inflexion website.
Analyse the following page intelligence data and provide a structured interpretation.

PAGE: {page_id}
URL: {run.page_states[page_id].url if page_id in run.page_states else 'N/A'}
PAGE TYPE: {run.page_states[page_id].page_type.value if page_id in run.page_states else 'N/A'}

QUALITY VECTOR:
{json.dumps(quality_vector, indent=2) if hasattr(quality_vector, '__dict__') else quality_vector}

TOP FINDINGS:
{self._format_findings(findings)}

TOP ISSUES:
{self._format_issues(issues)}

JEV RESULTS SUMMARY:
{self._summarize_jev(jev_results)}

Provide your interpretation in this exact format:

OBSERVATION:
[2-3 sentences: what the data shows]

EVIDENCE:
[Specific evidence from the data supporting your observation]

INTERPRETATION:
[What this means strategically - why it matters]

UNCERTAINTY:
[What we don't know or where confidence is low]

IMPLICATION:
[What this implies for the site/strategy]

POSSIBLE ACTION:
[One specific, evidence-backed action - NOT a generic recommendation]"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=800
            )
            return response.choices[0].message.content
        except Exception as e:
            return self._fallback_page_interpretation(page_id, run, quality_vector, jev_results, findings, issues)

    def interpret_site(
        self,
        run: IntelligenceRun,
        all_findings: list[DerivedFinding],
        all_issues: list[Issue],
        all_insights: list[Insight]
    ) -> str:
        """Generate site-level strategic interpretation."""
        if not self.client:
            return self._fallback_site_interpretation(run, all_findings, all_issues, all_insights)

        context = self._build_site_context(run, all_findings, all_issues, all_insights)

        prompt = f"""You are a senior media strategist analysing the Inflexion website as a whole.
Analyse the following site-wide intelligence data and provide a strategic interpretation.

SITE OVERVIEW:
- Pages analysed: {len(run.pages_analyzed)}
- Git commit: {run.git_commit}
- Run ID: {run.run_id}

QUALITY DISTRIBUTION:
{self._quality_distribution(run)}

TOP FINDINGS BY TYPE:
{self._group_findings_by_type(all_findings)}

TOP INSIGHTS:
{self._format_insights(all_insights)}

HIGH-CONFIDENCE ISSUES:
{self._format_high_confidence_issues(all_issues)}

Provide your interpretation in this exact format:

OBSERVATION:
[3-4 sentences: what the site-level data reveals]

EVIDENCE:
[Specific evidence from the data]

INTERPRETATION:
[Strategic meaning - what this tells us about Inflexion's position]

UNCERTAINTY:
[Key unknowns, low-confidence areas, data gaps]

IMPLICATION:
[Strategic implications for Inflexion's positioning and service architecture]

POSSIBLE ACTIONS:
[2-3 specific, prioritised actions with evidence]"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=1200
            )
            return response.choices[0].message.content
        except Exception as e:
            return self._fallback_site_interpretation(run, all_findings, all_issues, all_insights)

    def generate_hermes_tasks(
        self,
        run: IntelligenceRun,
        issues: list[Issue],
        insights: list[Insight]
    ) -> list[dict]:
        """Generate constrained Hermes tasks from high-confidence issues."""
        tasks = []

        # Sort issues by severity * confidence
        sorted_issues = sorted(issues, key=lambda i: (i.severity.value == "critical", i.severity.value == "high", i.confidence), reverse=True)

        for issue in sorted_issues[:5]:  # Top 5 issues
            if issue.confidence < 0.6:
                continue

            # Find the primary page
            page_id = issue.affected_pages[0] if issue.affected_pages else None
            if not page_id or page_id not in run.page_states:
                continue

            page_state = run.page_states[page_id]

            # Find relevant text sections
            relevant_sections = self._find_relevant_sections(page_state, issue)

            task = {
                "task_id": f"hermes_{issue.issue_id}",
                "page": page_id,
                "objective": issue.affected_objectives[0] if issue.affected_objectives else "Improve page quality",
                "issue": issue.description,
                "why_it_matters": self._explain_why_it_matters(issue, run),
                "evidence": issue.evidence,
                "exact_text_section": relevant_sections,
                "constraints": self._generate_constraints(page_state, issue),
                "what_must_not_change": self._generate_protections(page_state),
                "expected_improvement": self._generate_expected_improvement(issue),
                "related_pages": issue.affected_pages[1:] if len(issue.affected_pages) > 1 else [],
                "regression_risks": self._generate_regression_risks(issue, run),
                "max_iterations": 3,
                "priority": "high" if issue.severity in [Severity.HIGH, Severity.CRITICAL] else "medium"
            }
            tasks.append(task)

        return tasks

    def _build_page_context(self, page_id: str, run: IntelligenceRun, quality_vector, jev_results, findings, issues) -> dict:
        return {
            "page_id": page_id,
            "quality_vector": quality_vector.to_dict() if hasattr(quality_vector, 'to_dict') else quality_vector,
            "top_findings": [f.title for f in findings if page_id in f.affected_pages][:5],
            "top_issues": [i.description for i in issues if page_id in i.affected_pages][:5],
            "jev_summary": self._summarize_jev(jev_results)
        }

    def _build_site_context(self, run: IntelligenceRun, findings, issues, insights) -> dict:
        return {
            "page_count": len(run.pages_analyzed),
            "quality_distribution": self._quality_distribution(run),
            "findings_by_type": self._group_findings_by_type(findings),
            "insights": [i.title for i in insights],
            "high_confidence_issues": [i.description for i in issues if i.confidence > 0.7][:10]
        }

    def _quality_distribution(self, run: IntelligenceRun) -> dict:
        dist = {"high": 0, "medium": 0, "low": 0}
        for qv in run.quality_vectors.values():
            overall = qv.overall if hasattr(qv, 'overall') else qv.get('overall', 0)
            if overall > 0.7:
                dist["high"] += 1
            elif overall > 0.5:
                dist["medium"] += 1
            else:
                dist["low"] += 1
        return dist

    def _group_findings_by_type(self, findings: list[DerivedFinding]) -> dict:
        grouped = {}
        for f in findings:
            if f.type not in grouped:
                grouped[f.type] = []
            grouped[f.type].append(f.title)
        return {k: v[:3] for k, v in grouped.items()}

    def _format_findings(self, findings: list[DerivedFinding]) -> str:
        return "\n".join(f"- {f.title}: {f.description}" for f in findings[:5])

    def _format_issues(self, issues: list[Issue]) -> str:
        return "\n".join(f"- {i.description} (severity: {i.severity.value}, confidence: {i.confidence:.0%})" for i in issues[:5])

    def _format_insights(self, insights: list[Insight]) -> str:
        return "\n".join(f"- {i.title}: {i.observation}" for i in insights[:5])

    def _format_high_confidence_issues(self, issues: list[Issue]) -> str:
        high_conf = [i for i in issues if i.confidence > 0.7]
        return "\n".join(f"- {i.description} (confidence: {i.confidence:.0%})" for i in high_conf[:5])

    def _summarize_jev(self, jev_results: list) -> str:
        if not jev_results:
            return "No Jev results"
        by_type = {}
        for r in jev_results:
            t = r.question_type.value
            if t not in by_type:
                by_type[t] = {"yes": 0, "no": 0, "unclear": 0, "avg_conf": 0}
            if t == "noul":
                val = r.result if isinstance(r.result, (int, float)) else 0.5
                if val > 0.6:
                    by_type[t]["yes"] += 1
                elif val < 0.4:
                    by_type[t]["no"] += 1
                else:
                    by_type[t]["unclear"] += 1
            by_type[t]["avg_conf"] += r.confidence
        for t in by_type:
            by_type[t]["avg_conf"] /= len([r for r in jev_results if r.question_type.value == t])
        return json.dumps(by_type, indent=2)

    def _find_relevant_sections(self, page_state, issue: Issue) -> list[str]:
        """Find sections relevant to the issue."""
        relevant = []
        issue_keywords = issue.description.lower().split()

        for section in page_state.sections:
            text = section.get("text", "").lower()
            if any(kw in text for kw in issue_keywords if len(kw) > 4):
                relevant.append(f"Section: {section.get('heading', 'Unknown')}\n{section.get('text', '')[:500]}")

        return relevant[:3]

    def _generate_constraints(self, page_state, issue: Issue) -> list[str]:
        constraints = [
            "Do not change the page's core argument or positioning",
            "Preserve all existing evidence and citations",
            "Maintain the page's unique intellectual territory",
            "Do not introduce generic/template language",
            "Keep the existing heading structure unless restructuring is the explicit goal"
        ]

        if issue.category.value == "differentiation":
            constraints.append("Do not make the page more similar to its overlap pages")
        if issue.category.value == "evidence":
            constraints.append("Do not remove existing evidence; only add or improve attribution")

        return constraints

    def _generate_protections(self, page_state) -> list[str]:
        return [
            "Core argument and thesis",
            "All cited statistics and their sources",
            "Page's unique intellectual territory vs. other Inflexion pages",
            "Technical accuracy of platform-specific claims",
            "Commercial pathway and qualification logic"
        ]

    def _generate_expected_improvement(self, issue: Issue) -> str:
        return f"Resolve {issue.category.value} issue: {issue.description}. Target: improve relevant quality dimension by 15-20%."

    def _generate_regression_risks(self, issue: Issue, run: IntelligenceRun) -> list[str]:
        risks = []
        for page in issue.affected_pages[1:]:
            if page in run.quality_vectors:
                risks.append(f"Changes may affect {page}'s differentiation")
        if issue.category.value == "differentiation":
            risks.append("Over-correction may make page too distinct from service family")
        return risks

    def _explain_why_it_matters(self, issue: Issue, run: IntelligenceRun) -> str:
        page = issue.affected_pages[0] if issue.affected_pages else "unknown"
        return f"This {issue.category.value} issue on {page} undermines {', '.join(issue.affected_objectives) if issue.affected_objectives else 'page objectives'}. Confidence: {issue.confidence:.0%}."

    def _fallback_page_interpretation(self, page_id, run, quality_vector, jev_results, findings, issues) -> str:
        qv = quality_vector.to_dict() if hasattr(quality_vector, 'to_dict') else quality_vector
        overall = qv.get('overall', 0) if isinstance(qv, dict) else getattr(quality_vector, 'overall', 0)

        page_type = run.page_states[page_id].page_type.value if page_id in run.page_states else 'unknown'
        dims = [f'{k}: {v.get("score", 0):.0%}' for k, v in qv.items() if isinstance(v, dict)][:5]
        top_issues = [i.description for i in issues if page_id in i.affected_pages][:3]
        jev_avg = sum(r.confidence for r in jev_results)/len(jev_results) if jev_results else 0

        if overall > 0.7:
            interp = "Strong page with good objective coverage"
            implication = "Maintain and monitor"
            action = "Run targeted Jev questions on weak dimensions"
        elif overall > 0.5:
            interp = "Page needs improvement in key dimensions"
            implication = "Targeted improvements needed"
            action = "Run targeted Jev questions on weak dimensions"
        else:
            interp = "Page has significant weaknesses requiring attention"
            implication = "Substantial revision recommended"
            action = "Structural review of page objectives and content"

        return f"""OBSERVATION:
Page {page_id} has an overall quality score of {overall:.0%}. The page is classified as {page_type}.

EVIDENCE:
Quality dimensions: {dims}
Top issues: {top_issues}

INTERPRETATION:
{interp}.

UNCERTAINTY:
Jev confidence average: {jev_avg:.0%}. Fallback interpretation used (no LLM).

IMPLICATION:
{implication}.

POSSIBLE ACTION:
{action}."""

    def _fallback_site_interpretation(self, run, findings, issues, insights) -> str:
        qv_dist = self._quality_distribution(run)
        high_conf_issues = [i for i in issues if i.confidence > 0.7]
        finding_types = list(self._group_findings_by_type(findings).keys())[:5]
        insight_titles = [i.title for i in insights[:3]]

        if qv_dist['high'] > qv_dist['low']:
            interp = "strong overall foundation"
            implication = "Optimise and differentiate"
        else:
            interp = "significant improvement needed"
            implication = "Foundation repair needed before optimisation"

        return f"""OBSERVATION:
Site analysis of {len(run.pages_analyzed)} pages shows {qv_dist['high']} high-quality, {qv_dist['medium']} medium, {qv_dist['low']} low-quality pages. {len(high_conf_issues)} high-confidence issues detected.

EVIDENCE:
Quality distribution: {qv_dist}
Top finding types: {finding_types}
Key insights: {insight_titles}

INTERPRETATION:
The site has a quality distribution suggesting {interp}. Key structural issues include differentiation between service pages and evidence gaps.

UNCERTAINTY:
Fallback interpretation used (no LLM API). Jev confidence varies. Performance data not connected.

IMPLICATION:
{implication}.

POSSIBLE ACTIONS:
1. Address top differentiation issues between AEO/AI Discovery/Technical GEO
2. Add evidence to central claims on flagged pages
3. Clarify concept ownership for overclaimed territories
4. Connect performance data sources for quality/performance analysis"""


def create_interpreter(api_key: str | None = None, model: str = "gpt-4o-mini") -> LLMInterpreter:
    return LLMInterpreter(api_key=api_key, model=model)