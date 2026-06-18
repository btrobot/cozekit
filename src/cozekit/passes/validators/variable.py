"""Node validators — Variable assign/merge nodes."""
from __future__ import annotations
from ...diagnostics.core import Checkability, Diagnostic, DiagnosticKind
from ...ast.workflow_ast import NodeAST
from ..diag_helper import diag_fe
from ..constants import (
    SET_VARIABLE_NODE_TYPE_ID, VARIABLE_ASSIGN_NODE_TYPE_ID,
    VARIABLE_MERGE_NODE_TYPE_ID,
)

def _ref_has_identifier(ref) -> bool:
    """Check if a RefAST has a meaningful identifier.

    For global_variable refs, the identifier is in ``path`` (e.g. ('app_v1',)).
    For block-output refs, the identifier is in ``name``.
    """
    if ref is None:
        return False
    if ref.name and ref.name.strip():
        return True
    if ref.path and ref.path[0] and ref.path[0].strip():
        return True
    return False


def _check_variable_assign_fields(node, diagnostics: list[Diagnostic]) -> None:
    """FE-001: validate Variable Assign — left and right are required.

    Supports two data formats:

    1. Coze-studio format (real platform data):
       Each parameter has ``left_ref`` and ``right_ref`` populated by the
       AST builder from entries like ``{name: "var", left: {...}, input: {...}}``.
       Every entry must have a valid left (target) and right (value).

    2. Cozekit internal format (test fixtures):
       Parameters named "left" and "right" with ``input_ref`` populated.
    """
    found_coze_format = False
    found_left = False
    found_right = False

    for param in node.parameters:
        # --- Coze-studio format: check left_ref / right_ref ---
        if param.left_ref is not None or param.right_ref is not None:
            found_coze_format = True
            if not _ref_has_identifier(param.left_ref):
                diagnostics.append(diag_fe(
                    'SEMANTIC-FE-001', 'violation',
                    'Variable Assign node requires left (target variable)',
                    checkability=Checkability.OFFLINE,
                    source_span=node.source_span,
                ))
            if not _ref_has_identifier(param.right_ref):
                diagnostics.append(diag_fe(
                    'SEMANTIC-FE-001', 'violation',
                    'Variable Assign node requires right (value)',
                    checkability=Checkability.OFFLINE,
                    source_span=node.source_span,
                ))
            continue

        # --- Cozekit internal format: check param name ---
        if not param.name:
            continue
        if param.name == 'left':
            found_left = True
            if not _ref_has_identifier(param.input_ref):
                diagnostics.append(diag_fe(
                    'SEMANTIC-FE-001', 'violation',
                    'Variable Assign node requires left (target variable)',
                    checkability=Checkability.OFFLINE,
                    source_span=node.source_span,
                ))
        elif param.name == 'right':
            found_right = True
            if not _ref_has_identifier(param.input_ref):
                diagnostics.append(diag_fe(
                    'SEMANTIC-FE-001', 'violation',
                    'Variable Assign node requires right (value)',
                    checkability=Checkability.OFFLINE,
                    source_span=node.source_span,
                ))

    # For cozekit internal format, also flag if expected params are entirely absent
    if not found_coze_format:
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
