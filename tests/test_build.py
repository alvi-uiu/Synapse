from synapse.build import build_graph, merge_graphs
from synapse.schema import NodeType


def test_build_graph(sample_extraction):
    G = build_graph(sample_extraction)
    assert G.is_directed()
    assert G.number_of_nodes() == 4
    assert G.number_of_edges() == 2


def test_build_graph_empty():
    G = build_graph({"nodes": [], "edges": []})
    assert G.number_of_nodes() == 0
    assert G.number_of_edges() == 0


def test_dangling_edges_pruned(sample_extraction_dangling):
    G = build_graph(sample_extraction_dangling)
    assert G.number_of_nodes() == 1
    assert G.number_of_edges() == 0


def test_self_loop_removed(sample_extraction_dangling):
    G = build_graph(sample_extraction_dangling)
    edges = list(G.edges())
    assert ("task_drift", "task_drift") not in edges


def test_node_type_fallback():
    extraction = {
        "nodes": [
            {"id": "weird_node", "type": "alien_invasion", "label": "Alien"},
        ],
        "edges": [],
    }
    G = build_graph(extraction)
    assert G.nodes["weird_node"]["type"] == "concept"


def test_node_without_id_skipped():
    extraction = {
        "nodes": [
            {"id": "", "type": "task", "label": "Ghost"},
            {"id": "real_node", "type": "task", "label": "Real"},
        ],
        "edges": [],
    }
    G = build_graph(extraction)
    assert G.number_of_nodes() == 1


def test_merge_graphs(sample_extraction):
    G1 = build_graph(sample_extraction)

    extraction2 = {
        "nodes": [
            {
                "id": "task_drift_detection",
                "type": "task",
                "label": "Drift Detection",
                "source_file": "/papers/paper2.pdf",
            },
            {
                "id": "technique_lwf",
                "type": "technique",
                "label": "Learning Without Forgetting",
                "aliases": ["LwF"],
                "source_file": "/papers/paper2.pdf",
            },
        ],
        "edges": [
            {
                "source": "paper_author2_2024_title2",
                "target": "task_drift_detection",
                "relation": "addresses",
                "confidence": "EXTRACTED",
                "confidence_score": 1.0,
            },
            {
                "source": "technique_lwf",
                "target": "task_drift_detection",
                "relation": "addresses",
                "confidence": "EXTRACTED",
                "confidence_score": 1.0,
            },
        ],
    }
    G2 = build_graph(extraction2)
    merged = merge_graphs([G1, G2])
    assert merged.number_of_nodes() == 5
    task_node = merged.nodes["task_drift_detection"]
    assert task_node is not None
