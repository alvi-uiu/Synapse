from collections import Counter

import networkx as nx


def god_nodes(G: nx.Graph, top_k: int = 20) -> list[dict]:
    degrees = dict(G.degree())
    ranked = sorted(degrees.items(), key=lambda x: -x[1])
    results = []
    for nid, deg in ranked[:top_k]:
        data = G.nodes[nid]
        results.append({
            "id": nid,
            "label": data.get("label", nid),
            "type": data.get("type", "unknown"),
            "degree": deg,
        })
    return results


def surprising_connections(
    G: nx.Graph,
    communities: dict[str, int],
    top_k: int = 20,
) -> list[dict]:
    results = []
    for src, tgt, data in G.edges(data=True):
        src_c = communities.get(src)
        tgt_c = communities.get(tgt)
        if src_c is not None and tgt_c is not None and src_c != tgt_c:
            results.append({
                "source": src,
                "source_label": G.nodes[src].get("label", src),
                "target": tgt,
                "target_label": G.nodes[tgt].get("label", tgt),
                "relation": data.get("relation", "related_to"),
                "relation_label": data.get("relation", "related"),
            })
    return results[:top_k]
