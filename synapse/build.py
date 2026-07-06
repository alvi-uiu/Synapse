import networkx as nx
from synapse.schema import NodeType


def build_graph(extraction: dict, directed: bool = True) -> nx.DiGraph:
    G = nx.DiGraph() if directed else nx.Graph()

    node_ids = set()
    for node in extraction.get("nodes", []):
        nid = node.get("id")
        if not nid:
            continue
        ntype = node.get("type", "concept")
        if ntype not in [t.value for t in NodeType]:
            node["type"] = "concept"

        G.add_node(nid, **node)
        node_ids.add(nid)

    for edge in extraction.get("edges", []):
        src = edge.get("source")
        tgt = edge.get("target")
        if not src or not tgt:
            continue
        if src not in node_ids or tgt not in node_ids:
            continue
        if src == tgt:
            continue

        G.add_edge(src, tgt, **edge)

    return G


def merge_graphs(graphs: list[nx.DiGraph]) -> nx.DiGraph:
    merged = nx.DiGraph()
    for G in graphs:
        for nid, data in G.nodes(data=True):
            if merged.has_node(nid):
                existing = merged.nodes[nid]
                if "aliases" in data and "aliases" in existing:
                    merged.nodes[nid]["aliases"] = list(
                        set(existing["aliases"]) | set(data["aliases"])
                    )
                if "provenance" in data and "provenance" not in existing:
                    merged.nodes[nid]["provenance"] = data["provenance"]
            else:
                merged.add_node(nid, **data)
        for src, tgt, data in G.edges(data=True):
            if not merged.has_edge(src, tgt):
                merged.add_edge(src, tgt, **data)
    return merged
