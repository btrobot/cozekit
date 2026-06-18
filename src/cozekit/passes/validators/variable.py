"""Node validators — Variable assign/merge nodes."""
from __future__ import annotations
from ...diagnostics.core import Checkability, Diagnostic, DiagnosticKind
from ...ast.workflow_ast import NodeAST
from ..diag_helper import diag_fe
from ..constants import (
    SET_VARIABLE_NODE_TYPE_ID, VARIABLE_ASSIGN_NODE_TYPE_ID,
    VARIABLE_MERGE_NODE_TYPE_ID,
)

def _check_variable_assign_fields(node, diagnostics: list[Diagnostic]) -> None:
    """FE-001: validate Variable Assign — left and right are required."""
    found_left = False
    found_right = False

    for param in node.parameters:
        if not param.name:
            continue
        if param.name == 'left':
            found_left = True
            if not param.input_ref or not param.input_ref.name or param.input_ref.name.strip() == '':
                diagnostics.append(diag_fe(
                    'SEMANTIC-FE-001', 'violation',
                    'Variable Assign node requires left (target variable)',
                    checkability=Checkability.OFFLINE,
                    source_span=node.source_span,
                ))
        elif param.name == 'right':
            found_right = True
            if not param.input_ref or not param.input_ref.name or param.input_ref.name.strip() == '':
                diagnostics.append(diag_fe(
                    'SEMANTIC-FE-001', 'violation',
                    'Variable Assign node requires right (value)',
                    checkability=Checkability.OFFLINE,
                    source_span=node.source_span,
                ))

    # Also flag if expected params are entirely absent
    if not found_left:
        diagnostics.append(diag_fe(
            'SEMANTIC-FE-001', 'violation',
            'Variable Assign node requires left (target variable)',
            checkability=Checkability.OFFLINE,
            source_span=node.source_span,
        ))
    if not found_right:
        diagnostics.append(diag_fe(
            'SEMANTIC-FE-001', 'violation',
            'Variable Assign node requires right (value)',
            checkability=Checkability.OFFLINE,
            source_span=node.source_span,
        ))

# ── Intent node (type 22) ──────────────────────────────────


def _check_variable_merge_fields(node, diagnostics: list[Diagnostic]) -> None:
    """FE-001: VariableMerge node requires merge groups."""
    params_by_name = {p.name: p for p in node.node_specific_params if p.name}
    if 'mergeGroups' not in params_by_name:
        diagnostics.append(diag_fe(
            'SEMANTIC-FE-001', 'violation',
            'VariableMerge node requires merge groups',
            checkability=Checkability.OFFLINE,
            source_span=node.source_span,
        ))
