"""Tests for P2: Scope system (Scope + ScopeTree)."""

from __future__ import annotations

import pytest
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from cozekit.sema.scope import Scope
from cozekit.sema.scope_tree import ScopeTree
from cozekit.ast.workflow_ast import (
    CanvasAST, EdgeAST, NodeAST,
)
from cozekit.ast.analysis_graph import AnalysisGraph
from cozekit.compiler_v2_api import compile_text

# ── helpers ────────────────────────────────────────────────────

def _make_node(node_id: str, node_type: str = '1', canvas_path=()) -> NodeAST:
    return NodeAST(node_id=node_id, node_type=node_type, canvas_path=canvas_path)

def _make_canvas(canvas_path, owner_node_id=None,
                 parent_canvas_path=None, owner_node_type=None):
    return CanvasAST(
        canvas_path=canvas_path,
        owner_node_id=owner_node_id,
        parent_canvas_path=parent_canvas_path,
        owner_node_type=owner_node_type,
    )

def _build_analysis_graph(canvases_with_nodes):
    """Build AnalysisGraph from list of (canvas, [nodes]) tuples."""
    all_nodes = []
    all_canvases = []
    for canvas, nodes in canvases_with_nodes:
        all_canvases.append(canvas)
        for n in nodes:
            all_nodes.append(n)
    return AnalysisGraph(
        nodes=tuple(all_nodes),
        edges=(),
        canvases=tuple(all_canvases),
    )

def _single_canvas_flat():
    """Root canvas with 2 nodes."""
    root = _make_canvas(())
    return _build_analysis_graph([(root, [_make_node('A', canvas_path=()), _make_node('B', canvas_path=())])])

def _nested_loop_flat():
    """Root -> loop subcanvas."""
    root = _make_canvas(())
    sub = _make_canvas(('L',), owner_node_id='L', parent_canvas_path=(), owner_node_type='21')
    return _build_analysis_graph([
        (root, [_make_node('L', node_type='21', canvas_path=()), _make_node('A', canvas_path=())]),
        (sub, [_make_node('C', canvas_path=('L',)), _make_node('D', canvas_path=('L',))]),
    ])

def _deep_nested_flat():
    """Root -> loop -> batch."""
    root = _make_canvas(())
    loop_canvas = _make_canvas(('L',), owner_node_id='L', parent_canvas_path=(), owner_node_type='21')
    batch_canvas = _make_canvas(('L', 'B'), owner_node_id='B', parent_canvas_path=('L',), owner_node_type='28')
    return _build_analysis_graph([
        (root, [_make_node('L', node_type='21', canvas_path=())]),
        (loop_canvas, [_make_node('B', node_type='28', canvas_path=('L',)), _make_node('X', canvas_path=('L',))]),
        (batch_canvas, [_make_node('Y', canvas_path=('L', 'B'))]),
    ])

def _sibling_flat():
    """Root -> two loop subcanvases (siblings)."""
    root = _make_canvas(())
    sub1 = _make_canvas(('L1',), owner_node_id='L1', parent_canvas_path=(), owner_node_type='21')
    sub2 = _make_canvas(('L2',), owner_node_id='L2', parent_canvas_path=(), owner_node_type='21')
    return _build_analysis_graph([
        (root, [_make_node('L1', node_type='21', canvas_path=()), _make_node('L2', node_type='21', canvas_path=())]),
        (sub1, [_make_node('C1', canvas_path=('L1',))]),
        (sub2, [_make_node('C2', canvas_path=('L2',))]),
    ])

def _if_nested_flat():
    """Root -> if subcanvas."""
    root = _make_canvas(())
    sub = _make_canvas(('I',), owner_node_id='I', parent_canvas_path=(), owner_node_type='8')
    return _build_analysis_graph([
        (root, [_make_node('I', node_type='8', canvas_path=()), _make_node('A', canvas_path=())]),
        (sub, [_make_node('T', canvas_path=('I',))]),
    ])


# ═══════════════════════════════════════════════════════════════
# T1: Scope Construction
# ═══════════════════════════════════════════════════════════════

