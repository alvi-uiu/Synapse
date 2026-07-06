# Contributing

Thanks for considering contributing to Synapse.

## What counts as a contribution

- Bug reports and feature requests via GitHub Issues
- Pull requests with bug fixes, new features, or improved documentation
- New extraction prompt improvements or additional node types

## Before you open a PR

1. Open an issue first for significant changes — lets us discuss approach before you write code.
2. Keep changes focused. A PR should do one thing.
3. Run the tests: `pytest`
4. Add tests for new functionality — positive and negative cases.

## Development setup

```bash
git clone https://github.com/alvi-uiu/Synapse
cd Synapse
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Code style

- Follow PEP 8 (4-space indent, 88 char lines)
- Type annotations on all public functions
- No external runtime dependencies beyond what's in `pyproject.toml`
- Don't call the LLM unless necessary — graph traversal is free

## CI

Every PR runs through GitHub Actions: `pytest`. Make sure it passes.
