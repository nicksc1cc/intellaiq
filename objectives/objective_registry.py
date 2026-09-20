"""
Inflexion Intelligence Engine — Objective Model
Phase 5: Objective Model
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

try:
    from intelligence.core.models import Objective, PageType
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from intelligence.core.models import Objective, PageType


OBJECTIVE_REGISTRY: dict[str, Objective] = {}


def register_objective(obj: Objective) -> None:
    OBJECTIVE_REGISTRY[obj.objective_id] = obj


# TECHNICAL GEO OBJECTIVES
register_objective(Objective(
    objective_id="O_TGEO_01",
    code="O01",
    title="Establish Technical GEO as a Distinct Discipline",
    description="The page must clearly establish Technical GEO as a separate discipline from traditional SEO and AEO, with its own technical foundations.",
    page_type=PageType.TECHNICAL,
    applies_to=["technical-geo"],
    weight=1.5,
    question_templates=["TGEO_DISTINCT_DISCIPLINE", "TGEO_VS_AEO", "TGEO_VS_SEO"]
))

register_objective(Objective(
    objective_id="O_TGEO_02",
    code="O02",
    title="Explain AI Crawler Accessibility",
    description="The page must explain how AI crawlers differ from traditional search crawlers and what technical requirements they impose.",
    page_type=PageType.TECHNICAL,
    applies_to=["technical-geo"],
    weight=1.3,
    question_templates=["CRAWLER_ACCESSIBILITY", "AI_CRAWLER_REQUIREMENTS", "RENDERING_BUDGET"]
))

register_objective(Objective(
    objective_id="O_TGEO_03",
    code="O03",
    title="Explain Rendering and Machine-Readable Infrastructure",
    description="The page must cover JavaScript rendering challenges, structured data, and machine-readable content for AI systems.",
    page_type=PageType.TECHNICAL,
    applies_to=["technical-geo"],
    weight=1.4,
    question_templates=["JS_RENDERING", "STRUCTURED_DATA", "MACHINE_READABLE"]
))

register_objective(Objective(
    objective_id="O_TGEO_04",
    code="O04",
    title="Demonstrate Technical Expertise",
    description="The page must demonstrate genuine technical expertise through specific implementation details, not generic advice.",
    page_type=PageType.TECHNICAL,
    applies_to=["technical-geo"],
    weight=1.2,
    question_templates=["TECHNICAL_DEPTH", "IMPLEMENTATION_SPECIFICS", "CODE_EXAMPLES"]
))

register_objective(Objective(
    objective_id="O_TGEO_05",
    code="O05",
    title="Differentiate Technical GEO from AEO",
    description="The page must clearly articulate the conceptual and practical differences between Technical GEO and Answer Engine Optimisation.",
    page_type=PageType.TECHNICAL,
    applies_to=["technical-geo", "aeo"],
    weight=1.5,
    question_templates=["TGEO_VS_AEO_DISTINCTION", "OVERLAP_BOUNDARIES", "COMPLEMENTARY_ROLES"]
))

register_objective(Objective(
    objective_id="O_TGEO_06",
    code="O06",
    title="Connect Technical Implementation to AI Visibility",
    description="The page must connect specific technical implementations to measurable AI visibility outcomes.",
    page_type=PageType.TECHNICAL,
    applies_to=["technical-geo", "ai-visibility-analytics"],
    weight=1.3,
    question_templates=["TECH_TO_VISIBILITY", "MEASURABLE_OUTCOMES", "CAUSAL_LINKS"]
))

register_objective(Objective(
    objective_id="O_TGEO_07",
    code="O07",
    title="Provide Actionable Technical Diagnosis",
    description="The page must enable a reader to diagnose their own technical AI readiness.",
    page_type=PageType.TECHNICAL,
    applies_to=["technical-geo"],
    weight=1.2,
    question_templates=["ACTIONABLE_DIAGNOSIS", "CHECKLIST_COMPLETENESS", "PRIORITISATION"]
))

register_objective(Objective(
    objective_id="O_TGEO_08",
    code="O08",
    title="Establish Inflexion Technical Authority",
    description="The page must establish Inflexion as a technical authority in this domain.",
    page_type=PageType.TECHNICAL,
    applies_to=["technical-geo"],
    weight=1.0,
    question_templates=["AUTHORITY_SIGNALS", "UNIQUE_INSIGHTS", "CREDIBLE_EVIDENCE"]
))

register_objective(Objective(
    objective_id="O_TGEO_09",
    code="O09",
    title="Connect Technical GEO to Wider AI Discovery Proposition",
    description="The page must position Technical GEO within Inflexion's broader AI Discovery service.",
    page_type=PageType.TECHNICAL,
    applies_to=["technical-geo", "ai-discovery"],
    weight=1.1,
    question_templates=["SERVICE_INTEGRATION", "CROSS_REFERENCE", "UPSELL_PATHWAY"]
))

register_objective(Objective(
    objective_id="O_TGEO_10",
    code="O10",
    title="Generate Qualified Commercial Interest",
    description="The page must create a credible pathway to commercial engagement for technical GEO services.",
    page_type=PageType.TECHNICAL,
    applies_to=["technical-geo"],
    weight=1.0,
    question_templates=["COMMERCIAL_PATHWAY", "QUALIFICATION_SIGNALS", "CTA_RELEVANCE"]
))

# AEO OBJECTIVES
register_objective(Objective(
    objective_id="O_AEO_01",
    code="O01",
    title="Establish AEO as Citation Mechanics",
    description="The page must establish AEO as fundamentally about citation mechanics — how AI systems extract, attribute, and cite sources.",
    page_type=PageType.SERVICE,
    applies_to=["aeo"],
    weight=1.5,
    question_templates=["AEO_CITATION_MECHANICS", "EXTRACTION_PROCESS", "ATTRIBUTION_MODELS"]
))

register_objective(Objective(
    objective_id="O_AEO_02",
    code="O02",
    title="Explain Entity Structure and Schema",
    description="The page must explain how entity understanding and schema markup influence AI citation.",
    page_type=PageType.SERVICE,
    applies_to=["aeo"],
    weight=1.3,
    question_templates=["ENTITY_STRUCTURE", "SCHEMA_ROLE", "KNOWLEDGE_GRAPH_INTEGRATION"]
))

register_objective(Objective(
    objective_id="O_AEO_03",
    code="O03",
    title="Differentiate AEO from Technical GEO and AI Discovery",
    description="The page must clearly distinguish AEO's focus (citation/extraction) from Technical GEO (infrastructure) and AI Discovery (interpretation).",
    page_type=PageType.SERVICE,
    applies_to=["aeo", "technical-geo", "ai-discovery"],
    weight=1.4,
    question_templates=["AEO_VS_TGEO", "AEO_VS_AI_DISCOVERY", "THREE_PILLARS"]
))

register_objective(Objective(
    objective_id="O_AEO_04",
    code="O04",
    title="Demonstrate Citation Pattern Expertise",
    description="The page must show deep understanding of how different AI systems cite sources differently.",
    page_type=PageType.SERVICE,
    applies_to=["aeo"],
    weight=1.2,
    question_templates=["CITATION_PATTERNS", "PLATFORM_DIFFERENCES", "SOURCE_SELECTION"]
))

register_objective(Objective(
    objective_id="O_AEO_05",
    code="O05",
    title="Provide Citation Optimisation Framework",
    description="The page must give actionable guidance on optimising for AI citation.",
    page_type=PageType.SERVICE,
    applies_to=["aeo"],
    weight=1.1,
    question_templates=["OPTIMISATION_FRAMEWORK", "ACTIONABLE_STEPS", "MEASUREMENT"]
))

register_objective(Objective(
    objective_id="O_AEO_06",
    code="O06",
    title="Connect AEO to Commercial Outcomes",
    description="The page must explain how citation visibility translates to business outcomes.",
    page_type=PageType.SERVICE,
    applies_to=["aeo"],
    weight=1.0,
    question_templates=["CITATION_TO_COMMERCIAL", "ATTRIBUTION", "ROI_ESTIMATION"]
))

# AI DISCOVERY OBJECTIVES
register_objective(Objective(
    objective_id="O_AIDISC_01",
    code="O01",
    title="Establish AI Discovery as Interpretation Layer",
    description="The page must establish AI Discovery as the interpretation/recognition layer — how AI systems understand and select sources.",
    page_type=PageType.SERVICE,
    applies_to=["ai-discovery"],
    weight=1.5,
    question_templates=["AI_DISCOVERY_INTERPRETATION", "SOURCE_SELECTION", "RECOGNITION_MECHANICS"]
))

register_objective(Objective(
    objective_id="O_AIDISC_02",
    code="O02",
    title="Explain Prompt Construction and Cross-Model Testing",
    description="The page must cover how prompts are constructed for testing and how behaviour varies across models.",
    page_type=PageType.SERVICE,
    applies_to=["ai-discovery"],
    weight=1.3,
    question_templates=["PROMPT_CONSTRUCTION", "CROSS_MODEL_TESTING", "VARIANCE_ANALYSIS"]
))

register_objective(Objective(
    objective_id="O_AIDISC_03",
    code="O03",
    title="Cover Source Tracing and Attribution",
    description="The page must explain how to trace where AI systems get their information.",
    page_type=PageType.SERVICE,
    applies_to=["ai-discovery"],
    weight=1.2,
    question_templates=["SOURCE_TRACING", "ATTRIBUTION_CHAINS", "PROVENANCE"]
))

register_objective(Objective(
    objective_id="O_AIDISC_04",
    code="O04",
    title="Differentiate from AEO and Technical GEO",
    description="The page must clearly distinguish AI Discovery (interpretation) from AEO (citation) and Technical GEO (infrastructure).",
    page_type=PageType.SERVICE,
    applies_to=["ai-discovery", "aeo", "technical-geo"],
    weight=1.4,
    question_templates=["THREE_PILLARS_DISTINCTION", "AI_DISCOVERY_UNIQUE", "BOUNDARY_CLARITY"]
))

register_objective(Objective(
    objective_id="O_AIDISC_05",
    code="O05",
    title="Forensic Diagnostic Capability",
    description="The page must demonstrate forensic diagnostic capability — finding what others miss.",
    page_type=PageType.SERVICE,
    applies_to=["ai-discovery"],
    weight=1.3,
    question_templates=["FORENSIC_DEPTH", "HIDDEN_SIGNALS", "DIAGNOSTIC_RIGOUR"]
))

# AI VISIBILITY ANALYTICS OBJECTIVES
register_objective(Objective(
    objective_id="O_AIVIS_01",
    code="O01",
    title="Establish Share-of-Answer Tracking",
    description="The page must explain how to measure share-of-answer across AI systems.",
    page_type=PageType.SERVICE,
    applies_to=["ai-visibility-analytics"],
    weight=1.5,
    question_templates=["SHARE_OF_ANSWER", "TRACKING_METHODOLOGY", "COMPETITIVE_BASELINE"]
))

register_objective(Objective(
    objective_id="O_AIVIS_02",
    code="O02",
    title="Cover Competitive Intelligence",
    description="The page must cover how to track competitor visibility in AI answers.",
    page_type=PageType.SERVICE,
    applies_to=["ai-visibility-analytics"],
    weight=1.3,
    question_templates=["COMPETITIVE_INTEL", "COMPETITOR_TRACKING", "MARKET_POSITION"]
))

register_objective(Objective(
    objective_id="O_AIVIS_03",
    code="O03",
    title="Explain Product Limitations Honestly",
    description="The page must honestly address current limitations of AI visibility measurement tools.",
    page_type=PageType.SERVICE,
    applies_to=["ai-visibility-analytics"],
    weight=1.2,
    question_templates=["LIMITATIONS_HONESTY", "TOOL_CONSTRAINTS", "DATA_GAPS"]
))

register_objective(Objective(
    objective_id="O_AIVIS_04",
    code="O04",
    title="Differentiate from Measurement Methodology",
    description="The page must distinguish AI visibility analytics (what to measure) from measurement methodology (how to measure).",
    page_type=PageType.SERVICE,
    applies_to=["ai-visibility-analytics", "measurement"],
    weight=1.3,
    question_templates=["AIVIS_VS_MEASUREMENT", "METHODOLOGY_VS_ANALYTICS", "SCOPE_BOUNDARIES"]
))

# DIGITAL PR OBJECTIVES
register_objective(Objective(
    objective_id="O_DPR_01",
    code="O01",
    title="Establish Earned Media as Source Authority",
    description="The page must establish that earned media creates the source environment AI systems draw from.",
    page_type=PageType.SERVICE,
    applies_to=["digital-pr"],
    weight=1.5,
    question_templates=["EARNED_MEDIA_AUTHORITY", "SOURCE_ENVIRONMENT", "AI_TRAINING_DATA"]
))

register_objective(Objective(
    objective_id="O_DPR_02",
    code="O02",
    title="Explain Source Diversity and Credibility",
    description="The page must explain how source diversity and credibility affect AI citation.",
    page_type=PageType.SERVICE,
    applies_to=["digital-pr"],
    weight=1.3,
    question_templates=["SOURCE_DIVERSITY", "CREDIBILITY_SIGNALS", "DOMAIN_AUTHORITY"]
))

register_objective(Objective(
    objective_id="O_DPR_03",
    code="O03",
    title="Differentiate from Technical GEO and AEO",
    description="The page must distinguish Digital PR (external authority) from Technical GEO (infrastructure) and AEO (citation mechanics).",
    page_type=PageType.SERVICE,
    applies_to=["digital-pr", "technical-geo", "aeo"],
    weight=1.3,
    question_templates=["DPR_VS_TGEO", "DPR_VS_AEO", "EXTERNAL_VS_INTERNAL"]
))

# RETAIL MEDIA OBJECTIVES
register_objective(Objective(
    objective_id="O_RETAIL_01",
    code="O01",
    title="Establish Retailer Algorithm Expertise",
    description="The page must demonstrate expertise in retailer-specific algorithms (not just Amazon).",
    page_type=PageType.APPLICATION,
    applies_to=["retail-media"],
    weight=1.4,
    question_templates=["RETAILER_ALGORITHMS", "MULTI_RETAILER", "PLATFORM_SPECIFICS"]
))

register_objective(Objective(
    objective_id="O_RETAIL_02",
    code="O02",
    title="Separate Paid and Organic Retail Signals",
    description="The page must clearly separate paid retail media from organic retailer signals.",
    page_type=PageType.APPLICATION,
    applies_to=["retail-media"],
    weight=1.3,
    question_templates=["PAID_VS_ORGANIC_RETAIL", "SIGNAL_SEPARATION", "ATTRIBUTION"]
))

register_objective(Objective(
    objective_id="O_RETAIL_03",
    code="O03",
    title="Differentiate from Amazon-Specific Page",
    description="The page must distinguish multi-retailer strategy from Amazon-specific execution.",
    page_type=PageType.APPLICATION,
    applies_to=["retail-media", "amazon"],
    weight=1.2,
    question_templates=["RETAIL_VS_AMAZON", "MULTI_RETAILER_STRATEGY", "SCOPE_BOUNDARIES"]
))

# AMAZON OBJECTIVES
register_objective(Objective(
    objective_id="O_AMZN_01",
    code="O01",
    title="Establish A9/Rufus Algorithm Expertise",
    description="The page must demonstrate deep expertise in Amazon's A9 algorithm and Rufus.",
    page_type=PageType.APPLICATION,
    applies_to=["amazon"],
    weight=1.5,
    question_templates=["A9_ALGORITHM", "RUFUS_PROMPTS", "AMAZON_SEARCH"]
))

register_objective(Objective(
    objective_id="O_AMZN_02",
    code="O02",
    title="Cover Four Amazon Ad Products",
    description="The page must cover all four Amazon ad products with technical specificity.",
    page_type=PageType.APPLICATION,
    applies_to=["amazon"],
    weight=1.3,
    question_templates=["AMAZON_AD_PRODUCTS", "SPONSORED_PRODUCTS", "DSP_DETAIL"]
))

register_objective(Objective(
    objective_id="O_AMZN_03",
    code="O03",
    title="Cover FBA and Operational Mechanics",
    description="The page must cover FBA, inventory, and operational mechanics that affect visibility.",
    page_type=PageType.APPLICATION,
    applies_to=["amazon"],
    weight=1.2,
    question_templates=["FBA_MECHANICS", "INVENTORY_VISIBILITY", "OPERATIONAL_FACTORS"]
))

# AI MEDIA OBJECTIVES
register_objective(Objective(
    objective_id="O_AIMEDIA_01",
    code="O01",
    title="Establish Agentic Buying as Distinct from Programmatic",
    description="The page must establish agentic/autonomous media buying as fundamentally different from programmatic.",
    page_type=PageType.SERVICE,
    applies_to=["ai-media"],
    weight=1.5,
    question_templates=["AGENTIC_VS_PROGRAMMATIC", "AUTONOMOUS_DECISIONS", "GOVERNANCE"]
))

register_objective(Objective(
    objective_id="O_AIMEDIA_02",
    code="O02",
    title="Cover Supply Path and Clean Rooms",
    description="The page must cover supply path optimisation and clean room technology.",
    page_type=PageType.SERVICE,
    applies_to=["ai-media"],
    weight=1.3,
    question_templates=["SUPPLY_PATH", "CLEAN_ROOMS", "DATA_COLLABORATION"]
))

register_objective(Objective(
    objective_id="O_AIMEDIA_03",
    code="O03",
    title="Cover CTV and Audio in Agentic Context",
    description="The page must address how agentic buying extends to CTV and audio.",
    page_type=PageType.SERVICE,
    applies_to=["ai-media"],
    weight=1.2,
    question_templates=["CTV_AGENTIC", "AUDIO_AGENTIC", "OMNICHANNEL"]
))

# MEDIA OBJECTIVES
register_objective(Objective(
    objective_id="O_MEDIA_01",
    code="O01",
    title="Establish Cross-Channel Integration",
    description="The page must demonstrate how Inflexion integrates across paid, earned, and owned media.",
    page_type=PageType.SERVICE,
    applies_to=["media"],
    weight=1.4,
    question_templates=["CROSS_CHANNEL", "INTEGRATION_MODEL", "UNIFIED_MEASUREMENT"]
))

register_objective(Objective(
    objective_id="O_MEDIA_02",
    code="O02",
    title="Differentiate from AI Media",
    description="The page must distinguish traditional media integration from agentic/algorithmic media buying.",
    page_type=PageType.SERVICE,
    applies_to=["media", "ai-media"],
    weight=1.3,
    question_templates=["MEDIA_VS_AI_MEDIA", "HUMAN_VS_AGENTIC", "EVOLUTION_PATH"]
))

# CONSULTANCY OBJECTIVES
register_objective(Objective(
    objective_id="O_CONSULT_01",
    code="O01",
    title="Establish Operating Model Transformation",
    description="The page must establish consultancy as operating model transformation, not just advisory.",
    page_type=PageType.SERVICE,
    applies_to=["consultancy"],
    weight=1.5,
    question_templates=["OPERATING_MODEL", "TRANSFORMATION_VS_ADVISORY", "IMPLEMENTATION"]
))

register_objective(Objective(
    objective_id="O_CONSULT_02",
    code="O02",
    title="Cover Organisational Change",
    description="The page must cover organisational structure, skills, and process change.",
    page_type=PageType.SERVICE,
    applies_to=["consultancy"],
    weight=1.3,
    question_templates=["ORG_CHANGE", "SKILLS_GAP", "PROCESS_REDESIGN"]
))

# MEASUREMENT OBJECTIVES
register_objective(Objective(
    objective_id="O_MEAS_01",
    code="O01",
    title="Establish Measurement Methodology",
    description="The page must establish Inflexion's measurement methodology: fixed prompts, 4 signals, attribution limitations.",
    page_type=PageType.SERVICE,
    applies_to=["measurement"],
    weight=1.5,
    question_templates=["METHODOLOGY_FIXED_PROMPTS", "FOUR_SIGNALS", "ATTRIBUTION_LIMITATIONS"]
))

register_objective(Objective(
    objective_id="O_MEAS_02",
    code="O02",
    title="Differentiate from AI Visibility Analytics",
    description="The page must distinguish measurement methodology (how) from AI visibility analytics (what).",
    page_type=PageType.SERVICE,
    applies_to=["measurement", "ai-visibility-analytics"],
    weight=1.3,
    question_templates=["MEAS_VS_AIVIS", "METHODOLOGY_VS_ANALYTICS", "TOOL_VS_FRAMEWORK"]
))

# WHITEPAPER OBJECTIVES
register_objective(Objective(
    objective_id="O_WP_01",
    code="O01",
    title="Provide System-Level Explanation",
    description="The whitepaper must provide a broad system-level explanation of AI-mediated commerce.",
    page_type=PageType.WHITEPAPER,
    applies_to=["ecommerce-whitepaper"],
    weight=1.5,
    question_templates=["SYSTEM_LEVEL", "HOLISTIC_VIEW", "INTERCONNECTIONS"]
))

register_objective(Objective(
    objective_id="O_WP_02",
    code="O02",
    title="Establish Parent Concepts for Service Pages",
    description="The whitepaper must establish parent concepts that service pages specialise, not duplicate.",
    page_type=PageType.WHITEPAPER,
    applies_to=["ecommerce-whitepaper"],
    weight=1.4,
    question_templates=["PARENT_CONCEPTS", "SPECIALISATION_NOT_DUPLICATION", "CONCEPT_HIERARCHY"]
))

# HOMEPAGE OBJECTIVES
register_objective(Objective(
    objective_id="O_HOME_01",
    code="O01",
    title="Establish Inflexion Worldview",
    description="The homepage must establish Inflexion's overall worldview and positioning.",
    page_type=PageType.FOUNDATIONAL,
    applies_to=["index"],
    weight=1.5,
    question_templates=["WORLDVIEW", "POSITIONING", "DIFFERENTIATION"]
))

register_objective(Objective(
    objective_id="O_HOME_02",
    code="O02",
    title="Navigate to Service Pages",
    description="The homepage must effectively navigate users to the right service page.",
    page_type=PageType.FOUNDATIONAL,
    applies_to=["index"],
    weight=1.2,
    question_templates=["NAVIGATION_CLARITY", "SERVICE_DISCOVERY", "USER_JOURNEY"]
))


def get_objectives_for_page(page_id: str, page_type: PageType) -> list[Objective]:
    objectives = []
    for obj in OBJECTIVE_REGISTRY.values():
        if page_id in obj.applies_to or (obj.page_type == page_type and not obj.applies_to):
            objectives.append(obj)
    return objectives


def get_all_objectives() -> list[Objective]:
    return list(OBJECTIVE_REGISTRY.values())


def get_objective_by_id(objective_id: str) -> Objective | None:
    return OBJECTIVE_REGISTRY.get(objective_id)