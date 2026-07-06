# Security Policy

## Threat model

Synapse is a local-only research tool. It runs entirely on your machine and makes network requests only to:

- The LLM API (Anthropic Claude) during paper extraction — you control the API key
- Hugging Face Hub (first run only, to download the sentence-transformers model)

**What Synapse does NOT do:**
- Store or transmit your API keys beyond what's needed for the LLM call
- Send your paper content to any third party (only to the LLM API you configured)
- Open network ports or run a server
- Execute untrusted code

## What counts as a vulnerability

1. An extraction cache file containing sensitive paper data being readable by unauthorized users — caches are stored in `kg-out/cache/` as JSON files.
2. The LLM prompt accidentally leaking source file paths or paper content — prompts are structured and bounded.

## Reporting

Open a [GitHub Security Advisory](https://github.com/alvi-uiu/Synapse/security/advisories/new) for anything sensitive, or a regular issue otherwise.
