"""SpanMap — maps YAML path tuples to SourceSpans for precise diagnostics.

Used to associate YAML structural locations with compiler diagnostics
so error messages can point to exact source locations.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..diagnostics.core import SourceSpan


@dataclass(frozen=True)
class SpanMap:
    """Maps YAML paths to SourceSpans for precise diagnostics.

    Path tuples mirror the YAML structure, e.g.:
        ('nodes', '0', 'id')  -> SourceSpan for the id scalar
        ('nodes', '0')        -> SourceSpan for the entire node mapping
        ('edges', '1')        -> SourceSpan for the entire edge mapping

    Supports lookup by exact path and prefix stripping for envelope unpacking.
    """

    _path_to_span: dict[tuple[str, ...], SourceSpan] = field(default_factory=dict)

    def lookup(self, *path_parts: str) -> SourceSpan | None:
        """Look up a SourceSpan by path parts."""
        return self._path_to_span.get(path_parts)

    def lookup_path(self, path: tuple[str, ...]) -> SourceSpan | None:
        """Look up a SourceSpan by path tuple."""
        return self._path_to_span.get(path)

    def strip_prefix(self, prefix: tuple[str, ...]) -> SpanMap:
        """Return a new SpanMap with all paths trimmed by the given prefix.

        Used after envelope unpacking (.flow canvas, export/clipboard json)
        so path tuples align with the unpacked raw_document structure.
        """
        plen = len(prefix)
        new_map: dict[tuple[str, ...], SourceSpan] = {}
        for path, span in self._path_to_span.items():
            if path[:plen] == prefix:
                new_map[path[plen:]] = span
        return SpanMap(_path_to_span=new_map)


def build_span_map(node: object) -> SpanMap:
    """Build a SpanMap from a composed YAML node tree.

    Walks the tree recursively, storing SourceSpan for every node
    (mappings, sequences, and scalars) so both container and leaf
    paths are resolvable.
    """
    path_to_span: dict[tuple[str, ...], SourceSpan] = {}
    _walk_node(node, (), path_to_span)
    return SpanMap(_path_to_span=path_to_span)


def _walk_node(
    node: object,
    path: tuple[str, ...],
    path_to_span: dict[tuple[str, ...], SourceSpan],
) -> None:
    """Recursively walk a composed YAML node tree and populate span map."""
    import yaml

    # Store span for all non-root nodes (mappings, sequences, and scalars)
    if path:
        path_to_span[path] = SourceSpan(
            start_line=node.start_mark.line,
            start_column=node.start_mark.column,
            end_line=node.end_mark.line,
            end_column=node.end_mark.column,
        )

    if isinstance(node, yaml.MappingNode):
        for key_node, value_node in node.value:
            key = key_node.value
            _walk_node(value_node, path + (key,), path_to_span)
    elif isinstance(node, yaml.SequenceNode):
        for i, item in enumerate(node.value):
            _walk_node(item, path + (str(i),), path_to_span)
    # ScalarNode: no children to recurse into; span already stored above
