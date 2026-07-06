from pathlib import Path


def parse_paper(file_path: Path) -> dict:
    ext = file_path.suffix.lower()
    if ext == ".tex":
        from synapse.parse_tex import parse_tex
        return parse_tex(file_path)
    elif ext == ".pdf":
        return _parse_pdf(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext} (only .pdf and .tex supported)")


def _parse_pdf(pdf_path: Path) -> dict:
    from docling.document_converter import DocumentConverter

    converter = DocumentConverter()
    result = converter.convert(str(pdf_path))
    doc = result.document

    return {
        "title": doc.name or "",
        "full_text": doc.export_to_markdown(),
        "sections": _extract_sections(doc),
        "references": _extract_references(doc),
        "tables": _extract_tables(doc),
        "metadata": {
            "authors": _extract_authors(doc),
            "year": _extract_year(doc),
            "venue": _extract_venue(doc),
        },
    }


def _extract_sections(doc) -> dict[str, str]:
    sections = {}
    try:
        for item, level in doc.iterate_items():
            text = item.text.strip() if item.text else ""
            if level == 1 and text:
                sections[text.lower()[:50]] = text
    except Exception:
        pass
    return sections


def _extract_references(doc) -> list[dict]:
    refs = []
    try:
        for ref in doc.references:
            refs.append({
                "label": ref.label or "",
                "title": getattr(ref, "title", "") or "",
                "authors": getattr(ref, "authors", []) or [],
            })
    except Exception:
        pass
    return refs


def _extract_tables(doc) -> list[dict]:
    tables = []
    try:
        for table in doc.tables:
            rows = []
            for row in table.data:
                rows.append([str(cell) for cell in row])
            tables.append({
                "caption": table.caption or "",
                "rows": rows,
            })
    except Exception:
        pass
    return tables


def _extract_authors(doc) -> list[str]:
    try:
        authors = []
        for ref in doc.references:
            if hasattr(ref, "authors") and ref.authors:
                for author in ref.authors:
                    if isinstance(author, str) and author not in authors:
                        authors.append(author)
        return authors
    except Exception:
        return []


def _extract_year(doc) -> int:
    try:
        for ref in doc.references:
            if hasattr(ref, "date") and ref.date:
                return int(str(ref.date)[:4])
    except Exception:
        pass
    return 0


def _extract_venue(doc) -> str:
    return ""
