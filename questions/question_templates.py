"""
Inflexion Intelligence Engine — Question Primitives and Templates
Phase 6: Question Primitives
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any

try:
    from intelligence.core.models import QuestionTemplate, QuestionPrimitive, QuestionType, PageType
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from intelligence.core.models import QuestionTemplate, QuestionPrimitive, QuestionType, PageType


QUESTION_TEMPLATES: dict[str, QuestionTemplate] = {}


def register_template(template: QuestionTemplate) -> None:
    QUESTION_TEMPLATES[template.template_id] = template


# ============================================================
# PURPOSE PRIMITIVES
# ============================================================

register_template(QuestionTemplate(
    template_id="PURPOSE_CLEAR",
    primitive=QuestionPrimitive.PURPOSE,
    question_type=QuestionType.NOUL,
    instructions_template=(
        "Does the page clearly communicate its primary purpose within the first two sections? "
        "A reader should understand what this page is for without scrolling past the fold."
    ),
    criteria_template={
        "true": "Purpose is explicit and specific in the opening sections",
        "false": "Purpose is vague, generic, or only implied"
    },
    applies_to_objectives=["*"],
    applies_to_page_types=[PageType.SERVICE, PageType.TECHNICAL, PageType.APPLICATION, PageType.WHITEPAPER],
    variables=["page_type", "service_name"]
))

register_template(QuestionTemplate(
    template_id="PURPOSE_UNIQUE",
    primitive=QuestionPrimitive.PURPOSE,
    question_type=QuestionType.NOUL,
    instructions_template=(
        "Is the page's purpose distinct from every other page on the Inflexion site? "
        "Could this purpose statement apply to another Inflexion page?"
    ),
    criteria_template={
        "true": "Purpose is uniquely owned by this page",
        "false": "Purpose overlaps with one or more other pages"
    },
    applies_to_objectives=["*"],
    applies_to_page_types=[PageType.SERVICE, PageType.TECHNICAL, PageType.APPLICATION],
    variables=["page_id", "other_page_ids"]
))

# ============================================================
# DISTINCTIVENESS PRIMITIVES
# ============================================================

register_template(QuestionTemplate(
    template_id="DISTINCT_ARGUMENT",
    primitive=QuestionPrimitive.DISTINCTIVENESS,
    question_type=QuestionType.NOUL,
    instructions_template=(
        "Does this page make a core argument that no other Inflexion page makes? "
        "Identify the central thesis and check whether it appears elsewhere."
    ),
    criteria_template={
        "true": "Central argument is unique to this page",
        "false": "Central argument appears substantially on another page"
    },
    applies_to_objectives=["*"],
    applies_to_page_types=[PageType.SERVICE, PageType.TECHNICAL, PageType.APPLICATION, PageType.WHITEPAPER, PageType.THOUGHT_LEADERSHIP],
    variables=["page_id", "core_argument"]
))

register_template(QuestionTemplate(
    template_id="DISTINCT_VS_SPECIFIC_PAGE",
    primitive=QuestionPrimitive.DISTINCTIVENESS,
    question_type=QuestionType.NOUL,
    instructions_template=(
        "Does this page make a meaningful conceptual distinction from {other_page}? "
        "The distinction should be substantive (different mechanics, different scope, different level) not merely lexical."
    ),
    criteria_template={
        "true": "Clear conceptual boundary with {other_page} is established",
        "false": "Boundary is blurred, overlapping, or only lexical"
    },
    applies_to_objectives=["*"],
    applies_to_page_types=[PageType.SERVICE, PageType.TECHNICAL, PageType.APPLICATION],
    variables=["page_id", "other_page", "distinction_type"]
))

register_template(QuestionTemplate(
    template_id="DISTINCT_INTELLECTUAL_JOB",
    primitive=QuestionPrimitive.DISTINCTIVENESS,
    question_type=QuestionType.CHOICE,
    instructions_template=(
        "What is the primary intellectual job this page does for the Inflexion site? "
        "Choose the single best description."
    ),
    criteria_template={
        "foundational": "Establishes the firm's worldview and positioning",
        "explanatory": "Explains a concept or mechanism in depth",
        "technical": "Provides implementation-level technical guidance",
        "commercial": "Connects expertise to a commercial problem and pathway",
        "comparative": "Distinguishes between related concepts/services",
        "evidence_led": "Presents original research or data analysis",
        "application": "Shows how a concept applies in a specific vertical",
        "research": "Contributes new knowledge to the field",
        "opinion": "Offers a distinctive perspective or judgement",
        "navigational": "Helps users find the right service page"
    },
    applies_to_objectives=["*"],
    applies_to_page_types=[PageType.SERVICE, PageType.TECHNICAL, PageType.APPLICATION, PageType.WHITEPAPER, PageType.THOUGHT_LEADERSHIP, PageType.FOUNDATIONAL],
    variables=["page_id"]
))

# ============================================================
# EVIDENCE PRIMITIVES
# ============================================================

register_template(QuestionTemplate(
    template_id="EVIDENCE_CENTRAL_CLAIM",
    primitive=QuestionPrimitive.EVIDENCE,
    question_type=QuestionType.NOUL,
    instructions_template=(
        "Is the page's central claim supported by specific evidence (data, citations, case details, named sources)? "
        "Not generic references like 'studies show' or 'research indicates'."
    ),
    criteria_template={
        "true": "Central claim has specific, traceable evidence",
        "false": "Central claim relies on generic or absent evidence"
    },
    applies_to_objectives=["*"],
    applies_to_page_types=[PageType.SERVICE, PageType.TECHNICAL, PageType.APPLICATION, PageType.WHITEPAPER, PageType.THOUGHT_LEADERSHIP],
    variables=["page_id", "central_claim"]
))

register_template(QuestionTemplate(
    template_id="EVIDENCE_VENDOR_ATTRIBUTED",
    primitive=QuestionPrimitive.EVIDENCE,
    question_type=QuestionType.NOUL,
    instructions_template=(
        "Are vendor/platform claims (Google, Amazon, Meta, etc.) explicitly attributed to their source "
        "with dates and context, rather than presented as universal facts?"
    ),
    criteria_template={
        "true": "Vendor claims are attributed with source, date, context",
        "false": "Vendor claims presented as universal facts without attribution"
    },
    applies_to_objectives=["*"],
    applies_to_page_types=[PageType.TECHNICAL, PageType.APPLICATION, PageType.SERVICE],
    variables=["page_id"]
))

register_template(QuestionTemplate(
    template_id="EVIDENCE_FORECASTS_LABELLED",
    primitive=QuestionPrimitive.EVIDENCE,
    question_type=QuestionType.NOUL,
    instructions_template=(
        "Are forecasts, predictions, and forward-looking statements explicitly labelled as such "
        "with source, methodology, and time horizon?"
    ),
    criteria_template={
        "true": "Forecasts are clearly labelled with source/methodology/horizon",
        "false": "Forecasts presented as facts or without proper labelling"
    },
    applies_to_objectives=["*"],
    applies_to_page_types=[PageType.WHITEPAPER, PageType.THOUGHT_LEADERSHIP, PageType.APPLICATION],
    variables=["page_id"]
))

register_template(QuestionTemplate(
    template_id="EVIDENCE_CHARTS_REAL",
    primitive=QuestionPrimitive.EVIDENCE,
    question_type=QuestionType.NOUL,
    instructions_template=(
        "Are charts and visualisations based on real data with cited sources, "
        "or are they illustrative/conceptual diagrams?"
    ),
    criteria_template={
        "true": "Charts use real data with cited sources",
        "false": "Charts are illustrative without data attribution"
    },
    applies_to_objectives=["*"],
    applies_to_page_types=[PageType.WHITEPAPER, PageType.APPLICATION, PageType.THOUGHT_LEADERSHIP],
    variables=["page_id"]
))

# ============================================================
# SPECIFICITY PRIMITIVES
# ============================================================

register_template(QuestionTemplate(
    template_id="SPECIFICITY_DOMAIN_KNOWLEDGE",
    primitive=QuestionPrimitive.SPECIFICITY,
    question_type=QuestionType.NOUL,
    instructions_template=(
        "Does the page contain domain-specific information (specific platforms, technologies, "
        "mechanisms, parameters, thresholds) rather than generic industry language?"
    ),
    criteria_template={
        "true": "Page contains specific technical/platform/mechanism details",
        "false": "Page uses generic language applicable to any domain"
    },
    applies_to_objectives=["*"],
    applies_to_page_types=[PageType.TECHNICAL, PageType.APPLICATION, PageType.SERVICE],
    variables=["page_id", "domain"]
))

register_template(QuestionTemplate(
    template_id="SPECIFICITY_NAMED_ENTITIES",
    primitive=QuestionPrimitive.SPECIFICITY,
    question_type=QuestionType.SCORE,
    instructions_template=(
        "How many named, specific entities (platforms, technologies, companies, algorithms, "
        "regulations, people) does the page reference in a meaningful way?"
    ),
    criteria_template=[
        "0-2 named entities",
        "3-5 named entities",
        "6-10 named entities",
        "11-20 named entities",
        "20+ named entities"
    ],
    applies_to_objectives=["*"],
    applies_to_page_types=[PageType.TECHNICAL, PageType.APPLICATION, PageType.WHITEPAPER],
    variables=["page_id"]
))

# ============================================================
# DIFFERENTIATION PRIMITIVES
# ============================================================

register_template(QuestionTemplate(
    template_id="DIFF_SITE_OVERLAP",
    primitive=QuestionPrimitive.DIFFERENTIATION,
    question_type=QuestionType.SCORE,
    instructions_template=(
        "What percentage of this page's core arguments, claims, and evidence overlap "
        "with other Inflexion pages?"
    ),
    criteria_template=[
        "0-10% overlap (highly distinctive)",
        "11-25% overlap (moderately distinctive)",
        "26-40% overlap (some overlap)",
        "41-60% overlap (significant overlap)",
        "60%+ overlap (substantially duplicated)"
    ],
    applies_to_objectives=["*"],
    applies_to_page_types=[PageType.SERVICE, PageType.TECHNICAL, PageType.APPLICATION],
    variables=["page_id", "other_pages"]
))

register_template(QuestionTemplate(
    template_id="DIFF_CONCEPT_OWNERSHIP",
    primitive=QuestionPrimitive.DIFFERENTIATION,
    question_type=QuestionType.NOUL,
    instructions_template=(
        "Does this page clearly own its key concepts, or are they contested/unclear "
        "across the site? Can you identify which page owns each major concept?"
    ),
    criteria_template={
        "true": "Clear concept ownership — this page is the definitive source for its concepts",
        "false": "Concept ownership is contested, unclear, or shared without differentiation"
    },
    applies_to_objectives=["*"],
    applies_to_page_types=[PageType.SERVICE, PageType.TECHNICAL, PageType.APPLICATION],
    variables=["page_id", "key_concepts"]
))

# ============================================================
# TECHNICAL PRECISION PRIMITIVES
# ============================================================

register_template(QuestionTemplate(
    template_id="TECH_PRECISION_PLATFORM_CONFLATION",
    primitive=QuestionPrimitive.TECHNICAL_PRECISION,
    question_type=QuestionType.NOUL,
    instructions_template=(
        "Does the page conflate distinct platforms/systems (e.g., treating Google Search, "
        "Google AI Overviews, Gemini, ChatGPT, Perplexity, Claude, Amazon, Rufus as interchangeable)?"
    ),
    criteria_template={
        "true": "Distinct platforms/systems are correctly distinguished throughout",
        "false": "Platforms/systems are conflated or treated as interchangeable"
    },
    applies_to_objectives=["*"],
    applies_to_page_types=[PageType.TECHNICAL, PageType.APPLICATION, PageType.SERVICE],
    variables=["page_id"]
))

register_template(QuestionTemplate(
    template_id="TECH_PRECISION_CAUSAL_CLAIMS",
    primitive=QuestionPrimitive.TECHNICAL_PRECISION,
    question_type=QuestionType.NOUL,
    instructions_template=(
        "Does the page make unsupported causal claims (e.g., 'implementing X causes Y') "
        "without evidence or with correlation-only evidence?"
    ),
    criteria_template={
        "true": "Causal claims are supported by evidence or explicitly labelled as hypotheses",
        "false": "Unsupported causal claims presented as facts"
    },
    applies_to_objectives=["*"],
    applies_to_page_types=[PageType.TECHNICAL, PageType.APPLICATION, PageType.WHITEPAPER],
    variables=["page_id"]
))

register_template(QuestionTemplate(
    template_id="TECH_PRECISION_TEMPORAL_AMBIGUITY",
    primitive=QuestionPrimitive.TECHNICAL_PRECISION,
    question_type=QuestionType.NOUL,
    instructions_template=(
        "Are technical claims temporally scoped (e.g., 'as of 2024', 'in current version', "
        "'since the March 2024 update') rather than presented as timeless truths?"
    ),
    criteria_template={
        "true": "Technical claims have temporal scope",
        "false": "Technical claims presented as timeless without dates"
    },
    applies_to_objectives=["*"],
    applies_to_page_types=[PageType.TECHNICAL, PageType.APPLICATION, PageType.SERVICE],
    variables=["page_id"]
))

register_template(QuestionTemplate(
    template_id="TECH_PRECISION_OVERGENERALIZATION",
    primitive=QuestionPrimitive.TECHNICAL_PRECISION,
    question_type=QuestionType.NOUL,
    instructions_template=(
        "Does the page overgeneralise from specific cases to universal rules "
        "(e.g., 'all AI systems work this way', 'every retailer uses this algorithm')?"
    ),
    criteria_template={
        "true": "Claims are appropriately scoped to specific systems/contexts",
        "false": "Broad universal claims made from limited evidence"
    },
    applies_to_objectives=["*"],
    applies_to_page_types=[PageType.TECHNICAL, PageType.APPLICATION, PageType.SERVICE],
    variables=["page_id"]
))

# ============================================================
# COMMERCIAL RELEVANCE PRIMITIVES
# ============================================================

register_template(QuestionTemplate(
    template_id="COMMERCIAL_PROBLEM_CONNECTION",
    primitive=QuestionPrimitive.COMMERCIAL_RELEVANCE,
    question_type=QuestionType.NOUL,
    instructions_template=(
        "Does the page connect its expertise to a specific, credible commercial problem "
        "that a client would pay to solve?"
    ),
    criteria_template={
        "true": "Clear connection to a specific commercial problem",
        "false": "Expertise presented without commercial problem connection"
    },
    applies_to_objectives=["*"],
    applies_to_page_types=[PageType.SERVICE, PageType.APPLICATION, PageType.COMMERCIAL],
    variables=["page_id", "service_name"]
))

register_template(QuestionTemplate(
    template_id="COMMERCIAL_PATHWAY_CLEAR",
    primitive=QuestionPrimitive.COMMERCIAL_RELEVANCE,
    question_type=QuestionType.NOUL,
    instructions_template=(
        "Is there a credible, specific pathway from reading this page to commercial engagement "
        "(not a generic 'contact us')?"
    ),
    criteria_template={
        "true": "Specific, credible commercial pathway present",
        "false": "Generic or missing commercial pathway"
    },
    applies_to_objectives=["*"],
    applies_to_page_types=[PageType.SERVICE, PageType.APPLICATION, PageType.COMMERCIAL],
    variables=["page_id"]
))

# ============================================================
# HUMAN WRITING PRIMITIVES
# ============================================================

register_template(QuestionTemplate(
    template_id="WRITING_FORMULAIC_PATTERNS",
    primitive=QuestionPrimitive.HUMAN_WRITING,
    question_type=QuestionType.SCORE,
    instructions_template=(
        "To what extent does the page accumulate formulaic patterns: "
        "'not X but Y', 'X is no longer', 'this is why', 'this means', "
        "'the real question', 'the opportunity is', 'brands that win', "
        "'the shift', 'the new model', 'from X to Y', 'where X meets Y', "
        "numbered frameworks, three-part rhetorical structures, "
        "repeated paragraph structures, manufactured rhetorical questions?"
    ),
    criteria_template=[
        "No formulaic patterns detected",
        "1-2 minor instances",
        "3-5 instances across page",
        "6-10 instances, noticeable pattern",
        "10+ instances, dominant writing style"
    ],
    applies_to_objectives=["*"],
    applies_to_page_types=[PageType.SERVICE, PageType.TECHNICAL, PageType.APPLICATION, PageType.WHITEPAPER, PageType.THOUGHT_LEADERSHIP, PageType.EDITORIAL],
    variables=["page_id"]
))

register_template(QuestionTemplate(
    template_id="WRITING_CONCRETE_DETAIL",
    primitive=QuestionPrimitive.HUMAN_WRITING,
    question_type=QuestionType.NOUL,
    instructions_template=(
        "Does the writing contain concrete, specific observations that could only come from "
        "direct experience (named restaurants, specific parameters, observed behaviours, "
        "measured values) rather than abstract descriptions?"
    ),
    criteria_template={
        "true": "Multiple concrete, specific observations from direct experience",
        "false": "Abstract descriptions without concrete observational detail"
    },
    applies_to_objectives=["*"],
    applies_to_page_types=[PageType.APPLICATION, PageType.WHITEPAPER, PageType.THOUGHT_LEADERSHIP, PageType.EDITORIAL],
    variables=["page_id"]
))

register_template(QuestionTemplate(
    template_id="WRITING_OVEREXPLANATION",
    primitive=QuestionPrimitive.HUMAN_WRITING,
    question_type=QuestionType.NOUL,
    instructions_template=(
        "Does the page over-explain concepts that the target audience already understands, "
        "treating the reader as ignorant rather than expert?"
    ),
    criteria_template={
        "true": "Appropriate level of explanation for expert audience",
        "false": "Excessive explanation of known concepts"
    },
    applies_to_objectives=["*"],
    applies_to_page_types=[PageType.TECHNICAL, PageType.SERVICE, PageType.APPLICATION],
    variables=["page_id", "target_audience"]
))

register_template(QuestionTemplate(
    template_id="WRITING_CAUSAL_HUMILITY",
    primitive=QuestionPrimitive.HUMAN_WRITING,
    question_type=QuestionType.NOUL,
    instructions_template=(
        "Does the writing show causal humility — acknowledging uncertainty, "
        "multiple contributing factors, and limits of knowledge — "
        "rather than excessive certainty?"
    ),
    criteria_template={
        "true": "Appropriate uncertainty and causal humility present",
        "false": "Excessive certainty, single-cause explanations"
    },
    applies_to_objectives=["*"],
    applies_to_page_types=[PageType.TECHNICAL, PageType.WHITEPAPER, PageType.THOUGHT_LEADERSHIP],
    variables=["page_id"]
))

register_template(QuestionTemplate(
    template_id="WRITING_WRITER_NOTICED",
    primitive=QuestionPrimitive.HUMAN_WRITING,
    question_type=QuestionType.NOUL,
    instructions_template=(
        "Does the writing give the sense that a particular writer noticed something specific "
        "— selective attention, uneven emphasis, interpretive space — "
        "rather than comprehensive coverage?"
    ),
    criteria_template={
        "true": "Writer's selective attention and judgement visible",
        "false": "Comprehensive, even coverage without distinctive judgement"
    },
    applies_to_objectives=["*"],
    applies_to_page_types=[PageType.THOUGHT_LEADERSHIP, PageType.EDITORIAL, PageType.WHITEPAPER, PageType.APPLICATION],
    variables=["page_id"]
))

# ============================================================
# STRUCTURAL COHERENCE PRIMITIVES
# ============================================================

register_template(QuestionTemplate(
    template_id="STRUCTURE_TEMPLATE_REUSE",
    primitive=QuestionPrimitive.STRUCTURAL_COHERENCE,
    question_type=QuestionType.NOUL,
    instructions_template=(
        "Does the page follow a generic template structure (e.g., 'Framework Applied', "
        "'What We Won't Tell You', 'Concrete Deliverables' repeated across pages) "
        "rather than a structure that emerges from its specific argument?"
    ),
    criteria_template={
        "true": "Structure emerges from the page's specific argument",
        "false": "Generic template structure imposed on the page"
    },
    applies_to_objectives=["*"],
    applies_to_page_types=[PageType.SERVICE, PageType.APPLICATION],
    variables=["page_id"]
))

register_template(QuestionTemplate(
    template_id="STRUCTURE_FRAMEWORK_FORCING",
    primitive=QuestionPrimitive.STRUCTURAL_COHERENCE,
    question_type=QuestionType.NOUL,
    instructions_template=(
        "Does the page force its content into a numbered framework (e.g., 'Five dimensions. One system.', "
        "'Three pillars', 'Four phases') that doesn't naturally fit the material?"
    ),
    criteria_template={
        "true": "No forced framework; structure follows argument",
        "false": "Content forced into artificial numbered framework"
    },
    applies_to_objectives=["*"],
    applies_to_page_types=[PageType.SERVICE, PageType.APPLICATION, PageType.WHITEPAPER],
    variables=["page_id"]
))

# ============================================================
# ARGUMENT PRIMITIVES
# ============================================================

register_template(QuestionTemplate(
    template_id="ARGUMENT_COHERENT",
    primitive=QuestionPrimitive.ARGUMENT,
    question_type=QuestionType.NOUL,
    instructions_template=(
        "Does the page develop a coherent argument from premise through evidence to conclusion, "
        "or is it a collection of disconnected observations?"
    ),
    criteria_template={
        "true": "Coherent argument with logical progression",
        "false": "Disconnected observations without argument structure"
    },
    applies_to_objectives=["*"],
    applies_to_page_types=[PageType.SERVICE, PageType.TECHNICAL, PageType.APPLICATION, PageType.WHITEPAPER, PageType.THOUGHT_LEADERSHIP],
    variables=["page_id"]
))

register_template(QuestionTemplate(
    template_id="ARGUMENT_OWNERSHIP",
    primitive=QuestionPrimitive.ARGUMENT,
    question_type=QuestionType.NOUL,
    instructions_template=(
        "Does this page own its arguments, or does it inherit arguments from the whitepaper "
        "or other parent pages without adding distinctive specialisation?"
    ),
    criteria_template={
        "true": "Page owns and specialises its arguments",
        "false": "Arguments inherited without distinctive specialisation"
    },
    applies_to_objectives=["*"],
    applies_to_page_types=[PageType.SERVICE, PageType.APPLICATION],
    variables=["page_id", "parent_pages"]
))

# ============================================================
# CITATION PRIMITIVES
# ============================================================

register_template(QuestionTemplate(
    template_id="CITATION_IMPORTANT_CLAIMS",
    primitive=QuestionPrimitive.CITATION,
    question_type=QuestionType.NOUL,
    instructions_template=(
        "Are important claims (not all claims) appropriately supported with citations "
        "that a reader could verify?"
    ),
    criteria_template={
        "true": "Important claims have verifiable citations",
        "false": "Important claims lack verifiable citations"
    },
    applies_to_objectives=["*"],
    applies_to_page_types=[PageType.TECHNICAL, PageType.WHITEPAPER, PageType.APPLICATION, PageType.THOUGHT_LEADERSHIP],
    variables=["page_id"]
))

# ============================================================
# REPETITION PRIMITIVES
# ============================================================

register_template(QuestionTemplate(
    template_id="REPETITION_ARGUMENT",
    primitive=QuestionPrimitive.REPETITION,
    question_type=QuestionType.NOUL,
    instructions_template=(
        "Does this page repeat arguments already established on other Inflexion pages "
        "without adding new evidence, new angle, or new specialisation?"
    ),
    criteria_template={
        "true": "Arguments are distinctive or meaningfully specialised",
        "false": "Arguments repeated without new value"
    },
    applies_to_objectives=["*"],
    applies_to_page_types=[PageType.SERVICE, PageType.APPLICATION],
    variables=["page_id", "other_pages"]
))

register_template(QuestionTemplate(
    template_id="REPETITION_STATISTIC",
    primitive=QuestionPrimitive.REPETITION,
    question_type=QuestionType.NOUL,
    instructions_template=(
        "Does this page reuse statistics from other pages without new context "
        "or new interpretation?"
    ),
    criteria_template={
        "true": "Statistics are unique or recontextualised",
        "false": "Statistics reused without new context"
    },
    applies_to_objectives=["*"],
    applies_to_page_types=[PageType.SERVICE, PageType.APPLICATION, PageType.WHITEPAPER],
    variables=["page_id", "other_pages"]
))

register_template(QuestionTemplate(
    template_id="REPETITION_METAPHOR",
    primitive=QuestionPrimitive.REPETITION,
    question_type=QuestionType.NOUL,
    instructions_template=(
        "Does this page reuse metaphors, analogies, or framing devices from other pages "
        "without adaptation?"
    ),
    criteria_template={
        "true": "Metaphors/framing are unique or adapted",
        "false": "Metaphors/framing reused identically"
    },
    applies_to_objectives=["*"],
    applies_to_page_types=[PageType.SERVICE, PageType.APPLICATION, PageType.WHITEPAPER, PageType.THOUGHT_LEADERSHIP],
    variables=["page_id", "other_pages"]
))

# ============================================================
# KNOWLEDGE PRIMITIVES
# ============================================================

register_template(QuestionTemplate(
    template_id="KNOWLEDGE_CONTRIBUTION",
    primitive=QuestionPrimitive.KNOWLEDGE,
    question_type=QuestionType.SCORE,
    instructions_template=(
        "How much does this page contribute to the site's knowledge graph — "
        "new concepts, new evidence, new arguments, new connections?"
    ),
    criteria_template=[
        "No new knowledge contribution",
        "Minor addition to existing knowledge",
        "Moderate contribution (1-2 new concepts/evidence)",
        "Significant contribution (3-5 new concepts/evidence)",
        "Major contribution (5+ new concepts/evidence/connections)"
    ],
    applies_to_objectives=["*"],
    applies_to_page_types=[PageType.SERVICE, PageType.TECHNICAL, PageType.APPLICATION, PageType.WHITEPAPER, PageType.THOUGHT_LEADERSHIP],
    variables=["page_id"]
))

# ============================================================
# INTERNAL RELATIONSHIP PRIMITIVES
# ============================================================

register_template(QuestionTemplate(
    template_id="INTERNAL_LINKS_CORRECT",
    primitive=QuestionPrimitive.INTERNAL_RELATIONSHIP,
    question_type=QuestionType.NOUL,
    instructions_template=(
        "Does the page correctly link to related Inflexion pages — "
        "specialisations, generalisations, evidence sources, complementary perspectives?"
    ),
    criteria_template={
        "true": "Correct, meaningful internal links present",
        "false": "Missing, incorrect, or generic internal links"
    },
    applies_to_objectives=["*"],
    applies_to_page_types=[PageType.SERVICE, PageType.TECHNICAL, PageType.APPLICATION],
    variables=["page_id", "related_pages"]
))

# ============================================================
# TOPICAL AUTHORITY PRIMITIVES
# ============================================================

register_template(QuestionTemplate(
    template_id="AUTHORITY_DEPTH",
    primitive=QuestionPrimitive.TOPICAL_AUTHORITY,
    question_type=QuestionType.SCORE,
    instructions_template=(
        "How deeply does this page demonstrate topical authority — "
        "technical depth, proprietary insights, unique evidence, expert judgement?"
    ),
    criteria_template=[
        "Surface-level coverage only",
        "Some depth in places",
        "Consistent depth across key topics",
        "Deep expertise with proprietary insights",
        "Definitive authority in this topic"
    ],
    applies_to_objectives=["*"],
    applies_to_page_types=[PageType.TECHNICAL, PageType.APPLICATION, PageType.SERVICE, PageType.WHITEPAPER],
    variables=["page_id", "topic"]
))

# ============================================================
# AI DISCOVERY PRIMITIVES
# ============================================================

register_template(QuestionTemplate(
    template_id="AI_DISCOVERY_RETRIEVAL",
    primitive=QuestionPrimitive.AI_DISCOVERY,
    question_type=QuestionType.NOUL,
    instructions_template=(
        "Does the page contain information structured for AI retrieval — "
        "clear entity definitions, structured data, answerable questions, "
        "source-attributable claims?"
    ),
    criteria_template={
        "true": "Content structured for AI retrieval with clear entities/claims",
        "false": "Content not structured for AI retrieval"
    },
    applies_to_objectives=["*"],
    applies_to_page_types=[PageType.TECHNICAL, PageType.SERVICE, PageType.APPLICATION],
    variables=["page_id"]
))

# ============================================================
# TECHNICAL GEO PRIMITIVES
# ============================================================

register_template(QuestionTemplate(
    template_id="TECH_GEO_ACCESSIBLE",
    primitive=QuestionPrimitive.TECHNICAL_GEO,
    question_type=QuestionType.NOUL,
    instructions_template=(
        "Does the page expose its information in technically accessible, "
        "machine-readable form (structured data, semantic HTML, clean rendering)?"
    ),
    criteria_template={
        "true": "Page is technically accessible and machine-readable",
        "false": "Page has technical accessibility issues"
    },
    applies_to_objectives=["*"],
    applies_to_page_types=[PageType.TECHNICAL, PageType.SERVICE, PageType.APPLICATION],
    variables=["page_id"]
))

# ============================================================
# COMMERCIAL PRIMITIVES
# ============================================================

register_template(QuestionTemplate(
    template_id="COMMERCIAL_QUALIFICATION",
    primitive=QuestionPrimitive.COMMERCIAL,
    question_type=QuestionType.NOUL,
    instructions_template=(
        "Does the page qualify the reader — helping them self-assess whether "
        "they need this service — rather than just selling?"
    ),
    criteria_template={
        "true": "Page helps reader self-qualify with specific criteria",
        "false": "Page sells without qualification"
    },
    applies_to_objectives=["*"],
    applies_to_page_types=[PageType.SERVICE, PageType.APPLICATION, PageType.COMMERCIAL],
    variables=["page_id"]
))

# ============================================================
# OUTCOME PRIMITIVES
# ============================================================

register_template(QuestionTemplate(
    template_id="OUTCOME_QUALITY_TRAFFIC",
    primitive=QuestionPrimitive.OUTCOME,
    question_type=QuestionType.NOUL,
    instructions_template=(
        "Is the observed page quality consistent with observed traffic/performance? "
        "High quality + low traffic or low quality + high traffic are anomalies to investigate."
    ),
    criteria_template={
        "true": "Quality and performance are consistent",
        "false": "Quality/performance anomaly detected"
    },
    applies_to_objectives=["*"],
    applies_to_page_types=[PageType.SERVICE, PageType.APPLICATION, PageType.TECHNICAL],
    variables=["page_id", "quality_score", "traffic_data"]
))


def get_templates_for_objective(objective_id: str) -> list[QuestionTemplate]:
    return [t for t in QUESTION_TEMPLATES.values() if objective_id in t.applies_to_objectives or "*" in t.applies_to_objectives]


def get_templates_for_page_type(page_type: PageType) -> list[QuestionTemplate]:
    return [t for t in QUESTION_TEMPLATES.values() if page_type in t.applies_to_page_types]


def get_all_templates() -> list[QuestionTemplate]:
    return list(QUESTION_TEMPLATES.values())


def get_template(template_id: str) -> QuestionTemplate | None:
    return QUESTION_TEMPLATES.get(template_id)