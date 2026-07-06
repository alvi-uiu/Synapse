from collections import Counter

import networkx as nx

from synapse.analyze import god_nodes, surprising_connections
from synapse.cluster import score_all
from synapse.schema import NodeType


def generate_report(
    G: nx.DiGraph,
    communities: dict[str, int],
    extraction: dict | None = None,
) -> str:
    lines = []
    lines.append("# Synapse Knowledge Graph Report\n")

    _section_corpus_summary(lines, G, extraction)
    _section_god_nodes(lines, G)
    _section_communities(lines, G, communities)
    _section_surprising_connections(lines, G, communities)
    _section_missing_coverage(lines, G)
    _section_suggested_queries(lines, G)

    return "\n".join(lines)


def _section_corpus_summary(lines: list, G: nx.DiGraph, extraction: dict | None) -> None:
    lines.append("## Corpus Summary\n")
    lines.append(f"- **Total papers**: {sum(1 for _, d in G.nodes(data=True) if d.get('type') == 'paper')}")
    lines.append(f"- **Total techniques**: {sum(1 for _, d in G.nodes(data=True) if d.get('type') == 'technique')}")
    lines.append(f"- **Total tasks**: {sum(1 for _, d in G.nodes(data=True) if d.get('type') == 'task')}")
    lines.append(f"- **Total datasets**: {sum(1 for _, d in G.nodes(data=True) if d.get('type') == 'dataset')}")
    lines.append(f"- **Total results**: {sum(1 for _, d in G.nodes(data=True) if d.get('type') == 'result')}")
    lines.append(f"- **Total claims**: {sum(1 for _, d in G.nodes(data=True) if d.get('type') == 'claim')}")
    lines.append(f"- **Total nodes**: {G.number_of_nodes()}")
    lines.append(f"- **Total edges**: {G.number_of_edges()}")

    if extraction:
        lines.append(f"- **Input tokens**: {extraction.get('input_tokens', 0):,}")
        lines.append(f"- **Output tokens**: {extraction.get('output_tokens', 0):,}")

    lines.append("")


def _section_god_nodes(lines: list, G: nx.DiGraph) -> None:
    lines.append("## God Nodes (Most Connected)\n")
    gods = god_nodes(G, top_k=15)
    for g in gods:
        lines.append(f"- **{g['label']}** ({g['type']}) — degree {g['degree']}")
    lines.append("")


def _section_communities(lines: list, G: nx.DiGraph, communities: dict[str, int]) -> None:
    from collections import defaultdict

    lines.append("## Communities\n")
    community_nodes: dict[int, list[str]] = defaultdict(list)
    for nid, cid in communities.items():
        community_nodes[cid].append(nid)

    cohesion = score_all(G, communities)

    for cid in sorted(community_nodes.keys()):
        members = community_nodes[cid]
        types = Counter()
        labels = []
        for nid in members:
            data = G.nodes[nid]
            types[data.get("type", "unknown")] += 1
            label = data.get("label", nid)
            if data.get("type") in ("technique", "task", "dataset"):
                labels.append(label)

        avg_cohesion = sum(cohesion.get(n, 0) for n in members) / len(members)

        lines.append(f"### Community {cid} ({len(members)} nodes)")
        lines.append(f"- **Cohesion**: {avg_cohesion:.2f}")
        lines.append(f"- **Types**: {dict(types)}")
        lines.append(f"- **Key nodes**: {', '.join(labels[:10])}")
        lines.append("")


def _section_surprising_connections(lines: list, G: nx.DiGraph, communities: dict[str, int]) -> None:
    lines.append("## Cross-Community Connections\n")
    surprises = surprising_connections(G, communities, top_k=20)
    if not surprises:
        lines.append("No cross-community connections found.\n")
        return
    for s in surprises:
        lines.append(
            f"- **{s['source_label']}** → **{s['target_label']}** "
            f"({s['relation_label']})"
        )
    lines.append("")


def _section_missing_coverage(lines: list, G: nx.DiGraph) -> None:
    lines.append("## Missing Coverage\n")
    technique_ids = [
        nid for nid, d in G.nodes(data=True) if d.get("type") == "technique"
    ]
    missing = []
    for tid in technique_ids:
        has_result = any(
            d.get("relation") == "achieves"
            for _, _, d in G.out_edges(tid, data=True)
        )
        if not has_result:
            missing.append(tid)

    if missing:
        lines.append("These techniques have no numeric results:")
        for tid in missing:
            label = G.nodes[tid].get("label", tid)
            lines.append(f"- {label}")
    else:
        lines.append("No missing coverage detected — all techniques have results.")
    lines.append("")


def _section_suggested_queries(lines: list, G: nx.DiGraph) -> None:
    lines.append("## Suggested Queries\n")
    tasks = [
        G.nodes[nid].get("label", nid)
        for nid, d in G.nodes(data=True)
        if d.get("type") == "task"
    ]
    techniques = [
        G.nodes[nid].get("label", nid)
        for nid, d in G.nodes(data=True)
        if d.get("type") == "technique"
    ]

    if tasks:
        for t in tasks[:5]:
            lines.append(f'- "Which techniques address **{t}**?"')

    if techniques:
        for t in techniques[:3]:
            lines.append(f'- "What results does **{t}** achieve?"')

    if tasks and techniques:
        lines.append(f'- "Compare **{tasks[0]}** and **{tasks[1] if len(tasks) > 1 else techniques[0]}** approaches"')
        lines.append(f'- "What research gaps exist in **{tasks[0]}**?"')

    lines.append("")
