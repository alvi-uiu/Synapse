from enum import Enum
import re


SCHEMA_VERSION = 1


class NodeType(str, Enum):
    PAPER = "paper"
    TASK = "task"
    TECHNIQUE = "technique"
    DATASET = "dataset"
    METRIC = "metric"
    RESULT = "result"
    CLAIM = "claim"
    LIMITATION = "limitation"
    CONTRIBUTION = "contribution"
    BASELINE = "baseline"
    CONCEPT = "concept"


class EdgeType(str, Enum):
    PROPOSES = "proposes"
    ADDRESSES = "addresses"
    EVALUATES_ON = "evaluates_on"
    ACHIEVES = "achieves"
    RESULT_ON = "result_on"
    RESULT_USING = "result_using"
    CITES = "cites"
    BUILDS_ON = "builds_on"
    COMPARES_WITH = "compares_with"
    CLAIMS = "claims"
    HAS_LIMITATION = "has_limitation"
    HAS_CONTRIBUTION = "has_contribution"
    RELATED_TO = "related_to"
    SAME_TASK_AS = "same_task_as"


def make_id(node_type: str, label: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")
    return f"{node_type}_{slug}"


NODE_REQUIRED_FIELDS = {
    NodeType.PAPER: ["id", "type", "label", "authors", "year", "venue", "abstract", "source_file"],
    NodeType.TECHNIQUE: ["id", "type", "label", "source_file"],
    NodeType.TASK: ["id", "type", "label", "source_file"],
    NodeType.DATASET: ["id", "type", "label", "source_file"],
    NodeType.METRIC: ["id", "type", "label", "source_file"],
    NodeType.RESULT: ["id", "type", "label", "value", "metric_name", "dataset_name", "source_file"],
    NodeType.CLAIM: ["id", "type", "label", "source_file"],
    NodeType.LIMITATION: ["id", "type", "label", "source_file"],
    NodeType.CONTRIBUTION: ["id", "type", "label", "source_file"],
    NodeType.BASELINE: ["id", "type", "label", "source_file"],
    NodeType.CONCEPT: ["id", "type", "label", "source_file"],
}
