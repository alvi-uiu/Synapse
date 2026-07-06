import re
from pathlib import Path


def parse_tex(tex_path: Path) -> dict:
    text = tex_path.read_text(encoding="utf-8", errors="replace")

    title = _extract_title(text)
    authors = _extract_authors(text)
    year = _extract_year(text, tex_path)
    sections = _extract_sections(text)
    abstract = _extract_abstract(text)
    references = _extract_references(text)
    tables = _extract_tables(text)

    sections["abstract"] = abstract

    return {
        "title": title or tex_path.stem,
        "full_text": text,
        "sections": sections,
        "references": references,
        "tables": tables,
        "metadata": {
            "authors": authors,
            "year": year,
            "venue": "",
        },
    }


def _extract_title(text: str) -> str:
    m = re.search(r"\\title\s*\{([^}]+)\}", text, re.DOTALL)
    if m:
        return _clean_tex(m.group(1))
    return ""


def _extract_authors(text: str) -> list[str]:
    m = re.search(r"\\author\s*\{([^}]+)\}", text, re.DOTALL)
    if not m:
        return []
    raw = _clean_tex(m.group(1))
    parts = re.split(r"\\and|,", raw)
    authors = []
    for p in parts:
        p = p.strip().strip(",").strip()
        if p and not p.startswith("\\"):
            authors.append(p)
    return authors


def _extract_year(text: str, tex_path: Path) -> int:
    import datetime
    m = re.search(r"\\(?:year|Date)\s*\{(\d{4})\}", text)
    if m:
        return int(m.group(1))
    m = re.search(r"\(?(\d{4})\)?", tex_path.parent.name)
    if m:
        return int(m.group(1))
    m = re.search(r"(\d{4})", str(tex_path.parent))
    if m:
        return int(m.group(1))
    return datetime.date.today().year


def _extract_sections(text: str) -> dict[str, str]:
    sections = {}
    section_pattern = re.compile(
        r"\\(?:section|subsection|section\*)\s*\{([^}]+)\}(.*?)(?=\\(?:section|subsection|section\*)|\Z)",
        re.DOTALL,
    )
    for m in section_pattern.finditer(text):
        heading = _clean_tex(m.group(1)).lower().strip()
        content = _clean_tex(m.group(2)).strip()
        if heading and content:
            key = heading[:50]
            sections[key] = content[:5000]
    return sections


def _extract_abstract(text: str) -> str:
    m = re.search(
        r"\\begin\{abstract\}(.*?)\\end\{abstract\}", text, re.DOTALL
    )
    if m:
        return _clean_tex(m.group(1)).strip()
    m = re.search(r"\\abstract\s*\{([^}]+)\}", text, re.DOTALL)
    if m:
        return _clean_tex(m.group(1)).strip()
    return ""


def _extract_references(text: str) -> list[dict]:
    refs = []
    bib_items = re.findall(
        r"\\bibitem\s*\{([^}]*)\}\s*(.*?)(?=\\bibitem|\Z)", text, re.DOTALL
    )
    for key, rest in bib_items:
        rest = _clean_tex(rest).strip()
        refs.append({"label": key, "title": rest[:200], "authors": []})

    if not refs:
        bib = re.search(r"\\bibliography\s*\{([^}]+)\}", text)
        if bib:
            refs.append({"label": f"bibliography: {bib.group(1)}", "title": "", "authors": []})

    return refs


def _extract_tables(text: str) -> list[dict]:
    tables = []
    table_pattern = re.compile(
        r"\\begin\{table\}(.*?)\\end\{table\}", re.DOTALL
    )
    for m in table_pattern.finditer(text):
        block = m.group(1)
        caption_m = re.search(r"\\caption\s*\{([^}]+)\}", block)
        caption = _clean_tex(caption_m.group(1)) if caption_m else ""
        rows = []
        tabular = re.search(
            r"\\begin\{tabular\}.*?\n(.*?)\\end\{tabular\}", block, re.DOTALL
        )
        if tabular:
            for line in tabular.group(1).splitlines():
                line = line.strip()
                if line and not line.startswith("%"):
                    cells = [c.strip().rstrip("\\\\").strip() for c in line.split("&")]
                    cells = [_clean_tex(c) for c in cells]
                    rows.append(cells)
        tables.append({"caption": caption, "rows": rows})
    return tables


def _clean_tex(text: str) -> str:
    text = re.sub(r"\\(?:emph|textbf|textit|texttt|textsc)\{([^}]+)\}", r"\1", text)
    text = re.sub(r"\\(?:cite|ref|label)\{([^}]*)\}", "", text)
    text = re.sub(r"\$([^$]+)\$", r"\1", text)
    text = re.sub(r"\\%", "%", text)
    text = re.sub(r"\\[a-zA-Z]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text
