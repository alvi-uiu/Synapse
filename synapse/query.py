import anthropic
import networkx as nx
import numpy as np

from synapse.schema import NodeType


_model = None
_client = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def find_task_nodes(G: nx.DiGraph, query: str, top_k: int = 5) -> list[str]:
    model = _get_model()
    query_emb = model.encode(query, normalize_embeddings=True)

    task_nodes = [
        (nid, data)
        for nid, data in G.nodes(data=True)
        if data.get("type") == NodeType.TASK.value
    ]

    if not task_nodes:
        return []

    labels = [data.get("label", "") for _, data in task_nodes]
    label_embs = model.encode(labels, normalize_embeddings=True)

    scores = np.dot(label_embs, query_emb)
    ranked = sorted(zip(scores, [nid for nid, _ in task_nodes]), reverse=True)

    return [nid for score, nid in ranked[:top_k] if score > 0.3]


def get_techniques_for_task(G: nx.DiGraph, task_node_ids: list[str]) -> list[dict]:
    results = []

    for task_id in task_node_ids:
        if task_id not in G:
            continue
        task_data = G.nodes[task_id]

        for src, tgt, edge_data in G.in_edges(task_id, data=True):
            if edge_data.get("relation") != "addresses":
                continue

            technique_data = dict(G.nodes[src])
            technique_data["addressing_task"] = task_data.get("label")
            technique_data["results"] = []
            technique_data["papers"] = []
            technique_data["confidence"] = edge_data.get("confidence")

            for t_src, t_tgt, r_edge in G.out_edges(src, data=True):
                if r_edge.get("relation") == "achieves":
                    result_data = dict(G.nodes[t_tgt])
                    technique_data["results"].append(result_data)

            for p_src, p_tgt, p_edge in G.in_edges(src, data=True):
                if p_edge.get("relation") == "proposes":
                    paper_data = G.nodes[p_src]
                    technique_data["papers"].append({
                        "title": paper_data.get("label"),
                        "year": paper_data.get("year"),
                        "venue": paper_data.get("venue"),
                    })

            results.append(technique_data)

    return results


def _keyword_fallback(G: nx.DiGraph, query: str) -> list[str]:
    query_lower = query.lower()
    matches = []
    for nid, data in G.nodes(data=True):
        label = data.get("label", "").lower()
        if query_lower in label:
            matches.append((len(label), nid))
    matches.sort(key=lambda x: x[0])
    return [nid for _, nid in matches[:5]]


def _build_context(G, task_ids, techniques) -> str:
    lines = []

    lines.append("## Tasks Being Addressed")
    for tid in task_ids:
        if tid in G:
            lines.append(f"- {G.nodes[tid].get('label', tid)}")

    lines.append("\n## Techniques Found in Knowledge Graph")
    for t in techniques:
        lines.append(f"\n### {t.get('label', 'Unknown Technique')}")
        lines.append(f"- Type: {t.get('type', '')}")
        lines.append(f"- Aliases: {', '.join(t.get('aliases', []))}")
        lines.append(f"- Confidence this addresses task: {t.get('confidence', '')}")

        if t.get("papers"):
            lines.append("- Proposed in:")
            for p in t["papers"]:
                lines.append(f"  - {p['title']} ({p['year']}, {p['venue']})")

        if t.get("results"):
            lines.append("- Numeric Results:")
            for r in t["results"]:
                lines.append(
                    f"  - {r.get('label', '')} (dataset: {r.get('dataset_name', '')}, "
                    f"metric: {r.get('metric_name', '')}, value: {r.get('value', '')})"
                )

        provenance = t.get("provenance")
        if provenance:
            lines.append(
                f"- Source: page {provenance.get('page', '?')}, "
                f"section {provenance.get('section', '?')}, "
                f"paragraph {provenance.get('paragraph', '?')}"
            )

    return "\n".join(lines)


def answer_query(G: nx.DiGraph, question: str) -> str:
    task_ids = find_task_nodes(G, question)

    if not task_ids:
        task_ids = _keyword_fallback(G, question)

    techniques = get_techniques_for_task(G, task_ids)

    if not techniques:
        return "No techniques found for this query in the knowledge graph."

    context = _build_context(G, task_ids, techniques)

    return _call_llm(question, context)


def _call_llm(question: str, context: str) -> str:
    client = anthropic.Anthropic()
    prompt = f"""You are Synapse, a research analyst with access to a structured knowledge graph of papers.

The following data was retrieved from the knowledge graph for the question below.
Answer based ONLY on what is in the retrieved data. Do not hallucinate results or papers not listed.
If the data is insufficient, say so explicitly.

Question: {question}

Retrieved Knowledge Graph Data:
{context}

Answer the question with:
1. A direct answer naming the best technique(s) and why
2. Supporting evidence: specific numeric results from the graph
3. Caveats: limitations or conditions under which different techniques perform better
4. Gaps: what the graph does not cover (missing evaluations, missing datasets)
"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text
