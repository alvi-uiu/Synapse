import re


def make_id(node_type: str, label: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")
    return f"{node_type}_{slug}"
