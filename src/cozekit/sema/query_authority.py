"""Sema query authority — the pass-facing query interface.

This is the ONLY surface passes use to access semantic information.
Dataclasses and concrete implementation are co-located here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .symbol_table import SymbolTable
from .type_system import TypeFact, infer_type, canonicalize_type, TypeCategory, CompatibilityState, ParameterTypeFact, build_parameter_type_facts, resolve_ref_type, check_compatibility
from .reference_resolution import ReferenceResolver
from .resolution_table import ResolutionTable, ResolvedRef

from ..ast.workflow_ast import NodeAST

if TYPE_CHECKING:
    from ..ast.workflow_ast import NodeAST, EdgeAST


@dataclass(frozen=True)
class SymbolInfo:
    """Symbol table entry for a registered entity."""
    name: str
    kind: str  # 'node', 'canvas', 'parameter', 'variable'
    path: tuple[str | int, ...]
    node_type: str | None = None


@dataclass(frozen=True)
class TypeInfo:
    """Type information for a parameter or value."""
    category: str  # 'scalar', 'object', 'list', 'unknown'
    declared_type: str | None = None
    item_type: str | None = None


@dataclass(frozen=True)
class ScopeInfo:
    """Scope information for a canvas."""
    scope_id: str
    scope_kind: str  # 'root', 'loop', 'batch', 'if', 'block'
    canvas_path: tuple[str | int, ...]
    parent_canvas_path: tuple[str | int, ...] | None
    child_canvas_paths: tuple[tuple[str | int, ...], ...]


@dataclass(frozen=True)
class CanvasView:
    """Canvas information for pass iteration.

    Nodes and edges are populated from ASTIndices.
    shape_issues carries any shape diagnostics from CanvasAST metadata.
    """
    canvas_path: tuple[str | int, ...]
    canvas_id: str | None = None
    nodes: tuple[NodeAST, ...] = ()
    edges: tuple[EdgeAST, ...] = ()
    owner_node_id: str | None = None
    parent_canvas_path: tuple[str | int, ...] | None = None
    non_object_node_count: int = 0
    raw_node_count: int = 0
    shape_issues: frozenset[str] = frozenset()


class WorkflowSemaQueryAuthority:
    """Concrete implementation of the pass-facing sema query interface."""

    def __init__(self, symbol_table: SymbolTable,
                 resolution_table: ResolutionTable | None = None) -> None:
        self._symtab = symbol_table
        self._ref_resolver = ReferenceResolver(symbol_table)
        self._resolution_table = resolution_table or ResolutionTable()

    def lookup_symbol(self, name: str) -> SymbolInfo | None:
        """Look up a symbol by node_id across all canvases."""
        ns = self._symtab.lookup_node_by_id(name)
        if ns is not None:
            return SymbolInfo(
                name=name,
                kind='node',
                path=ns.node_path,
                node_type=ns.node.node_type,
            )
        return None

    def lookup_node_by_id(self, node_id: str) -> tuple:
        """Return the NodeSymbol for node_id via O(1) lookup."""
        ns = self._symtab.lookup_node_by_id(node_id)
        if ns is not None:
            return (ns,)
        return ()

    def symbols_in_scope(self, scope_path: tuple[str | int, ...]) -> tuple[SymbolInfo, ...]:
        """Return all symbols visible from a given canvas scope."""
        result = []
        for node_sym in self._symtab.symbols_in_scope(scope_path):
            result.append(SymbolInfo(
                name=node_sym.node.node_id,
                kind='node',
                path=node_sym.node_path,
                node_type=node_sym.node.node_type,
            ))
        return tuple(result)

    def type_of(self, path: tuple[str | int, ...]) -> TypeInfo | None:
        """Get type info for a symbol at a given path."""
        node_sym = self._symtab.lookup_node(path)
        if node_sym is None:
            return None
        type_fact = infer_type(node_sym.node.node_type)
        return TypeInfo(
            category=type_fact.category.value,
            declared_type=type_fact.declared_type,
            item_type=type_fact.item_type,
        )

    def resolve_ref(self, ref_source: str, ref_name: str) -> SymbolInfo | None:
        """Resolve a reference to its target symbol."""
        resolved = self._ref_resolver.resolve(ref_source, None, ref_name)
        if resolved.target_node_path:
            ns = self._symtab.lookup_node(resolved.target_node_path)
            if ns is not None:
                return SymbolInfo(
                    name=ns.node.node_id,
                    kind='node',
                    path=ns.node_path,
                    node_type=ns.node.node_type,
                )
        if resolved.is_global:
            return SymbolInfo(
                name=ref_name or '',
                kind='variable',
                path=(),
            )
        return None

    def resolve_full_ref(self, ref_source: str | None, ref_block_id: str | None,
                         ref_name: str | None,
                         from_canvas_path: tuple[str | int, ...] | None = None) -> ResolvedRef:
        """Full reference resolution with optional scope awareness."""
        return self._ref_resolver.resolve(ref_source, ref_block_id, ref_name,
                                          from_canvas_path=from_canvas_path)

    def resolved_ref_for(self, node_id: str, param_index: int) -> ResolvedRef | None:
        """Look up a resolved reference from the ResolutionTable."""
        return self._resolution_table.get(node_id, param_index)

    def is_global_var_def(self, node_id: str) -> bool:
        """Check whether node_id is a global variable definition node."""
        return self._symtab.is_global_var_def(node_id)

    def node_by_id(self, node_id: str) -> NodeAST | None:
        """Look up a NodeAST by node_id."""
        ns = self._symtab.lookup_node_by_id(node_id)
        return ns.node if ns is not None else None

    def all_node_ids(self) -> frozenset[str]:
        """Return all node IDs as a frozenset."""
        return self._symtab.all_node_ids()

    def parameter_type_facts(self, node_path: tuple[str | int, ...]) -> tuple[ParameterTypeFact, ...]:
        """Return type facts for all parameters of a node."""
        node_sym = self._symtab.lookup_node(node_path)
        if node_sym is None:
            return ()
        facts = []
        for param in node_sym.node.parameters:
            facts.append(build_parameter_type_facts(param, symbol_table=self._symtab))
        return tuple(facts)

    def build_type_fact_for_param(self, param) -> ParameterTypeFact:
        """Build a ParameterTypeFact for a single parameter — public API."""
        return build_parameter_type_facts(param, symbol_table=self._symtab)

    def canvases(self) -> tuple[CanvasView, ...]:
        """Return CanvasView for all canvases."""
        result = []
        for cs in self._symtab.all_canvas_symbols():
            cp = cs.canvas_path
            nodes_in = self._symtab.nodes_in_canvas(cp)
            canvas_key = str(cp)
            edges_tuple = self._symtab.edges_by_canvas_for_canvas(canvas_key)
            result.append(CanvasView(
                canvas_path=cp,
                canvas_id=cs.canvas.canvas_id,
                nodes=tuple(ns.node for ns in nodes_in),
                edges=edges_tuple,
                owner_node_id=cs.owner_node_id,
                parent_canvas_path=cs.parent_canvas_path,
                non_object_node_count=cs.canvas.non_object_node_count,
                raw_node_count=cs.canvas.raw_node_count,
                shape_issues=cs.canvas.shape_issues,
            ))
        return tuple(result)

    def iter_canvas_nodes(self):
        "Yield (canvas, node) tuples across all canvases."
        for canvas in self.canvases():
            for node in canvas.nodes:
                yield canvas, node

    def canvas_for_node(self, node_id: str) -> CanvasView | None:
        """Return the CanvasView containing a given node."""
        ns = self._symtab.lookup_node_by_id(node_id)
        if ns is None:
            return None
        cs = self._symtab.lookup_canvas(ns.canvas_path)
        if cs is None:
            return None
        nodes_in = self._symtab.nodes_in_canvas(ns.canvas_path)
        canvas_key = str(ns.canvas_path)
        edges_tuple = self._symtab.edges_by_canvas_for_canvas(canvas_key)
        return CanvasView(
            canvas_path=ns.canvas_path,
            canvas_id=cs.canvas.canvas_id,
            nodes=tuple(n.node for n in nodes_in),
            edges=edges_tuple,
            owner_node_id=cs.owner_node_id,
            parent_canvas_path=cs.parent_canvas_path,
            non_object_node_count=cs.canvas.non_object_node_count,
            raw_node_count=cs.canvas.raw_node_count,
            shape_issues=cs.canvas.shape_issues,
        )

    def workflow_version_is_valid(self) -> bool | None:
        """Return version validity."""
        return self._symtab.workflow_version_is_valid()

    def workflow_envelope_type(self) -> str | None:
        """Return envelope type."""
        return self._symtab.workflow_envelope_type()

    def edge_source_targets(self, node_id: str) -> tuple:
        """Return all edges where node_id is the source."""
        return self._symtab.edge_source_targets(node_id)

    def edge_target_sources(self, node_id: str) -> tuple:
        """Return all edges where node_id is the target."""
        return self._symtab.edge_target_sources(node_id)

    def has_outgoing_edges(self, node_id: str) -> bool:
        """Check whether node_id has any outgoing edges."""
        return self._symtab.has_outgoing_edges(node_id)

    def has_incoming_edges(self, node_id: str) -> bool:
        """Check whether node_id has any incoming edges."""
        return self._symtab.has_incoming_edges(node_id)

    def isolated_node_ids(self, canvas_path: tuple[str | int, ...] = ()) -> tuple[str, ...]:
        """Return node IDs that have no incoming or outgoing edges.

        Excludes start (type 1), end (type 2), and comment (type 31) nodes.
        """
        result: list[str] = []
        for ns in self._symtab.nodes_in_canvas(canvas_path):
            nid = ns.node.node_id
            ntype = ns.node.node_type
            if ntype in ('1', '2', '31'):
                continue
            if not self._symtab.has_outgoing_edges(nid) and not self._symtab.has_incoming_edges(nid):
                result.append(nid)
        return tuple(result)
