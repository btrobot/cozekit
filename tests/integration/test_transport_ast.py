"""Phase 1 verification: transport normalization + AST builder.

Tests:
1. Transport normalization: YAML/JSON produce same AST structure
2. AST builder: correct node/edge extraction from oracle corpus
3. Legacy oracle: new AST node/edge counts match old API baseline
4. Source span: provenance is carried through
"""

import json
from pathlib import Path

import pytest
import yaml

FIXTURES_DIR = Path(__file__).parent.parent / 'fixtures'
YAML_DIR = FIXTURES_DIR / 'yaml'
JSON_DIR = FIXTURES_DIR / 'json'
EXPECTED_DIR = FIXTURES_DIR / 'expected'


@pytest.fixture
def oracle_baseline():
    path = EXPECTED_DIR / 'oracle_baseline.json'
    with open(path) as f:
        return {r['fixture_id']: r for r in json.load(f)}


@pytest.fixture
def normalizer():
    from cozekit.transport.normalizer import TransportNormalizer
    return TransportNormalizer()


@pytest.fixture
def ast_builder():
    from cozekit.ast.builder import ASTBuilder
    return ASTBuilder()


class TestTransportNormalization:
    """Transport normalization isolates format differences."""

    def test_yaml_parse(self, normalizer):
        from cozekit.transport.input_source import InputSource
        doc = normalizer.normalize(InputSource(text='nodes: []'))
        assert doc.transport_format == 'yaml'
        assert doc.raw_document == {'nodes': []}

    def test_json_parse(self, normalizer):
        from cozekit.transport.input_source import InputSource
        doc = normalizer.normalize(InputSource(text='{"nodes": []}'))
        assert doc.transport_format == 'json'
        assert doc.raw_document == {'nodes': []}

    def test_yaml_json_same_ast(self, normalizer, ast_builder):
        """YAML and JSON input with same content must produce same AST."""
        from cozekit.transport.input_source import InputSource
        yaml_text = 'nodes:\n  - id: "1"\n    type: "1"\n'
        json_text = '{"nodes": [{"id": "1", "type": "1"}]}'
        yaml_doc = normalizer.normalize(InputSource(text=yaml_text))
        json_doc = normalizer.normalize(InputSource(text=json_text))
        yaml_ast = ast_builder.build(yaml_doc)
        json_ast = ast_builder.build(json_doc)
        assert len(yaml_ast.root_canvas.nodes) == len(json_ast.root_canvas.nodes)
        assert len(yaml_ast.root_canvas.edges) == len(json_ast.root_canvas.edges)
        assert yaml_ast.root_canvas.nodes[0].node_id == json_ast.root_canvas.nodes[0].node_id

    def test_flow_format_detected(self, normalizer):
        from cozekit.transport.input_source import InputSource
        doc = normalizer.normalize(InputSource(text='nodes: []', format_hint='flow'))
        assert doc.transport_format == 'flow'

    def test_flow_envelope_unpacked(self, normalizer):
        """A .flow file with 'canvas' key should be unpacked."""
        from cozekit.transport.input_source import InputSource
        flow_text = 'canvas:\n  nodes:\n    - id: "1"\n      type: "1"\n'
        doc = normalizer.normalize(InputSource(text=flow_text, format_hint='flow'))
        assert isinstance(doc.raw_document, dict)
        assert 'nodes' in doc.raw_document


class TestASTBuilder:
    """AST builder extracts correct structure from normalized documents."""

    def test_empty_workflow(self, normalizer, ast_builder):
        from cozekit.transport.input_source import InputSource
        doc = normalizer.normalize(InputSource(text='nodes: []'))
        ast = ast_builder.build(doc)
        assert len(ast.root_canvas.nodes) == 0
        assert len(ast.root_canvas.edges) == 0

    def test_single_node(self, normalizer, ast_builder):
        from cozekit.transport.input_source import InputSource
        text = 'nodes:\n  - id: "100001"\n    type: "1"\n'
        doc = normalizer.normalize(InputSource(text=text))
        ast = ast_builder.build(doc)
        assert len(ast.root_canvas.nodes) == 1
        node = ast.root_canvas.nodes[0]
        assert node.node_id == '100001'
        assert node.node_type == '1'

    def test_node_title_extracted(self, normalizer, ast_builder):
        from cozekit.transport.input_source import InputSource
        text = 'nodes:\n  - id: "1"\n    type: "1"\n    data:\n      nodeMeta:\n        title: Start\n'
        doc = normalizer.normalize(InputSource(text=text))
        ast = ast_builder.build(doc)
        assert ast.root_canvas.nodes[0].title == 'Start'

    def test_edges_extracted(self, normalizer, ast_builder):
        from cozekit.transport.input_source import InputSource
        text = 'nodes:\n  - id: "1"\n    type: "1"\nedges:\n  - sourceNodeID: "1"\n    targetNodeID: "2"\n'
        doc = normalizer.normalize(InputSource(text=text))
        ast = ast_builder.build(doc)
        assert len(ast.root_canvas.edges) == 1
        edge = ast.root_canvas.edges[0]
        assert edge.source_node_id == '1'
        assert edge.target_node_id == '2'

    def test_no_semantic_markers(self, normalizer, ast_builder):
        """AST must not contain semantic markers like node_id_is_string."""
        from cozekit.transport.input_source import InputSource
        text = 'nodes:\n  - id: "1"\n    type: "1"\n'
        doc = normalizer.normalize(InputSource(text=text))
        ast = ast_builder.build(doc)
        node = ast.root_canvas.nodes[0]
        assert not hasattr(node, 'node_id_is_string')


