"""Transport normalizer — YAML/JSON/.flow envelope unpacking.

This layer owns all transport-format differences. After normalization,
the raw document is a plain dict/list regardless of source format.
Provides line-accurate source span data for diagnostics.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from .input_source import InputSource, ParsedDocument
from .span_map import SpanMap, build_span_map
from .yaml_source_converter import YamlSourceConverter
from ..diagnostics.core import Checkability, Diagnostic, DiagnosticParseError, DiagnosticKind


class TransportNormalizer:
    """Parse and normalize YAML/JSON/.flow inputs into a ParsedDocument."""

    def __init__(self):
        self._yaml_converter = YamlSourceConverter()

    def normalize(self, source: InputSource) -> ParsedDocument:
        text = self._resolve_text(source)
        source_file = self._resolve_source_file(source)
        fmt = self._detect_format(source, text)

        # Build span map for YAML formats using yaml.compose()
        span_map: SpanMap | None = None
        if fmt in ('yaml', 'flow'):
            try:
                composed = yaml.compose(text)
                span_map = build_span_map(composed)
            except yaml.YAMLError as e:
                self._raise_yaml_error(e)

        raw = self._parse(text, fmt)

        # Extract versions and envelope_type before unpacking
        versions = None
        envelope_type = None

        # .flow envelope unpacking
        if fmt == 'flow' and isinstance(raw, dict) and 'canvas' in raw:
            raw = raw['canvas']
            if span_map is not None:
                span_map = span_map.strip_prefix(('canvas',))

        # Export/clipboard envelope unpacking
        if isinstance(raw, dict):
            envelope_type = raw.get('type')
            if envelope_type in ('coze-workflow-export-data', 'coze-workflow-clipboard-data'):
                json_payload = raw.get('json')
                if isinstance(json_payload, dict):
                    raw = json_payload
                    if span_map is not None:
                        span_map = span_map.strip_prefix(('json',))

        # YAML source format conversion
        # Detect and convert YAML source format (flat structure, string types)
        # to JSON export format (nested structure, numeric types)
        if fmt == 'yaml' and isinstance(raw, dict):
            if self._yaml_converter.is_yaml_source_format(raw):
                raw = self._yaml_converter.convert(raw)

        # Extract versions from normalized document
        if isinstance(raw, dict):
            versions = raw.get('versions')

        return ParsedDocument(
            raw_document=raw,
            source_file=source_file,
            transport_format=fmt,
            source_text=text,
            versions=versions,
            envelope_type=envelope_type if envelope_type in ('export', 'clipboard') else None,
            span_map=span_map,
        )

    def _resolve_text(self, source: InputSource) -> str:
        if source.text is not None:
            return source.text
        if source.path is not None:
            return source.path.read_text(encoding='utf-8')
        raise ValueError('InputSource must have text or path')

    def _resolve_source_file(self, source: InputSource) -> str | None:
        if source.source_file is not None:
            return source.source_file
        if source.path is not None:
            return str(source.path)
        return None

    def _detect_format(self, source: InputSource, text: str) -> str:
        if source.format_hint:
            return source.format_hint
        if source.path is not None:
            suffix = source.path.suffix.lower()
            if suffix == '.flow':
                return 'flow'
            if suffix == '.json':
                return 'json'
        stripped = text.lstrip()
        if stripped.startswith('{'):
            return 'json'
        return 'yaml'

    def _parse(self, text: str, fmt: str) -> Any:
        try:
            if fmt == 'json':
                return json.loads(text)
            # YAML handles both yaml and .flow (before envelope detection)
            return yaml.safe_load(text)
        except json.JSONDecodeError as e:
            diag = Diagnostic(
                rule_id='TRANSPORT-001',
                layer='transport',
                kind=DiagnosticKind.VIOLATION,
                checkability=Checkability.OFFLINE,
                message=f'JSON syntax error: {e.msg}',
            )
            raise DiagnosticParseError(diag, original=e) from e
        except yaml.YAMLError as e:
            self._raise_yaml_error(e)

    @staticmethod
    def _raise_yaml_error(e: yaml.YAMLError) -> None:
        """Convert a YAML error to DiagnosticParseError."""
        problem = getattr(e, 'problem', str(e))
        mark = getattr(e, 'problem_mark', None)
        location = ''
        if mark is not None:
            location = f' at line {mark.line + 1}, column {mark.column + 1}'
        diag = Diagnostic(
            rule_id='TRANSPORT-002',
            layer='transport',
            kind=DiagnosticKind.VIOLATION,
            checkability=Checkability.OFFLINE,
            message=f'YAML syntax error{location}: {problem}',
        )
        raise DiagnosticParseError(diag, original=e) from e
