# Synapse

Research paper knowledge graph — one LLM pass per paper, graph-first querying.

## Quick reference

```bash
# Build graph from papers/
synapse build papers/

# Query (graph-first, LLM only for reasoning)
synapse query "what techniques address this task?"

# Visualize
synapse visualize
```

## Key invariants

- LLM is called exactly **once per paper** (cached by SHA256). Second build of same paper = $0.
- No dangling edges. If source or target node doesn't exist, edge is pruned.
- Node IDs are deterministic from type + label. Same technique in two papers = same ID → auto-merge.
- Graph is directed (`nx.DiGraph`). Technique --addresses--> Task, not the reverse.
- Zero-node extraction results are never cached.
- Query pipeline never sends full PDFs to the LLM. Max 6,000 tokens of structured context.

## File structure

| File | Role | Calls LLM? |
|------|------|-----------|
| `parse.py` / `parse_tex.py` | PDF/TeX → structured sections | No |
| `extract.py` | Sections → JSON nodes/edges | Yes (once per paper) |
| `ingest.py` | Orchestrates parse + extract | No |
| `build.py` | JSON → NetworkX DiGraph | No |
| `dedup.py` | MinHash entity dedup | No |
| `cluster.py` | Leiden communities | No |
| `analyze.py` | God nodes + surprise edges | No |
| `query.py` | Graph traversal + LLM reasoning | Only for reasoning |
| `report.py` | Graph → GRAPH_REPORT.md | No |
| `cli.py` | Click CLI commands | No |
| `cache.py` | SHA256 cache with versioning | No |

## Provenance schema

Every extracted node includes:
```json
"provenance": {
  "page": 5,
  "section": "Results",
  "paragraph": 2
}
```

## Cache versioning

Cached extractions store `schema_version` + `prompt_version`. When either changes, old caches are invalidated and re-extracted.
