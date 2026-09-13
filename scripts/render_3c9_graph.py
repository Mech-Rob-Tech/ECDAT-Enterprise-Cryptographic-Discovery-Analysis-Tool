from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evidence" / "v0.6" / "3C.9"

NODES = 1000
VISIBLE_HEAD = 8
VISIBLE_TAIL = 8


def make_graph():
    nodes = [f"n{i}" for i in range(NODES)]
    edges = [
        (f"n{i}", f"n{i + 1}")
        for i in range(NODES - 1)
    ]
    return nodes, edges


def write_json(nodes, edges):
    data = {
        "gate": "3C.9",
        "graph_type": "chain",
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": nodes,
        "edges": [
            {"source": source, "target": target}
            for source, target in edges
        ],
    }

    (OUT / "graph.json").write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_dot(nodes, edges):
    lines = [
        "digraph ECDAT_3C9 {",
        '    graph [rankdir=LR, labelloc="t", '
        'label="ECDAT v0.6 — 3C.9 — Complete 1,000-node chain"];',
        '    node [shape=box];',
    ]

    for node in nodes:
        lines.append(f'    "{node}";')

    for source, target in edges:
        lines.append(f'    "{source}" -> "{target}";')

    lines.append("}")

    (OUT / "graph.dot").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def write_overview_dot(nodes):
    head = nodes[:VISIBLE_HEAD]
    tail = nodes[-VISIBLE_TAIL:]

    lines = [
        "digraph ECDAT_3C9_OVERVIEW {",
        '    graph [rankdir=LR, bgcolor="white", '
        'labelloc="t", '
        'label="ECDAT v0.6 — 3C.9 — 1,000-node chain overview"];',
        '    node [shape=box, style="rounded"];',
    ]

    for node in head:
        lines.append(f'    "{node}" [label="{node}"];')

    lines.append(
        '    "collapsed" '
        '[label="⋮\\n984 middle nodes\\ncollapsed", shape=box];'
    )

    for node in tail:
        lines.append(f'    "{node}" [label="{node}"];')

    for left, right in zip(head, head[1:]):
        lines.append(f'    "{left}" -> "{right}";')

    lines.append(f'    "{head[-1]}" -> "collapsed";')

    for left, right in zip(tail, tail[1:]):
        lines.append(f'    "{left}" -> "{right}";')

    lines.append(f'    "collapsed" -> "{tail[0]}";')

    lines.append("}")

    (OUT / "graph_overview.dot").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def render_overview():
    subprocess.run(
        [
            "dot",
            "-Tsvg",
            str(OUT / "graph_overview.dot"),
            "-o",
            str(OUT / "graph_overview.svg"),
        ],
        check=True,
    )

    subprocess.run(
        [
            "dot",
            "-Tpng",
            str(OUT / "graph_overview.dot"),
            "-o",
            str(OUT / "graph_overview.png"),
        ],
        check=True,
    )


def write_manifest():
    files = sorted(
        path
        for path in OUT.iterdir()
        if path.is_file()
        and path.name != "SHA256SUMS"
    )

    lines = []

    for path in files:
        digest = hashlib.sha256(
            path.read_bytes()
        ).hexdigest()

        lines.append(f"{digest}  {path.name}")

    (OUT / "SHA256SUMS").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    nodes, edges = make_graph()

    write_json(nodes, edges)
    write_dot(nodes, edges)
    write_overview_dot(nodes)
    render_overview()
    write_manifest()

    print(f"✓ Evidence written to {OUT}")


if __name__ == "__main__":
    main()
