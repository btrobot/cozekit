"""AnalysisGraph + ASTIndices verification — successor to test_phase2_ir.py.

Tests:
1. AnalysisGraphBuilder: correct flattening from AST (no lowering)
2. ASTIndices construction: O(1) lookup by node_id, canvas_path, type
3. Legacy oracle: new AnalysisGraph node/edge counts match old IR baseline
4. Nested canvas handling: subcanvas nodes appear in flat graph
5. Global var node detection
"""

import json
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent.parent / 'fixtures'
YAML_DIR = FIXTURES_DIR / 'yaml'
EXPECTED_DIR = FIXTURES_DIR / 'expected'


@pytest.fixture
def ir_baseline():
    path = EXPECTED_DIR / 'ir_baseline.json'
    with open(path) as f:
        return {r['fixture_id']: r for r in json.load(f) if 'error' not in r}


@pytest.fixture
def build_analysis_graph():
    from cozekit.transport.normalizer import TransportNormalizer
    from cozekit.transport.input_source import InputSource
    from cozekit.ast.builder import ASTBuilder
    from cozekit.ast.analysis_graph import AnalysisGraphBuilder

    def _build(text: str, source_file: str | None = None):
        normalizer = TransportNormalizer()
        doc = normalizer.normalize(InputSource(text=text, source_file=source_file))
        ast = ASTBuilder().build(doc)
        flat, indices = AnalysisGraphBuilder().build(ast)
        return flat, indices, ast
    return _build


class TestAnalysisGraphBuilder:
    """AnalysisGraphBuilder flattens AST correctly."""

    def test_empty_workflow(self, build_analysis_graph):
        flat, indices, _ = build_analysis_graph('nodes: []')
        assert len(flat.canvases) == 1
        assert indices.node_count == 0
        assert indices.edge_count == 0

    def test_single_node(self, build_analysis_graph):
        flat, indices, _ = build_analysis_graph('nodes:\n  - id: "1"\n    type: "1"\n')
        assert indices.node_count == 1
        assert '1' in indices.node_by_id
        node = indices.node_by_id['1']
        assert node.node_id == '1'
        assert node.node_type == '1'

    def test_edges_indexed(self, build_analysis_graph):
        text = 'nodes:\n  - id: "1"\n    type: "1"\n  - id: "2"\n    type: "2"\nedges:\n  - sourceNodeID: "1"\n    targetNodeID: "2"\n'
        flat, indices, _ = build_analysis_graph(text)
        assert indices.edge_count == 1
        assert '1' in indices.edges_by_source
        assert '2' in indices.edges_by_target
        edge = indices.edges_by_source['1'][0]
        assert edge.source_node_id == '1'
        assert edge.target_node_id == '2'

    def test_subcanvas_nodes_in_analysis_graph(self, build_analysis_graph):
        """Composite nodes with blocks/edges produce multiple canvases in flat graph."""
        text = """nodes:
  - id: "100001"
    type: "1"
  - id: "loop-1"
    type: "21"
    blocks:
      - id: "batch-1"
        type: "28"
    edges:
      - sourceNodeID: "loop-1"
        targetNodeID: "batch-1"
  - id: "900001"
    type: "2"
edges:
  - sourceNodeID: "100001"
    targetNodeID: "loop-1"
  - sourceNodeID: "loop-1"
    targetNodeID: "900001"
"""
        flat, indices, ast = build_analysis_graph(text)
        # Root: 3 nodes, 2 edges + subcanvas: 1 node, 1 edge = 4 nodes, 3 edges total
        assert indices.node_count >= 3  # at least top-level
        assert len(flat.canvases) >= 2  # root + subcanvas

    def test_global_var_nodes_computed(self, build_analysis_graph):
        """Global var nodes (type=11) are tracked in _global_var_nodes."""
        text = """nodes:
  - id: "100001"
    type: "1"
  - id: "set-1"
    type: "11"
  - id: "900001"
    type: "2"
edges:
  - sourceNodeID: "100001"
    targetNodeID: "set-1"
  - sourceNodeID: "set-1"
    targetNodeID: "900001"
"""
        flat, indices, _ = build_analysis_graph(text)
        assert 'set-1' in flat._global_var_nodes
        assert '100001' not in flat._global_var_nodes


