"""Resolution table — stores resolved parameter references.

After IR removal, resolved references live here instead of on ParameterIR.resolved_ref.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResolvedRef:
    source: str | None = None
    block_id: str | None = None
    name: str | None = None
    target_node_path: tuple[str | int, ...] = ()
    is_global: bool = False
    is_unresolved: bool = False


class ResolutionTable:
    def __init__(self) -> None:
        self._table: dict[tuple[str, int], ResolvedRef] = {}

    def put(self, node_id: str, param_index: int, resolved: ResolvedRef) -> None:
        self._table[(node_id, param_index)] = resolved

    def get(self, node_id: str, param_index: int) -> ResolvedRef | None:
        return self._table.get((node_id, param_index))

    def get_all_for_node(self, node_id: str) -> tuple[ResolvedRef, ...]:
        result = []
        idx = 0
        while (node_id, idx) in self._table:
            result.append(self._table[(node_id, idx)])
            idx += 1
        return tuple(result)
