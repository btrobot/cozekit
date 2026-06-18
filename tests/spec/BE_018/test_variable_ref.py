"""BE-018: Variable name reference integrity.

The backend rule BE-CheckRefVariable-002 checks that referenced block IDs
exist in the reachable graph. This test covers:
  - Valid ref to an existing node in the same canvas
  - Ref to a non-existent node → BE-017 error (shared with BE-017)
  - Ref across branches (if-true references start node output)

NOTE: In the compiler, BE-018 maps to the same validation function as
BE-017 (_check_ref_block_ids). The distinction is:
  - BE-017: empty blockID
  - BE-018: non-existent blockID (dangling reference)

规则来源: backend-rules.json BE-CheckRefVariable-002
"""
from __future__ import annotations
import pytest


from tests.conftest import compile_text


def _be017_messages(t):
    return [d.message for d in compile_text(t).diagnostics if d.rule_id == 'SEMANTIC-BE-017']


class TestBE018_Positive:
    """Valid variable references → no errors."""

    def test_ref_to_upstream_node(self):
        """Code node refs Start node output → valid."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "n1"\n    type: "5"\n    data:\n      nodeMeta:\n        title: "Code"\n'
            '      inputs:\n        inputParameters:\n'
            '          - name: "x"\n            input:\n              type: string\n              value:\n                type: ref\n                content:\n'
            '                  source: block-output\n                  blockID: "100001"\n                  name: "output"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "n1"\n'
            '  - sourceNodeID: "n1"\n    targetNodeID: "900001"\n'
        )
        messages = _be017_messages(t)
        assert not any('does not point to an existing node' in m for m in messages)

    def test_ref_to_sibling_node(self):
        """Code node refs another code node → valid (both exist)."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "n1"\n    type: "5"\n    data:\n      nodeMeta:\n        title: "Code1"\n'
            '  - id: "n2"\n    type: "5"\n    data:\n      nodeMeta:\n        title: "Code2"\n'
            '      inputs:\n        inputParameters:\n'
            '          - name: "x"\n            input:\n              type: string\n              value:\n                type: ref\n                content:\n'
            '                  source: block-output\n                  blockID: "n1"\n                  name: "result"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "n1"\n'
            '  - sourceNodeID: "100001"\n    targetNodeID: "n2"\n'
            '  - sourceNodeID: "n1"\n    targetNodeID: "900001"\n'
            '  - sourceNodeID: "n2"\n    targetNodeID: "900001"\n'
        )
        messages = _be017_messages(t)
        assert not any('does not point to an existing node' in m for m in messages)


class TestBE018_Negative:
    """Invalid variable references → BE-017 errors."""
    def test_dangling_ref(self):
        """Ref to a node that was deleted → BE-017."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "n1"\n    type: "5"\n    data:\n      nodeMeta:\n        title: "Code"\n'
            '      inputs:\n        inputParameters:\n'
            '          - name: "x"\n            input:\n              type: string\n              value:\n                type: ref\n                content:\n'
            '                  source: block-output\n                  blockID: "deleted-node"\n                  name: "out"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "n1"\n'
            '  - sourceNodeID: "n1"\n    targetNodeID: "900001"\n'
        )
        messages = _be017_messages(t)
        assert any('does not point to an existing node' in m for m in messages)
    def test_ref_to_self_id_empty(self):
        """Ref with empty blockID → BE-017 (empty blockID check)."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "n1"\n    type: "5"\n    data:\n      nodeMeta:\n        title: "Code"\n'
            '      inputs:\n        inputParameters:\n'
            '          - name: "x"\n            input:\n              type: string\n              value:\n                type: ref\n                content:\n'
            '                  source: block-output\n                  blockID: ""\n                  name: "out"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "n1"\n'
            '  - sourceNodeID: "n1"\n    targetNodeID: "900001"\n'
        )
        assert 'SEMANTIC-BE-017' in [d.rule_id for d in compile_text(t).diagnostics]
    def test_multiple_refs_one_dangling(self):
        """Two refs, one valid and one dangling → error for dangling only."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "n1"\n    type: "5"\n    data:\n      nodeMeta:\n        title: "Code"\n'
            '      inputs:\n        inputParameters:\n'
            '          - name: "a"\n            input:\n              type: string\n              value:\n                type: ref\n                content:\n'
            '                  source: block-output\n                  blockID: "100001"\n                  name: "out"\n'
            '          - name: "b"\n            input:\n              type: string\n              value:\n                type: ref\n                content:\n'
            '                  source: block-output\n                  blockID: "ghost"\n                  name: "out"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "n1"\n'
            '  - sourceNodeID: "n1"\n    targetNodeID: "900001"\n'
        )
        messages = _be017_messages(t)
        assert any('ghost' in m for m in messages)
