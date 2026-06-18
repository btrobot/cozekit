"""Phase 3 verification: Sema layer (scope/symbol/type/value/reference).

Tests:
1. Symbol table: register all nodes and canvases
2. Type system: infer types, check compatibility
3. Reference resolution: resolve node refs and global variable refs
4. Query authority: pass-facing interface works
5. Legacy oracle: symbol count matches AnalysisGraph node count
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
def build_sema():
    from cozekit.transport.normalizer import TransportNormalizer
    from cozekit.transport.input_source import InputSource
    from cozekit.ast.builder import ASTBuilder
    from cozekit.ast.analysis_graph import AnalysisGraphBuilder
    from cozekit.sema.symbol_table import SymbolTable
    from cozekit.sema.reference_resolution import resolve_all_refs
    from cozekit.sema.query_authority import WorkflowSemaQueryAuthority

    def _build(text: str):
        normalizer = TransportNormalizer()
        doc = normalizer.normalize(InputSource(text=text))
        ast = ASTBuilder().build(doc)
        flat, indices = AnalysisGraphBuilder().build(ast)
        symtab = SymbolTable(flat, indices)
        resolution_table = resolve_all_refs(flat, symtab)
        query = WorkflowSemaQueryAuthority(symtab, resolution_table)
        return symtab, query, flat, indices
    return _build


class TestSymbolTable:
    """Symbol table must register all entities from AnalysisGraph."""

    def test_empty_workflow(self, build_sema):
        symtab, _, _, _ = build_sema('nodes: []')
        assert symtab.node_count() == 0
        assert symtab.canvas_count() >= 1  # root canvas

    def test_registers_nodes(self, build_sema):
        text = 'nodes:\n  - id: "1"\n    type: "1"\n  - id: "2"\n    type: "2"\n'
        symtab, _, _, _ = build_sema(text)
        assert symtab.node_count() == 2

    def test_registers_canvases(self, build_sema):
        text = 'nodes:\n  - id: "1"\n    type: "1"\n'
        symtab, _, _, _ = build_sema(text)
        assert symtab.canvas_count() >= 1

    def test_registers_subcanvas_nodes(self, build_sema):
        text = """nodes:
  - id: "loop-1"
    type: "21"
    blocks:
      - id: "inner-1"
        type: "28"
    edges:
      - sourceNodeID: "loop-1"
        targetNodeID: "inner-1"
"""
        symtab, _, _, _ = build_sema(text)
        assert symtab.node_count() == 2  # loop-1 + inner-1

    def test_lookup_node(self, build_sema):
        text = 'nodes:\n  - id: "start"\n    type: "1"\n'
        symtab, _, _, _ = build_sema(text)
        # Node is at root canvas path ()
        node_sym = symtab.lookup_node(('start',))
        assert node_sym is not None
        assert node_sym.node.node_id == 'start'

    def test_nodes_in_canvas(self, build_sema):
        text = 'nodes:\n  - id: "1"\n    type: "1"\n  - id: "2"\n    type: "2"\n'
        symtab, _, _, _ = build_sema(text)
        nodes = symtab.nodes_in_canvas(())
        assert len(nodes) == 2


class TestTypeSystem:
    """Type system must infer and compare types correctly."""

    def test_scalar_types(self):
        from cozekit.sema.type_system import infer_type, TypeCategory
        fact = infer_type('string')
        assert fact.category == TypeCategory.SCALAR
        assert fact.canonical_type == 'string'

    def test_type_synonyms(self):
        from cozekit.sema.type_system import canonicalize_type
        assert canonicalize_type('str') == 'string'
        assert canonicalize_type('int') == 'integer'
        assert canonicalize_type('bool') == 'boolean'
        assert canonicalize_type('array') == 'list'
        assert canonicalize_type('map') == 'object'

    def test_global_variable_deferred(self):
        from cozekit.sema.type_system import infer_type, TypeCategory
        fact = infer_type('string', ref_source='global_variable_app')
        assert fact.category == TypeCategory.RUNTIME_DEFERRED

    def test_compatibility(self):
        from cozekit.sema.type_system import infer_type, check_compatibility, CompatibilityState
        s1 = infer_type('string')
        s2 = infer_type('integer')
        assert check_compatibility(s1, s2) == CompatibilityState.INCOMPATIBLE  # exact match required

    def test_incompatible_types(self):
        from cozekit.sema.type_system import infer_type, check_compatibility, CompatibilityState
        obj = infer_type('object')
        lst = infer_type('list')
        assert check_compatibility(obj, lst) == CompatibilityState.INCOMPATIBLE


class TestReferenceResolution:
    """Reference resolution must find targets correctly."""

    def test_node_ref_resolved(self, build_sema):
        text = """nodes:
  - id: "source-1"
    type: "1"
    data:
      inputs:
        - name: "val"
          inputRef:
            source: "node"
            blockID: "source-1"
            name: "output"
  - id: "target-1"
    type: "2"
