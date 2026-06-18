"""Compiler pipeline - orchestrates all phases.

Single-pass architecture:
  Transport -> AST -> AnalysisGraph -> Sema -> Passes -> Report

One SymbolTable build — resolve_all_refs produces ResolutionTable.
"""

from __future__ import annotations

from .transport.input_source import InputSource, ParsedDocument
from .transport.normalizer import TransportNormalizer
from .ast.builder import ASTBuilder
from .ast.analysis_graph import AnalysisGraphBuilder
from .sema.symbol_table import SymbolTable
from .sema.query_authority import WorkflowSemaQueryAuthority
from .sema.reference_resolution import resolve_all_refs
from .passes.registry import PassRegistry
from .passes.context import PassContext
from .diagnostics.report import CompilerV2Report
from .diagnostics.core import DiagnosticParseError


class CompilerV2Pipeline:
    """Default pipeline: transport -> AST -> AnalysisGraph -> Sema -> passes -> report."""

    def __init__(self) -> None:
        self.transport_normalizer = TransportNormalizer()
        self.ast_builder = ASTBuilder()
        self.analysis_graph_builder = AnalysisGraphBuilder()
        self.pass_registry = PassRegistry()

    def compile_source(self, source: InputSource) -> CompilerV2Report:
        try:
            document = self.transport_normalizer.normalize(source)
        except DiagnosticParseError as e:
            return CompilerV2Report(
                diagnostics=[e.diagnostic],
                source_file=getattr(source, 'source_file', None) or (str(source.path) if source.path else None),
            )
        return self.compile_document(document)

    def compile_document(self, document: ParsedDocument) -> CompilerV2Report:
        ast = self.ast_builder.build(document)

        # Flat graph building (successor to IRBuilder)
        version_is_valid = isinstance(document.versions, dict) if document.versions is not None else None
        flat, indices = self.analysis_graph_builder.build(
            ast,
            versions=document.versions,
            version_is_valid=version_is_valid,
            envelope_type=document.envelope_type,
        )

        # Build sema from AST types
        symtab = SymbolTable(flat, indices)
        resolution_table = resolve_all_refs(flat, symtab)
        sema = WorkflowSemaQueryAuthority(symtab, resolution_table)

        ctx = PassContext(
            ast=ast,
            sema=sema,
            source_text=document.source_text,
            source_file=document.source_file,
            transport_format=document.transport_format,
            span_map=document.span_map,
        )

        all_diagnostics = self.pass_registry.run_all(ctx)

        return CompilerV2Report(
            diagnostics=all_diagnostics,
            source_file=document.source_file,
        )
