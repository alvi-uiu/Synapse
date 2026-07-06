from rapidfuzz import fuzz
from synapse._minhash import generate_minhash, jaccard_similarity


_ENTROPY_THRESHOLD = 2.5
_JARO_WINKLER_THRESHOLD = 0.88
_JACCARD_THRESHOLD = 0.6


def deduplicate_entities(
    nodes: list[dict],
    edges: list[dict],
    communities: dict[str, int],
) -> tuple[list[dict], list[dict]]:
    if len(nodes) < 2:
        return nodes, edges

    label_to_id: dict[str, str] = {}
    duplicate_ids: dict[str, str] = {}

    for node in nodes:
        nid = node.get("id", "")
        label = node.get("label", "")
        if not label:
            continue

        ntype = node.get("type", "")
        if ntype not in ("technique", "task", "dataset", "baseline", "concept"):
            continue

        match = _find_similar(label, list(label_to_id.keys()))
        if match:
            duplicate_ids[nid] = label_to_id[match]
        else:
            label_to_id[label] = nid

    deduped_nodes = [n for n in nodes if n.get("id") not in duplicate_ids]

    deduped_edges = []
    for edge in edges:
        src = edge.get("source", "")
        tgt = edge.get("target", "")
        src = duplicate_ids.get(src, src)
        tgt = duplicate_ids.get(tgt, tgt)
        if src != tgt:
            edge["source"] = src
            edge["target"] = tgt
            deduped_edges.append(edge)

    return deduped_nodes, deduped_edges


def _find_similar(label: str, candidates: list[str]) -> str | None:
    for candidate in candidates:
        jw = fuzz.token_sort_ratio(label.lower(), candidate.lower()) / 100.0
        if jw >= _JARO_WINKLER_THRESHOLD:
            return candidate

        m1 = generate_minhash(label)
        m2 = generate_minhash(candidate)
        if jaccard_similarity(m1, m2) >= _JACCARD_THRESHOLD:
            return candidate

    return None
