<div align="center">

# Synapse

### Research Paper Knowledge Graph — one LLM pass per paper, query forever

**Turn a folder of research papers (PDF or LaTeX) into a persistent, queryable knowledge graph. Extract once with an LLM, then ask any question via graph traversal — no repeated API costs.**

[![CI](https://github.com/alvi-uiu/Synapse/actions/workflows/ci.yml/badge.svg)](https://github.com/alvi-uiu/Synapse/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-%E2%89%A53.10-blue.svg)](pyproject.toml)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

<img src="Synapse.png" alt="Synapse — Research Paper Knowledge Graph" width="600">

</div>

---

## Why Synapse?

Reading research papers is slow. Re-reading them to answer questions is worse.

Synapse solves this by building a **structured knowledge graph** from your papers. Every technique, task, dataset, result, claim, and limitation is extracted — with provenance (page, section, paragraph) — and linked together. After extraction, basic queries like *"Which papers use this dataset?"* or *"What techniques address this task?"* cost **$0** — they're pure graph traversal.

**Key design principle (from the original project):** For ~100 papers, you don't need Neo4j, microservices, or multi-agent systems. NetworkX + SQLite-style cache + one LLM pass per paper is sufficient.

---

## Features

- **Provenance tracking** — every node knows exactly where it came from (page, section, paragraph)
- **Cache versioning** — schema and prompt versions stored with every extraction; stale caches auto-invalidate
- **Graph-first queries** — embedding similarity + graph traversal for most queries; LLM called only for reasoning (compare, gaps, critique)
- **PDF + LaTeX support** — auto-detects `.pdf` (via Docling OCR) and `.tex` (via regex parser)
- **Interactive visualization** — `synapse visualize` generates a browser-ready force-directed graph
- **CLI-first** — `synapse build`, `synapse query`, `synapse add`, `synapse info`, `synapse visualize`
- **Incremental** — adding a new paper re-clusters and regenerates the report without re-processing existing papers

---

## Quick start

```bash
# Clone
git clone https://github.com/alvi-uiu/Synapse
cd Synapse

# Set up environment
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# Set your API key
export ANTHROPIC_API_KEY="sk-ant-..."

# Drop PDFs or .tex files into papers/
cp your-papers/*.pdf papers/

# Build the knowledge graph
synapse build papers/

# Query (graph-only, no API cost for basic questions)
synapse query "what techniques does this paper propose?"
synapse query "which datasets are used?"

# Visualize interactively
synapse visualize
# Then open kg-out/graph.html in your browser
```

---

## How it works

```
papers/*.pdf / .tex
       │
       ▼
  parse.py     ─── Docling (PDF) or parse_tex (LaTeX)
       │
       ▼
  extract.py   ─── LLM extraction → structured JSON nodes + edges
       │                  (cached after first run, versioned)
       ▼
  build.py     ─── NetworkX DiGraph construction
       │
       ▼
  dedup.py     ─── MinHash + Jaro-Winkler entity deduplication
       │
       ▼
  cluster.py   ─── Leiden community detection
       │
       ▼
  report.py    ─── GRAPH_REPORT.md with 6 sections
       │
       ▼
  query.py     ─── Embedding lookup → graph traversal → LLM (only when needed)
```

| Step | Calls LLM? | Cached? |
|------|-----------|---------|
| Parse (PDF or TeX) | No | No |
| Extract (JSON nodes/edges) | **Yes** (once per paper) | Yes |
| Build graph | No | No |
| Deduplicate | No | No |
| Cluster | No | No |
| Report | No | No |
| Query (basic, graph-only) | No | — |
| Query (reasoning) | **Yes** (per question) | — |

---

## Token cost

**~3¢ per paper** using Claude Sonnet 4. A 50-paper corpus costs ~$1.57 total, **one-time cost**. After extraction, the LLM is only called when you ask a reasoning question (compare papers, find gaps).

---

## Commands

| Command | Description |
|---------|-------------|
| `synapse build <dir>` | Ingest all PDFs/TeX files and build the graph |
| `synapse query <question>` | Query the graph (graph-first, LLM for reasoning) |
| `synapse add <file>` | Add a single paper to existing graph |
| `synapse info` | Show graph statistics |
| `synapse visualize` | Generate interactive HTML visualization |

---

## Directory structure

```
Synapse/
├── .github/workflows/ci.yml
├── CHANGELOG.md
├── CLAUDE.md
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── LICENSE
├── README.md
├── SECURITY.md
├── Synapse.png
├── pyproject.toml
├── papers/                  # Drop your PDFs and .tex files here
├── kg-out/                  # Output: graph.json, GRAPH_REPORT.md, graph.html
│   └── cache/               # Per-paper extraction cache (versioned)
├── synapse/                 # Python package
│   ├── __init__.py
│   ├── _minhash.py
│   ├── analyze.py
│   ├── build.py
│   ├── cache.py
│   ├── cli.py
│   ├── cluster.py
│   ├── dedup.py
│   ├── extract.py
│   ├── ids.py
│   ├── ingest.py
│   ├── parse.py
│   ├── parse_tex.py
│   ├── query.py
│   ├── report.py
│   └── schema.py
└── tests/
    ├── conftest.py
    ├── test_build.py
    ├── test_cache.py
    ├── test_extract.py
    ├── test_query.py
    └── test_schema.py
```

---

## Development

```bash
git clone https://github.com/alvi-uiu/Synapse
cd Synapse
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

---

## License

MIT