class TestLegacyOracle:
    """New AST must match old API's node/edge counts for all corpus samples."""

    @pytest.mark.parametrize('fixture_id', [
        'fixture-minimal-start-end',
        'fixture-if-missing-branch-ports',
        'fixture-loop-nested-batch',
        'fixture-global-variable-type-mismatch',
        'fixture-non-assign-global-ref-read',
        'fixture-title-rules',
        'fixture-loop-partial-subcanvas-ports',
    ])
    def test_node_count_matches(self, fixture_id, normalizer, ast_builder, oracle_baseline):
        from cozekit.compiler_v2_api import compile_text
        baseline = oracle_baseline.get(fixture_id)
        if baseline is None:
            pytest.skip('No baseline')
        yaml_path = YAML_DIR / f'{fixture_id}.yaml'
        text = yaml_path.read_text()
        from cozekit.transport.input_source import InputSource
        doc = normalizer.normalize(InputSource(text=text))
        ast = ast_builder.build(doc)
        assert len(ast.root_canvas.nodes) == baseline['node_count'], \
            f'{fixture_id}: expected {baseline["node_count"]} nodes, got {len(ast.root_canvas.nodes)}'

    @pytest.mark.parametrize('fixture_id', [
        'fixture-minimal-start-end',
        'fixture-if-missing-branch-ports',
        'fixture-loop-nested-batch',
        'fixture-global-variable-type-mismatch',
        'fixture-non-assign-global-ref-read',
        'fixture-title-rules',
        'fixture-loop-partial-subcanvas-ports',
    ])
    def test_edge_count_matches(self, fixture_id, normalizer, ast_builder, oracle_baseline):
        baseline = oracle_baseline.get(fixture_id)
        if baseline is None:
            pytest.skip('No baseline')
        yaml_path = YAML_DIR / f'{fixture_id}.yaml'
        text = yaml_path.read_text()
        from cozekit.transport.input_source import InputSource
        doc = normalizer.normalize(InputSource(text=text))
        ast = ast_builder.build(doc)
        assert len(ast.root_canvas.edges) == baseline['edge_count'], \
            f'{fixture_id}: expected {baseline["edge_count"]} edges, got {len(ast.root_canvas.edges)}'

    @pytest.mark.parametrize('fixture_id', [
        'fixture-minimal-start-end',
        'fixture-if-missing-branch-ports',
        'fixture-loop-nested-batch',
        'fixture-global-variable-type-mismatch',
        'fixture-non-assign-global-ref-read',
        'fixture-title-rules',
        'fixture-loop-partial-subcanvas-ports',
    ])
    def test_node_ids_match(self, fixture_id, normalizer, ast_builder, oracle_baseline):
        baseline = oracle_baseline.get(fixture_id)
        if baseline is None:
            pytest.skip('No baseline')
        yaml_path = YAML_DIR / f'{fixture_id}.yaml'
        text = yaml_path.read_text()
        from cozekit.transport.input_source import InputSource
        doc = normalizer.normalize(InputSource(text=text))
        ast = ast_builder.build(doc)
        new_ids = sorted([n.node_id for n in ast.root_canvas.nodes])
        assert new_ids == baseline['node_ids'], \
            f'{fixture_id}: expected {baseline["node_ids"]}, got {new_ids}'


class TestSourceProvenance:
    """Source provenance must be carried through all AST nodes."""

    def test_node_has_provenance(self, normalizer, ast_builder):
        from cozekit.transport.input_source import InputSource
        text = 'nodes:\n  - id: "1"\n    type: "1"\n'
        doc = normalizer.normalize(InputSource(text=text, source_file='test.yaml'))
        ast = ast_builder.build(doc)
        node = ast.root_canvas.nodes[0]
        assert node.provenance.source_file == 'test.yaml'

    def test_edge_has_provenance(self, normalizer, ast_builder):
        from cozekit.transport.input_source import InputSource
        text = 'nodes:\n  - id: "1"\n    type: "1"\nedges:\n  - sourceNodeID: "1"\n    targetNodeID: "2"\n'
        doc = normalizer.normalize(InputSource(text=text, source_file='test.yaml'))
        ast = ast_builder.build(doc)
        edge = ast.root_canvas.edges[0]
        assert edge.provenance.source_file == 'test.yaml'
