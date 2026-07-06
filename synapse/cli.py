import json
from pathlib import Path

import click
import networkx as nx
from networkx.readwrite import json_graph
from rich.console import Console

from synapse.analyze import god_nodes, surprising_connections
from synapse.build import build_graph
from synapse.cluster import cluster, score_all
from synapse.dedup import deduplicate_entities
from synapse.ingest import ingest_directory, ingest_paper
from synapse.query import answer_query
from synapse.report import generate_report

NODE_COLORS = {
    "paper": "#4A90D9",
    "task": "#50C878",
    "technique": "#E67E22",
    "dataset": "#9B59B6",
    "metric": "#F1C40F",
    "result": "#E74C3C",
    "claim": "#1ABC9C",
    "limitation": "#E91E63",
    "contribution": "#3498DB",
    "baseline": "#95A5A6",
    "concept": "#7F8C8D",
}

KG_OUT = Path("kg-out")
console = Console()


@click.group()
def cli():
    """Synapse — Research Paper Knowledge Graph"""
    pass


@cli.command()
@click.argument("papers_dir", type=click.Path(exists=True))
def build(papers_dir: str) -> None:
    """Ingest all PDFs/.tex files in PAPERS_DIR and build the knowledge graph."""
    KG_OUT.mkdir(exist_ok=True)
    cache_root = KG_OUT / "cache"
    cache_root.mkdir(exist_ok=True)

    console.log(f"Ingesting papers from: {papers_dir}")
    extraction = ingest_directory(Path(papers_dir), cache_root)

    console.log(
        f"Building graph: {len(extraction['nodes'])} nodes, "
        f"{len(extraction['edges'])} edges"
    )
    G = build_graph(extraction)

    if G.number_of_nodes() == 0:
        console.log("ERROR: Graph is empty. Check that PDFs were parsed correctly.")
        return

    console.log("Deduplicating entities...")
    nodes_list = [data for _, data in G.nodes(data=True)]
    edges_list = [
        {"source": s, "target": t, **d} for s, t, d in G.edges(data=True)
    ]
    deduped_nodes, deduped_edges = deduplicate_entities(
        nodes_list, edges_list, communities={}
    )

    deduped_extraction = {"nodes": deduped_nodes, "edges": deduped_edges}
    G = build_graph(deduped_extraction)

    console.log("Clustering communities...")
    communities = cluster(G)
    nx.set_node_attributes(
        G, {k: v for k, v in communities.items()}, "community"
    )

    graph_data = json_graph.node_link_data(G, edges="links")
    (KG_OUT / "graph.json").write_text(
        json.dumps(graph_data, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    report = generate_report(G, communities, extraction)
    (KG_OUT / "GRAPH_REPORT.md").write_text(report, encoding="utf-8")

    console.log(f"Graph saved to {KG_OUT / 'graph.json'}")
    console.log(f"  Nodes: {G.number_of_nodes()}")
    console.log(f"  Edges: {G.number_of_edges()}")
    console.log(f"  Communities: {len(set(communities.values()))}")
    console.log(
        f"  Token cost: {extraction['input_tokens']:,} in / "
        f"{extraction['output_tokens']:,} out"
    )


@cli.command()
@click.argument("question")
def query(question: str) -> None:
    """Query the knowledge graph with a natural language question."""
    graph_path = KG_OUT / "graph.json"
    if not graph_path.exists():
        console.log(
            "ERROR: No graph found. Run `synapse build <papers_dir>` first."
        )
        return

    data = json.loads(graph_path.read_text(encoding="utf-8"))
    G = json_graph.node_link_graph(data, edges="links")

    console.log(f"\nQuerying: {question}\n")
    answer = answer_query(G, question)
    console.log(answer)


@cli.command()
@click.argument("pdf_path", type=click.Path(exists=True))
def add(pdf_path: str) -> None:
    """Add a single new paper to the existing knowledge graph."""
    graph_path = KG_OUT / "graph.json"
    if not graph_path.exists():
        console.log(
            "ERROR: No existing graph found. Run `synapse build` first."
        )
        return

    cache_root = KG_OUT / "cache"
    cache_root.mkdir(exist_ok=True)

    data = json.loads(graph_path.read_text(encoding="utf-8"))
    G = json_graph.node_link_graph(data, edges="links")

    console.log(f"Adding: {pdf_path}")
    extraction = ingest_paper(Path(pdf_path), cache_root)

    new_G = build_graph(extraction)
    G = nx.compose(G, new_G)

    console.log("Re-clustering...")
    communities = cluster(G)
    nx.set_node_attributes(
        G, {k: v for k, v in communities.items()}, "community"
    )

    graph_data = json_graph.node_link_data(G, edges="links")
    (KG_OUT / "graph.json").write_text(
        json.dumps(graph_data, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    report = generate_report(G, communities)
    (KG_OUT / "GRAPH_REPORT.md").write_text(report, encoding="utf-8")

    console.log(f"Graph updated: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")


@cli.command()
@click.option("--output", "-o", default="kg-out/graph.html", help="Output HTML file path")
def visualize(output: str) -> None:
    """Generate an interactive HTML visualization of the knowledge graph."""
    graph_path = KG_OUT / "graph.json"
    if not graph_path.exists():
        console.log("No graph found. Run `synapse build <papers_dir>` first.")
        return

    from pyvis.network import Network

    data = json.loads(graph_path.read_text(encoding="utf-8"))
    G = json_graph.node_link_graph(data, edges="links")

    net = Network(height="800px", width="100%", directed=True, notebook=False)

    for nid, d in G.nodes(data=True):
        label = d.get("label", nid)
        ntype = d.get("type", "unknown")
        color = NODE_COLORS.get(ntype, "#7F8C8D")
        title = f"<b>{label}</b><br/>Type: {ntype}"
        if d.get("provenance"):
            p = d["provenance"]
            title += f"<br/>Source: p.{p.get('page','?')} §{p.get('section','?')}"
        if d.get("value"):
            title += f"<br/>Value: {d['value']} ({d.get('metric_name','')})"
        net.add_node(nid, label=label, title=title, color=color, size=25 if ntype == "paper" else 20)

    for src, tgt, d in G.edges(data=True):
        relation = d.get("relation", "related_to")
        label = d.get("confidence", "")
        title = f"Relation: {relation}<br/>Confidence: {label}"
        arrow_type = "arrow" if G.is_directed() else ""
        color = "#666"
        net.add_edge(src, tgt, title=title, label=relation, arrows=arrow_type, color=color)

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    net.save_graph(str(output_path))
    console.log(f"Interactive graph saved to {output_path}")
    console.log(f"  Open in browser: file://{output_path.resolve()}")


@cli.command()
def info() -> None:
    """Show current knowledge graph statistics."""
    graph_path = KG_OUT / "graph.json"
    if not graph_path.exists():
        console.log("No graph found. Run `synapse build <papers_dir>` first.")
        return

    data = json.loads(graph_path.read_text(encoding="utf-8"))
    G = json_graph.node_link_graph(data, edges="links")

    console.log("\n[bold]Synapse Knowledge Graph[/bold]\n")
    console.log(f"  Nodes: {G.number_of_nodes()}")
    console.log(f"  Edges: {G.number_of_edges()}")

    from collections import Counter

    types = Counter(d.get("type", "unknown") for _, d in G.nodes(data=True))
    console.log(f"  Types: {dict(types)}")

    communities = nx.get_node_attributes(G, "community")
    if communities:
        n_comms = len(set(communities.values()))
        console.log(f"  Communities: {n_comms}")

    gods = god_nodes(G, top_k=5)
    if gods:
        console.log("\n  Top connected nodes:")
        for g in gods:
            console.log(f"    {g['label']} ({g['type']}, degree {g['degree']})")
