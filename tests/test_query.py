import networkx as nx

from synapse.query import find_task_nodes, get_techniques_for_task


def _make_test_graph() -> nx.DiGraph:
    G = nx.DiGraph()
    G.add_node("task_drift", type="task", label="Drift Detection")
    G.add_node("task_continual", type="task", label="Continual Learning")
    G.add_node("task_classification", type="task", label="Image Classification")
    G.add_node("technique_ewc", type="technique", label="EWC", aliases=["Elastic Weight Consolidation"])
    G.add_node("technique_lwf", type="technique", label="LwF", aliases=["Learning Without Forgetting"])
    G.add_node("result_ewc_acc", type="result", label="EWC Accuracy 87.3%", value=87.3, metric_name="Accuracy", dataset_name="CIFAR-100")
    G.add_node("paper_author", type="paper", label="A Paper on Drift", year=2024, venue="NeurIPS")
    G.add_edge("technique_ewc", "task_drift", relation="addresses", confidence="EXTRACTED")
    G.add_edge("technique_lwf", "task_drift", relation="addresses", confidence="EXTRACTED")
    G.add_edge("technique_ewc", "result_ewc_acc", relation="achieves", confidence="EXTRACTED")
    G.add_edge("paper_author", "technique_ewc", relation="proposes", confidence="EXTRACTED")
    return G


def test_find_task_nodes():
    G = _make_test_graph()
    task_ids = find_task_nodes(G, "drift detection in data streams")
    assert len(task_ids) >= 1
    assert task_ids[0] == "task_drift"


def test_find_task_nodes_no_match():
    G = _make_test_graph()
    task_ids = find_task_nodes(G, "quantum physics")
    assert len(task_ids) == 0


def test_get_techniques_for_task():
    G = _make_test_graph()
    techniques = get_techniques_for_task(G, ["task_drift"])
    assert len(techniques) == 2


def test_get_techniques_with_results():
    G = _make_test_graph()
    techniques = get_techniques_for_task(G, ["task_drift"])
    for t in techniques:
        if t.get("label") == "EWC":
            assert len(t["results"]) == 1
            assert t["results"][0]["value"] == 87.3
            assert len(t["papers"]) == 1
            assert t["papers"][0]["year"] == 2024
