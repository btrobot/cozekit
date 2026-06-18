"""Node validators — If/Condition node (type 8)."""
from __future__ import annotations
from ...diagnostics.core import Checkability, Diagnostic, DiagnosticKind
from ...ast.workflow_ast import NodeAST
from ..diag_helper import diag_fe
from ..constants import IF_NODE_TYPE_ID, UNARY_CONDITION_OPERATORS

def _check_if_conditions(node, diagnostics: list[Diagnostic]) -> None:
    """FE-001: validate If node condition branches.

    For each branch's conditions:
    - left: required — must have a value expression
    - operator: required — must not be None
    - right: required for binary operators; disabled for unary operators
      (Null, NotNull, True, False)
    """
    for branch in node.branches:
        if not branch.condition:
            continue
        for cb in branch.condition.branches:
            # left is required
            if cb.left is None or cb.left.input_ref is None:
                diagnostics.append(diag_fe(
                    'SEMANTIC-FE-001', 'violation',
                    'If condition left operand is required',
                    checkability=Checkability.OFFLINE,
                    source_span=node.source_span,
                ))
            # operator is required
            if cb.operator is None:
                diagnostics.append(diag_fe(
                    'SEMANTIC-FE-001', 'violation',
                    'If condition operator is required',
                    checkability=Checkability.OFFLINE,
                    source_span=node.source_span,
                ))
            # right is required unless operator is unary
            if cb.operator and cb.operator not in UNARY_CONDITION_OPERATORS:
                if cb.right is None or cb.right.input_ref is None:
                    diagnostics.append(diag_fe(
                        'SEMANTIC-FE-001', 'violation',
                        'If condition right operand is required for binary operator',
                        checkability=Checkability.OFFLINE,
                        source_span=node.source_span,
                    ))




# ── Registry ──────────────────────────────────────────────────
# Maps node_type_id -> list of validator functions.
# Each validator has signature: (node: NodeAST, diagnostics: list[Diagnostic]) -> None

