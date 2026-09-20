"""
Quick statistical analysis on JSON run data
"""

import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

# Load latest run
run_files = sorted(Path('/Users/nicholaschristensen/Projects/04-inflexion/08-Website/intelligence/data/runs').glob('run_run_*.json'))
run_path = run_files[-1]
with open(run_path) as f:
    run = json.load(f)

pages = run['pages_analyzed']
qv = run['quality_vectors']
jev = run['jev_results']
issues = run['issues']
kg_nodes = run['knowledge_graph']['nodes']
kg_edges = run['knowledge_graph']['edges']
page_states = run['page_states']

print("=" * 60)
print("INFLEXION INTELLIGENCE — STATISTICAL ANALYSIS")
print(f"Run: {run['run_id']}")
print("=" * 60)

# ===== QUALITY VECTOR SUMMARY =====
print("\n=== QUALITY VECTORS ===")
for page_id in pages:
    q = qv[page_id]
    overall = q.get('overall', 0)
    dims = {k: v.get('score', 0) for k, v in q.items() if isinstance(v, dict) and 'score' in v}
    ps = page_states.get(page_id, {})
    ptype = ps.get('page_type', 'unknown')
    print(f"{page_id:30s} [{ptype:15s}] overall={overall:.2f}  distinct={dims.get('intellectual_distinctiveness',0):.2f}  evidence={dims.get('evidence_quality',0):.2f}  diff={dims.get('site_differentiation',0):.2f}  tech={dims.get('technical_accuracy',0):.2f}  writing={dims.get('human_writing',0):.2f}")

# ===== ISSUE SUMMARY =====
print("\n=== ISSUES ===")
print(f"Total: {len(issues)}")
cat_counts = Counter(i['category'] for i in issues)
for cat, count in cat_counts.most_common():
    print(f"  {cat}: {count}")

page_issues = Counter()
for i in issues:
    for p in i.get('affected_pages', []):
        page_issues[p] += 1
print("\nIssues by page:")
for p, count in page_issues.most_common(10):
    print(f"  {p}: {count}")

# ===== CLUSTER ANALYSIS =====
print("\n=== CLUSTER ANALYSIS ===")
clusters = {
    'AI_DISCOVERY': ['aeo', 'ai-discovery', 'ai-visibility-analytics', 'technical-geo', 'digital-pr'],
    'RETAIL_MEDIA': ['retail-media', 'amazon', 'beauty-media-strategy', 'ai-in-retail-media', 'amazon-ai-creative-studio', 'amazon-rufus-sponsored-prompts'],
    'MEDIA': ['ai-media', 'media', 'agentic-media-buying', 'shoppable-ai-search'],
    'STRATEGY': ['consultancy', 'measurement'],
    'RESEARCH': ['ecommerce-whitepaper'],
    'CORE': ['index', 'contact'],
    'ARTICLES': ['aeo-rankings-to-citations', 'blog']
}

for cluster_name, page_ids in clusters.items():
    valid = [p for p in page_ids if p in pages]
    if not valid:
        continue
    qualities = [qv.get(p, {}).get('overall', 0) for p in valid]
    avg_q = statistics.mean(qualities) if qualities else 0
    std_q = statistics.stdev(qualities) if len(qualities) > 1 else 0
    types = Counter(page_states.get(p, {}).get('page_type', 'unknown') for p in valid)
    
    # Internal overlap
    internal = []
    for p in valid:
        for edge in kg_edges:
            if edge.get('relationship') == 'OVERLAPS':
                src = edge.get('source', '').replace('page:', '')
                tgt = edge.get('target', '').replace('page:', '')
                if src == p and tgt in valid:
                    internal.append(edge.get('weight', 0))
                elif tgt == p and src in valid:
                    internal.append(edge.get('weight', 0))
    avg_int = statistics.mean(internal) if internal else 0
    
    # Shared concepts
    concept_pages = defaultdict(list)
    for node in kg_nodes:
        if node.get('node_type') == 'concept':
            for edge in kg_edges:
                if edge.get('target') == node.get('node_id') and edge.get('relationship') == 'uses':
                    src = edge.get('source', '').replace('page:', '')
                    if src in valid:
                        concept_pages[node.get('label')].append(src)
    shared = {c: ps for c, ps in concept_pages.items() if len(ps) > 1}
    
    print(f"\n{cluster_name}: {len(valid)} pages, avg_quality={avg_q:.2f}, std={std_q:.2f}")
    print(f"  Types: {dict(types)}")
    print(f"  Internal overlap: {avg_int:.2f}")
    print(f"  Shared concepts ({len(shared)}): {list(shared.keys())[:5]}")
    
    # Quality leaders/laggards
    sorted_pages = sorted(valid, key=lambda p: qv.get(p, {}).get('overall', 0), reverse=True)
    print(f"  Leaders: {sorted_pages[:2]}, Laggards: {sorted_pages[-2:]}")

