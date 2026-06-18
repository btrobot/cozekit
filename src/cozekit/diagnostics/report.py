"""Report dataclass and summary — diagnostics assembly layer.

The diagnostics layer owns the stable report contract. Passes emit individual
Diagnostic objects; this layer assembles them into CompilerV2Report.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field

from .core import Diagnostic, DiagnosticKind


@dataclass(frozen=True)
class ReportSummary:
    """Summary counts by diagnostic kind."""
    total: int
    violations: int
    warnings: int
    dynamic_preflight: int
    partial_checks: int
    requires_live_validation: int
    deferred: int


@dataclass(frozen=True)
class CompilerV2Report:
    """Stable report output — the diagnostics layer's contract.

    Schema design:
    - diagnostics: list of diagnostic records
    - summary: counts by kind
    - source_file: origin file path
    """
    diagnostics: tuple[Diagnostic, ...] = field(default_factory=tuple)
    source_file: str | None = None

    @property
    def summary(self) -> ReportSummary:
        counts = {k: 0 for k in DiagnosticKind}
        for d in self.diagnostics:
            counts[d.kind] = counts.get(d.kind, 0) + 1
        return ReportSummary(
            total=len(self.diagnostics),
            violations=counts[DiagnosticKind.VIOLATION],
            warnings=counts[DiagnosticKind.WARNING],
            dynamic_preflight=counts[DiagnosticKind.DYNAMIC_PREFLIGHT],
            partial_checks=counts[DiagnosticKind.PARTIAL_CHECK],
            requires_live_validation=counts[DiagnosticKind.REQUIRES_LIVE_VALIDATION],
            deferred=counts[DiagnosticKind.DEFERRED],
        )

    @property
    def exit_code(self) -> int:
        return 1 if self.summary.violations > 0 else 0

    def to_dict(self) -> dict:
        s = self.summary
        return {
            'diagnostics': [asdict(d) for d in self.diagnostics],
            'summary': {
                'total': s.total,
                'violations': s.violations,
                'warnings': s.warnings,
                'dynamic_preflight': s.dynamic_preflight,
                'partial_checks': s.partial_checks,
                'requires_live_validation': s.requires_live_validation,
                'deferred': s.deferred,
            },
            'source_file': self.source_file,
        }

    def to_json(self, **kwargs) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2, **kwargs)
