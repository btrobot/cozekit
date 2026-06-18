"""Symbol table — registers and resolves all named entities.

The symbol table is the single owner of "what exists" in the workflow.
Passes query it through SemaQueryAuthority, never scan IR directly.
P2: Integrates ScopeTree for hierarchical scope-aware queries.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..ast.workflow_ast import CanvasAST, NodeAST
from ..ast.analysis_graph import AnalysisGraph
from ..ast.indices import ASTIndices
from .scope_tree import ScopeTree


@dataclass(frozen=True)
class NodeSymbol:
    """Symbol table entry for a node."""
    node: NodeAST
    canvas_path: tuple[str | int, ...]
    node_path: tuple[str | int, ...]


@dataclass(frozen=True)
class CanvasSymbol:
    """Symbol table entry for a canvas."""
    canvas: CanvasAST
    canvas_path: tuple[str | int, ...]
    parent_canvas_path: tuple[str | int, ...] | None
    owner_node_id: str | None


@dataclass(frozen=True)
class ParameterSymbol:
    """Symbol table entry for a parameter."""
    name: str | None
    node_path: tuple[str | int, ...]
    declared_type: str | None = None
    ref_source: str | None = None
    ref_block_id: str | None = None


class SymbolTable:
    """Build and query the workflow symbol table.

    Constructed from AnalysisGraph + ASTIndices. Provides O(1) lookup
    by node_id, canvas_path, and scope traversal.
    P2: Embeds ScopeTree for hierarchical visibility queries.
    """

    def __init__(self, flat: AnalysisGraph, indices: ASTIndices) -> None:
        self._flat = flat
        self._indices = indices
        self._node_symbols: dict[tuple[str | int, ...], NodeSymbol] = {}
        self._node_id_to_symbol: dict[str, NodeSymbol] = {}
        self._canvas_symbols: dict[tuple[str | int, ...], CanvasSymbol] = {}
        self._parameter_symbols: list[ParameterSymbol] = []
        self._nodes_by_canvas: dict[tuple[str | int, ...], list[NodeSymbol]] = {}
        self._build()
        # Build canvas_path -> node_ids mapping for ScopeTree
        canvas_node_ids: dict[tuple[str | int, ...], list[str]] = {}
        for ns in self._node_symbols.values():
            canvas_node_ids.setdefault(ns.canvas_path, []).append(ns.node.node_id)
        self._scope_tree = ScopeTree(flat, canvas_node_ids)

    def _build(self) -> None:
        # Register canvas symbols from CanvasAST metadata
        for canvas in self._flat.canvases:
            cp = canvas.canvas_path
            parent = canvas.parent_canvas_path
            owner = canvas.owner_node_id
            cs = CanvasSymbol(canvas=canvas, canvas_path=cp, parent_canvas_path=parent, owner_node_id=owner)
            self._canvas_symbols[cp] = cs

        # Register node symbols from flat nodes
        for node in self._flat.nodes:
            cp = node.canvas_path
            np = cp + (node.node_id,)
            ns = NodeSymbol(node=node, canvas_path=cp, node_path=np)
            self._node_symbols[np] = ns
            self._node_id_to_symbol[node.node_id] = ns
            self._nodes_by_canvas.setdefault(cp, []).append(ns)
            for param in node.parameters:
                ps = ParameterSymbol(
                    name=param.name,
                    node_path=np,
                    declared_type=param.left_type,
                    ref_source=param.input_ref.source if param.input_ref else None,
                    ref_block_id=param.input_ref.block_id if param.input_ref else None,
                )
                self._parameter_symbols.append(ps)

    # ── scope access ────────────────────────────────────────────

    @property
    def scope_tree(self) -> ScopeTree:
        """The ScopeTree built from the workflow flat graph."""
        return self._scope_tree

    # ── counts ──────────────────────────────────────────────────

    def node_count(self) -> int:
        return len(self._node_symbols)

    def canvas_count(self) -> int:
        return len(self._canvas_symbols)

    def parameter_count(self) -> int:
        return len(self._parameter_symbols)

    # ── lookups ─────────────────────────────────────────────────

    def lookup_node(self, node_path: tuple[str | int, ...]) -> NodeSymbol | None:
        return self._node_symbols.get(node_path)

    def lookup_canvas(self, canvas_path: tuple[str | int, ...]) -> CanvasSymbol | None:
        return self._canvas_symbols.get(canvas_path)

    def nodes_in_canvas(self, canvas_path: tuple[str | int, ...]) -> tuple[NodeSymbol, ...]:
        return tuple(self._nodes_by_canvas.get(canvas_path, []))

    def all_node_symbols(self) -> tuple[NodeSymbol, ...]:
        return tuple(self._node_symbols.values())

    def all_canvas_symbols(self) -> tuple[CanvasSymbol, ...]:
        return tuple(self._canvas_symbols.values())

    def all_parameter_symbols(self) -> tuple[ParameterSymbol, ...]:
        return tuple(self._parameter_symbols)

    def lookup_node_by_id(self, node_id: str) -> NodeSymbol | None:
        """Find a node symbol by node_id — O(1) via dict index."""
        return self._node_id_to_symbol.get(node_id)

    def is_global_var_def(self, node_id: str) -> bool:
        """Check whether node_id is a global variable definition node."""
        return node_id in self._flat._global_var_nodes

    # ── edge / node queries (public API for query_authority) ────

    def edge_source_targets(self, node_id: str) -> tuple:
        """Return all edges where node_id is the source."""
        return self._indices.edges_by_source.get(node_id, ())

    def edge_target_sources(self, node_id: str) -> tuple:
        """Return all edges where node_id is the target."""
        return self._indices.edges_by_target.get(node_id, ())

    def all_node_ids(self) -> frozenset[str]:
        """Return all node IDs as a frozenset."""
        return frozenset(self._node_id_to_symbol.keys())

    def node_edges(self, node_id: str) -> tuple:
        """Return all edges where node_id is source or target."""
        outgoing = self._indices.edges_by_source.get(node_id, ())
        incoming = self._indices.edges_by_target.get(node_id, ())
        return outgoing + incoming

    def has_outgoing_edges(self, node_id: str) -> bool:
        """Check whether node_id has any outgoing edges."""
        return bool(self._indices.edges_by_source.get(node_id))

    def has_incoming_edges(self, node_id: str) -> bool:
        """Check whether node_id has any incoming edges."""
        return bool(self._indices.edges_by_target.get(node_id))

    def nodes_by_canvas_for_canvas(self, canvas_path_key: str) -> tuple:
        """Return nodes tuple from indices for the given canvas path key."""
        return self._indices.nodes_by_canvas.get(canvas_path_key, ())

    def edges_by_canvas_for_canvas(self, canvas_path_key: str) -> tuple:
        """Return edges tuple from indices for the given canvas path key."""
        return self._indices.edges_by_canvas.get(canvas_path_key, ())

    # ── scope-aware queries (P2) ────────────────────────────────

    def symbols_in_scope(self, canvas_path: tuple[str | int, ...]) -> tuple[NodeSymbol, ...]:
        """Return all symbols visible from canvas_path (current + ancestors).

        Uses ScopeTree to walk the scope chain and collect node symbols
        from each visible scope.
        """
        visible_ids = self._scope_tree.visible_symbols(canvas_path)
        result: list[NodeSymbol] = []
        for node_id in visible_ids:
            ns = self._node_id_to_symbol.get(node_id)
            if ns is not None:
                result.append(ns)
        return tuple(result)

    def symbols_defined_in(self, canvas_path: tuple[str | int, ...]) -> tuple[NodeSymbol, ...]:
        """Return only symbols directly defined in canvas_path (no ancestors)."""
        return tuple(self._nodes_by_canvas.get(canvas_path, []))

    def is_visible(self, from_canvas_path: tuple[str | int, ...],
                   target_node_id: str) -> bool:
        """Check whether target_node_id is visible from from_canvas_path."""
        return self._scope_tree.is_visible(from_canvas_path, target_node_id)

    def workflow_version_is_valid(self) -> bool | None:
        """Return version validity from flat graph."""
        return self._flat.version_is_valid

    def workflow_envelope_type(self) -> str | None:
        """Return envelope type from flat graph."""
        return self._flat.envelope_type
