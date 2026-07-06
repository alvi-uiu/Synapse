import json
from pathlib import Path

import pytest


@pytest.fixture
def sample_extraction() -> dict:
    return {
        "nodes": [
            {
                "id": "task_drift_detection",
                "type": "task",
                "label": "Drift Detection",
                "source_file": "/papers/paper1.pdf",
                "provenance": {"page": 1, "section": "Abstract", "paragraph": 1},
            },
            {
                "id": "technique_ewc",
                "type": "technique",
                "label": "Elastic Weight Consolidation",
                "aliases": ["EWC"],
                "source_file": "/papers/paper1.pdf",
                "provenance": {"page": 3, "section": "Method", "paragraph": 2},
            },
            {
                "id": "dataset_cifar100",
                "type": "dataset",
                "label": "CIFAR-100",
                "source_file": "/papers/paper1.pdf",
                "provenance": {"page": 5, "section": "Experiments", "paragraph": 1},
            },
            {
                "id": "result_ewc_acc",
                "type": "result",
                "label": "EWC Accuracy = 87.3% on CIFAR-100",
                "value": 87.3,
                "metric_name": "Accuracy",
                "dataset_name": "CIFAR-100",
                "source_file": "/papers/paper1.pdf",
                "provenance": {"page": 6, "section": "Results", "paragraph": 2},
            },
        ],
        "edges": [
            {
                "source": "paper_author_2024_title",
                "target": "task_drift_detection",
                "relation": "addresses",
                "confidence": "EXTRACTED",
                "confidence_score": 1.0,
            },
            {
                "source": "paper_author_2024_title",
                "target": "technique_ewc",
                "relation": "proposes",
                "confidence": "EXTRACTED",
                "confidence_score": 1.0,
            },
            {
                "source": "technique_ewc",
                "target": "task_drift_detection",
                "relation": "addresses",
                "confidence": "EXTRACTED",
                "confidence_score": 1.0,
            },
            {
                "source": "technique_ewc",
                "target": "result_ewc_acc",
                "relation": "achieves",
                "confidence": "EXTRACTED",
                "confidence_score": 1.0,
            },
        ],
        "input_tokens": 500,
        "output_tokens": 200,
    }


@pytest.fixture
def sample_extraction_dangling() -> dict:
    return {
        "nodes": [
            {
                "id": "task_drift",
                "type": "task",
                "label": "Drift Detection",
                "source_file": "/papers/p1.pdf",
            },
        ],
        "edges": [
            {
                "source": "technique_phantom",
                "target": "task_drift",
                "relation": "addresses",
                "confidence": "EXTRACTED",
                "confidence_score": 1.0,
            },
            {
                "source": "task_drift",
                "target": "task_drift",
                "relation": "related_to",
                "confidence": "INFERRED",
                "confidence_score": 0.5,
            },
        ],
    }
