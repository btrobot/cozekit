"""Pass registry — collects and runs all registered passes."""

from __future__ import annotations

from ..diagnostics.core import Diagnostic
from .context import PassContext


class PassRegistry:
    """Manages and executes compiler passes."""

    def __init__(self) -> None:
        self._passes: list = []

    def register(self, pass_instance) -> None:
        """Register a compiler pass."""
        self._passes.append(pass_instance)

    def run_all(self, ctx: PassContext) -> tuple[Diagnostic, ...]:
        """Execute all registered passes and collect diagnostics."""
        all_diagnostics: list[Diagnostic] = []
        for p in self._passes:
            result = p.run(ctx)
            all_diagnostics.extend(result)
        return tuple(all_diagnostics)
