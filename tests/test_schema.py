from synapse.schema import NodeType, EdgeType, make_id, NODE_REQUIRED_FIELDS


def test_node_types():
    assert NodeType.PAPER.value == "paper"
    assert NodeType.TECHNIQUE.value == "technique"
    assert NodeType.TASK.value == "task"
    assert NodeType.DATASET.value == "dataset"
    assert NodeType.RESULT.value == "result"
    assert NodeType.CLAIM.value == "claim"
    assert len(NodeType) == 11


def test_edge_types():
    assert EdgeType.PROPOSES.value == "proposes"
    assert EdgeType.ADDRESSES.value == "addresses"
    assert EdgeType.CITES.value == "cites"
    assert len(EdgeType) == 14


def test_make_id():
    assert make_id("technique", "Elastic Weight Consolidation") == "technique_elastic_weight_consolidation"
    assert make_id("task", "Drift Detection!") == "task_drift_detection"
    assert make_id("dataset", "CIFAR-100") == "dataset_cifar_100"


def test_make_id_empty():
    assert make_id("paper", "") == "paper_"


def test_required_fields_exist():
    for ntype in NodeType:
        assert ntype in NODE_REQUIRED_FIELDS
        assert "id" in NODE_REQUIRED_FIELDS[ntype]
        assert "type" in NODE_REQUIRED_FIELDS[ntype]
        assert "label" in NODE_REQUIRED_FIELDS[ntype]
