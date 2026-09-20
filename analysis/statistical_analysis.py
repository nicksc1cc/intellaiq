"""
Inflexion Intelligence Engine — Statistical Analysis
Deep data science analyses on the intelligence data
"""

from __future__ import annotations
import json
import statistics
from dataclasses import dataclass, field
from typing import Any
from collections import defaultdict, Counter
from pathlib import Path

try:
    from intelligence.core.models import IntelligenceRun, QualityVector, QualityDimension
    from intelligence.graph.knowledge_graph import KnowledgeGraph, GraphNode, GraphEdge
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from intelligence.core.models import IntelligenceRun, QualityVector, QualityDimension
    from intelligence.graph.knowledge_graph import KnowledgeGraph, GraphNode, GraphEdge


@dataclass
class PageProfile:
    page_id: str
    page_type: str
    quality_vector: dict
    overall_quality: float
    issue_count: int
    issue_severity_dist: dict
    jev_question_count: int
    jev_avg_confidence: float
    jev_yes_rate: float
    jev_no_rate: float
    jev_unclear_rate: float
    concept_count: int
    statistic_count: int
    claim_count: int
    argument_count: int
    overlap_pages: list[str]
    overlap_scores: dict[str, float]


@dataclass
class ClusterAnalysis:
    cluster_name: str
    pages: list[str]
    avg_quality: float
    quality_std: float
    internal_overlap: float
    external_overlap: float
    shared_concepts: list[str]
    dominant_page_types: dict[str, int]
    quality_leaders: list[str]
    quality_laggards: list[str]


@dataclass
class ConceptCentrality:
    concept: str
    degree: int
    betweenness: float
    page_count: int
    avg_page_quality: float
    is_bridge: bool
    owning_pages: list[str]


@dataclass
class JevAnalysis:
    total_questions: int
    by_type: dict[str, int]
    by_theme: dict[str, dict]
    confidence_distribution: dict
    calibration: dict
    question_difficulty: list[dict]


@dataclass
class QualityPerformanceGap:
    page_id: str
    quality_score: float
    traffic_estimate: float
    gap_type: str  # HIGH_QUALITY_LOW_TRAFFIC, LOW_QUALITY_HIGH_TRAFFIC, ALIGNED
    severity: str