class TestLegacyOracle:
    """New AnalysisGraph must match old IR's node/edge counts for all corpus samples."""

    @pytest.mark.parametrize('fixture_id', [
        'fixture-minimal-start-end',
        'fixture-if-missing-branch-ports',
        'fixture-loop-nested-batch',
        'fixture-global-variable-type-mismatch',
        'fixture-non-assign-global-ref-read',
        'fixture-title-rules',
        'fixture-loop-partial-subcanvas-ports',
    ])
    def test_analysis_graph_node_count_matches(self, fixture_id, build_analysis_graph, ir_baseline):
        baseline = ir_baseline.get(fixture_id)
        if baseline is None:
            pytest.skip('No baseline')
        yaml_path = YAML_DIR / f'{fixture_id}.yaml'
        text = yaml_path.read_text()
        flat, indices, _ = build_analysis_graph(text)
        assert indices.node_count == baseline['ir_node_count'], \
            f'{fixture_id}: expected {baseline["ir_node_count"]} nodes, got {indices.node_count}'

    @pytest.mark.parametrize('fixture_id', [
        'fixture-minimal-start-end',
        'fixture-if-missing-branch-ports',
        'fixture-loop-nested-batch',
        'fixture-global-variable-type-mismatch',
        'fixture-non-assign-global-ref-read',
        'fixture-title-rules',
        'fixture-loop-partial-subcanvas-ports',
    ])
    def test_analysis_graph_edge_count_matches(self, fixture_id, build_analysis_graph, ir_baseline):
        baseline = ir_baseline.get(fixture_id)
        if baseline is None:
            pytest.skip('No baseline')
        yaml_path = YAML_DIR / f'{fixture_id}.yaml'
        text = yaml_path.read_text()
        flat, indices, _ = build_analysis_graph(text)
        assert indices.edge_count == baseline['ir_edge_count'], \
            f'{fixture_id}: expected {baseline["ir_edge_count"]} edges, got {indices.edge_count}'

    @pytest.mark.parametrize('fixture_id', [
        'fixture-minimal-start-end',
        'fixture-if-missing-branch-ports',
        'fixture-loop-nested-batch',
        'fixture-global-variable-type-mismatch',
        'fixture-non-assign-global-ref-read',
        'fixture-title-rules',
        'fixture-loop-partial-subcanvas-ports',
    ])
    def test_analysis_graph_canvas_count_matches(self, fixture_id, build_analysis_graph, ir_baseline):
        baseline = ir_baseline.get(fixture_id)
        if baseline is None:
            pytest.skip('No baseline')
        yaml_path = YAML_DIR / f'{fixture_id}.yaml'
        text = yaml_path.read_text()
        flat, indices, _ = build_analysis_graph(text)
        assert len(flat.canvases) == baseline['ir_canvas_count'], \
            f'{fixture_id}: expected {baseline["ir_canvas_count"]} canvases, got {len(flat.canvases)}'


class TestASTIndicesLookup:
    """ASTIndices queries must be O(1)."""

    def test_lookup_by_node_id(self, build_analysis_graph):
        text = 'nodes:\n  - id: "start-1"\n    type: "1"\n  - id: "end-1"\n    type: "2"\n'
        flat, indices, _ = build_analysis_graph(text)
        node = indices.node_by_id.get('start-1')
        assert node is not None
        assert node.node_type == '1'

    def test_lookup_nonexistent_node(self, build_analysis_graph):
        text = 'nodes:\n  - id: "1"\n    type: "1"\n'
        flat, indices, _ = build_analysis_graph(text)
        assert indices.node_by_id.get('nonexistent') is None

    def test_edges_by_source(self, build_analysis_graph):
        text = 'nodes:\n  - id: "1"\n    type: "1"\n  - id: "2"\n    type: "2"\nedges:\n  - sourceNodeID: "1"\n    targetNodeID: "2"\n'
        flat, indices, _ = build_analysis_graph(text)
        out_edges = indices.edges_by_source.get('1', ())
        assert len(out_edges) == 1

    def test_nodes_by_canvas(self, build_analysis_graph):
        text = 'nodes:\n  - id: "1"\n    type: "1"\n  - id: "2"\n    type: "2"\n'
        flat, indices, _ = build_analysis_graph(text)
        nodes_in_root = indices.nodes_by_canvas.get('()', ())
        assert len(nodes_in_root) == 2
