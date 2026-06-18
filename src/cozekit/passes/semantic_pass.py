"""SemanticPass — facade for all semantic rules.

Delegates to FrontendPass (FE-*) and BackendPass (BE-*).
Kept for backward compatibility; new code should use the specific passes.
"""

from __future__ import annotations

from ..diagnostics.core import Diagnostic
from .context import PassContext
from .frontend_pass import FrontendPass
from .backend_pass import BackendPass


class SemanticPass:
    """Validates all semantic rules (SEMANTIC-FE-* + SEMANTIC-BE-*).

    This is a facade that delegates to FrontendPass and BackendPass.
    """

    requires_document: bool = False

    def __init__(self) -> None:
        self._fe = FrontendPass()
        self._be = BackendPass()

    @property
    def name(self) -> str:
        return 'semantic'

    def run(self, ctx: PassContext) -> tuple[Diagnostic, ...]:
        diagnostics: list[Diagnostic] = []
        diagnostics.extend(self._fe.run(ctx))
        diagnostics.extend(self._be.run(ctx))
        return tuple(diagnostics)