class StatisticalAnalyzer:
    def __init__(self, run: IntelligenceRun):
        self.run = run
        self.pages = run.pages_analyzed
        self.qv = run.quality_vectors
        self.jev = run.jev_results
        self.kg = run.knowledge_graph
        self.issues = run.issues
        self.page_states = run.page_states

    def build_page_profiles(self) -> dict[str, PageProfile]:
        profiles = {}
        for page_id in self.pages:
            qv = self.qv.get(page_id, {})
            jev_results = self.jev.get(page_id, [])
            ps = self.page_states.get(page_id)

            # Jev stats
            if jev_results:
                jev_count = len(jev_results)
                confidences = [r.get('confidence', 0) for r in jev_results]
                yes_count = sum(1 for r in jev_results if r.get('result') == 'YES')
                no_count = sum(1 for r in jev_results if r.get('result') == 'NO')
                unclear_count = sum(1 for r in jev_results if r.get('result') == 'UNCLEAR')
            else:
                jev_count = 0
                confidences = [0]
                yes_count = no_count = unclear_count = 0

            # Issue stats
            page_issues = [i for i in self.issues if page_id in i.get('affected_pages', [])]
            severity_dist = Counter(i.get('severity', 'low') for i in page_issues)

            # Overlap from knowledge graph
            overlap_pages = []
            overlap_scores = {}
            for edge in self.kg.edges:
                if edge.relationship == 'OVERLAPS':
                    src = edge.source.replace('page:', '')
                    tgt = edge.target.replace('page:', '')
                    if src == page_id:
                        overlap_pages.append(tgt)
                        overlap_scores[tgt] = edge.weight
                    elif tgt == page_id:
                        overlap_pages.append(src)
                        overlap_scores[src] = edge.weight

            # Concept/stat/claim counts
            concept_count = sum(1 for n in self.kg.nodes
                                if n.node_type == 'CONCEPT' and page_id in n.properties.get('page_ids', []))
            # Use page state for counts
            stat_count = len(ps.statistics) if ps else 0
            claim_count = len(ps.claims) if ps else 0
            arg_count = len(ps.arguments) if ps else 0

            profiles[page_id] = PageProfile(
                page_id=page_id,
                page_type=ps.page_type.value if ps else 'unknown',
                quality_vector=qv.to_dict() if hasattr(qv, 'to_dict') else qv,
                overall_quality=qv.overall if hasattr(qv, 'overall') else qv.get('overall', 0),
                issue_count=len(page_issues),
                issue_severity_dist=dict(severity_dist),
                jev_question_count=jev_count,
                jev_avg_confidence=statistics.mean(confidences) if confidences else 0,
                jev_yes_rate=yes_count / jev_count if jev_count else 0,
                jev_no_rate=no_count / jev_count if jev_count else 0,
                jev_unclear_rate=unclear_count / jev_count if jev_count else 0,
                concept_count=concept_count,
                statistic_count=stat_count,
                claim_count=claim_count,
                argument_count=arg_count,
                overlap_pages=overlap_pages,
                overlap_scores=overlap_scores
            )
        return profiles

    def analyze_clusters(self) -> list[ClusterAnalysis]:
        """Analyze page clusters by topic."""
        # Define clusters based on page types and objectives
        clusters = {
            'AI_DISCOVERY': ['aeo', 'ai-discovery', 'ai-visibility-analytics', 'technical-geo', 'digital-pr'],
            'RETAIL_MEDIA': ['retail-media', 'amazon', 'beauty-media-strategy', 'ai-in-retail-media', 'amazon-ai-creative-studio', 'amazon-rufus-sponsored-prompts'],
            'MEDIA': ['ai-media', 'media', 'agentic-media-buying', 'shoppable-ai-search'],
            'STRATEGY': ['consultancy', 'measurement'],
            'RESEARCH': ['ecommerce-whitepaper'],
            'CORE': ['index', 'contact'],
            'ARTICLES': ['aeo-rankings-to-citations', 'blog']
        }

        profiles = self.build_page_profiles()
        analyses = []

        for cluster_name, page_ids in clusters.items():
            valid_pages = [p for p in page_ids if p in profiles]
            if not valid_pages:
                continue

            qualities = [profiles[p].overall_quality for p in valid_pages]
            issue_counts = [profiles[p].issue_count for p in valid_pages]

            # Internal overlap
            internal_overlaps = []
            for p in valid_pages:
                for other, score in profiles[p].overlap_scores.items():
                    if other in valid_pages:
                        internal_overlaps.append(score)
            avg_internal = statistics.mean(internal_overlaps) if internal_overlaps else 0

            # External overlap
            external_overlaps = []
            for p in valid_pages:
                for other, score in profiles[p].overlap_scores.items():
                    if other not in valid_pages:
                        external_overlaps.append(score)
            avg_external = statistics.mean(external_overlaps) if external_overlaps else 0

            # Shared concepts
            concept_pages = defaultdict(list)
            for node in self.kg.nodes:
                if node.node_type == 'CONCEPT':
                    for edge in self.kg.edges:
                        if edge.target == node.node_id and edge.relationship == 'USES':
                            src = edge.source.replace('page:', '')
                            if src in valid_pages:
                                concept_pages[node.label].append(src)
            shared = {c: pages for c, pages in concept_pages.items() if len(pages) > 1}

            # Page types
            page_types = Counter(profiles[p].page_type for p in valid_pages)

            # Quality leaders/laggards
            sorted_pages = sorted(valid_pages, key=lambda p: profiles[p].overall_quality, reverse=True)

            analyses.append(ClusterAnalysis(
                cluster_name=cluster_name,
                pages=valid_pages,
                avg_quality=statistics.mean(qualities) if qualities else 0,
                quality_std=statistics.stdev(qualities) if len(qualities) > 1 else 0,
                internal_overlap=avg_internal,
                external_overlap=avg_external,
                shared_concepts=list(shared.keys())[:10],
                dominant_page_types=dict(page_types),
                quality_leaders=sorted_pages[:2],
                quality_laggards=sorted_pages[-2:]
            ))
        return analyses

    def analyze_concept_centrality(self) -> list[ConceptCentrality]:
        """Analyze concept centrality in the knowledge graph."""
        concept_nodes = [n for n in self.kg.nodes if n.node_type == 'CONCEPT']
        results = []

        for node in concept_nodes:
            # Degree = number of pages using this concept
            page_count = 0
            owning_pages = []
            for edge in self.kg.edges:
                if edge.target == node.node_id and edge.relationship == 'USES':
                    src = edge.source.replace('page:', '')
                    if src in self.pages:
                        page_count += 1
                        owning_pages.append(src)

            if page_count == 0:
                continue

            # Avg quality of owning pages
            qualities = [self.qv.get(p, {}).overall if hasattr(self.qv.get(p, {}), 'overall')
                         else self.qv.get(p, {}).get('overall', 0) for p in owning_pages]
            avg_quality = statistics.mean(qualities) if qualities else 0

            # Betweenness proxy: does this concept connect different clusters?
            cluster_pages = {
                'AI_DISCOVERY': {'aeo', 'ai-discovery', 'ai-visibility-analytics', 'technical-geo', 'digital-pr'},
                'RETAIL_MEDIA': {'retail-media', 'amazon', 'beauty-media-strategy', 'ai-in-retail-media'},
                'MEDIA': {'ai-media', 'media', 'agentic-media-buying', 'shoppable-ai-search'},
                'STRATEGY': {'consultancy', 'measurement'},
                'RESEARCH': {'ecommerce-whitepaper'}
            }
            clusters_covered = sum(1 for cluster, pages in cluster_pages.items()
                                   if owning_pages and set(owning_pages) & pages)
            is_bridge = clusters_covered >= 2

            results.append(ConceptCentrality(
                concept=node.label,
                degree=page_count,
                betweenness=float(clusters_covered),
                page_count=page_count,
                avg_page_quality=avg_quality,
                is_bridge=is_bridge,
                owning_pages=owning_pages
            ))

        return sorted(results, key=lambda x: (x.is_bridge, x.degree), reverse=True)

    def analyze_jev_results(self) -> JevAnalysis:
        """Statistical analysis of Jev results."""
        all_results = []
        for page_id, results in self.jev.items():
            for r in results:
                r['page_id'] = page_id
                all_results.append(r)

        by_type = Counter(r.get('question_type', 'unknown') for r in all_results)

        by_theme = {}
        for r in all_results:
            # Infer theme from question_id
            qid = r.get('question_id', '')
            theme = 'unknown'
            for t in ['PURPOSE', 'DISTINCT', 'EVIDENCE', 'SPECIFICITY', 'DIFF', 'TECH_PRECISION',
                      'COMMERCIAL', 'WRITING', 'STRUCTURE', 'ARGUMENT', 'CITATION', 'REPETITION',
                      'KNOWLEDGE', 'INTERNAL', 'AUTHORITY', 'AI_DISCOVERY', 'TECH_GEO', 'OUTCOME']:
                if t in qid:
                    theme = t
                    break
            if theme not in by_theme:
                by_theme[theme] = {'total': 0, 'yes': 0, 'no': 0, 'unclear': 0, 'confidences': []}
            by_theme[theme]['total'] += 1
            result = r.get('result', '')
            if result == 'YES':
                by_theme[theme]['yes'] += 1
            elif result == 'NO':
                by_theme[theme]['no'] += 1
            else:
                by_theme[theme]['unclear'] += 1
            by_theme[theme]['confidences'].append(r.get('confidence', 0))

        confidences = [r.get('confidence', 0) for r in all_results]
        conf_dist = {
            '0.0-0.2': sum(1 for c in confidences if 0 <= c < 0.2),
            '0.2-0.4': sum(1 for c in confidences if 0.2 <= c < 0.4),
            '0.4-0.6': sum(1 for c in confidences if 0.4 <= c < 0.6),
            '0.6-0.8': sum(1 for c in confidences if 0.6 <= c < 0.8),
            '0.8-1.0': sum(1 for c in confidences if 0.8 <= c < 1.0),
        }

        # Calibration: for NOUL questions, check if confidence matches correctness
        # (Would need ground truth - skipped)

        # Question difficulty: questions with lowest YES rate across pages
        question_stats = defaultdict(lambda: {'yes': 0, 'no': 0, 'unclear': 0, 'pages': 0})
        for r in all_results:
            qid = r.get('question_id', '')
            question_stats[qid]['pages'] += 1
            result = r.get('result', '')
            if result == 'YES':
                question_stats[qid]['yes'] += 1
            elif result == 'NO':
                question_stats[qid]['no'] += 1
            else:
                question_stats[qid]['unclear'] += 1

        difficulty = []
        for qid, stats in question_stats.items():
            if stats['pages'] >= 3:
                yes_rate = stats['yes'] / stats['pages']
                difficulty.append({
                    'question_id': qid,
                    'yes_rate': yes_rate,
                    'no_rate': stats['no'] / stats['pages'],
                    'unclear_rate': stats['unclear'] / stats['pages'],
                    'pages_evaluated': stats['pages']
                })
        difficulty.sort(key=lambda x: x['yes_rate'])

        return JevAnalysis(
            total_questions=len(all_results),
            by_type=dict(by_type),
            by_theme={k: {**v, 'avg_confidence': statistics.mean(v['confidences']) if v['confidences'] else 0}
                      for k, v in by_theme.items()},
            confidence_distribution=conf_dist,
            calibration={},  # Would need ground truth
            question_difficulty=difficulty[:20]
        )

    def detect_quality_performance_gaps(self) -> list[QualityPerformanceGap]:
        """Detect pages where quality and estimated performance diverge."""
        # Use heuristic traffic estimates based on page characteristics
        gaps = []
        for page_id in self.pages:
            qv = self.qv.get(page_id)
            if not qv:
                continue
            quality = qv.overall if hasattr(qv, 'overall') else qv.get('overall', 0)

            # Heuristic traffic estimate
            ps = self.page_states.get(page_id)
            traffic = 0
            if ps:
                # More headings/sections = more content = potentially more traffic
                traffic += len(ps.headings) * 0.02
                traffic += len(ps.sections) * 0.03
                traffic += len(ps.statistics) * 0.05
                traffic += len(ps.claims) * 0.02
                # Service pages typically get more traffic
                if ps.page_type.value in ['service', 'technical']:
                    traffic += 0.3
                # Whitepaper gets traffic
                if ps.page_type.value == 'whitepaper':
                    traffic += 0.4

            traffic = min(1.0, traffic)

            if quality > 0.7 and traffic < 0.3:
                gaps.append(QualityPerformanceGap(page_id, quality, traffic, 'HIGH_QUALITY_LOW_TRAFFIC', 'high'))
            elif quality < 0.4 and traffic > 0.5:
                gaps.append(QualityPerformanceGap(page_id, quality, traffic, 'LOW_QUALITY_HIGH_TRAFFIC', 'high'))
            elif abs(quality - traffic) < 0.15:
                gaps.append(QualityPerformanceGap(page_id, quality, traffic, 'ALIGNED', 'low'))
        return gaps

    def run_all_analyses(self) -> dict:
        """Run all analyses and return combined results."""
        profiles = self.build_page_profiles()
        clusters = self.analyze_clusters()
        concepts = self.analyze_concept_centrality()
        jev = self.analyze_jev_results()
        gaps = self.detect_quality_performance_gaps()

        return {
            'page_profiles': {k: v.__dict__ for k, v in profiles.items()},
            'cluster_analyses': [c.__dict__ for c in clusters],
            'concept_centrality': [c.__dict__ for c in concepts],
            'jev_analysis': jev.__dict__,
            'quality_performance_gaps': [g.__dict__ for g in gaps]
        }


def analyze_run(run: IntelligenceRun) -> dict:
    analyzer = StatisticalAnalyzer(run)
    return analyzer.run_all_analyses()


def export_analysis(analysis: dict, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for key, value in analysis.items():
        filepath = output_dir / f"{key}.json"
        filepath.write_text(json.dumps(value, indent=2, default=str))