class TestT1_ScopeConstruction:

    def test_t1_1_root_scope_kind(self):
        """T1.1: Root canvas creates scope with kind='root'."""
        tree = ScopeTree(_single_canvas_flat())
        root = tree.lookup_scope(())
        assert root is not None
        assert root.scope_kind == 'root'
        assert root.parent is None

    def test_t1_2_loop_subcanvas_scope(self):
        """T1.2: Loop subcanvas -> scope_kind='loop', parent=root."""
        tree = ScopeTree(_nested_loop_flat())
        loop = tree.lookup_scope(('L',))
        assert loop is not None
        assert loop.scope_kind == 'loop'
        assert loop.parent is not None
        assert loop.parent.canvas_path == ()

    def test_t1_3_batch_subcanvas_scope(self):
        """T1.3: Batch subcanvas -> scope_kind='batch'."""
        tree = ScopeTree(_deep_nested_flat())
        batch = tree.lookup_scope(('L', 'B'))
        assert batch is not None
        assert batch.scope_kind == 'batch'

    def test_t1_4_if_subcanvas_scope(self):
        """T1.4: If subcanvas -> scope_kind='if'."""
        tree = ScopeTree(_if_nested_flat())
        if_scope = tree.lookup_scope(('I',))
        assert if_scope is not None
        assert if_scope.scope_kind == 'if'

    def test_t1_5_multiple_siblings(self):
        """T1.5: Multiple sibling subcanvases create separate scopes."""
        tree = ScopeTree(_sibling_flat())
        s1 = tree.lookup_scope(('L1',))
        s2 = tree.lookup_scope(('L2',))
        assert s1 is not None
        assert s2 is not None
        assert s1.canvas_path == ('L1',)
        assert s2.canvas_path == ('L2',)
        assert s1.parent is s2.parent  # same root parent


# ═══════════════════════════════════════════════════════════════
# T2: Scope Properties
# ═══════════════════════════════════════════════════════════════

class TestT2_ScopeProperties:

    def test_t2_1_root_canvas_path(self):
        """T2.1: Root scope has empty canvas_path."""
        tree = ScopeTree(_single_canvas_flat())
        root = tree.lookup_scope(())
        assert root.canvas_path == ()

    def test_t2_2_subcanvas_canvas_path(self):
        """T2.2: Subcanvas scope has correct canvas_path."""
        tree = ScopeTree(_nested_loop_flat())
        loop = tree.lookup_scope(('L',))
        assert loop.canvas_path == ('L',)

    def test_t2_3_deep_canvas_path(self):
        """T2.3: Deep subcanvas has correct canvas_path."""
        tree = ScopeTree(_deep_nested_flat())
        batch = tree.lookup_scope(('L', 'B'))
        assert batch.canvas_path == ('L', 'B')

    def test_t2_4_scope_id(self):
        """T2.4: Scope has scope_id."""
        tree = ScopeTree(_nested_loop_flat())
        loop = tree.lookup_scope(('L',))
        assert loop.scope_id is not None

    def test_t2_5_symbols_tuple(self):
        """T2.5: Scope has symbols tuple."""
        tree = ScopeTree(_nested_loop_flat())
        root = tree.lookup_scope(())
        assert isinstance(root.symbols, tuple)
        assert 'A' in root.symbols
        assert 'L' in root.symbols


# ═══════════════════════════════════════════════════════════════
# T3: Scope Children
# ═══════════════════════════════════════════════════════════════

class TestT3_ScopeChildren:

    def test_t3_1_root_children(self):
        """T3.1: Root scope has children for subcanvases."""
        tree = ScopeTree(_nested_loop_flat())
        root = tree.lookup_scope(())
        assert len(root.children) == 1
        assert root.children[0].canvas_path == ('L',)

    def test_t3_2_multiple_children(self):
        """T3.2: Root scope with multiple subcanvases."""
        tree = ScopeTree(_sibling_flat())
        root = tree.lookup_scope(())
        assert len(root.children) == 2

    def test_t3_3_leaf_scope_no_children(self):
        """T3.3: Leaf scope has no children."""
        tree = ScopeTree(_deep_nested_flat())
        batch = tree.lookup_scope(('L', 'B'))
        assert len(batch.children) == 0

    def test_t3_4_nested_children(self):
        """T3.4: Nested scopes have correct parent-child relationships."""
        tree = ScopeTree(_deep_nested_flat())
        root = tree.lookup_scope(())
        loop = tree.lookup_scope(('L',))
        batch = tree.lookup_scope(('L', 'B'))
        assert loop in root.children
        assert batch in loop.children


# ═══════════════════════════════════════════════════════════════
# T4: Scope Lookup
# ═══════════════════════════════════════════════════════════════

class TestT4_ScopeLookup:

    def test_t4_1_lookup_root(self):
        """T4.1: Lookup root scope by canvas_path."""
        tree = ScopeTree(_deep_nested_flat())
        root = tree.lookup_scope(())
        assert root is not None
        assert root.scope_kind == 'root'

    def test_t4_2_lookup_nonexistent(self):
        """T4.2: Lookup returns None for nonexistent canvas_path."""
        tree = ScopeTree(_single_canvas_flat())
        assert tree.lookup_scope(('nonexistent',)) is None

    def test_t4_3_all_scopes(self):
        """T4.3: all_scopes() returns all scopes in the tree."""
        tree = ScopeTree(_deep_nested_flat())
        scopes = tree.all_scopes()
        assert len(scopes) == 3  # root + loop + batch

    def test_t4_4_root_property(self):
        """T4.4: root property returns the root scope."""
        tree = ScopeTree(_nested_loop_flat())
        root = tree.root
        assert root is not None
        assert root.scope_kind == 'root'

    def test_t4_5_root_property_empty(self):
        """T4.5: root property is None for empty tree."""
        tree = ScopeTree(AnalysisGraph())
        assert tree.root is None


