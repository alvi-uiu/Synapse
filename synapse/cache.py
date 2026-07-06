import hashlib
import json
from pathlib import Path
from typing import Optional

from synapse.schema import SCHEMA_VERSION


EXTRACTION_PROMPT_VERSION = 1


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cache_path(pdf_path: Path, cache_root: Path) -> Path:
    h = file_hash(pdf_path)
    return cache_root / f"{h}.json"


def load_cached(pdf_path: Path, cache_root: Path) -> Optional[dict]:
    cp = cache_path(pdf_path, cache_root)
    if not cp.exists():
        return None
    data = json.loads(cp.read_text(encoding="utf-8"))
    if data.get("schema_version") != SCHEMA_VERSION:
        return None
    if data.get("prompt_version") != EXTRACTION_PROMPT_VERSION:
        return None
    return data.get("extraction")


def save_cached(pdf_path: Path, cache_root: Path, extraction: dict) -> None:
    cp = cache_path(pdf_path, cache_root)
    cp.write_text(
        json.dumps(
            {
                "schema_version": SCHEMA_VERSION,
                "prompt_version": EXTRACTION_PROMPT_VERSION,
                "source_file": str(pdf_path.resolve()),
                "extraction": extraction,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def cached_papers(cache_root: Path) -> list[dict]:
    papers = []
    for f in sorted(cache_root.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            papers.append(data)
        except (json.JSONDecodeError, KeyError):
            continue
    return papers
