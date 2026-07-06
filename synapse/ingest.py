from pathlib import Path

from synapse.parse import parse_paper
from synapse.extract import extract_paper
from synapse.schema import make_id


def ingest_paper(pdf_path: Path, cache_root: Path) -> dict:
    pdf_path = pdf_path.resolve()
    parsed = parse_paper(pdf_path)

    paper_node = _make_paper_node(pdf_path, parsed)

    extraction = extract_paper(pdf_path, parsed, cache_root)

    extraction["nodes"] = [paper_node] + extraction["nodes"]

    return extraction


def ingest_directory(papers_dir: Path, cache_root: Path) -> dict:
    files = sorted(papers_dir.glob("**/*.pdf")) + sorted(papers_dir.glob("**/*.tex"))
    all_nodes, all_edges = [], []
    total_in, total_out = 0, 0

    for f in files:
        print(f"Ingesting: {f.name}")
        result = ingest_paper(f, cache_root)
        all_nodes.extend(result["nodes"])
        all_edges.extend(result["edges"])
        total_in += result.get("input_tokens", 0)
        total_out += result.get("output_tokens", 0)

    return {
        "nodes": all_nodes,
        "edges": all_edges,
        "input_tokens": total_in,
        "output_tokens": total_out,
    }


def _make_paper_node(pdf_path: Path, parsed: dict) -> dict:
    title = parsed.get("title", pdf_path.stem)
    metadata = parsed.get("metadata", {})
    authors = metadata.get("authors", [])
    year = metadata.get("year", 0)
    venue = metadata.get("venue", "")

    first_author = authors[0].split()[-1].lower() if authors else "unknown"
    first_word = title.split()[0].lower() if title else "paper"

    return {
        "id": make_id("paper", f"{first_author}_{year}_{first_word}"),
        "type": "paper",
        "label": title,
        "authors": authors,
        "year": year,
        "venue": venue,
        "abstract": parsed.get("sections", {}).get("abstract", ""),
        "source_file": str(pdf_path),
    }
