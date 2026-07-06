import json
from pathlib import Path

from synapse.cache import file_hash, cache_path, load_cached, save_cached
from synapse.schema import SCHEMA_VERSION


def test_file_hash(tmp_path):
    f = tmp_path / "test.pdf"
    f.write_text("hello world")
    h = file_hash(f)
    assert len(h) == 64
    assert h == "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"


def test_cache_path(tmp_path):
    f = tmp_path / "test.pdf"
    f.write_text("data")
    cache_root = tmp_path / "cache"
    cache_root.mkdir()
    cp = cache_path(f, cache_root)
    assert cp.parent == cache_root
    assert cp.suffix == ".json"


def test_save_and_load_cache(tmp_path):
    f = tmp_path / "paper.pdf"
    f.write_text("paper content")
    cache_root = tmp_path / "cache"
    cache_root.mkdir()

    extraction = {"nodes": [{"id": "test", "type": "task"}], "edges": []}
    save_cached(f, cache_root, extraction)

    loaded = load_cached(f, cache_root)
    assert loaded is not None
    assert loaded["nodes"][0]["id"] == "test"


def test_cache_miss_on_version_change(tmp_path):
    f = tmp_path / "paper.pdf"
    f.write_text("content")
    cache_root = tmp_path / "cache"
    cache_root.mkdir()

    extraction = {"nodes": [], "edges": []}
    save_cached(f, cache_root, extraction)

    cp = cache_path(f, cache_root)
    data = json.loads(cp.read_text(encoding="utf-8"))
    data["schema_version"] = SCHEMA_VERSION + 999
    cp.write_text(json.dumps(data), encoding="utf-8")

    assert load_cached(f, cache_root) is None