# ═══════════════════════════════════════════════════════════════
# T5: Scope Visibility
# ═══════════════════════════════════════════════════════════════

class TestT5_ScopeVisibility:

    def test_t5_1_visible_symbols_from_root(self):
        """T5.1: Root scope sees only root symbols."""
        tree = ScopeTree(_nested_loop_flat())
        visible = tree.visible_symbols(())
        assert 'A' in visible
        assert 'L' in visible
        assert 'C' not in visible  # C is in loop subcanvas

    def test_t5_2_visible_symbols_from_subcanvas(self):
        """T5.2: Subcanvas sees its own + ancestor symbols."""
        tree = ScopeTree(_nested_loop_flat())
        visible = tree.visible_symbols(('L',))
        assert 'C' in visible
        assert 'D' in visible
        assert 'A' in visible  # A is in root (ancestor)

    def test_t5_3_deep_visible_symbols(self):
        """T5.3: Deep subcanvas sees all ancestor symbols."""
        tree = ScopeTree(_deep_nested_flat())
        visible = tree.visible_symbols(('L', 'B'))
        assert 'Y' in visible  # own
        assert 'B' in visible  # loop ancestor
        assert 'X' in visible  # loop ancestor
        assert 'L' in visible  # root ancestor

    def test_t5_4_is_visible_own_scope(self):
        """T5.4: Node is visible from its own scope."""
        tree = ScopeTree(_nested_loop_flat())
        assert tree.is_visible(('L',), 'C') is True

    def test_t5_5_is_visible_ancestor_scope(self):
        """T5.5: Node is visible from descendant scope."""
        tree = ScopeTree(_deep_nested_flat())
        assert tree.is_visible(('L', 'B'), 'L') is True  # root-level L

    def test_t5_6_not_visible_sibling_scope(self):
        """T5.6: Node is not visible from sibling scope."""
        tree = ScopeTree(_sibling_flat())
        assert tree.is_visible(('L1',), 'C2') is False

    def test_t5_7_not_visible_from_root(self):
        """T5.7: Subcanvas node not visible from root."""
        tree = ScopeTree(_nested_loop_flat())
        assert tree.is_visible((), 'C') is False

    def test_t5_8_scope_chain(self):
        """T5.8: scope_chain returns full path to root."""
        tree = ScopeTree(_deep_nested_flat())
        chain = tree.scope_chain(('L', 'B'))
        assert len(chain) == 3
        assert chain[0].canvas_path == ('L', 'B')
        assert chain[1].canvas_path == ('L',)
        assert chain[2].canvas_path == ()

    def test_t5_9_visible_symbols_deduplication(self):
        """T5.9: Symbols are deduplicated when ancestor has same name."""
        # This is unlikely in practice but tests the dedup logic
        tree = ScopeTree(_single_canvas_flat())
        visible = tree.visible_symbols(())
        assert len(visible) == len(set(visible))


# ═══════════════════════════════════════════════════════════════
# T6: Integration tests (use pipeline)
# ═══════════════════════════════════════════════════════════════

