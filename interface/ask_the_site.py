"""
Inflexion Intelligence Engine — Interface Layer
Phases 21-22: Ask the Site & Hermes Task Generation
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from pathlib import Path

try:
    from intelligence.core.models import IntelligenceRun, Issue, Insight, Severity
    from intelligence.llm.llm_interpreter import LLMInterpreter
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from intelligence.core.models import IntelligenceRun, Issue, Insight, Severity
    from intelligence.llm.llm_interpreter import LLMInterpreter


@dataclass
class QueryResult:
    query: str
    answer: str
    evidence: list[str]
    related_pages: list[str]
    related_objectives: list[str]
    confidence: float
    uncertainty: str
    visualization_type: str  # graph, matrix, evidence, change, page
    visualization_data: dict


class AskTheSite:
    """Natural language query interface for the intelligence engine."""

    def __init__(self, run: IntelligenceRun, interpreter: LLMInterpreter = None):
        self.run = run
        self.interpreter = interpreter or LLMInterpreter()

    def query(self, question: str) -> QueryResult:
        """Process a natural language query and return structured answer."""
        question_lower = question.lower()

        # Route to appropriate handler
        if any(kw in question_lower for kw in ["why", "underperform", "weak", "problem", "issue"]):
            return self._handle_diagnostic_query(question)
        elif any(kw in question_lower for kw in ["repeat", "duplicate", "same", "overlap"]):
            return self._handle_duplication_query(question)
        elif any(kw in question_lower for kw in ["know", "knowledge", "concept", "topic", "territory"]):
            return self._handle_knowledge_query(question)
        elif any(kw in question_lower for kw in ["strong", "weak", "quality", "score", "performance"]):
            return self._handle_quality_query(question)
        elif any(kw in question_lower for kw in ["change", "changed", "improve", "worse", "history"]):
            return self._handle_change_query(question)
        elif any(kw in question_lower for kw in ["evidence", "claim", "support", "source"]):
            return self._handle_evidence_query(question)
        elif any(kw in question_lower for kw in ["objective", "goal", "purpose", "coverage"]):
            return self._handle_objective_query(question)
        elif any(kw in question_lower for kw in ["hermes", "investigate", "fix", "task", "action"]):
            return self._handle_hermes_query(question)
        else:
            return self._handle_general_query(question)

    def _handle_diagnostic_query(self, question: str) -> QueryResult:
        """Handle 'why is X underperforming' type queries."""
        # Find relevant pages/issues
        pages = []
        for issue in self.run.issues:
            if any(kw in issue.description.lower() for kw in question.lower().split() if len(kw) > 4):
                pages.extend(issue.affected_pages)

        if not pages:
            # Default to low quality pages
            pages = [p for p, qv in self.run.quality_vectors.items()
                     if (qv.overall if hasattr(qv, 'overall') else qv.get('overall', 0)) < 0.5]

        evidence = []
        for page_id in pages[:3]:
            page_issues = [i for i in self.run.issues if page_id in i.affected_pages]
            for i in page_issues[:2]:
                evidence.append(f"{page_id}: {i.description}")

        return QueryResult(
            query=question,
            answer=f"Based on the intelligence run, {len(pages)} pages show issues related to your question. "
                   f"Primary issues: {evidence[:2] if evidence else 'See issue map for details'}",
            evidence=evidence,
            related_pages=pages[:5],
            related_objectives=[],
            confidence=0.7,
            uncertainty="Specific page diagnosis requires deeper Jev analysis",
            visualization_type="issue_map",
            visualization_data={"pages": pages[:5]}
        )

    def _handle_duplication_query(self, question: str) -> QueryResult:
        """Handle duplication/overlap queries."""
        from intelligence.derived.derived_intelligence import derive_all_intelligence
        findings = derive_all_intelligence(self.run)
        dup_findings = [f for f in findings if "DUPLICATION" in f.type or "OVERLAP" in f.type]

        evidence = [f"{f.title}: {f.description}" for f in dup_findings[:5]]
        pages = list(set(p for f in dup_findings for p in f.affected_pages))

        return QueryResult(
            query=question,
            answer=f"Found {len(dup_findings)} duplication/overlap issues across {len(pages)} pages. "
                   f"Key overlaps: {', '.join(pages[:5])}",
            evidence=evidence,
            related_pages=pages,
            related_objectives=[],
            confidence=0.8,
            uncertainty="Overlap scores are lexical; semantic overlap may differ",
            visualization_type="knowledge_graph",
            visualization_data={"view": "site", "filter": "overlaps"}
        )

    def _handle_knowledge_query(self, question: str) -> QueryResult:
        """Handle knowledge/territory queries."""
        from intelligence.visual.visualisations import prepare_intellectual_territory
        territory = prepare_intellectual_territory(self.run)

        concepts = []
        for cat, items in territory["territories"].items():
            concepts.extend([i["concept"] for i in items])

        return QueryResult(
            query=question,
            answer=f"The site covers {len(concepts)} concepts across {len(territory['territories'])} territory categories. "
                   f"Core territories: {len(territory['territories']['core_territories'])}, "
                   f"Overclaimed: {len(territory['territories']['overclaimed_territories'])}, "
                   f"Underdeveloped: {len(territory['territories']['underdeveloped_territories'])}",
            evidence=[f"{cat}: {len(items)}" for cat, items in territory["territories"].items()],
            related_pages=[],
            related_objectives=[],
            confidence=0.85,
            uncertainty="Territory classification is based on graph structure, not semantic analysis",
            visualization_type="intellectual_territory",
            visualization_data=territory
        )

    def _handle_quality_query(self, question: str) -> QueryResult:
        """Handle quality/performance queries."""
        from intelligence.visual.visualisations import prepare_quality_performance
        qp = prepare_quality_performance(self.run)

        high_quality_low_traffic = len(qp["quadrants"]["high_quality_low_traffic"])
        low_quality_high_traffic = len(qp["quadrants"]["low_quality_high_traffic"])

        return QueryResult(
            query=question,
            answer=f"Quality/Performance analysis: {high_quality_low_traffic} pages high-quality/low-traffic, "
                   f"{low_quality_high_traffic} pages low-quality/high-traffic. "
                   f"{len(qp['anomalies'])} total anomalies detected.",
            evidence=[f"{a['page_id']}: {a['type']}" for a in qp["anomalies"][:5]],
            related_pages=[a["page_id"] for a in qp["anomalies"]],
            related_objectives=[],
            confidence=0.75,
            uncertainty="Traffic scores are normalized heuristics; real analytics not connected",
            visualization_type="quality_performance",
            visualization_data=qp
        )

    def _handle_change_query(self, question: str) -> QueryResult:
        """Handle change/history queries."""
        from intelligence.history.historical_runs import list_runs, compare_runs, load_run

        runs = list_runs()
        if len(runs) < 2:
            return QueryResult(
                query=question,
                answer="Insufficient historical runs for change analysis. Need at least 2 runs.",
                evidence=[],
                related_pages=[],
                related_objectives=[],
                confidence=0.0,
                uncertainty="No previous run to compare against",
                visualization_type="change_graph",
                visualization_data={}
            )

        # Compare latest two runs
        run_b = load_run(runs[-1]["run_id"])
        run_a = load_run(runs[-2]["run_id"])

        # Note: full comparison would need proper deserialization
        return QueryResult(
            query=question,
            answer=f"Latest run ({runs[-1]['run_id']}) vs previous ({runs[-2]['run_id']}). "
                   f"Full change analysis requires run deserialization.",
            evidence=[f"Run {runs[-1]['run_id']}: {runs[-1]['pages_analyzed']} pages",
                      f"Run {runs[-2]['run_id']}: {runs[-2]['pages_analyzed']} pages"],
            related_pages=[],
            related_objectives=[],
            confidence=0.5,
            uncertainty="Historical comparison not fully implemented",
            visualization_type="change_graph",
            visualization_data={"run_a": runs[-2]["run_id"], "run_b": runs[-1]["run_id"]}
        )

    def _handle_evidence_query(self, question: str) -> QueryResult:
        """Handle evidence/claim queries."""
        from intelligence.evidence.evidence_graph import build_evidence_graph, analyze_evidence_health
        graph = build_evidence_graph(self.run.page_states)
        health = analyze_evidence_health(graph)

        return QueryResult(
            query=question,
            answer=f"Evidence health: {health['claims_without_evidence']} claims lack evidence, "
                   f"{health['weak_evidence_claims']} claims have weak evidence, "
                   f"{health['overused_statistics']} statistics overused, "
                   f"{health['stale_sources']} sources potentially stale.",
            evidence=[
                f"Claims without evidence: {health['claims_without_evidence']}",
                f"Weak evidence claims: {health['weak_evidence_claims']}",
                f"Overused statistics: {health['overused_statistics']}",
                f"Stale sources: {health['stale_sources']}"
            ],
            related_pages=[],
            related_objectives=[],
            confidence=0.8,
            uncertainty="Evidence strength scoring is heuristic",
            visualization_type="evidence_graph",
            visualization_data=graph.to_dict()
        )

    def _handle_objective_query(self, question: str) -> QueryResult:
        """Handle objective/coverage queries."""
        from intelligence.visual.visualisations import prepare_ownership_map
        ownership = prepare_ownership_map(self.run)

        unowned = [obj_id for obj_id, data in ownership.items() if data["unowned"]]
        contested = [obj_id for obj_id, data in ownership.items() if data["contested"]]

        return QueryResult(
            query=question,
            answer=f"Objective coverage: {len(unowned)} unowned objectives, {len(contested)} contested objectives. "
                   f"Total objectives: {len(self.run.objectives)}.",
            evidence=[
                f"Unowned: {', '.join(unowned[:5])}",
                f"Contested: {', '.join(contested[:5])}"
            ],
            related_pages=[],
            related_objectives=unowned + contested,
            confidence=0.85,
            uncertainty="Ownership based on quality thresholds, not human judgement",
            visualization_type="ownership_map",
            visualization_data=ownership
        )

    def _handle_hermes_query(self, question: str) -> QueryResult:
        """Handle Hermes task generation queries."""
        high_conf_issues = [i for i in self.run.issues if i.confidence > 0.7]
        tasks = self.interpreter.generate_hermes_tasks(self.run, high_conf_issues, self.run.insights)

        return QueryResult(
            query=question,
            answer=f"Generated {len(tasks)} Hermes tasks from {len(high_conf_issues)} high-confidence issues. "
                   f"Top priority: {tasks[0]['page'] if tasks else 'none'}",
            evidence=[f"{t['page']}: {t['issue']}" for t in tasks[:5]],
            related_pages=[t["page"] for t in tasks],
            related_objectives=[t["objective"] for t in tasks],
            confidence=0.8,
            uncertainty="Tasks are proposals; human approval required before execution",
            visualization_type="page",
            visualization_data={"hermes_tasks": tasks}
        )

    def _handle_general_query(self, question: str) -> QueryResult:
        """Handle general queries with LLM interpretation."""
        if self.interpreter.client:
            site_interpretation = self.interpreter.interpret_site(
                self.run,
                [],  # Would need derived findings
                self.run.issues,
                self.run.insights
            )
            return QueryResult(
                query=question,
                answer=site_interpretation,
                evidence=[],
                related_pages=self.run.pages_analyzed[:5],
                related_objectives=[],
                confidence=0.7,
                uncertainty="LLM interpretation based on structured data",
                visualization_type="site_interpretation",
                visualization_data={}
            )
        else:
            return QueryResult(
                query=question,
                answer="I can answer specific questions about: page quality, duplication, knowledge territories, "
                       "evidence gaps, objective coverage, quality/performance anomalies, and Hermes tasks. "
                       "Try asking: 'Why is AI Discovery underperforming?' or 'Which pages duplicate content?'",
                evidence=[],
                related_pages=[],
                related_objectives=[],
                confidence=0.5,
                uncertainty="General query - no LLM available for open-ended interpretation",
                visualization_type="overview",
                visualization_data={}
            )


def create_ask_the_site(run: IntelligenceRun, interpreter: LLMInterpreter = None) -> AskTheSite:
    return AskTheSite(run, interpreter)