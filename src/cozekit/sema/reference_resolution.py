"""Reference resolution — resolves parameter references to their source symbols.

References in Coze workflow:
- node output refs: source=node, blockId=<node_id>, name=<output_name>
- global variable refs: source=global_variable_app/system/user, name=<var_name>

After IR removal, resolved references live in ResolutionTable (from .resolution_table).
ResolutionTable is populated via put() — no mutation of frozen AST objects.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .symbol_table import SymbolTable, NodeSymbol
from .resolution_table import ResolvedRef, ResolutionTable

if TYPE_CHECKING:
    from ..ast.analysis_graph import AnalysisGraph
    from ..ast.workflow_ast import ParameterAST, RefAST


class ReferenceResolver:
    """Resolves parameter references to their targets.

    P2: Supports optional from_canvas_path for scope-aware resolution.
    When from_canvas_path is provided, only nodes visible from that
    scope are considered valid targets.
    """

    def __init__(self, symbol_table: SymbolTable) -> None:
        self._symtab = symbol_table

    def resolve(self, ref_source: str | None, ref_block_id: str | None,
                ref_name: str | None,
                from_canvas_path: tuple[str | int, ...] | None = None) -> ResolvedRef:
        """Resolve a reference to its target.

        Args:
            ref_source: The source type (e.g. 'node', 'global_variable_app').
            ref_block_id: The block ID being referenced.
            ref_name: The output/variable name.
            from_canvas_path: Optional canvas path for scope-aware resolution.
                When provided, only nodes visible from this scope are valid.
        """
        # When source is None but block_id exists, treat as node output reference
        if ref_source is None:
            if ref_block_id:
                # Implicit node output reference — resolve via global fallback
                target = self._find_node_by_id(ref_block_id)
                if target is not None:
                    return ResolvedRef(
                        source='block-output',
                        block_id=ref_block_id,
                        name=ref_name,
                        target_node_path=target.node_path,
                    )
            return ResolvedRef(source=None, block_id=ref_block_id, name=ref_name, is_unresolved=True)

        # Global variable reference — name-based lookup, empty blockID is valid
        if ref_source.startswith('global_variable'):
            return ResolvedRef(
                source=ref_source,
                block_id=ref_block_id,
                name=ref_name,
                is_global=True,
                is_unresolved=False,
            )

        # Node output reference — find the source node
        if ref_block_id:
            # Scope-aware: check visibility first
            if from_canvas_path is not None:
                if self._symtab.is_visible(from_canvas_path, ref_block_id):
                    # Find the node symbol
                    target = self._find_node_by_id(ref_block_id)
                    if target is not None:
                        return ResolvedRef(
                            source=ref_source,
                            block_id=ref_block_id,
                            name=ref_name,
                            target_node_path=target.node_path,
                        )
                # Not visible from this scope
                return ResolvedRef(
                    source=ref_source,
                    block_id=ref_block_id,
                    name=ref_name,
                    is_unresolved=True,
                )

            # Global fallback: O(1) index lookup (no scope constraint)
            target = self._find_node_by_id(ref_block_id)
            if target is not None:
                return ResolvedRef(
                    source=ref_source,
                    block_id=ref_block_id,
                    name=ref_name,
                    target_node_path=target.node_path,
                )

        return ResolvedRef(
            source=ref_source,
            block_id=ref_block_id,
            name=ref_name,
            is_unresolved=True,
        )

    def _find_node_by_id(self, node_id: str) -> NodeSymbol | None:
        """Find a node symbol by node_id using O(1) index lookup."""
        return self._symtab.lookup_node_by_id(node_id)


def resolve_all_refs(flat: AnalysisGraph, symbol_table: SymbolTable) -> ResolutionTable:
    """Resolve all parameter references and populate a ResolutionTable.

    Returns a ResolutionTable — no mutation of frozen AST objects.
    Iterates flat.nodes — no recursive block traversal needed.
    """
    resolver = ReferenceResolver(symbol_table)
    table = ResolutionTable()

    for node in flat.nodes:
        if node.node_id is None:
            continue
        _resolve_node_refs(node.node_id, node.parameters, resolver, table)

    return table


def _resolve_node_refs(
    node_id: str,
    parameters: tuple,
    resolver: ReferenceResolver,
    table: ResolutionTable,
) -> None:
    """Resolve refs for a single node, populating the ResolutionTable."""
    for idx, param in enumerate(parameters):
        resolved = _resolve_param_refs(param, resolver)
        table.put(node_id, idx, resolved)


def _resolve_param_refs(param: ParameterAST, resolver: ReferenceResolver) -> ResolvedRef:
    """Resolve a single parameter's references."""
    if param.input_ref:
        # Skip literal types — they don't need reference resolution
        if param.input_ref.ref_type == 'literal':
            return ResolvedRef()
        # Prefer explicit name; fall back to last path segment
        effective_name = param.input_ref.name
        if not effective_name and param.input_ref.path:
            effective_name = param.input_ref.path[-1]
        return resolver.resolve(param.input_ref.source, param.input_ref.block_id, effective_name)
    return ResolvedRef()
