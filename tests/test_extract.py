from pathlib import Path

from synapse.extract import _build_prompt


def test_extract_prompt_build():
    parsed = {
        "title": "Test Paper",
        "sections": {
            "abstract": "This is a test paper.",
            "method": "We propose a new method.",
        },
        "references": [],
    }

    prompt = _build_prompt(Path("/tmp/test.pdf"), parsed)
    assert "Test Paper" in prompt
    assert "provenance" in prompt
    assert "source_file" in prompt
    assert "/tmp/test.pdf" in prompt
