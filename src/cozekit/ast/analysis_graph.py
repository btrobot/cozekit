"""Analysis graph builder — successor to IRBuilder.

Flattens WorkflowAST into AnalysisGraph + ASTIndices.
No lowering to IR types — reuses AST types directly.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .workflow_ast import (
    CanvasAST,
    EdgeAST,
    NodeAST,
    SourceProvenance,
    WorkflowAST,
)
from .indices import ASTIndices, build_ast_indices
from ..types import VARIABLE_NODE_TYPE_ID



@dataclass(frozen=True)
class AnalysisGraph:
    """Flat graph representation built from WorkflowAST.
    
    Successor to WorkflowIR — same flattening semantics, typed over AST.
    """
    nodes: tuple[NodeAST, ...] = ()
    edges: tuple[EdgeAST, ...] = ()
    canvases: tuple[CanvasAST, ...] = ()
    root_canvas_path: tuple[str | int, ...] = ()
    provenance: SourceProvenance = field(default_factory=SourceProvenance)
    versions: dict | None = None
    version_is_valid: bool | None = None
    envelope_type: str | None = None
    _global_var_nodes: frozenset[str] = frozenset()  # node_ids that are global var defs


class AnalysisGraphBuilder:
    """Build AnalysisGraph from WorkflowAST.

    Pure flattening - no lowering to IR types.
    Reuses NodeAST, EdgeAST directly; creates CanvasAST with structural metadata.
    """

    def build(
        self,
        ast: WorkflowAST,
        *,
        versions: dict | None = None,
        version_is_valid: bool | None = None,
        envelope_type: str | None = None,
    ) -> tuple[AnalysisGraph, ASTIndices]:
        """Build AnalysisGraph from AST. Single-pass flat flattening only."""
        all_nodes: list[NodeAST] = []
        all_edges: list[EdgeAST] = []
        all_canvases: list[CanvasAST] = []
        shape_issues_per_canvas: dict[tuple[str | int, ...], set[str]] = {}

        if not ast.canvases:
            flat = AnalysisGraph(
                provenance=ast.provenance,
                versions=versions,
                version_is_valid=version_is_valid,
                envelope_type=envelope_type,
            )
            return flat, build_ast_indices(flat)

        root_canvas = ast.root_canvas
        self._flatten_canvas(
            root_canvas,
            owner_node_id=None,
            parent_canvas_path=None,
            all_nodes=all_nodes,
            all_edges=all_edges,
            all_canvases=all_canvases,
            shape_issues_per_canvas=shape_issues_per_canvas,
        )

        # Compute global var nodes
        global_var_nodes = frozenset(
            n.node_id for n in all_nodes if n.node_type == VARIABLE_NODE_TYPE_ID
        )

        # Finalize canvases with shape issues
        finalized_canvases: list[CanvasAST] = []
        for c in all_canvases:
            issues = shape_issues_per_canvas.get(c.canvas_path, set())
            finalized_canvases.append(CanvasAST(
                canvas_id=c.canvas_id,
                canvas_path=c.canvas_path,
                provenance=c.provenance,
                owner_node_type=c.owner_node_type,
                owner_node_id=c.owner_node_id,
                parent_canvas_path=c.parent_canvas_path,
                raw_node_count=c.raw_node_count,
                shape_is_valid=c.shape_is_valid,
                nested_shape_issues=c.nested_shape_issues,
                non_object_node_count=c.non_object_node_count,
                shape_issues=frozenset(issues),
            ))

        flat = AnalysisGraph(
            root_canvas_path=root_canvas.canvas_path,
            nodes=tuple(all_nodes),
            edges=tuple(all_edges),
            canvases=tuple(finalized_canvases),
            provenance=ast.provenance,
            versions=versions,
            version_is_valid=version_is_valid,
            envelope_type=envelope_type,
            _global_var_nodes=global_var_nodes,
        )

        indices = build_ast_indices(flat)
        return flat, indices

    def _flatten_canvas(
        self,
        canvas: CanvasAST,
        owner_node_id: str | None,
        parent_canvas_path: tuple | None,
        all_nodes: list[NodeAST],
        all_edges: list[EdgeAST],
        all_canvases: list[CanvasAST],
        shape_issues_per_canvas: dict[tuple[str | int, ...], set[str]],
    ) -> None:
        """Flatten a single canvas and all its subcanvases into flat lists."""
        issues: set[str] = set()
        canvas_path = canvas.canvas_path

        # Collect nodes and edges
        for n in canvas.nodes:
            all_nodes.append(n)
            if n.node_type == VARIABLE_NODE_TYPE_ID:
                issues.add(n.node_id)

        for e in canvas.edges:
            all_edges.append(e)

        # Create canvas metadata (no nodes/edges containers)
        all_canvases.append(CanvasAST(
            canvas_id=None,
            canvas_path=canvas_path,
            provenance=canvas.provenance,
            owner_node_id=owner_node_id,
            parent_canvas_path=parent_canvas_path,
            raw_node_count=len(canvas.nodes),
            non_object_node_count=canvas.non_object_node_count,
        ))
        shape_issues_per_canvas[canvas_path] = issues

        # Flatten subcanvases
        for n in canvas.nodes:
            if n.blocks:
                sub_path = canvas_path + (n.node_id,)
                sub_canvas = self._build_subcanvas(n, sub_path, canvas_path)
                self._flatten_canvas(
                    sub_canvas,
                    owner_node_id=n.node_id,
                    parent_canvas_path=canvas_path,
                    all_nodes=all_nodes,
                    all_edges=all_edges,
                    all_canvases=all_canvases,
                    shape_issues_per_canvas=shape_issues_per_canvas,
                )

    def _build_subcanvas(
        self,
        owner_node: NodeAST,
        sub_path: tuple,
        parent_path: tuple,
    ) -> CanvasAST:
        """Synthesize a CanvasAST from a composite node blocks and nested edges."""
        return CanvasAST(
            canvas_path=sub_path,
            provenance=owner_node.provenance,
            nodes=owner_node.blocks,
            edges=owner_node.nested_edges,
        )
