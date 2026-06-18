"""Portability pass — implements portability rules.

All canvas iteration uses sema.canvases() which returns all canvases
(root + nested).  No node.blocks recursion — flat IR design.
No IR layer — operates on flat graph via sema.
"""

from __future__ import annotations

from typing import Any

from ...diagnostics.core import Checkability, Diagnostic, DiagnosticKind, SourceSpan
from ..constants import LOOP_NODE_TYPE_ID, SUBWORKFLOW_NODE_TYPE_ID
from ..context import PassContext
from ..diag_helper import make_diag

# Loop control node types: Break=19, Continue=29, SetVariable=20
LOOP_CONTROL_TYPES = {'19', '29', '20'}

# Subworkflow node type: SubWorkflow=9
SUBWORKFLOW_NODE_TYPE = SUBWORKFLOW_NODE_TYPE_ID

# Cross-space blocked node types
CROSS_SPACE_BLOCKED_TYPES = frozenset({'6', '27', '9', '14', '42', '43', '44', '46', '12'})

WORKFLOW_EXPORT_TYPE = 'coze-workflow-export-data'
WORKFLOW_CLIPBOARD_TYPE = 'coze-workflow-clipboard-data'


class PortabilityPass:
    """Validates portability rules (PORTABILITY-*).

    Operates on flat graph via sema.
    """

    requires_document: bool = False

    @property
    def name(self) -> str:
        return 'portability'

    def run(self, ctx: PassContext) -> tuple[Diagnostic, ...]:
        diagnostics: list[Diagnostic] = []

        source_file = ctx.source_file

        # PORT-001~004: transport envelope validation
        self._check_transport_envelope(ctx, diagnostics)

        # PORT-009: loop control nodes only portable inside Loop subcanvas
        for canvas in ctx.sema.canvases():
            inside_loop = False
            if canvas.owner_node_id and ctx.sema:
                owner_nodes = ctx.sema.lookup_node_by_id(canvas.owner_node_id)
                inside_loop = any(ns.node.node_type == LOOP_NODE_TYPE_ID for ns in owner_nodes)
            for node in canvas.nodes:
                if node.node_type in LOOP_CONTROL_TYPES and not inside_loop:
                    diagnostics.append(self._diag(
                        'PORTABILITY-009',
                        'violation',
                        'loop control node (break/continue/set_variable) is only portable inside a Loop subcanvas',
                        checkability=Checkability.OFFLINE,
                        source_span=node.source_span,
                    ))

        # PORT-011: subworkflow self-reference requires live validation
        for canvas in ctx.sema.canvases():
            for node in canvas.nodes:
                if node.node_type == SUBWORKFLOW_NODE_TYPE:
                    diagnostics.append(self._diag(
                        'PORTABILITY-011',
                        'violation',
                        'subworkflow self-reference portability requires the current workflow id',
                        checkability=Checkability.REQUIRES_LIVE_VALIDATION,
                        source_span=node.source_span,
                    ))

        # PORT-012: cross-space blocked node types require live validation
        for canvas in ctx.sema.canvases():
            for node in canvas.nodes:
                if node.node_type in CROSS_SPACE_BLOCKED_TYPES:
                    diagnostics.append(self._diag(
                        'PORTABILITY-012',
                        'violation',
                        'this node type has cross-space portability restrictions; live source/target context is required',
                        checkability=Checkability.REQUIRES_LIVE_VALIDATION,
                        source_span=node.source_span,
                    ))

        # PORT-014: contract consistency
        self._check_contract_consistency(ctx, diagnostics)

        return tuple(diagnostics)

    # PORT-002: Import payload JSON-parseability
    # Implicitly handled: TransportNormalizer raises on invalid JSON/YAML.
    # No explicit check needed in the pass.

    # PORT-013: Cross-space API/plugin nodes require Listed product status
    # Requires space_id and product status context (live-only).
    # TODO: Add when pipeline provides space/product metadata.

    def _check_transport_envelope(self, ctx: PassContext, diagnostics: list[Diagnostic]) -> None:
        """PORT-001~004: transport envelope validation."""
        source_file = ctx.source_file
        if source_file:
            if not source_file.endswith(('.json', '.flow', '.yaml', '.yml')):
                diagnostics.append(self._diag(
                    'PORTABILITY-001',
                    'violation',
                    'studio import shortcut accepts only .json or .flow files',
                    checkability=Checkability.OFFLINE,
                ))

        # PORT-003/004: use envelope_type from IR metadata
        envelope_type = ctx.sema.workflow_envelope_type()
        if envelope_type not in {WORKFLOW_EXPORT_TYPE, WORKFLOW_CLIPBOARD_TYPE}:
            # Check via source_text for envelope markers
            if ctx.source_text:
                try:
                    import json
                    raw = json.loads(ctx.source_text) if ctx.source_text.strip().startswith('{') else None
                except (json.JSONDecodeError, ValueError):
                    raw = None
                if isinstance(raw, dict):
                    envelope_type = raw.get('type')
                    if envelope_type not in {WORKFLOW_EXPORT_TYPE, WORKFLOW_CLIPBOARD_TYPE}:
                        return
                    json_payload = raw.get('json')
                    if not isinstance(json_payload, dict):
                        if envelope_type == WORKFLOW_EXPORT_TYPE:
                            diagnostics.append(self._diag(
                                'PORTABILITY-003',
                                'violation',
                                'workflow export envelope must use the Coze workflow export type marker',
                                checkability=Checkability.OFFLINE,
                            ))
                        else:
                            diagnostics.append(self._diag(
                                'PORTABILITY-004',
                                'violation',
                                'workflow clipboard envelope must use the Coze clipboard type marker',
                                checkability=Checkability.OFFLINE,
                            ))

    def _check_contract_consistency(self, ctx: PassContext, diagnostics: list[Diagnostic]) -> None:
        """PORT-014: portability contract verification."""
        for canvas in ctx.sema.canvases():
            for node in canvas.nodes:
                if node.node_id not in ctx.sema.all_node_ids():
                    diagnostics.append(self._diag(
                        'PORTABILITY-014',
                        'violation',
                        'shared portability facts are incomplete for this node; '
                        'portability analysis contract is broken',
                        checkability=Checkability.OFFLINE,
                        source_span=node.source_span,
                    ))

    def _diag(
        self,
        rule_id: str,
        kind_str: str,
        message: str,
        checkability: Checkability = Checkability.OFFLINE,
        source_span: SourceSpan | None = None,
    ) -> Diagnostic:
        kind = DiagnosticKind.WARNING if kind_str == 'warning' else DiagnosticKind.VIOLATION
        return Diagnostic(
            rule_id=rule_id,
            layer='portability',
            kind=kind,
            checkability=checkability,
            message=message,
            source_span=source_span,
        )
