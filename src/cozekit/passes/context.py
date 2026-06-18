"""PassContext — the unified context object passed to all compiler passes.

Passes access structural and semantic data through sema.
source_file and transport_format provide metadata without exposing the
full ParsedDocument.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..ast.workflow_ast import WorkflowAST
    from ..sema.query_authority import WorkflowSemaQueryAuthority
    from ..transport.span_map import SpanMap


@dataclass(frozen=True)
class PassContext:
    """Unified context for all compiler passes.

    Passes access structural and semantic data through sema.
    ast provides the raw AST for Visitor-based traversal.
    """
    sema: WorkflowSemaQueryAuthority
    ast: WorkflowAST | None = None
    metadata: dict[str, Any] | None = None
    source_text: str = ''
    source_file: str | None = None
    transport_format: str | None = None
    span_map: SpanMap | None = None