"""
        symtab, query, _, _ = build_sema(text)
        result = query.resolve_full_ref('node', 'source-1', 'output')
        assert result.target_node_path  # resolved to a node path
        assert not result.is_unresolved

    def test_global_variable_ref(self, build_sema):
        text = 'nodes:\n  - id: "1"\n    type: "1"\n'
        symtab, query, _, _ = build_sema(text)
        result = query.resolve_full_ref('global_variable_app', None, 'my_var')
        assert result.is_global is True

    def test_unresolved_ref(self, build_sema):
        text = 'nodes:\n  - id: "1"\n    type: "1"\n'
        symtab, query, _, _ = build_sema(text)
        result = query.resolve_full_ref('node', 'nonexistent', 'output')
        assert result.is_unresolved is True


class TestQueryAuthority:
    """Query authority must provide pass-facing interface."""

    def test_lookup_symbol(self, build_sema):
        text = 'nodes:\n  - id: "node-1"\n    type: "1"\n'
        symtab, query, _, _ = build_sema(text)
        info = query.lookup_symbol('node-1')
        assert info is not None
        assert info.kind == 'node'
        assert info.node_type == '1'

    def test_symbols_in_scope(self, build_sema):
        text = 'nodes:\n  - id: "1"\n    type: "1"\n  - id: "2"\n    type: "2"\n'
        symtab, query, _, _ = build_sema(text)
        symbols = query.symbols_in_scope(())
        assert len(symbols) == 2

    def test_type_of(self, build_sema):
        text = 'nodes:\n  - id: "1"\n    type: "1"\n'
        symtab, query, _, _ = build_sema(text)
        # Type of a node is inferred from node_type
        node_sym = symtab.lookup_node(('1',))
        assert node_sym is not None
        t = query.type_of(node_sym.node_path)
        # Type for a node might not be directly meaningful, but should not crash
        # (type_of is more useful for parameters)


class TestLegacyOracle:
    """Symbol table node count must match AnalysisGraph node count for all corpus samples."""

    @pytest.mark.parametrize('fixture_id', [
        'fixture-minimal-start-end',
        'fixture-if-missing-branch-ports',
        'fixture-loop-nested-batch',
        'fixture-global-variable-type-mismatch',
        'fixture-non-assign-global-ref-read',
        'fixture-title-rules',
        'fixture-loop-partial-subcanvas-ports',
    ])
    def test_symbol_count_matches_ir(self, fixture_id, build_sema, ir_baseline):
        baseline = ir_baseline.get(fixture_id)
        if baseline is None:
            pytest.skip('No baseline')
        yaml_path = YAML_DIR / f'{fixture_id}.yaml'
        text = yaml_path.read_text()
        symtab, _, _, _ = build_sema(text)
        assert symtab.node_count() == baseline['ir_node_count'], \
            f'{fixture_id}: expected {baseline["ir_node_count"]} symbols, got {symtab.node_count()}'
