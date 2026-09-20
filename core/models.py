"""
Inflexion Intelligence Engine — Core Data Models
Phase 3: Data Model
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
import json


class PageType(Enum):
    FOUNDATIONAL = "foundational"
    SERVICE = "service"
    TECHNICAL = "technical"
    THOUGHT_LEADERSHIP = "thought_leadership"
    RESEARCH = "research"
    APPLICATION = "application"
    COMMERCIAL = "commercial"
    EDITORIAL = "editorial"
    RESOURCE = "resource"
    CASE_STUDY = "case_study"
    WHITEPAPER = "whitepaper"
    NAVIGATIONAL = "navigational"
    OTHER = "other"


class QuestionType(Enum):
    NOUL = "noul"
    CHOICE = "choice"
    SCORE = "score"


class QuestionPrimitive(Enum):
    PURPOSE = "purpose"
    DISTINCTIVENESS = "distinctiveness"
    EVIDENCE = "evidence"
    SPECIFICITY = "specificity"
    DIFFERENTIATION = "differentiation"
    TECHNICAL_PRECISION = "technical_precision"
    COMMERCIAL_RELEVANCE = "commercial_relevance"
    HUMAN_WRITING = "human_writing"
    STRUCTURAL_COHERENCE = "structural_coherence"
    ARGUMENT = "argument"
    CITATION = "citation"
    REPETITION = "repetition"
    KNOWLEDGE = "knowledge"
    INTERNAL_RELATIONSHIP = "internal_relationship"
    TOPICAL_AUTHORITY = "topical_authority"
    AI_DISCOVERY = "ai_discovery"
    TECHNICAL_GEO = "technical_geo"
    COMMERCIAL = "commercial"
    OUTCOME = "outcome"


class Severity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IssueCategory(Enum):
    CONTENT = "content"
    ARGUMENT = "argument"
    EVIDENCE = "evidence"
    TECHNICAL = "technical"
    DIFFERENTIATION = "differentiation"
    DUPLICATION = "duplication"
    WRITING = "writing"
    VISUAL = "visual"
    SEO = "seo"
    AEO = "aeo"
    GEO = "geo"
    AI_VISIBILITY = "ai_visibility"
    COMMERCIAL = "commercial"
    KNOWLEDGE_GRAPH = "knowledge_graph"
    STRUCTURE = "structure"
    PERFORMANCE = "performance"
    UNCERTAINTY = "uncertainty"


class RelationshipType(Enum):
    OWNS = "owns"
    SUPPORTED_BY = "supported_by"
    TARGETS = "targets"
    COVERS = "covers"
    CONTAINS = "contains"
    USES = "uses"
    LINKS_TO = "links_to"
    OVERLAPS = "overlaps"
    DUPLICATES = "duplicates"
    CONTRADICTS = "contradicts"
    SPECIALISES = "specialises"
    GENERALISES = "generalises"
    EXEMPLIFIES = "exemplifies"
    COMPETES_FOR = "competes_for"
    ATTRACTS = "attracts"
    RECEIVES = "receives"
    GENERATES = "generates"
    EVALUATED_BY = "evaluated_by"


class NodeType(Enum):
    PAGE = "page"
    TOPIC = "topic"
    ARGUMENT = "argument"
    CLAIM = "claim"
    EVIDENCE = "evidence"
    SOURCE = "source"
    STATISTIC = "statistic"
    PLATFORM = "platform"
    TECHNOLOGY = "technology"
    SERVICE = "service"
    CONCEPT = "concept"
    ENTITY = "entity"
    OBSERVATION = "observation"
    RECOMMENDATION = "recommendation"
    OBJECTIVE = "objective"
    QUESTION = "question"
    ISSUE = "issue"
    IMAGE = "image"
    QUERY = "query"
    COMPETITOR = "competitor"
    METRIC = "metric"
    OUTCOME = "outcome"
    RUN = "run"
    VERSION = "version"


@dataclass
class QualityDimension:
    score: float
    confidence: float
    evidence_refs: list[str] = field(default_factory=list)
    weak_questions: list[str] = field(default_factory=list)
    strong_questions: list[str] = field(default_factory=list)

    def __post_init__(self):
        self.score = max(0.0, min(1.0, self.score))
        self.confidence = max(0.0, min(1.0, self.confidence))


@dataclass
class QualityVector:
    intellectual_distinctiveness: QualityDimension
    evidence_quality: QualityDimension
    subject_specificity: QualityDimension
    argument_quality: QualityDimension
    human_writing: QualityDimension
    structural_quality: QualityDimension
    site_differentiation: QualityDimension
    technical_accuracy: QualityDimension
    commercial_usefulness: QualityDimension
    editorial_quality: QualityDimension
    knowledge_contribution: QualityDimension
    objective_coverage: QualityDimension
    confidence: QualityDimension

    def to_dict(self) -> dict:
        d = {k: v.__dict__ for k, v in self.__dict__.items()}
        d["overall"] = self.overall
        return d

    @property
    def overall(self) -> float:
        scores = [v.score for v in self.__dict__.values()]
        return sum(scores) / len(scores) if scores else 0.0


@dataclass
class PageState:
    page_id: str
    url: str
    title: str
    page_type: PageType
    body_text: str
    headings: list[str]
    sections: list[dict]
    claims: list["Claim"]
    arguments: list["Argument"]
    topics: list[str]
    entities: list[str]
    statistics: list["Statistic"]
    evidence_refs: list[str]
    internal_links: list[str]
    images: list[dict]
    schema: dict
    word_count: int
    last_modified: datetime
    git_commit: str

    def to_dict(self) -> dict:
        d = self.__dict__.copy()
        d["page_type"] = self.page_type.value
        d["last_modified"] = self.last_modified.isoformat()
        d["claims"] = [c.to_dict() for c in self.claims]
        d["arguments"] = [a.to_dict() for a in self.arguments]
        d["statistics"] = [s.to_dict() for s in self.statistics]
        return d


@dataclass
class Claim:
    claim_id: str
    text: str
    page_id: str
    section_id: str | None
    evidence_refs: list[str]
    claim_type: str
    confidence: float
    is_central: bool = False

    def to_dict(self) -> dict:
        return self.__dict__.copy()


@dataclass
class Argument:
    argument_id: str
    text: str
    page_id: str
    claims: list[str]
    objectives: list[str]
    is_distinctive: bool = False
    overlap_pages: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return self.__dict__.copy()


@dataclass
class Statistic:
    statistic_id: str
    value: str
    context: str
    page_id: str
    source: str | None
    date: str | None
    used_on_pages: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return self.__dict__.copy()


@dataclass
class Objective:
    objective_id: str
    code: str
    title: str
    description: str
    page_type: PageType | None
    applies_to: list[str] = field(default_factory=list)
    weight: float = 1.0
    question_templates: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = self.__dict__.copy()
        d["page_type"] = self.page_type.value if self.page_type else None
        return d


@dataclass
class PageObjective:
    page_id: str
    objective_id: str
    is_primary: bool = False
    coverage: float = 0.0
    quality: float = 0.0
    confidence: float = 0.0
    question_count: int = 0
    weak_questions: list[str] = field(default_factory=list)
    strong_questions: list[str] = field(default_factory=list)
    uncertainty: float = 0.0
    ownership: str | None = None
    relationships: list[str] = field(default_factory=list)
    historical_change: float = 0.0

    def to_dict(self) -> dict:
        return self.__dict__.copy()


@dataclass
class QuestionTemplate:
    template_id: str
    primitive: QuestionPrimitive
    question_type: QuestionType
    instructions_template: str
    criteria_template: dict | list | None
    applies_to_objectives: list[str]
    applies_to_page_types: list[PageType]
    variables: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = self.__dict__.copy()
        d["primitive"] = self.primitive.value
        d["question_type"] = self.question_type.value
        d["applies_to_page_types"] = [p.value for p in self.applies_to_page_types]
        return d


@dataclass
class GeneratedQuestion:
    question_id: str
    template_id: str
    page_id: str
    objective_id: str
    question_type: QuestionType
    instructions: str
    criteria: dict | list | None
    variables: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = self.__dict__.copy()
        d["question_type"] = self.question_type.value
        return d


@dataclass
class JevResult:
    question_id: str
    page_id: str
    objective_id: str
    question_type: QuestionType
    result: Any
    probability: float | dict | None
    confidence: float
    evidence_refs: list[str]
    text_locations: list[str]
    timestamp: datetime
    run_id: str

    def to_dict(self) -> dict:
        d = self.__dict__.copy()
        d["question_type"] = self.question_type.value
        d["timestamp"] = self.timestamp.isoformat()
        return d


@dataclass
class GraphNode:
    node_id: str
    node_type: NodeType
    label: str
    properties: dict = field(default_factory=dict)
    centrality: float = 0.0
    community: int | None = None

    def to_dict(self) -> dict:
        d = self.__dict__.copy()
        d["node_type"] = self.node_type.value
        return d


@dataclass
class GraphEdge:
    edge_id: str
    source: str
    target: str
    relationship: RelationshipType
    weight: float = 1.0
    confidence: float = 1.0
    properties: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = self.__dict__.copy()
        d["relationship"] = self.relationship.value
        return d


@dataclass
class KnowledgeGraph:
    nodes: list[GraphNode] = field(default_factory=list)
    edges: list[GraphEdge] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges]
        }


@dataclass
class Evidence:
    evidence_id: str
    text: str
    source: str
    source_type: str
    date: str | None
    strength: float
    claims_supported: list[str]
    pages_using: list[str]
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return self.__dict__.copy()


@dataclass
class PerformanceSnapshot:
    page_id: str
    timestamp: datetime
    organic_impressions: int | None = None
    organic_clicks: int | None = None
    organic_ctr: float | None = None
    rankings: dict[str, int] = field(default_factory=dict)
    queries: list[str] = field(default_factory=list)
    landing_sessions: int | None = None
    ai_citations: int | None = None
    ai_mentions: int | None = None
    answer_visibility: float | None = None
    source_inclusion: float | None = None
    citation_frequency: float | None = None
    referring_ai_systems: list[str] = field(default_factory=list)
    competitor_citation_comparison: dict[str, int] = field(default_factory=dict)
    sessions: int | None = None
    engaged_sessions: int | None = None
    engagement_rate: float | None = None
    avg_time: float | None = None
    depth: float | None = None
    leads: int | None = None
    enquiries: int | None = None
    cta_interactions: int | None = None
    conversion_events: int | None = None
    assisted_conversions: int | None = None
    commercial_pathways: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = self.__dict__.copy()
        d["timestamp"] = self.timestamp.isoformat()
        return d


@dataclass
class Issue:
    issue_id: str
    category: IssueCategory
    severity: Severity
    confidence: float
    affected_pages: list[str]
    affected_objectives: list[str]
    root_cause: str
    evidence: list[str]
    description: str
    status: str = "open"
    owner: str | None = None
    history: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = self.__dict__.copy()
        d["category"] = self.category.value
        d["severity"] = self.severity.value
        return d


@dataclass
class Insight:
    insight_id: str
    type: str
    title: str
    observation: str
    supporting_pages: list[str]
    supporting_objectives: list[str]
    supporting_questions: list[str]
    supporting_evidence: list[str]
    confidence: float
    severity: Severity
    scope: str
    affected_relationships: list[str]
    historical_change: float
    possible_action: str
    recommended_owner: str
    uncertainty: float

    def to_dict(self) -> dict:
        d = self.__dict__.copy()
        d["severity"] = self.severity.value
        return d


@dataclass
class IntelligenceRun:
    run_id: str
    timestamp: datetime
    git_commit: str
    branch: str
    pages_analyzed: list[str]
    page_states: dict[str, PageState]
    quality_vectors: dict[str, QualityVector]
    jev_results: dict[str, list[JevResult]]
    knowledge_graph: KnowledgeGraph
    evidence_graph: dict[str, Evidence]
    performance_data: dict[str, PerformanceSnapshot]
    page_objectives: dict[str, list[PageObjective]]
    objectives: list[Objective]
    issues: list[Issue]
    insights: list[Insight]
    change_events: list[dict] = field(default_factory=list)
    hermes_tasks: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        def serialize(obj):
            if hasattr(obj, "to_dict"):
                return obj.to_dict()
            if hasattr(obj, "value"):
                return obj.value
            if isinstance(obj, datetime):
                return obj.isoformat()
            if isinstance(obj, dict):
                return {k: serialize(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [serialize(v) for v in obj]
            return obj
        return serialize(self.__dict__)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)