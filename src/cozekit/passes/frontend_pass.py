"""FrontendPass — SEMANTIC-FE-* rules.

Validates frontend-oriented semantic rules: titles, subcanvas ports,
exception ports, node-specific fields, output names, input trees.
"""

from __future__ import annotations

from collections import Counter

from ..diagnostics.core import Checkability, Diagnostic
from ..types import (
    COMMENT_NODE_TYPE_ID,
    COMPOSITE_NODE_TYPE_IDS,
    LOOP_NODE_TYPE_ID,
    BATCH_NODE_TYPE_ID,
)
from .context import PassContext
from .constants import TITLE_MAX_LENGTH
from .validators import NODE_VALIDATOR_REGISTRY
from .diag_helper import diag_fe as _diag_fe
from .io_validators import check_exception_json, check_input_tree, check_output_names


# Subcanvas entry/exit port IDs for composite nodes
_LOOP_BATCH_PORT_IDS: dict[str, tuple[str, str]] = {
    LOOP_NODE_TYPE_ID: ('loop-function-inline-input', 'loop-function-inline-output'),
    BATCH_NODE_TYPE_ID: ('batch-function-inline-input', 'batch-function-inline-output'),
}


class FrontendPass:
    """SEMANTIC-FE-* rules: titles, subcanvas ports, node-specific fields."""

    requires_document: bool = False

    @property
    def name(self) -> str:
        return 'semantic-fe'

    def run(self, ctx: PassContext) -> tuple[Diagnostic, ...]:
        diagnostics: list[Diagnostic] = []

        # Build subcanvas edge lookup
        subcanvas_edges: dict[str, tuple] = {}
        subcanvas_node_ids: set[str] = set()
        for canvas in ctx.sema.canvases():
            if canvas.owner_node_id:
                subcanvas_edges[canvas.owner_node_id] = canvas.edges
                subcanvas_node_ids.add(canvas.owner_node_id)

        # Check all canvases (root + nested)
        for canvas in ctx.sema.canvases():
            nodes = canvas.nodes
            if not nodes:
                continue
            self._check_titles(nodes, diagnostics)
            self._check_subcanvas_ports(nodes, diagnostics, subcanvas_edges, subcanvas_node_ids)

        # FE-008: exception port connectivity
        self._check_exception_ports(ctx, diagnostics)

        # FE-012: exception JSON parseability
        check_exception_json(ctx, diagnostics)

        # FE-001: node-specific field validation
        self._check_node_specific_fields(ctx, diagnostics)
        check_output_names(ctx, diagnostics)

        # FE-014: generic input parameter validation
        check_input_tree(ctx, diagnostics)

        return tuple(diagnostics)

    def _check_titles(self, nodes, diagnostics: list[Diagnostic]) -> None:
        """FE-009/010/011: title is required, max length, unique."""
        titles: list[tuple[str | None, str]] = []
        for node in nodes:
            titles.append((node.title, node.node_id))

        title_counts = Counter(t for t, _ in titles if t is not None)
        comment_ids = {n.node_id for n in nodes if n.node_type == COMMENT_NODE_TYPE_ID}

        for title, node_id in titles:
            if node_id in comment_ids:
                continue
            node = next((n for n in nodes if n.node_id == node_id), None)
            span = node.source_span if node else None

            if not title:
                diagnostics.append(_diag_fe(
                    'SEMANTIC-FE-009', 'violation',
                    'node title is required',
                    checkability=Checkability.OFFLINE,
                    source_span=span,
                ))
                continue

            if len(title) > TITLE_MAX_LENGTH:
                diagnostics.append(_diag_fe(
                    'SEMANTIC-FE-010', 'violation',
                    f'node title exceeds {TITLE_MAX_LENGTH} characters',
                    checkability=Checkability.OFFLINE,
                    source_span=span,
                ))

            if title_counts[title] > 1:
                diagnostics.append(_diag_fe(
                    'SEMANTIC-FE-011', 'violation',
                    'node title must be unique within the same canvas',
                    checkability=Checkability.OFFLINE,
                    source_span=span,
                ))

    def _check_subcanvas_ports(self, nodes, diagnostics: list[Diagnostic],
                               subcanvas_edges: dict[str, tuple],
                               subcanvas_node_ids: set[str]) -> None:
        """FE-006/007: subcanvas entry/exit port validation."""
        for node in nodes:
            node_type = node.node_type
            if node_type not in COMPOSITE_NODE_TYPE_IDS:
                continue
            if node.node_id not in subcanvas_node_ids:
                continue

            port_ids = _LOOP_BATCH_PORT_IDS.get(node_type)
            if port_ids is None:
                continue
            entry_port, exit_port = port_ids

            edges = subcanvas_edges.get(node.node_id, ())

            has_entry = any(e.target_port_id == entry_port for e in edges)
            if not has_entry:
                diagnostics.append(_diag_fe(
                    'SEMANTIC-FE-006', 'violation',
                    'subcanvas entry-port validation is only partially checked offline; '
                    'frontend port metadata is still required',
                    checkability=Checkability.PARTIAL,
                    source_span=node.source_span,
                ))

            has_exit = any(e.source_port_id == exit_port for e in edges)
            if not has_exit:
                diagnostics.append(_diag_fe(
                    'SEMANTIC-FE-007', 'violation',
                    'subcanvas exit-port validation is only partially checked offline; '
                    'frontend port metadata is still required',
                    checkability=Checkability.PARTIAL,
                    source_span=node.source_span,
                ))

    def _check_exception_ports(self, ctx: PassContext, diagnostics: list[Diagnostic]) -> None:
        """FE-008: exception port must be connected when exception branch is set."""
        for _canvas, node in ctx.sema.iter_canvas_nodes():
            cfg = node.on_error_config
            if not cfg:
                continue
            is_open = cfg.get('settingOnErrorIsOpen', False)
            process_type = cfg.get('processType', '')
            if not is_open or process_type != 'redirect':
                continue
            outgoing = ctx.sema.edge_source_targets(node.node_id)
            has_exception_port = any(
                e.source_port_id and 'exception' in e.source_port_id.lower()
                for e in outgoing
            )
            if not has_exception_port:
                diagnostics.append(_diag_fe(
                    'SEMANTIC-FE-008', 'violation',
                    'exception branch is set but exception port has no outgoing edge',
                    checkability=Checkability.PARTIAL,
                    source_span=node.source_span,
                ))

    def _check_node_specific_fields(self, ctx: PassContext, diagnostics: list[Diagnostic]) -> None:
        """FE-001: validate node-specific fields for all node types."""
        for _canvas, node in ctx.sema.iter_canvas_nodes():
            validators = NODE_VALIDATOR_REGISTRY.get(node.node_type, [])
            for validator in validators:
                validator(node, diagnostics)