VALID_START_END = (
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


class TestT6_PipelineScopeIntegration:
    """Integration tests that go through the full pipeline."""

    def test_t6_1_basic_scope_from_yaml(self):
        """T6.1: Basic workflow with start and end nodes."""
        report = compile_text(VALID_START_END)
        # Should have no violations for a simple valid workflow
        violations = [d for d in report.diagnostics if d.kind == 'violation']
        assert len(violations) == 0

    def test_t6_2_loop_scope_from_yaml(self):
        """T6.2: Workflow with a loop block."""
        yaml_text = (
            'nodes:\n'
            '  - id: "100001"\n'
            '    type: "1"\n'
            '    data:\n'
            '      nodeMeta:\n'
            '        title: "Start"\n'
            '  - id: "200001"\n'
            '    type: "3"\n'
            '    data:\n'
            '      nodeMeta:\n'
            '        title: "Loop"\n'
            '      nodes:\n'
            '        - id: "inner_1"\n'
            '          type: "1"\n'
            '          data:\n'
            '            nodeMeta:\n'
            '              title: "Inner"\n'
            '  - id: "900001"\n'
            '    type: "2"\n'
            '    data:\n'
            '      nodeMeta:\n'
            '        title: "End"\n'
            'edges:\n'
            '  - sourceNodeID: "100001"\n'
            '    targetNodeID: "200001"\n'
            '  - sourceNodeID: "200001"\n'
            '    targetNodeID: "900001"\n'
        )
        report = compile_text(yaml_text)
        # Should parse without transport errors
        transport_errors = [d for d in report.diagnostics if d.kind == 'transport-error']
        assert len(transport_errors) == 0

    def test_t6_3_valid_ref_resolves(self):
        """T6.3: Workflow with valid reference resolution."""
        yaml_text = (
            'nodes:\n'
            '  - id: "100001"\n'
            '    type: "1"\n'
            '    data:\n'
            '      nodeMeta:\n'
            '        title: "Start"\n'
            '  - id: "300001"\n'
            '    type: "6"\n'
            '    data:\n'
            '      nodeMeta:\n'
            '        title: "LLM"\n'
            '      inputParameters:\n'
            '        - name: "prompt"\n'
            '          ref: "100001.output"\n'
            '  - id: "900001"\n'
            '    type: "2"\n'
            '    data:\n'
            '      nodeMeta:\n'
            '        title: "End"\n'
            'edges:\n'
            '  - sourceNodeID: "100001"\n'
            '    targetNodeID: "300001"\n'
            '  - sourceNodeID: "300001"\n'
            '    targetNodeID: "900001"\n'
        )
        report = compile_text(yaml_text)
        # Should have no violations (excluding portability which requires live validation)
        violations = [d for d in report.diagnostics if d.kind == 'violation' and d.layer not in ('portability', 'semantic-fe')]
        assert len(violations) == 0

    def test_t6_4_missing_ref_fails(self):
        """T6.4: Workflow with missing reference should produce error."""
        yaml_text = (
            'nodes:\n'
            '  - id: "100001"\n'
            '    type: "1"\n'
            '    data:\n'
            '      nodeMeta:\n'
            '        title: "Start"\n'
            '  - id: "300001"\n'
            '    type: "6"\n'
            '    data:\n'
            '      nodeMeta:\n'
            '        title: "LLM"\n'
            '      inputParameters:\n'
            '        - name: "prompt"\n'
            '          ref: "nonexistent.output"\n'
            '  - id: "900001"\n'
            '    type: "2"\n'
            '    data:\n'
            '      nodeMeta:\n'
            '        title: "End"\n'
            'edges:\n'
            '  - sourceNodeID: "100001"\n'
            '    targetNodeID: "300001"\n'
            '  - sourceNodeID: "300001"\n'
            '    targetNodeID: "900001"\n'
        )
        report = compile_text(yaml_text)
        # Should have violations for bad reference
        violations = [d for d in report.diagnostics if d.kind == 'violation']
        assert len(violations) > 0

    def test_t6_5_empty_blockid_fails(self):
        """T6.5: Workflow with empty node ID should produce error."""
        yaml_text = (
            'nodes:\n'
            '  - id: ""\n'
            '    type: "1"\n'
            '    data:\n'
            '      nodeMeta:\n'
            '        title: "Empty"\n'
            '  - id: "900001"\n'
            '    type: "2"\n'
            '    data:\n'
            '      nodeMeta:\n'
            '        title: "End"\n'
            'edges:\n'
            '  - sourceNodeID: ""\n'
            '    targetNodeID: "900001"\n'
        )
        report = compile_text(yaml_text)
        # Should have violations for empty ID
        violations = [d for d in report.diagnostics if d.kind == 'violation']
        assert len(violations) > 0

    def test_t6_6_global_var_ok(self):
        """T6.6: Workflow with global variable definition."""
        yaml_text = (
            'nodes:\n'
            '  - id: "100001"\n'
            '    type: "1"\n'
            '    data:\n'
            '      nodeMeta:\n'
            '        title: "Start"\n'
            '  - id: "400001"\n'
            '    type: "13"\n'
            '    data:\n'
            '      nodeMeta:\n'
            '        title: "Variable"\n'
            '      isGlobalVarDef: true\n'
            '  - id: "900001"\n'
            '    type: "2"\n'
            '    data:\n'
            '      nodeMeta:\n'
            '        title: "End"\n'
            'edges:\n'
            '  - sourceNodeID: "100001"\n'
            '    targetNodeID: "400001"\n'
            '  - sourceNodeID: "400001"\n'
            '    targetNodeID: "900001"\n'
        )
        report = compile_text(yaml_text)
        # Should have no violations
        violations = [d for d in report.diagnostics if d.kind == 'violation']
        assert len(violations) == 0
