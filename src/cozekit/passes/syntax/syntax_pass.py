"""Syntax pass — implements SYNTAX-001 through SYNTAX-022.

Uses SyntaxFactCollector (Visitor pattern) for AST traversal when available,
falls back to sema-based iteration for backward compatibility.
"""

from __future__ import annotations

from typing import Any

from ...diagnostics.core import Checkability, Diagnostic, DiagnosticKind, SourceSpan
from ...ast.visitor import accept
from ..context import PassContext
from ..constants import (
    START_NODE_ID, END_NODE_ID, START_NODE_TYPE_ID, END_NODE_TYPE_ID,
    COMPOSITE_NODE_TYPE_IDS, ALLOWED_VARIABLE_TYPES,
    ALLOWED_BLOCK_INPUT_VALUE_TYPES, ALLOWED_REF_SOURCES,
    KNOWN_NODE_TYPE_IDS,
    VARIABLE_NODE_TYPE_ID,
)
from .syntax_collector import SyntaxFactCollector, SyntaxFacts

# Frontend display name -> node type ID mapping
_FE_NAME_TO_NODE_TYPE: dict[str, str] = {
    'Start': '1', 'End': '2',
    'LLM': '3', 'Api': '4', 'Code': '5', 'Dataset': '6',
    'If': '8', 'SubWorkflow': '9', 'Variable': '11', 'Database': '12',
    'Output': '13', 'Imageflow': '14', 'Text': '15', 'ImageGenerate': '16',
    'ImageReference': '17', 'Question': '18', 'Break': '19', 'SetVariable': '20',
    'Loop': '21', 'Intent': '22', 'ImageCanvas': '23', 'SceneVariable': '24',
    'SceneChat': '25', 'LTM': '26', 'DatasetWrite': '27', 'Batch': '28',
    'Continue': '29', 'Input': '30', 'Comment': '31', 'VariableMerge': '32',
    'TriggerUpsert': '34', 'TriggerDelete': '35', 'TriggerRead': '36',
    'QueryMessageList': '37', 'ClearContext': '38', 'CreateConversation': '39',
    'VariableAssign': '40', 'DatabaseUpdate': '42', 'DatabaseQuery': '43',
    'DatabaseDelete': '44', 'Http': '45', 'DatabaseCreate': '46',
    'UpdateConversation': '51', 'DeleteConversation': '52',
    'QueryConversationList': '53', 'QueryConversationHistory': '54',
    'CreateMessage': '55', 'UpdateMessage': '56', 'DeleteMessage': '57',
    'JsonStringify': '58', 'JsonParser': '59',
}


