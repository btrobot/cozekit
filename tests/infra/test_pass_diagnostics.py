"""Phase 4 verification: Pass framework + Diagnostics.

Tests:
1. Pass registry: registers and runs passes
2. Example pass: emits correct diagnostics
3. Diagnostics assembly: multi-pass merge into report
4. Report contract: correct summary counts
5. Clean corpus samples: 0 diagnostics for clean inputs
"""

import json
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent.parent / 'fixtures'
YAML_DIR = FIXTURES_DIR / 'yaml'
EXPECTED_DIR = FIXTURES_DIR / 'expected'


@pytest.fixture
def oracle_baseline():
    path = EXPECTED_DIR / 'oracle_baseline.json'
    with open(path) as f:
        return {r['fixture_id']: r for r in json.load(f)}


class TestPassRegistry:
    """Pass registry manages pass execution."""

    def test_empty_registry(self):
        from cozekit.passes.registry import PassRegistry
        from cozekit.transport.normalizer import TransportNormalizer
        from cozekit.transport.input_source import InputSource
        from cozekit.ast.builder import ASTBuilder
        from cozekit.ast.analysis_graph import AnalysisGraphBuilder
        from cozekit.sema.symbol_table import SymbolTable
        from cozekit.sema.query_authority import WorkflowSemaQueryAuthority

        from cozekit.passes.context import PassContext
        registry = PassRegistry()
        normalizer = TransportNormalizer()
        doc = normalizer.normalize(InputSource(text='nodes: []'))
        ast = ASTBuilder().build(doc)
        flat, indices = AnalysisGraphBuilder().build(ast)
        symtab = SymbolTable(flat, indices)
        sema = WorkflowSemaQueryAuthority(symtab)
        ctx = PassContext(sema=sema, source_file=doc.source_file, transport_format=doc.transport_format)
        result = registry.run_all(ctx)
        assert result == ()

    def test_register_and_run(self):
        from cozekit.passes.registry import PassRegistry
        from cozekit.passes.protocol import CompilerPass
        from cozekit.passes.context import PassContext
        from cozekit.passes.diag_helper import make_diag

        class _StubPass:
            name = 'stub'
            def run(self, ctx: PassContext):
                return ()

        registry = PassRegistry()
        registry.register(_StubPass())
        assert len(registry._passes) == 1


class TestExamplePass:
    """Example pass emits diagnostics correctly."""

    def test_empty_workflow_warning(self):
        from cozekit.compiler_v2_api import compile_text
        report = compile_text('nodes: []')
        # Empty workflow triggers SYNTAX-003 (missing edges) and BE-006 (bad shape)
        syntax_diags = [d for d in report.diagnostics if d.rule_id.startswith('SYNTAX')]
        assert len(syntax_diags) >= 1

    def test_valid_workflow_no_violations(self):
        from cozekit.compiler_v2_api import compile_text
        text = (
            'nodes:\n'
            '  - id: "100001"\n'
            '    type: "1"\n'
            '    data:\n'
            '      nodeMeta:\n'
            '        title: "Start"\n'
            '  - id: "900001"\n'
            '    type: "2"\n'
            '    data:\n'
            '      nodeMeta:\n'
            '        title: "End"\n'
            'edges:\n'
            '  - sourceNodeID: "100001"\n'
            '    targetNodeID: "900001"\n'
        )
        report = compile_text(text)
        violations = [d for d in report.diagnostics if d.kind.value == 'violation']
        assert len(violations) == 0

    def test_dangling_edge_violation(self):
        from cozekit.compiler_v2_api import compile_text
        text = 'nodes:\n  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\nedges:\n  - sourceNodeID: "100001"\n    targetNodeID: "nonexistent"\n'
        report = compile_text(text)
        # Dangling edge should be caught by SYNTAX or BE rules
        violations = [d for d in report.diagnostics if d.kind.value == 'violation']
        assert len(violations) >= 1


class TestDiagnosticsAssembly:
    """Diagnostics layer assembles reports correctly."""

    def test_report_summary_counts(self):
        from cozekit.compiler_v2_api import compile_text
        report = compile_text('nodes: []')
        summary = report.summary
        assert summary.total >= 1  # at least SYNTAX-003 violation
        assert summary.violations >= 1

    def test_report_has_required_fields(self):
        from cozekit.compiler_v2_api import compile_text
        report = compile_text('nodes: []')
        d = report.to_dict()
        assert 'diagnostics' in d
        assert 'summary' in d
        assert 'source_file' in d
        assert 'total' in d['summary']
        assert 'violations' in d['summary']
        assert 'warnings' in d['summary']

    def test_report_exit_code(self):
        from cozekit.compiler_v2_api import compile_text
        # Clean report (no violations) → exit_code 0
        clean = compile_text('nodes:\n  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\nedges:\n  - sourceNodeID: "100001"\n    targetNodeID: "900001"\n')
        assert clean.exit_code == 0


class TestCleanCorpusSamples:
    """Clean corpus samples (expected 0 diagnostics) should remain clean."""

    @pytest.mark.parametrize('fixture_id', [
        'fixture-minimal-start-end',
    ])
    def test_clean_sample_has_no_violations(self, fixture_id, oracle_baseline):
        from cozekit.compiler_v2_api import compile_text
        baseline = oracle_baseline.get(fixture_id)
        if baseline is None:
            pytest.skip('No baseline')
        if baseline.get('diag_count', 0) > 0:
            pytest.skip('Not a clean sample')
        yaml_path = YAML_DIR / f'{fixture_id}.yaml'
        text = yaml_path.read_text()
        report = compile_text(text)
        violations = [d for d in report.diagnostics if d.kind.value == 'violation']
        assert len(violations) == 0, \
            f'{fixture_id}: expected 0 violations, got {len(violations)}: {[d.rule_id for d in violations]}'


class TestPassDiagnosticsSeparation:
    """Pass emits diagnostics, diagnostics layer assembles report. Clear boundary."""

    def test_pass_does_not_assemble_report(self):
        """Pass.run returns tuple of Diagnostic, not a report."""
        from cozekit.passes.syntax.syntax_pass import SyntaxPass
        from cozekit.transport.normalizer import TransportNormalizer
        from cozekit.transport.input_source import InputSource
        from cozekit.ast.builder import ASTBuilder
        from cozekit.ast.analysis_graph import AnalysisGraphBuilder
        from cozekit.sema.symbol_table import SymbolTable
        from cozekit.sema.query_authority import WorkflowSemaQueryAuthority
        from cozekit.diagnostics.core import Diagnostic

        from cozekit.passes.context import PassContext
        p = SyntaxPass()
        normalizer = TransportNormalizer()
        doc = normalizer.normalize(InputSource(text='nodes: []'))
        ast = ASTBuilder().build(doc)
        flat, indices = AnalysisGraphBuilder().build(ast)
        symtab = SymbolTable(flat, indices)
        sema = WorkflowSemaQueryAuthority(symtab)
        ctx = PassContext(sema=sema, source_file=doc.source_file, transport_format=doc.transport_format)
        result = p.run(ctx)
        assert isinstance(result, tuple)
        assert all(isinstance(d, Diagnostic) for d in result)
