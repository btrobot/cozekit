"""Pass protocol — the contract for compiler passes.

Each pass:
- Receives: PassContext (IR + indices + sema + document + ast + metadata)
- Emits: tuple of Diagnostic (to the diagnostics layer)
- Must NOT assemble reports (that's the diagnostics layer's job)
"""

from __future__ import annotations

from typing import Protocol, Tuple

from ..diagnostics.core import Diagnostic
from .context import PassContext


class CompilerPass(Protocol):
    """A single compiler pass that emits diagnostics."""

    @property
    def name(self) -> str: ...

    def run(self, ctx: PassContext) -> Tuple[Diagnostic, ...]: ...