# Check USES edges targets
edges = run['knowledge_graph']['edges']
uses = [e for e in edges if e.get('relationship') == 'uses']
targets = set(e.get('target', '') for e in uses)
print('USES target types:', list(targets)[:20])

# Find what nodes have those target IDs
kg_nodes = run['knowledge_graph']['nodes']
for t in list(targets)[:5]:
    node = next((n for n in kg_nodes if n.get('node_id') == t), None)
    if node:
        print(f'  Target {t}: type={node.get("node_type")}, label={node.get("label")}')

# ===== CONCEPT CENTRALITY =====
print("\n=== CONCEPT CENTRALITY (Top 15) ===")
concept_centrality = []
for node in kg_nodes:
    if node.get('node_type') != 'concept':
        continue
    label = node.get('label', '')
    owning_pages = []
    for edge in kg_edges:
        if edge.get('target') == node.get('node_id') and edge.get('relationship') == 'uses':
            src = edge.get('source', '').replace('page:', '')
            if src in pages:
                owning_pages.append(src)
    if not owning_pages:
        continue
    degree = len(owning_pages)
    qualities = [qv.get(p, {}).get('overall', 0) for p in owning_pages]
    avg_quality = statistics.mean(qualities) if qualities else 0
    
    # Bridge check
    cluster_pages = {
        'AI_DISCOVERY': {'aeo', 'ai-discovery', 'ai-visibility-analytics', 'technical-geo', 'digital-pr'},
        'RETAIL_MEDIA': {'retail-media', 'amazon', 'beauty-media-strategy', 'ai-in-retail-media'},
        'MEDIA': {'ai-media', 'media', 'agentic-media-buying', 'shoppable-ai-search'},
        'STRATEGY': {'consultancy', 'measurement'},
        'RESEARCH': {'ecommerce-whitepaper'}
    }
    clusters_covered = sum(1 for cluster, pgs in cluster_pages.items() if set(owning_pages) & pgs)
    is_bridge = clusters_covered >= 2
    
    concept_centrality.append({
        'concept': label, 'degree': degree, 'clusters': clusters_covered,
        'avg_quality': avg_quality, 'is_bridge': is_bridge, 'pages': owning_pages
    })

concept_centrality.sort(key=lambda x: (x['is_bridge'], x['degree']), reverse=True)
for c in concept_centrality[:15]:
    bridge = " [BRIDGE]" if c['is_bridge'] else ""
    print(f"  {c['concept']:20s} degree={c['degree']:2d} clusters={c['clusters']} avg_q={c['avg_quality']:.2f}{bridge}")
    print(f"    pages: {c['pages']}")

# ===== JEV ANALYSIS =====
print("\n=== JEV ANALYSIS ===")
all_results = []
for page_id, results in jev.items():
    for r in results:
        r['page_id'] = page_id
        # Convert NOUL probability to YES/NO/UNCLEAR for analysis
        if r.get('question_type') == 'noul' and isinstance(r.get('result'), (int, float)):
            p = r['result']
            if p > 0.65:
                r['result_cat'] = 'YES'
            elif p < 0.35:
                r['result_cat'] = 'NO'
            else:
                r['result_cat'] = 'UNCLEAR'
        elif 'result' in r and isinstance(r['result'], str):
            r['result_cat'] = r['result']
        else:
            r['result_cat'] = 'UNKNOWN'
        all_results.append(r)

print(f"Total questions: {len(all_results)}")
by_type = Counter(r.get('question_type', 'unknown') for r in all_results)
print(f"By type: {dict(by_type)}")

