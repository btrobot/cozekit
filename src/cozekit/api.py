"""cozekit public API — compile_text, compile_path, compile_source."""
from __future__ import annotations

import sys
from pathlib import Path

from .transport.input_source import InputSource
from .pipeline import CompilerV2Pipeline
from .diagnostics.report import CompilerV2Report
from .passes.syntax.syntax_pass import SyntaxPass
from .passes.semantic_pass import SemanticPass
from .passes.portability.portability_pass import PortabilityPass


_pipeline: CompilerV2Pipeline | None = None


def _get_pipeline() -> CompilerV2Pipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = CompilerV2Pipeline()
        _pipeline.pass_registry.register(SyntaxPass())
        _pipeline.pass_registry.register(SemanticPass())
        _pipeline.pass_registry.register(PortabilityPass())
    return _pipeline


def compile_text(text: str, *, source_file: str | None = None) -> CompilerV2Report:
    """Compile YAML/JSON text to a CompilerV2Report."""
    source = InputSource(text=text, source_file=source_file)
    return _get_pipeline().compile_source(source)


def compile_path(path: str | Path) -> CompilerV2Report:
    """Compile a YAML/JSON/.flow file to a CompilerV2Report."""
    source = InputSource(path=Path(path))
    return _get_pipeline().compile_source(source)


def compile_source(source: InputSource) -> CompilerV2Report:
    """Compile an InputSource to a CompilerV2Report."""
    return _get_pipeline().compile_source(source)
