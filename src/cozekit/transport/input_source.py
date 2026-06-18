"""Input source and parsed document — the transport layer's public types."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .span_map import SpanMap


@dataclass(frozen=True)
class InputSource:
    """Unified input source for all transport formats."""
    text: str | None = None
    path: Path | None = None
    source_file: str | None = None
    format_hint: str | None = None  # 'yaml', 'json', 'flow' — auto-detected if None


@dataclass(frozen=True)
class ParsedDocument:
    """Parsed and transport-normalized document.

    raw_document: the parsed YAML/JSON dict/list (after envelope unpacking)
    source_file: origin file path for diagnostics
    transport_format: which transport format was used
    source_text: original source text (for line-number mapping)
    versions: versions metadata from root document (if present)
    envelope_type: envelope type marker ('export' | 'clipboard' | None)
    span_map: YAML path → SourceSpan mapping (None for JSON format)
    """
    raw_document: Any = None
    source_file: str | None = None
    transport_format: str = 'yaml'
    source_text: str = ''
    versions: Any = None
    envelope_type: str | None = None
    span_map: SpanMap | None = None