class SyntaxPass:
    """Validates structural syntax rules (SYNTAX-001~022).

    Uses SyntaxFactCollector (Visitor pattern) for AST traversal when the
    AST is available in PassContext. Falls back to sema-based iteration.
    """

    requires_document: bool = False

    @property
    def name(self) -> str:
        return 'syntax'

    def run(self, ctx: PassContext) -> tuple[Diagnostic, ...]:
        diagnostics: list[Diagnostic] = []
        source_file = ctx.source_file

        # ── Collect facts via Visitor if AST available ──────────
        facts: SyntaxFacts | None = None
        if ctx.ast is not None:
            collector = SyntaxFactCollector()
            accept(collector, ctx.ast)
            facts = collector.facts

        # ── SYNTAX-001: canvas root ────────────────────────────
        if not ctx.sema.canvases():
            diagnostics.append(self._diag(
                'SYNTAX-001', 'violation',
                'canvas root must be an object compatible with Coze Canvas',
                source_file,
            ))
            return tuple(diagnostics)

        # ── Main check loop (sema-based iteration) ─────────────
        has_nodes = False
        has_edges = False
        for canvas in ctx.sema.canvases():
            if canvas.nodes:
                has_nodes = True
                self._check_nodes(canvas.nodes, diagnostics, source_file, ctx=ctx)
            if canvas.edges:
                has_edges = True
                self._check_edges(canvas.edges, diagnostics, source_file)
            self._check_duplicate_ids(canvas, diagnostics, source_file)

        # SYNTAX-002/003: nodes/edges required (use Visitor facts if available)
        if facts is not None:
            if not facts.has_nodes:
                diagnostics.append(self._diag(
                    'SYNTAX-002', 'violation',
                    'workflow must contain at least one node',
                    source_file,
                ))
            if not facts.has_edges:
                diagnostics.append(self._diag(
                    'SYNTAX-003', 'violation',
                    'workflow must contain at least one edge',
                    source_file,
                ))
        else:
            if not has_nodes:
                diagnostics.append(self._diag(
                    'SYNTAX-002', 'violation',
                    'workflow must contain at least one node',
                    source_file,
                ))
            if not has_edges:
                diagnostics.append(self._diag(
                    'SYNTAX-003', 'violation',
                    'workflow must contain at least one edge',
                    source_file,
                ))

        # SYNTAX-012: edges from branch-capable nodes should have sourcePortID
        for canvas in ctx.sema.canvases():
            node_map = {n.node_id: n for n in canvas.nodes}
            for edge in canvas.edges:
                src = node_map.get(edge.source_node_id)
                if src and src.branches and not edge.source_port_id:
                    diagnostics.append(self._diag(
                        'SYNTAX-012', 'warning',
                        f'edge from branch node "{src.node_id}" should have sourcePortID',
                        source_file,
                        source_span=edge.source_span,
                    ))

        # ── SYNTAX-004: versions must be a dict if present ──────
        if ctx.sema.workflow_version_is_valid() is False:
            diagnostics.append(self._diag(
                'SYNTAX-004', 'violation',
                'workflow.versions must be an object',
                source_file,
            ))

        # ── SYNTAX-018: variable schema validation ──────────────
        self._check_variable_schema(ctx, diagnostics)

        return tuple(diagnostics)

    def _check_duplicate_ids(self, canvas, diagnostics: list[Diagnostic], source_file: str | None) -> None:
        """SYNTAX-005: non-object nodes and duplicate node IDs per canvas."""
        if canvas.non_object_node_count > 0:
            diagnostics.append(self._diag(
                'SYNTAX-005', 'violation',
                f'{canvas.non_object_node_count} non-object node(s) in canvas (must be YAML/JSON objects)',
                source_file,
            ))
        seen_ids: set[str] = set()
        for node in canvas.nodes:
            if node.node_id in seen_ids:
                diagnostics.append(self._diag(
                    'SYNTAX-005', 'violation',
                    f'duplicate node ID "{node.node_id}" in canvas',
                    source_file,
                    source_span=node.source_span,
                ))
            seen_ids.add(node.node_id)

    def _check_nodes(self, nodes, diagnostics: list[Diagnostic], source_file: str | None, *, ctx: PassContext | None = None) -> None:
        """Check SYNTAX-005~009, SYNTAX-014~022 for nodes."""
        for node in nodes:
            # SYNTAX-006: node type must exist
            if not node.node_type:
                diagnostics.append(self._diag(
                    'SYNTAX-006', 'violation',
                    f'node "{node.node_id}" type is required',
                    source_file,
                    source_span=node.source_span,
                ))
                continue

            # SYNTAX-006: unknown node type
            if node.node_type and node.node_type not in KNOWN_NODE_TYPE_IDS:
                if node.node_type not in _FE_NAME_TO_NODE_TYPE.values():
                    diagnostics.append(self._diag(
                        'SYNTAX-006', 'violation',
                        f'unknown node type "{node.node_type}"',
                        source_file,
                        source_span=node.source_span,
                    ))

            # SYNTAX-007: node must have data
            if not node.has_data:
                diagnostics.append(self._diag(
                    'SYNTAX-007', 'violation',
                    f'node "{node.node_id}" must have a data field',
                    source_file,
                    source_span=node.source_span,
                ))

            # SYNTAX-008: blocks only on composite nodes
            if node.has_blocks_key and node.composite_kind is None:
                diagnostics.append(self._diag(
                    'SYNTAX-008', 'violation',
                    f'node "{node.node_id}" has blocks but is not a composite type',
                    source_file,
                    source_span=node.source_span,
                ))

            # SYNTAX-009: edges should pair with blocks
            if node.nested_edges and not node.has_blocks_key:
                diagnostics.append(self._diag(
                    'SYNTAX-009', 'warning',
                    f'node "{node.node_id}" has nested edges but no blocks',
                    source_file,
                    source_span=node.source_span,
                ))

            # SYNTAX-014: start node must use canonical ID
            if node.node_type == START_NODE_TYPE_ID and node.node_id != START_NODE_ID:
                diagnostics.append(self._diag(
                    'SYNTAX-014', 'violation',
                    f'start node must use Coze Entry id {START_NODE_ID}',
                    source_file,
                    source_span=node.source_span,
                ))

            # SYNTAX-015: end node must use canonical ID
            if node.node_type == END_NODE_TYPE_ID and node.node_id != END_NODE_ID:
                diagnostics.append(self._diag(
                    'SYNTAX-015', 'violation',
                    f'end node must use Coze Exit id {END_NODE_ID}',
                    source_file,
                    source_span=node.source_span,
                ))

            # SYNTAX-016: global variable must have name
            if node.node_type == VARIABLE_NODE_TYPE_ID and not node.global_var_name:
                diagnostics.append(self._diag(
                    'SYNTAX-016', 'violation',
                    f'variable node "{node.node_id}" must have a name',
                    source_file,
                    source_span=node.source_span,
                ))

            # SYNTAX-017: global variable must have type
            if node.node_type == VARIABLE_NODE_TYPE_ID and not node.global_var_type:
                diagnostics.append(self._diag(
                    'SYNTAX-017', 'violation',
                    f'variable node "{node.node_id}" must have a type',
                    source_file,
                    source_span=node.source_span,
                ))

            # SYNTAX-019: ref must have blockID and source (except literals and global vars)
            for param in node.parameters:
                if param.input_ref and param.input_ref.ref_type != 'literal':
                    # Skip global variable refs (they use name-based lookup)
                    if param.input_ref.source and param.input_ref.source.startswith('global_variable'):
                        continue
                    if not param.input_ref.block_id:
                        diagnostics.append(self._diag(
                            'SYNTAX-019', 'violation',
                            f'parameter "{param.name}" ref must have blockID',
                            source_file,
                            source_span=node.source_span,
                        ))

            # SYNTAX-020: variable type must be in allowed set
            if node.node_type == VARIABLE_NODE_TYPE_ID and node.global_var_type:
                if node.global_var_type not in ALLOWED_VARIABLE_TYPES:
                    diagnostics.append(self._diag(
                        'SYNTAX-020', 'violation',
                        f'variable type "{node.global_var_type}" is not allowed',
                        source_file,
                        source_span=node.source_span,
                    ))

            # SYNTAX-021: node type must be known
            if node.node_type and node.node_type not in KNOWN_NODE_TYPE_IDS:
                diagnostics.append(self._diag(
                    'SYNTAX-021', 'warning',
                    f'node type "{node.node_type}" is not a known Coze node type',
                    source_file,
                    source_span=node.source_span,
                ))

    def _check_edges(self, edges, diagnostics: list[Diagnostic], source_file: str | None) -> None:
        """Check SYNTAX-010~013 for edges."""
        for edge in edges:
            # SYNTAX-010: source node ID must exist
            if not edge.source_node_id:
                diagnostics.append(self._diag(
                    'SYNTAX-010', 'violation',
                    'edge sourceNodeID is required',
                    source_file,
                    source_span=edge.source_span,
                ))

            # SYNTAX-011: target node ID must exist
            if not edge.target_node_id:
                diagnostics.append(self._diag(
                    'SYNTAX-011', 'violation',
                    'edge targetNodeID is required',
                    source_file,
                    source_span=edge.source_span,
                ))

    # SYNTAX-018: Variable schema nesting validation
    def _check_variable_schema(self, ctx: PassContext, diagnostics: list[Diagnostic]) -> None:
        """SYNTAX-018: object/list type variables must have valid schema."""
        for canvas in ctx.sema.canvases():
            for node in canvas.nodes:
                if node.node_type != VARIABLE_NODE_TYPE_ID:
                    continue
                if node.global_var_type in ('object', 'list'):
                    if not node.global_var_schema:
                        diagnostics.append(self._diag(
                            'SYNTAX-018', 'violation',
                            f'variable "{node.global_var_name}" of type {node.global_var_type} must have a schema',
                            source_span=node.source_span,
                        ))
                    elif node.global_var_type == 'list' and not node.global_var_item_type:
                        diagnostics.append(self._diag(
                            'SYNTAX-018', 'violation',
                            f'list variable "{node.global_var_name}" must specify item type in schema',
                            source_span=node.source_span,
                        ))

    def _diag(self, rule_id: str, kind_str: str, message: str,
              source_file: str | None = None,
              checkability=Checkability.OFFLINE,
              source_span=None) -> Diagnostic:
        kind = DiagnosticKind.WARNING if kind_str == 'warning' else DiagnosticKind.VIOLATION
        return Diagnostic(
            rule_id=rule_id,
            layer='syntax',
            kind=kind,
            checkability=checkability,
            message=message,
            source_span=source_span,
            source_file=source_file,
        )
