"""Scope — hierarchical visibility unit for the workflow symbol table.

Each canvas in the workflow maps to exactly one Scope. Scopes nest
mirroring the canvas/subcanvas hierarchy, forming a tree rooted at
the workflow's root canvas.

Lexical scoping: an inner scope can see symbols defined in its
ancestor scopes, but not vice versa. Sibling scopes are not
mutually visible.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


# Scope kinds derived from the owning composite node's composite_kind.
# 'root' is assigned to the top-level canvas with no parent.
ScopeKind = Literal['root', 'loop', 'batch', 'if', 'block']


@dataclass
class Scope:
    """A single scope in the hierarchical scope tree.

    Attributes:
        scope_id: Unique string identifier (typically the stringified canvas_path).
        scope_kind: Classification derived from the owning composite node.
        canvas_path: The canvas_path tuple this scope corresponds to.
        parent: Reference to the parent scope, or None for the root scope.
        children: Tuple of child scopes (subcanvas scopes).
        symbols: Tuple of node_ids directly defined in this scope's canvas.
    """
    scope_id: str
    scope_kind: ScopeKind
    canvas_path: tuple[str | int, ...]
    parent: Scope | None = None
    children: tuple[Scope, ...] = ()
    symbols: tuple[str, ...] = ()
