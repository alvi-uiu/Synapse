import json
from pathlib import Path

import anthropic

from synapse.cache import load_cached, save_cached


client = anthropic.Anthropic()


def extract_paper(pdf_path: Path, parsed: dict, cache_root: Path) -> dict:
    cached = load_cached(pdf_path, cache_root)
    if cached is not None:
        return cached

    result = _run_extraction(pdf_path, parsed)

    if result["nodes"]:
        save_cached(pdf_path, cache_root, result)

    return result


def _run_extraction(pdf_path: Path, parsed: dict) -> dict:
    prompt = _build_prompt(pdf_path, parsed)

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text
    raw = raw.strip().removeprefix("```json").removesuffix("```").strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        print(f"WARNING: JSON parse failed for {pdf_path.name}", flush=True)
        return {"nodes": [], "edges": [], "input_tokens": 0, "output_tokens": 0}

    data["input_tokens"] = response.usage.input_tokens
    data["output_tokens"] = response.usage.output_tokens
    return data


def _build_prompt(pdf_path: Path, parsed: dict) -> str:
    title = parsed.get("title", "Unknown")
    source_file = str(pdf_path.resolve())
    sections = parsed.get("sections", {})

    abstract = sections.get("abstract", "")
    method = sections.get("method", sections.get("methodology", ""))
    results = sections.get("results", sections.get("experiments", ""))
    conclusion = sections.get("conclusion", "")
    limitations = sections.get("limitations", "")
    related_work = sections.get("related_work", "")
    references = parsed.get("references", [])

    return f"""You are Synapse, a research knowledge graph extraction agent. Extract structured knowledge from this paper.

Output ONLY valid JSON. No explanation, no markdown fences, no preamble.

Paper Title: {title}

Abstract:
{abstract[:2000]}

Method Section:
{method[:3000]}

Results Section:
{results[:3000]}

Conclusion:
{conclusion[:1000]}

Limitations:
{limitations[:1000]}

Related Work (for citation extraction):
{related_work[:1500]}

References (first 20):
{json.dumps(references[:20], indent=2)[:2000]}

---

Extract the following and return as JSON matching this EXACT schema:

{{
  "nodes": [
    {{
      "id": "task_knowledge_drift_detection",
      "type": "task",
      "label": "Knowledge Drift Detection",
      "source_file": "{source_file}",
      "provenance": {{
        "page": 5,
        "section": "Introduction",
        "paragraph": 2
      }}
    }},
    {{
      "id": "technique_ewc",
      "type": "technique",
      "label": "Elastic Weight Consolidation",
      "aliases": ["EWC"],
      "source_file": "{source_file}",
      "provenance": {{
        "page": 3,
        "section": "Method",
        "paragraph": 1
      }}
    }},
    {{
      "id": "dataset_cifar100",
      "type": "dataset",
      "label": "CIFAR-100",
      "source_file": "{source_file}",
      "provenance": {{
        "page": 7,
        "section": "Experiments",
        "paragraph": 3
      }}
    }},
    {{
      "id": "result_ewc_accuracy_cifar100",
      "type": "result",
      "label": "EWC Accuracy = 87.3% on CIFAR-100",
      "value": 87.3,
      "metric_name": "Accuracy",
      "dataset_name": "CIFAR-100",
      "source_file": "{source_file}",
      "provenance": {{
        "page": 8,
        "section": "Results",
        "paragraph": 2
      }}
    }},
    {{
      "id": "claim_outperforms_baseline",
      "type": "claim",
      "label": "Proposed method outperforms all baselines on low-resource settings",
      "source_file": "{source_file}",
      "provenance": {{
        "page": 9,
        "section": "Results",
        "paragraph": 4
      }}
    }},
    {{
      "id": "limitation_computational_cost",
      "type": "limitation",
      "label": "High computational cost at scale",
      "source_file": "{source_file}",
      "provenance": {{
        "page": 10,
        "section": "Limitations",
        "paragraph": 1
      }}
    }},
    {{
      "id": "contribution_novel_loss_function",
      "type": "contribution",
      "label": "Novel regularization loss for continual learning",
      "source_file": "{source_file}",
      "provenance": {{
        "page": 4,
        "section": "Method",
        "paragraph": 3
      }}
    }}
  ],
  "edges": [
    {{"source": "paper_id", "target": "task_id", "relation": "addresses", "confidence": "EXTRACTED", "confidence_score": 1.0}},
    {{"source": "paper_id", "target": "technique_id", "relation": "proposes", "confidence": "EXTRACTED", "confidence_score": 1.0}},
    {{"source": "technique_id", "target": "task_id", "relation": "addresses", "confidence": "EXTRACTED", "confidence_score": 1.0}},
    {{"source": "paper_id", "target": "dataset_id", "relation": "evaluates_on", "confidence": "EXTRACTED", "confidence_score": 1.0}},
    {{"source": "technique_id", "target": "result_id", "relation": "achieves", "confidence": "EXTRACTED", "confidence_score": 1.0}},
    {{"source": "result_id", "target": "dataset_id", "relation": "result_on", "confidence": "EXTRACTED", "confidence_score": 1.0}},
    {{"source": "paper_id", "target": "cited_paper_id", "relation": "cites", "confidence": "EXTRACTED", "confidence_score": 1.0}},
    {{"source": "technique_id", "target": "baseline_technique_id", "relation": "compares_with", "confidence": "EXTRACTED", "confidence_score": 1.0}}
  ]
}}

Rules:
1. Node IDs: lowercase letters, digits, and underscores only. Format: {{type}}_{{slug}}. Example: technique_elastic_weight_consolidation.
2. type field MUST be one of exactly: paper, task, technique, dataset, metric, result, claim, limitation, contribution, baseline, concept.
3. Every node MUST include a "provenance" object with "page" (int), "section" (str), and "paragraph" (int) fields showing where in the paper the information was found.
4. confidence MUST be: EXTRACTED (explicitly stated), INFERRED (reasonable inference), or AMBIGUOUS (uncertain).
5. confidence_score: 1.0 for EXTRACTED, 0.75-0.95 for INFERRED, 0.1-0.5 for AMBIGUOUS.
6. Extract ALL techniques mentioned (both proposed and baselines). Mark baselines with type "baseline".
7. Extract ALL numeric results from tables. Each row in a results table = one result node.
8. Extract ALL datasets used for evaluation.
9. Extract ALL tasks/problems the paper addresses (there may be more than one).
10. For cited papers, create a node with type "paper" and a cites edge. Use the reference title as label.
11. For techniques that build on prior work, add builds_on edges.
12. aliases field on technique nodes: list all abbreviations and alternate names found in the paper.
13. Do NOT include the paper itself as a node -- the paper node is created by the ingestion pipeline separately.
14. If a numeric result appears in a table, set value as a float, metric_name and dataset_name must match existing dataset node labels exactly.
"""
