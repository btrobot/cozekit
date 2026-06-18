"""Shared diagnostic builder for all compiler passes.

Each pass calls ``make_diag`` (or wraps it in a thin layer method) instead of
duplicating the Diagnostic construction logic.
"""

from __future__ import annotations

from ..diagnostics.core import Diagnostic, DiagnosticKind, Checkability
from ..transport.span_map import SourceSpan


def make_diag(
    rule_id: str,
    kind_str: str,
    message: str,
    layer: str,
    *,
    checkability: Checkability = Checkability.OFFLINE,
    source_span: SourceSpan | None = None,
    source_file: str | None = None,
) -> Diagnostic:
    """Build a Diagnostic with the standard kind-mapping logic.

    Args:
        rule_id: e.g. 'SYNTAX-014', 'SEMANTIC-BE-021'.
        kind_str: 'warning' or 'violation'.
        message: Human-readable description.
        layer: Pass layer name ('syntax', 'semantic-be', etc.).
        checkability: Default OFFLINE.
        source_span: Optional source location for the diagnostic.
        source_file: Optional source file path (used by syntax pass).
    """
    kind = DiagnosticKind.WARNING if kind_str == 'warning' else DiagnosticKind.VIOLATION
    return Diagnostic(
        rule_id=rule_id,
        layer=layer,
        kind=kind,
        checkability=checkability,
        message=message,
        source_span=source_span,
        source_file=source_file,
    )


def diag_fe(
    rule_id: str,
    kind_str: str,
    message: str,
    checkability: Checkability = Checkability.OFFLINE,
    source_span: SourceSpan | None = None,
) -> Diagnostic:
    """Build a semantic-fe diagnostic — convenience wrapper for make_diag."""
    return make_diag(
        rule_id, kind_str, message, 'semantic-fe',
        checkability=checkability, source_span=source_span,
    )


def diag_be(
    rule_id: str,
    kind_str: str,
    message: str,
    checkability: Checkability = Checkability.OFFLINE,
    source_span: SourceSpan | None = None,
) -> Diagnostic:
    """Build a semantic-be diagnostic -- convenience wrapper for make_diag."""
    return make_diag(
        rule_id, kind_str, message, 'semantic-be',
        checkability=checkability, source_span=source_span,
    )
