#!/usr/bin/env python3
"""
Inflexion Intelligence Engine — Full Pipeline Runner
Manual run: PYTHONPATH=. python3 pipelines/full_run.py
"""

import sys
import os
import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path

# Add intelligence directory to path
INTELLIGENCE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(INTELLIGENCE_DIR))

try:
    from intelligence.core.models import IntelligenceRun
    from intelligence.ingestion.page_ingestion import PageIngestion
    from intelligence.objectives.objective_registry import get_objectives_for_page, get_all_objectives
    from intelligence.jev.jev_engine import create_jev_engine
    from intelligence.quality.quality_vectors import calculate_all_quality_vectors
    from intelligence.graph.knowledge_graph import build_knowledge_graph
    from intelligence.evidence.evidence_graph import build_evidence_graph
    from intelligence.history.historical_runs import save_run, load_latest_run
    from intelligence.derived.derived_intelligence import derive_all_intelligence, generate_issues_from_findings, generate_insights_from_findings
    from intelligence.llm.llm_interpreter import create_interpreter
    from intelligence.visual.visualisations import prepare_all_visualizations, export_visualizations
except ImportError as e:
    print(f"[ERROR] Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PipelineProgress:
    def __init__(self, stage: str, progress: float, message: str, details: dict = None):
        self.stage = stage
        self.progress = progress
        self.message = message
        self.details = details


class IntelligencePipeline:
    def __init__(
        self,
        site_root: Path,
        typesafe_api_key: str | None = None,
        openai_api_key: str | None = None,
        progress_callback=None
    ):
        self.site_root = Path(site_root)
        self.typesafe_api_key = typesafe_api_key or os.environ.get("TYPESAFE_API_KEY")
        self.openai_api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
        self.progress_callback = progress_callback

        self.ingestion = PageIngestion(self.site_root)
        self.jev_engine = create_jev_engine(self.typesafe_api_key)
        self.interpreter = create_interpreter(self.openai_api_key) if self.openai_api_key else None

    def _report(self, stage: str, progress: float, message: str, details: dict = None) -> None:
        if self.progress_callback:
            self.progress_callback(PipelineProgress(stage, progress, message, details))
        logger.info(f"[{progress:.0%}] {stage}: {message}")

        # Also print to console
        bar_len = 30
        filled = int(bar_len * progress)
        bar = "█" * filled + "░" * (bar_len - filled)
        print(f"\r{stage} |{bar}| {progress:.0%} - {message}", end="", flush=True)
        if progress >= 1.0:
            print()

    def _get_git_commit(self) -> str:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True, text=True, cwd=self.site_root, timeout=10
            )
            return result.stdout.strip()[:8]
        except:
            return "unknown"

    def _get_git_branch(self) -> str:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True, text=True, cwd=self.site_root, timeout=10
            )
            return result.stdout.strip()
        except:
            return "main"

    def run_full_intelligence(self) -> IntelligenceRun:
        """Run the complete intelligence pipeline."""
        run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        git_commit = self._get_git_commit()
        git_branch = self._get_git_branch()

        print("\n" + "=" * 60)
        print("INFLEXION INTELLIGENCE ENGINE")
        print(f"Run: {run_id}")
        print(f"Commit: {git_commit}")
        print(f"Branch: {git_branch}")
        print("=" * 60 + "\n")

        # STAGE 1: READ SITE
        self._report("READING SITE", 0.02, "Discovering and ingesting all pages")
        pages = self.ingestion.ingest_all()
        self._report("READING SITE", 0.05, f"Ingested {len(pages)} pages")

        # STAGE 2: EXTRACT KNOWLEDGE (done during ingestion)

        # STAGE 3: BUILD KNOWLEDGE GRAPH
        self._report("BUILDING KNOWLEDGE GRAPH", 0.15, "Building knowledge graph with relationships")
        knowledge_graph = build_knowledge_graph(pages)
        self._report("BUILDING KNOWLEDGE GRAPH", 0.20, f"Graph: {len(knowledge_graph.nodes)} nodes, {len(knowledge_graph.edges)} edges")

        # STAGE 4: LOAD OBJECTIVES
        self._report("LOADING OBJECTIVES", 0.22, "Mapping objectives to pages")
        all_objectives = get_all_objectives()
        page_objectives = {}
        for page_id, page in pages.items():
            objectives = get_objectives_for_page(page_id, page.page_type)
            page_objectives[page_id] = []
            for obj in objectives:
                from intelligence.core.models import PageObjective
                page_objectives[page_id].append(PageObjective(
                    page_id=page_id,
                    objective_id=obj.objective_id,
                    is_primary=(obj.code == "O01"),
                    coverage=0.0,
                    quality=0.0,
                    confidence=0.0,
                    question_count=0
                ))

        # STAGE 5: GENERATE QUESTIONS (done on-the-fly during Jev)

        # STAGE 6: RUN JEV EVALUATION
        self._report("EVALUATING JEV QUESTIONS", 0.30, f"Running Jev evaluation across {len(pages)} pages")
        def jev_progress(completed, total, page_id):
            pct = 0.30 + 0.35 * (completed / total)
            self._report("EVALUATING JEV QUESTIONS", pct, f"Evaluated {completed}/{total} pages (last: {page_id})")

        jev_results = self.jev_engine.evaluate_all_pages(pages, run_id, jev_progress)
        total_questions = sum(len(r) for r in jev_results.values())
        self._report("EVALUATING JEV QUESTIONS", 0.65, f"Completed: {total_questions} questions across {len(pages)} pages")

        # STAGE 7: CALCULATE QUALITY VECTORS
        self._report("COMPOSING INTELLIGENCE", 0.68, "Calculating quality vectors")
        quality_vectors = calculate_all_quality_vectors(pages, jev_results, page_objectives)
        self._report("COMPOSING INTELLIGENCE", 0.72, "Quality vectors calculated")

        # STAGE 8: DERIVED INTELLIGENCE
        self._report("CALCULATING DERIVED RELATIONSHIPS", 0.75, "Detecting duplication, gaps, concentration")
        temp_run = IntelligenceRun(
            run_id=run_id, timestamp=datetime.now(), git_commit=git_commit, branch=git_branch,
            pages_analyzed=list(pages.keys()), page_states=pages, quality_vectors=quality_vectors,
            jev_results=jev_results, knowledge_graph=knowledge_graph, evidence_graph={},
            performance_data={}, page_objectives=page_objectives, objectives=all_objectives,
            issues=[], insights=[], change_events=[], hermes_tasks=[]
        )
        findings = derive_all_intelligence(temp_run)
        self._report("CALCULATING DERIVED RELATIONSHIPS", 0.78, f"Found {len(findings)} derived findings")

        # STAGE 9: ISSUES & INSIGHTS
        self._report("GENERATING ISSUES & INSIGHTS", 0.80, "Converting findings to issues and insights")
        issues = generate_issues_from_findings(findings)
        insights = generate_insights_from_findings(findings)
        self._report("GENERATING ISSUES & INSIGHTS", 0.83, f"Generated {len(issues)} issues, {len(insights)} insights")

        # STAGE 10: EVIDENCE GRAPH
        self._report("BUILDING EVIDENCE GRAPH", 0.85, "Building evidence graph")
        evidence_graph = build_evidence_graph(pages)

        # STAGE 11: PERFORMANCE DATA (placeholder)
        self._report("LOADING PERFORMANCE DATA", 0.87, "Checking for performance data")
        performance_data = {}

        # STAGE 12: HISTORICAL COMPARISON
        self._report("COMPARING WITH PREVIOUS RUN", 0.89, "Comparing with previous run")
        prev_run = load_latest_run()
        change_events = []

        # STAGE 13: HERMES TASKS
        self._report("GENERATING HERMES TASKS", 0.92, "Generating Hermes intervention tasks")
        hermes_tasks = []
        if self.interpreter:
            final_run = IntelligenceRun(
                run_id=run_id, timestamp=datetime.now(), git_commit=git_commit, branch=git_branch,
                pages_analyzed=list(pages.keys()), page_states=pages, quality_vectors=quality_vectors,
                jev_results=jev_results, knowledge_graph=knowledge_graph, evidence_graph=evidence_graph.to_dict(),
                performance_data=performance_data, page_objectives=page_objectives, objectives=all_objectives,
                issues=issues, insights=insights, change_events=change_events, hermes_tasks=[]
            )
            hermes_tasks = self.interpreter.generate_hermes_tasks(final_run, issues, insights)

        # STAGE 14: SAVE RUN
        self._report("STORING RUN", 0.95, "Saving intelligence run")
        final_run = IntelligenceRun(
            run_id=run_id,
            timestamp=datetime.now(),
            git_commit=git_commit,
            branch=git_branch,
            pages_analyzed=list(pages.keys()),
            page_states=pages,
            quality_vectors=quality_vectors,
            jev_results=jev_results,
            knowledge_graph=knowledge_graph,
            evidence_graph=evidence_graph.to_dict(),
            performance_data=performance_data,
            page_objectives=page_objectives,
            objectives=all_objectives,
            issues=issues,
            insights=insights,
            change_events=change_events,
            hermes_tasks=hermes_tasks
        )

        save_run(final_run)

        # STAGE 15: VISUALIZATIONS
        self._report("RENDERING VISUALIZATIONS", 0.98, "Exporting visualization data")
        viz = prepare_all_visualizations(final_run)
        export_visualizations(viz, INTELLIGENCE_DIR / "data" / "visualisations" / run_id)

        self._report("COMPLETE", 1.0, f"Run {run_id} complete: {len(pages)} pages, {total_questions} questions, {len(issues)} issues, {len(insights)} insights, {len(hermes_tasks)} Hermes tasks")

        # Print summary
        print("\n" + "=" * 60)
        print("RUN COMPLETE")
        print("=" * 60)
        print(f"  Run ID: {run_id}")
        print(f"  Timestamp: {datetime.now().isoformat()}")
        print(f"  Commit: {git_commit}")
        print(f"  Pages analyzed: {len(pages)}")
        print(f"  Knowledge graph: {len(knowledge_graph.nodes)} nodes, {len(knowledge_graph.edges)} edges")
        print(f"  Jev questions: {total_questions}")
        print(f"  Issues: {len(issues)}")
        print(f"  Insights: {len(insights)}")
        print(f"  Hermes tasks: {len(hermes_tasks)}")

        if issues:
            high_issues = [i for i in issues if i.severity.value in ["high", "critical"]]
            print(f"\n  High-priority issues: {len(high_issues)}")
            for i in high_issues[:5]:
                print(f"    [{i.severity.value.upper()}] {i.affected_pages[0] if i.affected_pages else 'site'}: {i.description[:80]}")

        if hermes_tasks:
            print(f"\n  --- HERMES TASKS ---")
            for t in hermes_tasks[:5]:
                print(f"  [{t['priority'].upper()}] {t['page']}: {t['issue'][:80]}")

        print()
        return final_run


def run_pipeline_cli(
    site_root: str = ".",
    typesafe_api_key: str | None = None,
    openai_api_key: str | None = None
) -> IntelligenceRun:
    """CLI entry point for running the pipeline."""
    pipeline = IntelligencePipeline(
        site_root=Path(site_root),
        typesafe_api_key=typesafe_api_key,
        openai_api_key=openai_api_key,
        progress_callback=None  # Uses internal printing
    )
    return pipeline.run_full_intelligence()


if __name__ == "__main__":
    site_root = sys.argv[1] if len(sys.argv) > 1 else "."
    run = run_pipeline_cli(site_root)
    print(f"\nRun complete: {run.run_id}")