from collections import defaultdict

import networkx as nx


def cluster(G: nx.Graph) -> dict[str, int]:
    if G.number_of_nodes() == 0:
        return {}

    UG = G.to_undirected() if G.is_directed() else G

    communities = _leiden_clustering(UG)

    return communities


def _leiden_clustering(G: nx.Graph) -> dict[str, int]:
    communities = {}
    try:
        import community as community_lib

        partition = community_lib.best_partition(G)
        for node, cid in partition.items():
            communities[node] = int(cid)
    except ImportError:
        communities = _label_propagation(G)

    return communities


def _label_propagation(G: nx.Graph) -> dict[str, int]:
    return {node: 0 for node in G.nodes()}


def score_all(G: nx.Graph, communities: dict[str, int]) -> dict[str, float]:
    scores = {}
    for node in G.nodes():
        cid = communities.get(node, -1)
        neighbors = list(G.neighbors(node))
        if not neighbors:
            scores[node] = 0.0
            continue
        same = sum(1 for n in neighbors if communities.get(n) == cid)
        scores[node] = same / len(neighbors)
    return scores
