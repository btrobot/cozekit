"""Core diagnostic types — stable diagnostic model shared across all phases."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class DiagnosticKind(StrEnum):
    VIOLATION = 'violation'
    WARNING = 'warning'
    DYNAMIC_PREFLIGHT = 'dynamic_preflight'
    PARTIAL_CHECK = 'partial_check'
    REQUIRES_LIVE_VALIDATION = 'requires_live_validation'
    DEFERRED = 'deferred'


class Checkability(StrEnum):
    OFFLINE = 'offline'
    PARTIAL = 'partial'
    DYNAMIC_PREFLIGHT = 'dynamic_preflight'
    REQUIRES_LIVE_VALIDATION = 'requires_live_validation'
    DEFERRED = 'deferred'


class RuleHorizon(StrEnum):
    COMPILE_TIME = 'compile-time'
    LINK_TIME = 'link-time'
    RUN_PREFLIGHT = 'run-preflight'
    TRUE_RUNTIME = 'true-runtime'


@dataclass(frozen=True)
class SourceSpan:
    """Source location span — line/column zero-indexed."""
    start_line: int | None = None
    start_column: int | None = None
    end_line: int | None = None
    end_column: int | None = None


@dataclass(frozen=True)
class CanvasPath:
    """Dotted canvas path with optional index segments."""
    value: str = ''

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Diagnostic:
    """A single diagnostic output from any compiler phase."""
    rule_id: str
    layer: str
    kind: DiagnosticKind
    checkability: Checkability
    message: str
    source_span: SourceSpan | None = None
    canvas_path: CanvasPath | None = None
    source_file: str | None = None

    @property
    def severity(self) -> str:
        return self.kind.value

    @property
    def horizon(self) -> str:
        if self.checkability == Checkability.OFFLINE:
            return RuleHorizon.COMPILE_TIME.value
        if self.checkability == Checkability.PARTIAL:
            return RuleHorizon.LINK_TIME.value
        return RuleHorizon.TRUE_RUNTIME.value


class DiagnosticParseError(Exception):
    """Raised when transport-level parsing fails (YAML/JSON syntax error).

    Carries a Diagnostic for integration into CompilerV2Report.
    """

    def __init__(self, diagnostic: Diagnostic, *, original: Exception | None = None):
        self.diagnostic = diagnostic
        self.original = original
        super().__init__(diagnostic.message)
