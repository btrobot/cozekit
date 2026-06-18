"""AST indices — O(1) lookup tables over AnalysisGraph.

Successor to WorkflowIndices — same logic, typed over AST types.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .workflow_ast import CanvasAST, EdgeAST, NodeAST

if TYPE_CHECKING:
    from .analysis_graph import AnalysisGraph


@dataclass(frozen=True)
class ASTIndices:
    """Index structures for O(1) query over the flat graph.

    node_by_id: O(1) single-node lookup by node_id (NOT tuple-valued).
    edges_by_source / edges_by_target: adjacency lists.
    nodes_by_canvas / edges_by_canvas: canvas_path string -> items in that canvas.
    """
    node_by_id: dict[str, NodeAST] = field(default_factory=dict)
    canvases_by_id: dict[str, CanvasAST] = field(default_factory=dict)
    edges_by_source: dict[str, tuple[EdgeAST, ...]] = field(default_factory=dict)
    edges_by_target: dict[str, tuple[EdgeAST, ...]] = field(default_factory=dict)
    nodes_by_canvas: dict[str, tuple[NodeAST, ...]] = field(default_factory=dict)
    edges_by_canvas: dict[str, tuple[EdgeAST, ...]] = field(default_factory=dict)
    node_count: int = 0
    edge_count: int = 0
    canvas_count: int = 0
    canvas_by_path: dict[tuple, CanvasAST] = field(default_factory=dict)
    owner_node_by_canvas_path: dict[tuple, str] = field(default_factory=dict)
    subcanvas_path_by_node_id: dict[str, tuple] = field(default_factory=dict)
    parent_canvas_path_map: dict[tuple, tuple] = field(default_factory=dict)


def build_ast_indices(flat: AnalysisGraph) -> ASTIndices:
    """Build index structures from a AnalysisGraph.

    Takes flat.nodes and flat.edges directly - no canvas tree traversal needed.
    """
    node_by_id: dict[str, NodeAST] = {}
    canvases_by_id: dict[str, CanvasAST] = {}
    edges_by_source: dict[str, list[EdgeAST]] = {}
    edges_by_target: dict[str, list[EdgeAST]] = {}
    nodes_by_canvas: dict[str, list[NodeAST]] = {}
    edges_by_canvas: dict[str, list[EdgeAST]] = {}
    canvas_by_path: dict[tuple, CanvasAST] = {}
    owner_node_by_canvas_path: dict[tuple, str] = {}
    subcanvas_path_by_node_id: dict[str, tuple] = {}
    parent_canvas_path_map: dict[tuple, tuple] = {}

    # Index canvases
    for canvas in flat.canvases:
        cid = canvas.canvas_id or ""
        canvases_by_id[cid] = canvas
        canvas_by_path[canvas.canvas_path] = canvas
        if canvas.owner_node_id:
            owner_node_by_canvas_path[canvas.canvas_path] = canvas.owner_node_id
            subcanvas_path_by_node_id[canvas.owner_node_id] = canvas.canvas_path
        if canvas.parent_canvas_path is not None:
            parent_canvas_path_map[canvas.canvas_path] = canvas.parent_canvas_path

    # Index nodes from flat tuple
    for node in flat.nodes:
        node_by_id[node.node_id] = node
        cp = str(node.canvas_path)
        if cp not in nodes_by_canvas:
            nodes_by_canvas[cp] = []
        nodes_by_canvas[cp].append(node)

    # Index edges from flat tuple
    for edge in flat.edges:
        sid = edge.source_node_id
        tid = edge.target_node_id
        edges_by_source.setdefault(sid, []).append(edge)
        edges_by_target.setdefault(tid, []).append(edge)
        ep = str(edge.canvas_path)
        if ep not in edges_by_canvas:
            edges_by_canvas[ep] = []
        edges_by_canvas[ep].append(edge)

    return ASTIndices(
        node_by_id=node_by_id,
        canvases_by_id=canvases_by_id,
        edges_by_source={k: tuple(v) for k, v in edges_by_source.items()},
        edges_by_target={k: tuple(v) for k, v in edges_by_target.items()},
        nodes_by_canvas={k: tuple(v) for k, v in nodes_by_canvas.items()},
        edges_by_canvas={k: tuple(v) for k, v in edges_by_canvas.items()},
        node_count=len(flat.nodes),
        edge_count=len(flat.edges),
        canvas_count=len(canvases_by_id),
        canvas_by_path=canvas_by_path,
        owner_node_by_canvas_path=owner_node_by_canvas_path,
        subcanvas_path_by_node_id=subcanvas_path_by_node_id,
        parent_canvas_path_map=parent_canvas_path_map,
    )