by_theme = defaultdict(lambda: {'total': 0, 'yes': 0, 'no': 0, 'unclear': 0, 'confidences': []})
for r in all_results:
    qid = r.get('question_id', '')
    theme = 'unknown'
    for t in ['PURPOSE', 'DISTINCT', 'EVIDENCE', 'SPECIFICITY', 'DIFF', 'TECH_PRECISION',
              'COMMERCIAL', 'WRITING', 'STRUCTURE', 'ARGUMENT', 'CITATION', 'REPETITION',
              'KNOWLEDGE', 'INTERNAL', 'AUTHORITY', 'AI_DISCOVERY', 'TECH_GEO', 'OUTCOME']:
        if t in qid:
            theme = t
            break
    by_theme[theme]['total'] += 1
    result_cat = r.get('result_cat', 'UNCLEAR')
    if result_cat == 'YES': by_theme[theme]['yes'] += 1
    elif result_cat == 'NO': by_theme[theme]['no'] += 1
    elif result_cat == 'UNCLEAR': by_theme[theme]['unclear'] += 1
    by_theme[theme]['confidences'].append(r.get('confidence', 0))

print("\nBy theme:")
for theme, stats in sorted(by_theme.items(), key=lambda x: x[1]['total'], reverse=True):
    if stats['total'] == 0:
        continue
    avg_conf = statistics.mean(stats['confidences']) if stats['confidences'] else 0
    print(f"  {theme:25s} total={stats['total']:3d}  YES={stats['yes']:3d}  NO={stats['no']:3d}  UNCLEAR={stats['unclear']:3d}  avg_conf={avg_conf:.2f}")

# Question difficulty
question_stats = defaultdict(lambda: {'yes': 0, 'no': 0, 'unclear': 0, 'pages': 0})
for r in all_results:
    qid = r.get('question_id', '')
    question_stats[qid]['pages'] += 1
    result_cat = r.get('result_cat', 'UNCLEAR')
    if result_cat == 'YES': question_stats[qid]['yes'] += 1
    elif result_cat == 'NO': question_stats[qid]['no'] += 1
    elif result_cat == 'UNCLEAR': question_stats[qid]['unclear'] += 1

difficulty = []
for qid, stats in question_stats.items():
    if stats['pages'] >= 3:
        yes_rate = stats['yes'] / stats['pages']
        difficulty.append({
            'question_id': qid, 'yes_rate': yes_rate,
            'no_rate': stats['no'] / stats['pages'],
            'unclear_rate': stats['unclear'] / stats['pages'],
            'pages_evaluated': stats['pages']
        })
difficulty.sort(key=lambda x: x['yes_rate'])

print("\n=== HARDEST QUESTIONS (lowest YES rate) ===")
for q in difficulty[:15]:
    print(f"  {q['question_id']:50s} yes={q['yes_rate']:.2f}  no={q['no_rate']:.2f}  unclear={q['unclear_rate']:.2f}")

# ===== QUALITY/PERFORMANCE GAPS =====
print("\n=== QUALITY/PERFORMANCE GAPS (heuristic) ===")
for page_id in pages:
    q = qv.get(page_id, {})
    quality = q.get('overall', 0)
    ps = page_states.get(page_id, {})
    
    # Heuristic traffic
    traffic = 0
    if ps:
        traffic += len(ps.get('headings', [])) * 0.02
        traffic += len(ps.get('sections', [])) * 0.03
        traffic += len(ps.get('statistics', [])) * 0.05
        traffic += len(ps.get('claims', [])) * 0.02
        if ps.get('page_type') in ['service', 'technical']:
            traffic += 0.3
        if ps.get('page_type') == 'whitepaper':
            traffic += 0.4
    traffic = min(1.0, traffic)
    
    if quality > 0.7 and traffic < 0.3:
        print(f"  HIGH_QUALITY_LOW_TRAFFIC: {page_id:30s} quality={quality:.2f} traffic={traffic:.2f}")
    elif quality < 0.4 and traffic > 0.5:
        print(f"  LOW_QUALITY_HIGH_TRAFFIC: {page_id:30s} quality={quality:.2f} traffic={traffic:.2f}")

# ===== OVERLAP NETWORK =====
print("\n=== OVERLAP NETWORK (top 20) ===")
overlaps = []
for edge in kg_edges:
    if edge.get('relationship') == 'overlaps':
        src = edge.get('source', '').replace('page:', '')
        tgt = edge.get('target', '').replace('page:', '')
        weight = edge.get('weight', 0)
        if src in pages and tgt in pages:
            overlaps.append((src, tgt, weight))
overlaps.sort(key=lambda x: x[2], reverse=True)
for src, tgt, w in overlaps[:20]:
    q1 = qv.get(src, {}).get('overall', 0)
    q2 = qv.get(tgt, {}).get('overall', 0)
    print(f"  {src:30s} \u2194 {tgt:30s}  overlap={w:.2f}  q1={q1:.2f} q2={q2:.2f}")

print("\n" + "=" * 60)
print("ANALYSIS COMPLETE")
print("=" * 60)