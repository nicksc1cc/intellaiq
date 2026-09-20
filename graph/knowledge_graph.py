"""
Inflexion Intelligence Engine — Knowledge Graph
Phase 9: Knowledge Graph
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from collections import defaultdict
import itertools

try:
    from intelligence.core.models import (
        PageState, KnowledgeGraph, GraphNode, GraphEdge,
        NodeType, RelationshipType, Claim, Argument, Statistic
    )
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from intelligence.core.models import (
        PageState, KnowledgeGraph, GraphNode, GraphEdge,
        NodeType, RelationshipType, Claim, Argument, Statistic
    )


def build_knowledge_graph(
    pages: dict[str, PageState],
    jev_results: dict[str, list] | None = None
) -> KnowledgeGraph:
    nodes = []
    edges = []
    node_ids = set()
    edge_ids = set()

    # 1. Add PAGE nodes
    for page_id, page in pages.items():
        node_id = f"page:{page_id}"
        if node_id not in node_ids:
            nodes.append(GraphNode(
                node_id=node_id,
                node_type=NodeType.PAGE,
                label=page_id,
                properties={
                    "url": page.url,
                    "title": page.title,
                    "page_type": page.page_type.value,
                    "word_count": page.word_count
                }
            ))
            node_ids.add(node_id)

    # 2. Add ARGUMENT nodes and OWNS edges
    for page_id, page in pages.items():
        for arg in page.arguments:
            arg_node_id = f"argument:{arg.argument_id}"
            if arg_node_id not in node_ids:
                nodes.append(GraphNode(
                    node_id=arg_node_id,
                    node_type=NodeType.ARGUMENT,
                    label=arg.text[:80] + "..." if len(arg.text) > 80 else arg.text,
                    properties={
                        "page_id": page_id,
                        "full_text": arg.text,
                        "is_distinctive": arg.is_distinctive,
                        "overlap_pages": arg.overlap_pages
                    }
                ))
                node_ids.add(arg_node_id)

            # PAGE OWNS ARGUMENT
            edge_id = f"owns:{page_id}:{arg.argument_id}"
            if edge_id not in edge_ids:
                edges.append(GraphEdge(
                    edge_id=edge_id,
                    source=f"page:{page_id}",
                    target=arg_node_id,
                    relationship=RelationshipType.OWNS,
                    weight=1.0,
                    confidence=0.9
                ))
                edge_ids.add(edge_id)

    # 3. Add CLAIM nodes and SUPPORTED_BY edges
    for page_id, page in pages.items():
        for claim in page.claims:
            claim_node_id = f"claim:{claim.claim_id}"
            if claim_node_id not in node_ids:
                nodes.append(GraphNode(
                    node_id=claim_node_id,
                    node_type=NodeType.CLAIM,
                    label=claim.text[:80] + "..." if len(claim.text) > 80 else claim.text,
                    properties={
                        "page_id": page_id,
                        "claim_type": claim.claim_type,
                        "confidence": claim.confidence,
                        "is_central": claim.is_central
                    }
                ))
                node_ids.add(claim_node_id)

            # ARGUMENT/CONTAINS CLAIM (find parent argument)
            # For simplicity, link to page
            edge_id = f"contains:{page_id}:{claim.claim_id}"
            if edge_id not in edge_ids:
                edges.append(GraphEdge(
                    edge_id=edge_id,
                    source=f"page:{page_id}",
                    target=claim_node_id,
                    relationship=RelationshipType.CONTAINS,
                    weight=0.8,
                    confidence=claim.confidence
                ))
                edge_ids.add(edge_id)

            # CLAIM SUPPORTED_BY EVIDENCE (if evidence refs exist)
            for ev_ref in claim.evidence_refs:
                ev_node_id = f"evidence:{ev_ref}"
                if ev_node_id not in node_ids:
                    nodes.append(GraphNode(
                        node_id=ev_node_id,
                        node_type=NodeType.EVIDENCE,
                        label=ev_ref,
                        properties={"source": ev_ref}
                    ))
                    node_ids.add(ev_node_id)

                edge_id = f"supported_by:{claim.claim_id}:{ev_ref}"
                if edge_id not in edge_ids:
                    edges.append(GraphEdge(
                        edge_id=edge_id,
                        source=claim_node_id,
                        target=ev_node_id,
                        relationship=RelationshipType.SUPPORTED_BY,
                        weight=0.7,
                        confidence=0.6
                    ))
                    edge_ids.add(edge_id)

    # 4. Add STATISTIC nodes
    for page_id, page in pages.items():
        for stat in page.statistics:
            stat_node_id = f"statistic:{stat.statistic_id}"
            if stat_node_id not in node_ids:
                nodes.append(GraphNode(
                    node_id=stat_node_id,
                    node_type=NodeType.STATISTIC,
                    label=f"{stat.value}: {stat.context[:60]}",
                    properties={
                        "page_id": page_id,
                        "value": stat.value,
                        "context": stat.context,
                        "source": stat.source,
                        "date": stat.date,
                        "used_on_pages": stat.used_on_pages
                    }
                ))
                node_ids.add(stat_node_id)

            # PAGE USES STATISTIC
            edge_id = f"uses_stat:{page_id}:{stat.statistic_id}"
            if edge_id not in edge_ids:
                edges.append(GraphEdge(
                    edge_id=edge_id,
                    source=f"page:{page_id}",
                    target=stat_node_id,
                    relationship=RelationshipType.USES,
                    weight=0.6,
                    confidence=0.7
                ))
                edge_ids.add(edge_id)

    # 5. Add TOPIC/CONCEPT nodes and COVERS edges
    all_topics = set()
    all_concepts = set()
    for page in pages.values():
        all_topics.update(page.topics)
        # Extract key concepts from body text
        # Look for key AI/retail/media terms
        key_terms = {
            "ai", "aeo", "geo", "generative", "llm", "search", "citation", "entity",
            "retail", "amazon", "rufus", "a9", "media", "programmatic", "agentic",
            "technical", "rendering", "crawler", "schema", "structured", "visibility",
            "discovery", "measurement", "attribution", "consultancy", "strategy",
            "beauty", "ecommerce", "whitepaper", "digital pr", "earned media"
        }
        for term in key_terms:
            if term in page.body_text.lower():
                all_concepts.add(term)

    # Create TOPIC nodes
    for topic in all_topics:
        topic_node_id = f"topic:{topic}"
        if topic_node_id not in node_ids:
            nodes.append(GraphNode(
                node_id=topic_node_id,
                node_type=NodeType.TOPIC,
                label=topic,
                properties={"topic": topic}
            ))
            node_ids.add(topic_node_id)

    for page_id, page in pages.items():
        for topic in page.topics:
            edge_id = f"covers:{page_id}:{topic}"
            if edge_id not in edge_ids:
                edges.append(GraphEdge(
                    edge_id=edge_id,
                    source=f"page:{page_id}",
                    target=f"topic:{topic}",
                    relationship=RelationshipType.COVERS,
                    weight=0.5,
                    confidence=0.6
                ))
                edge_ids.add(edge_id)

    # Create CONCEPT nodes
    for concept in all_concepts:
        concept_node_id = f"concept:{concept}"
        if concept_node_id not in node_ids:
            nodes.append(GraphNode(
                node_id=concept_node_id,
                node_type=NodeType.CONCEPT,
                label=concept,
                properties={"concept": concept}
            ))
            node_ids.add(concept_node_id)

    for page_id, page in pages.items():
        for concept in all_concepts:
            if concept in page.body_text.lower():
                edge_id = f"uses_concept:{page_id}:{concept}"
                if edge_id not in edge_ids:
                    edges.append(GraphEdge(
                        edge_id=edge_id,
                        source=f"page:{page_id}",
                        target=f"concept:{concept}",
                        relationship=RelationshipType.USES,
                        weight=0.4,
                        confidence=0.5
                    ))
                    edge_ids.add(edge_id)
    _add_overlap_edges(pages, nodes, edges, node_ids, edge_ids)

    # 11. Detect DUPLICATES (shared statistics, identical claims)
    _add_duplicate_edges(pages, edges, edge_ids)

    # 12. Add INTERNAL LINKS relationships
    for page_id, page in pages.items():
        for link in page.internal_links:
            if link in pages:
                edge_id = f"links_to:{page_id}:{link}"
                if edge_id not in edge_ids:
                    edges.append(GraphEdge(
                        edge_id=edge_id,
                        source=f"page:{page_id}",
                        target=f"page:{link}",
                        relationship=RelationshipType.LINKS_TO,
                        weight=0.4,
                        confidence=0.8
                    ))
                    edge_ids.add(edge_id)

    # 13. Calculate centrality metrics
    _calculate_centrality(nodes, edges)

    return KnowledgeGraph(nodes=nodes, edges=edges)


def _add_overlap_edges(
    pages: dict[str, PageState],
    nodes: list[GraphNode],
    edges: list[GraphEdge],
    node_ids: set,
    edge_ids: set
) -> None:
    """Add OVERLAPS edges between pages with shared content."""
    page_ids = list(pages.keys())

    for page_a, page_b in itertools.combinations(page_ids, 2):
        overlap_score = _calculate_overlap(pages[page_a], pages[page_b])

        if overlap_score > 0.15:  # Threshold for meaningful overlap
            edge_id = f"overlaps:{page_a}:{page_b}"
            if edge_id not in edge_ids:
                edges.append(GraphEdge(
                    edge_id=edge_id,
                    source=f"page:{page_a}",
                    target=f"page:{page_b}",
                    relationship=RelationshipType.OVERLAPS,
                    weight=overlap_score,
                    confidence=0.7,
                    properties={"overlap_score": overlap_score}
                ))
                edge_ids.add(edge_id)


def _add_duplicate_edges(
    pages: dict[str, PageState],
    edges: list[GraphEdge],
    edge_ids: set
) -> None:
    """Add DUPLICATES edges for identical/near-identical statistics."""
    stat_to_pages = defaultdict(list)

    for page_id, page in pages.items():
        for stat in page.statistics:
            stat_to_pages[stat.value].append(page_id)

    # Filter out boilerplate/low-information statistics
    boilerplate_patterns = [
        r'^\d{4}$',           # bare years like 2026
        r'^\d{1,2}%?$',       # bare small numbers/percentages
        r'^\d+$',             # bare integers
        r'^\d+\.\d+$',        # bare decimals
    ]
    import re
    def is_boilerplate(val: str) -> bool:
        val = val.strip()
        if len(val) < 3:
            return True
        for pat in boilerplate_patterns:
            if re.match(pat, val):
                return True
        # Common filler values
        common = {'2026', '2025', '2024', '2023', '2022', '2021', '2020',
                  '92%', '100%', '50%', '25%', '75%', '80%', '90%',
                  '5%', '10%', '15%', '20%', '30%', '40%', '60%', '70%',
                  'yes', 'no', 'true', 'false'}
        if val.lower() in common:
            return True
        return False

    for stat_value, page_list in stat_to_pages.items():
        if is_boilerplate(stat_value):
            continue
        if len(page_list) > 1:
            for page_a, page_b in itertools.combinations(page_list, 2):
                edge_id = f"duplicates:{page_a}:{page_b}:{stat_value}"
                if edge_id not in edge_ids:
                    edges.append(GraphEdge(
                        edge_id=edge_id,
                        source=f"page:{page_a}",
                        target=f"page:{page_b}",
                        relationship=RelationshipType.DUPLICATES,
                        weight=0.8,
                        confidence=0.9,
                        properties={"statistic": stat_value}
                    ))
                    edge_ids.add(edge_id)


def _calculate_overlap(page_a: PageState, page_b: PageState) -> float:
    """Calculate lexical/content overlap between two pages."""
    # Simple Jaccard similarity on words
    words_a = set(page_a.body_text.lower().split())
    words_b = set(page_b.body_text.lower().split())

    if not words_a or not words_b:
        return 0.0

    intersection = len(words_a & words_b)
    union = len(words_a | words_b)

    jaccard = intersection / union if union > 0 else 0.0

    # Also check statistic overlap
    stats_a = {s.value for s in page_a.statistics}
    stats_b = {s.value for s in page_b.statistics}
    stat_overlap = len(stats_a & stats_b) / max(len(stats_a | stats_b), 1)

    # Also check argument overlap (simplified)
    args_a = {a.text[:100] for a in page_a.arguments}
    args_b = {a.text[:100] for a in page_b.arguments}
    arg_overlap = len(args_a & args_b) / max(len(args_a | args_b), 1)

    # Weighted combination
    return 0.5 * jaccard + 0.3 * stat_overlap + 0.2 * arg_overlap


def _calculate_centrality(nodes: list[GraphNode], edges: list[GraphEdge]) -> None:
    """Calculate basic centrality metrics for nodes."""
    # Build adjacency
    adjacency = defaultdict(list)
    for edge in edges:
        adjacency[edge.source].append(edge.target)
        adjacency[edge.target].append(edge.source)

    # Degree centrality
    for node in nodes:
        degree = len(adjacency.get(node.node_id, []))
        # Normalize by max possible
        max_degree = len(nodes) - 1
        node.centrality = degree / max_degree if max_degree > 0 else 0.0

    # Community detection (simple label propagation)
    _detect_communities(nodes, adjacency)


def _detect_communities(nodes: list[GraphNode], adjacency: dict) -> None:
    """Simple community detection via label propagation."""
    # Build node_id to node mapping
    node_map = {n.node_id: n for n in nodes}

    # Initialize each node with its own community
    for i, node in enumerate(nodes):
        node.community = i

    # Iterate
    for _ in range(5):
        for node in nodes:
            neighbor_communities = []
            for neighbor_id in adjacency.get(node.node_id, []):
                if neighbor_id in node_map:
                    neighbor_communities.append(node_map[neighbor_id].community)
            if neighbor_communities:
                # Take most common
                from collections import Counter
                node.community = Counter(neighbor_communities).most_common(1)[0][0]

    # Renumber communities to be contiguous
    community_map = {}
    for node in nodes:
        if node.community not in community_map:
            community_map[node.community] = len(community_map)
        node.community = community_map[node.community]


def get_page_subgraph(graph: KnowledgeGraph, page_id: str, depth: int = 2) -> KnowledgeGraph:
    """Extract a subgraph around a specific page."""
    from collections import deque

    start_node = f"page:{page_id}"
    visited = {start_node}
    queue = deque([(start_node, 0)])
    subgraph_nodes = {start_node}

    node_map = {n.node_id: n for n in graph.nodes}

    while queue:
        current, d = queue.popleft()
        if d >= depth:
            continue

        for edge in graph.edges:
            if edge.source == current and edge.target not in visited:
                visited.add(edge.target)
                subgraph_nodes.add(edge.target)
                queue.append((edge.target, d + 1))
            elif edge.target == current and edge.source not in visited:
                visited.add(edge.source)
                subgraph_nodes.add(edge.source)
                queue.append((edge.source, d + 1))

    subgraph_nodes_list = [node_map[nid] for nid in subgraph_nodes if nid in node_map]
    subgraph_edges = [e for e in graph.edges if e.source in subgraph_nodes and e.target in subgraph_nodes]

    return KnowledgeGraph(nodes=subgraph_nodes_list, edges=subgraph_edges)


def get_cluster_subgraph(graph: KnowledgeGraph, community_id: int) -> KnowledgeGraph:
    """Extract subgraph for a specific community."""
    cluster_nodes = [n for n in graph.nodes if n.community == community_id]
    cluster_node_ids = {n.node_id for n in cluster_nodes}
    cluster_edges = [e for e in graph.edges if e.source in cluster_node_ids and e.target in cluster_node_ids]
    return KnowledgeGraph(nodes=cluster_nodes, edges=cluster_edges)