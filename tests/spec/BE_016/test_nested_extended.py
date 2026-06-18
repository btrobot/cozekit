"""BE-016: Extended nested composite node tests.

Additional scenarios beyond the basic test in test_nested_composites.py:
  - Batch containing a Batch → error
  - Batch containing a Loop → error
  - Loop containing a Loop → error
  - If inside a Loop → error (If is composite)
  - Non-composite inside a Loop → valid

规则来源: backend-rules.json BE-ValidateNestedFlows-001, coze-workflow-spec.md §3.5.5
"""
from __future__ import annotations

from tests.conftest import compile_text


def _be016_ids(t):
    return [d.rule_id for d in compile_text(t).diagnostics if d.rule_id == 'SEMANTIC-BE-016']


class TestBE016_Extended_Positive:
    """Valid nesting configurations → no BE-016."""

    def test_code_inside_loop(self):
        """Code (5) inside Loop → valid (Code is not composite)."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "loop-1"\n    type: "21"\n    data:\n      nodeMeta:\n        title: "Loop"\n'
            '    blocks:\n'
            '      - id: "code-1"\n        type: "5"\n        data:\n          nodeMeta:\n            title: "Code"\n'
            '    edges: []\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "loop-1"\n'
            '  - sourceNodeID: "loop-1"\n    targetNodeID: "900001"\n'
        )
        assert 'SEMANTIC-BE-016' not in _be016_ids(t)

    def test_llm_inside_batch(self):
        """LLM (3) inside Batch → valid (LLM is not composite)."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "batch-1"\n    type: "28"\n    data:\n      nodeMeta:\n        title: "Batch"\n'
            '    blocks:\n'
            '      - id: "llm-1"\n        type: "3"\n        data:\n          nodeMeta:\n            title: "LLM"\n'
            '    edges: []\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "batch-1"\n'
            '  - sourceNodeID: "batch-1"\n    targetNodeID: "900001"\n'
        )
        assert 'SEMANTIC-BE-016' not in _be016_ids(t)


class TestBE016_Extended_Negative:
    """Invalid nesting configurations → BE-016 error."""

    def test_batch_inside_batch(self):
        """Batch inside Batch → BE-016."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "batch-1"\n    type: "28"\n    data:\n      nodeMeta:\n        title: "Outer Batch"\n'
            '    blocks:\n'
            '      - id: "batch-2"\n        type: "28"\n        data:\n          nodeMeta:\n            title: "Inner Batch"\n'
            '    edges: []\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "batch-1"\n'
            '  - sourceNodeID: "batch-1"\n    targetNodeID: "900001"\n'
        )
        assert 'SEMANTIC-BE-016' in _be016_ids(t)

    def test_loop_inside_loop(self):
        """Loop inside Loop → BE-016."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "loop-1"\n    type: "21"\n    data:\n      nodeMeta:\n        title: "Outer Loop"\n'
            '    blocks:\n'
            '      - id: "loop-2"\n        type: "21"\n        data:\n          nodeMeta:\n            title: "Inner Loop"\n'
            '    edges: []\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "loop-1"\n'
            '  - sourceNodeID: "loop-1"\n    targetNodeID: "900001"\n'
        )
        assert 'SEMANTIC-BE-016' in _be016_ids(t)

    def test_batch_inside_loop(self):
        """Batch inside Loop → BE-016."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "loop-1"\n    type: "21"\n    data:\n      nodeMeta:\n        title: "Loop"\n'
            '    blocks:\n'
            '      - id: "batch-1"\n        type: "28"\n        data:\n          nodeMeta:\n            title: "Batch"\n'
            '    edges: []\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "loop-1"\n'
            '  - sourceNodeID: "loop-1"\n    targetNodeID: "900001"\n'
        )
        assert 'SEMANTIC-BE-016' in _be016_ids(t)

    def test_loop_inside_batch(self):
        """Loop inside Batch → BE-016."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "batch-1"\n    type: "28"\n    data:\n      nodeMeta:\n        title: "Batch"\n'
            '    blocks:\n'
            '      - id: "loop-1"\n        type: "21"\n        data:\n          nodeMeta:\n            title: "Loop"\n'
            '    edges: []\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "batch-1"\n'
            '  - sourceNodeID: "batch-1"\n    targetNodeID: "900001"\n'
        )
        assert 'SEMANTIC-BE-016' in _be016_ids(t)

    def test_if_inside_loop_allowed(self):
        """If (8) inside Loop is allowed — only Loop/Batch nesting is forbidden."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "loop-1"\n    type: "21"\n    data:\n      nodeMeta:\n        title: "Loop"\n'
            '    blocks:\n'
            '      - id: "inner-if"\n        type: "8"\n        data:\n          nodeMeta:\n            title: "If"\n'
            '    edges: []\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "loop-1"\n'
            '  - sourceNodeID: "loop-1"\n    targetNodeID: "900001"\n'
        )
        assert 'SEMANTIC-BE-016' not in _be016_ids(t)
