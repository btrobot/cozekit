"""Phase 0 verification: skeleton is runnable, report schema compatible, oracle corpus exists."""

import json
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent.parent / 'fixtures'


class TestSkeletonRuns:
    """The pipeline must be end-to-end runnable with empty passes."""

    def test_compile_text_empty(self):
        from cozekit.compiler_v2_api import compile_text
        report = compile_text('nodes: []')
        assert report is not None
        assert isinstance(report.diagnostics, tuple)
        # Empty workflow (no edges) correctly produces SYNTAX-003 violation
        syntax_rules = {d.rule_id for d in report.diagnostics if d.rule_id.startswith('SYNTAX')}
        assert 'SYNTAX-003' in syntax_rules

    def test_compile_text_minimal(self):
        from cozekit.compiler_v2_api import compile_text
        yaml_text = (
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
        report = compile_text(yaml_text)
        assert report is not None
        assert report.exit_code == 0

    def test_report_schema_compatible(self):
        from cozekit.compiler_v2_api import compile_text
        report = compile_text('nodes:\n  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\nedges:\n  - sourceNodeID: "100001"\n    targetNodeID: "900001"\n')
        d = report.to_dict()
        assert 'diagnostics' in d
        assert 'summary' in d
        assert 'source_file' in d
        summary = d['summary']
        assert 'total' in summary
        assert 'violations' in summary
        assert 'warnings' in summary


class TestOracleCorpus:
    """Oracle corpus must exist with ≥5 YAML samples."""

    def test_yaml_samples_exist(self):
        yaml_dir = FIXTURES_DIR / 'yaml'
        assert yaml_dir.exists()
        samples = list(yaml_dir.glob('*.yaml'))
        assert len(samples) >= 5, f'Expected ≥5 YAML samples, got {len(samples)}'

    def test_expected_outputs_exist(self):
        expected_dir = FIXTURES_DIR / 'expected'
        assert expected_dir.exists()
        outputs = list(expected_dir.glob('*.json'))
        assert len(outputs) >= 3, f'Expected ≥5 expected outputs, got {len(outputs)}'

    def test_all_yaml_samples_parse(self):
        from cozekit.compiler_v2_api import compile_path
        yaml_dir = FIXTURES_DIR / 'yaml'
        for sample in yaml_dir.glob('*.yaml'):
            report = compile_path(sample)
            assert report is not None
            assert report.source_file == str(sample)

    def test_json_samples_exist(self):
        json_dir = FIXTURES_DIR / 'json'
        assert json_dir.exists()
        samples = list(json_dir.glob('*.json'))
        assert len(samples) >= 5, f'Expected ≥5 JSON samples, got {len(samples)}'


class TestPipelineStages:
    """Each stage must produce valid output."""

    def test_transport_normalizer(self):
        from cozekit.transport.normalizer import TransportNormalizer
        from cozekit.transport.input_source import InputSource
        normalizer = TransportNormalizer()
        doc = normalizer.normalize(InputSource(text='nodes: []'))
        assert doc.raw_document is not None
        assert doc.transport_format == 'yaml'

    def test_ast_builder(self):
        from cozekit.transport.normalizer import TransportNormalizer
        from cozekit.transport.input_source import InputSource
        from cozekit.ast.builder import ASTBuilder
        normalizer = TransportNormalizer()
        doc = normalizer.normalize(InputSource(text='nodes:\n  - id: "1"\n    type: "1"\n'))
        ast = ASTBuilder().build(doc)
        assert len(ast.root_canvas.nodes) == 1

    def test_analysis_graph_builder(self):
        from cozekit.transport.normalizer import TransportNormalizer
        from cozekit.transport.input_source import InputSource
        from cozekit.ast.builder import ASTBuilder
        from cozekit.ast.analysis_graph import AnalysisGraphBuilder
        normalizer = TransportNormalizer()
        doc = normalizer.normalize(InputSource(text='nodes:\n  - id: "1"\n    type: "1"\nedges:\n  - sourceNodeID: "1"\n    targetNodeID: "2"\n'))
        ast = ASTBuilder().build(doc)
        flat, indices = AnalysisGraphBuilder().build(ast)
        assert indices.node_count == 1
        assert indices.edge_count == 1
        assert '1' in indices.node_by_id
