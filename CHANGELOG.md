# Changelog

## 0.1.0 (2026-07-06)

- Initial release
- `synapse build` — ingest PDFs and .tex files, build NetworkX knowledge graph
- `synapse query` — graph-first querying with LLM fallback for reasoning
- `synapse add` — incrementally add papers to existing graph
- `synapse info` — graph statistics and god nodes
- `synapse visualize` — interactive HTML force-directed graph
- Provenance tracking (page/section/paragraph) on every extracted node
- Cache versioning (schema_version + prompt_version) for safe prompt evolution
- PDF parsing via Docling + LaTeX parsing via regex
- MinHash/Jaro-Winkler entity deduplication
- Leiden community detection
- GRAPH_REPORT.md generation with 6 sections
