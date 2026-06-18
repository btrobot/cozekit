"""ScopeTree — builds and queries the hierarchical scope tree.

The ScopeTree is constructed from a AnalysisGraph. Each canvas maps to
a Scope; parent-child relationships mirror the canvas/subcanvas nesting.
"""

from __future__ import annotations

from collections import deque

from .scope import Scope, ScopeKind

from ..ast.workflow_ast import CanvasAST
from ..ast.analysis_graph import AnalysisGraph
from ..types import (
    IF_NODE_TYPE_ID,
    LOOP_NODE_TYPE_ID,
    BATCH_NODE_TYPE_ID,
)

# Map owner node_type (string) to scope_kind.
_OWNER_TYPE_TO_SCOPE_KIND: dict[str, ScopeKind] = {
    IF_NODE_TYPE_ID: 'if',
    LOOP_NODE_TYPE_ID: 'loop',
    BATCH_NODE_TYPE_ID: 'batch',
}


def _scope_kind_for_canvas(canvas: CanvasAST) -> ScopeKind:
    """Determine the scope_kind for a canvas based on its owner node type."""
    if canvas.parent_canvas_path is None:
        return 'root'
    owner_type = canvas.owner_node_type
    if owner_type is not None:
        return _OWNER_TYPE_TO_SCOPE_KIND.get(owner_type, 'block')
    return 'block'


class ScopeTree:
    """Hierarchical scope tree built from AnalysisGraph.

    Provides lookup by canvas_path, visible-symbol enumeration
    (current scope + all ancestors), and visibility checks.

    Construction uses CanvasAST metadata for scope hierarchy and a
    pre-built canvas_path -> node_ids mapping for scope symbols.

    Mutable-during-construction pattern:
      1. Collect canvas metadata + wire parent_key/children_keys.
      2. Bottom-up: create frozen Scope objects with correct children
         (children already in self._scopes) and parent=None.
      3. Top-down: wire parent by replacing each Scope with a new
         frozen copy carrying the correct parent AND children.
    """

    def __init__(self, flat: AnalysisGraph,
                 canvas_node_ids: dict[tuple[str | int, ...], list[str]] | None = None) -> None:
        self._scopes: dict[tuple[str | int, ...], Scope] = {}
        self._root: Scope | None = None
        self._build(flat, canvas_node_ids or {})

    # ── construction ────────────────────────────────────────────

    def _build(self, flat: AnalysisGraph,
               canvas_node_ids: dict[tuple[str | int, ...], list[str]]) -> None:
        """Build scope tree from AnalysisGraph canvas metadata."""
        # Auto-derive canvas_node_ids from flat nodes if not provided
        if not canvas_node_ids:
            for node in flat.nodes:
                cp = (node.canvas_path if isinstance(node.canvas_path, tuple)
                      else tuple(node.canvas_path) if node.canvas_path else ())
                canvas_node_ids.setdefault(cp, []).append(node.node_id)

        if not flat.canvases:
            return

        # ── Pass 1: collect canvas metadata ──
        root_path: tuple[str | int, ...] = ()
        scope_meta: dict[tuple[str | int, ...], dict] = {}
        for canvas in flat.canvases:
            cp = canvas.canvas_path
            if canvas.parent_canvas_path is None:
                root_path = cp
            scope_meta[cp] = {
                'scope_id': str(cp),
                'scope_kind': _scope_kind_for_canvas(canvas),
                'canvas_path': cp,
                'symbols': tuple(canvas_node_ids.get(cp, [])),
                'parent_key': canvas.parent_canvas_path,
                'children_keys': [],
            }

        # Wire children_keys from parent references.
        for canvas in flat.canvases:
            cp = canvas.canvas_path
            if canvas.parent_canvas_path is not None:
                parent = scope_meta.get(canvas.parent_canvas_path)
                if parent is not None:
                    parent['children_keys'].append(cp)

        # Compute BFS levels for ordered traversal.
        levels: list[list[tuple[str | int, ...]]] = []
        queue: deque[tuple[str | int, ...]] = deque([root_path])
        while queue:
            level: list[tuple[str | int, ...]] = []
            for _ in range(len(queue)):
                cp = queue.popleft()
                if cp not in scope_meta:
                    continue
                level.append(cp)
                for ccp in scope_meta[cp]['children_keys']:
                    queue.append(ccp)
            if level:
                levels.append(level)

        # ── Pass 2: bottom-up — create frozen Scopes with correct
        #    children (deeper levels already in self._scopes) and
        #    parent=None.
        for level in reversed(levels):
            for cp in level:
                m = scope_meta[cp]
                children = tuple(
                    self._scopes[ccp] for ccp in m['children_keys']
                )
                self._scopes[cp] = Scope(
                    scope_id=m['scope_id'],
                    scope_kind=m['scope_kind'],
                    canvas_path=m['canvas_path'],
                    parent=None,
                    children=children,
                    symbols=m['symbols'],
                )

        # ── Pass 3: top-down — set parent on each Scope via __dict__
        #    Direct assignment (Scope is mutable).
        #    Parent scopes are already in self._scopes (shallower levels
        #    processed first), and children references remain correct from
        #    Pass 2.
        for level in levels:
            for cp in level:
                m = scope_meta[cp]
                pk = m['parent_key']
                if pk is not None and pk in self._scopes:
                    self._scopes[cp].parent = self._scopes[pk]

        self._root = self._scopes.get(root_path)

    # ── queries ─────────────────────────────────────────────────

    @property
    def root(self) -> Scope | None:
        """The root scope, or None if the tree is empty."""
        return self._root

    def lookup_scope(self, canvas_path: tuple[str | int, ...]) -> Scope | None:
        """Look up the scope for a given canvas path."""
        return self._scopes.get(canvas_path)

    def all_scopes(self) -> tuple[Scope, ...]:
        """Return all scopes in the tree."""
        return tuple(self._scopes.values())

    def visible_symbols(self, canvas_path: tuple[str | int, ...]) -> tuple[str, ...]:
        """Return all symbols visible from a canvas path (current + ancestors)."""
        result: list[str] = []
        seen: set[str] = set()
        scope = self._scopes.get(canvas_path)
        while scope is not None:
            for sym in scope.symbols:
                if sym not in seen:
                    result.append(sym)
                    seen.add(sym)
            scope = scope.parent
        return tuple(result)

    def is_visible(self, from_canvas_path: tuple[str | int, ...],
                   target_node_id: str) -> bool:
        """Check whether target_node_id is visible from from_canvas_path."""
        scope = self._scopes.get(from_canvas_path)
        while scope is not None:
            if target_node_id in scope.symbols:
                return True
            scope = scope.parent
        return False

    def scope_chain(self, canvas_path: tuple[str | int, ...]) -> tuple[Scope, ...]:
        """Return the full scope chain from canvas_path to root."""
        result: list[Scope] = []
        scope = self._scopes.get(canvas_path)
        while scope is not None:
            result.append(scope)
            scope = scope.parent
        return tuple(result)
