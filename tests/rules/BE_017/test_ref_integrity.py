"""BE-017: Reference blockID integrity — extended coverage.

Validates:
  - Valid ref with existing blockID → no error
  - Valid ref with global_variable source → no error
  - Empty blockID → BE-017 error
  - Non-existent blockID → BE-017 error
  - Ref in branch condition → validated

规则来源: backend-rules.json BE-CheckRefVariable-001/002, coze-workflow-spec.md §3.7
"""
from __future__ import annotations
import pytest


from tests.conftest import compile_text


def _be017_ids(t):
    return [d.rule_id for d in compile_text(t).diagnostics if d.rule_id == 'SEMANTIC-BE-017']


def _be017_messages(t):
    return [d.message for d in compile_text(t).diagnostics if d.rule_id == 'SEMANTIC-BE-017']


class TestBE017_Positive:
    """Valid references should produce no BE-017 errors."""

    def test_valid_ref_to_existing_node(self):
        """Ref with valid blockID pointing to Start node → no error."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "n1"\n    type: "5"\n    data:\n      nodeMeta:\n        title: "Code"\n'
            '      inputs:\n        inputParameters:\n'
            '          - name: "x"\n            input:\n              type: string\n              value:\n                type: ref\n                content:\n'
            '                  source: block-output\n                  blockID: "100001"\n                  name: out\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "n1"\n'
            '  - sourceNodeID: "n1"\n    targetNodeID: "900001"\n'
        )
        assert 'SEMANTIC-BE-017' not in _be017_ids(t)

    def test_valid_global_variable_ref(self):
        """Ref with global_variable_app source → no BE-017 (global vars are external)."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "n1"\n    type: "5"\n    data:\n      nodeMeta:\n        title: "Code"\n'
            '      inputs:\n        inputParameters:\n'
            '          - name: "x"\n            input:\n              type: string\n              value:\n                type: ref\n                content:\n'
            '                  source: global_variable_app\n                  blockID: ""\n                  name: "apiKey"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "n1"\n'
            '  - sourceNodeID: "n1"\n    targetNodeID: "900001"\n'
        )
        # Global variable refs with empty blockID are valid (name-based lookup)
        assert 'SEMANTIC-BE-017' not in _be017_ids(t)

    def test_literal_type_no_ref(self):
        """Literal input → no ref validation needed, no BE-017."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "n1"\n    type: "5"\n    data:\n      nodeMeta:\n        title: "Code"\n'
            '      inputs:\n        inputParameters:\n'
            '          - name: "x"\n            input:\n              type: string\n              value:\n                type: literal\n                content: "hello"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "n1"\n'
            '  - sourceNodeID: "n1"\n    targetNodeID: "900001"\n'
        )
        assert 'SEMANTIC-BE-017' not in _be017_ids(t)


class TestBE017_Negative:
    """Invalid references should produce BE-017 errors."""
    def test_empty_blockid(self):
        """block-output ref with empty blockID → BE-017."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "n1"\n    type: "5"\n    data:\n      nodeMeta:\n        title: "Code"\n'
            '      inputs:\n        inputParameters:\n'
            '          - name: "x"\n            input:\n              type: string\n              value:\n                type: ref\n                content:\n'
            '                  source: block-output\n                  blockID: ""\n                  name: out\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "n1"\n'
            '  - sourceNodeID: "n1"\n    targetNodeID: "900001"\n'
        )
        assert 'SEMANTIC-BE-017' in _be017_ids(t)
    def test_nonexistent_blockid(self):
        """block-output ref with non-existent blockID → BE-017."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "n1"\n    type: "5"\n    data:\n      nodeMeta:\n        title: "Code"\n'
            '      inputs:\n        inputParameters:\n'
            '          - name: "x"\n            input:\n              type: string\n              value:\n                type: ref\n                content:\n'
            '                  source: block-output\n                  blockID: "nonexistent-node"\n                  name: out\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "n1"\n'
            '  - sourceNodeID: "n1"\n    targetNodeID: "900001"\n'
        )
        assert 'SEMANTIC-BE-017' in _be017_ids(t)

    def test_ref_in_condition_left(self):
        """Ref in If condition left with empty blockID → BE-017."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "if-1"\n    type: "8"\n    data:\n      nodeMeta:\n        title: "If"\n'
            '      inputs:\n        branches:\n'
            '          - branchKey: "true"\n            condition:\n              logic: and\n              conditions:\n'
            '                - left:\n                    type: ref\n                    content:\n'
            '                      source: block-output\n                      blockID: ""\n                      name: "val"\n'
            '                  operator: "1"\n                  right:\n                    type: literal\n                    content: "x"\n'
            '          - branchKey: "false"\n            condition: {}\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "if-1"\n'
            '  - sourceNodeID: "if-1"\n    sourcePortID: "true"\n    targetNodeID: "900001"\n'
            '  - sourceNodeID: "if-1"\n    sourcePortID: "false"\n    targetNodeID: "900001"\n'
        )
        assert 'SEMANTIC-BE-017' in _be017_ids(t)

    def test_ref_in_condition_right(self):
        """Ref in If condition right with non-existent blockID → BE-017."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "if-1"\n    type: "8"\n    data:\n      nodeMeta:\n        title: "If"\n'
            '      inputs:\n        branches:\n'
            '          - branchKey: "true"\n            condition:\n              logic: and\n              conditions:\n'
            '                - left:\n                    type: ref\n                    content:\n'
            '                      source: block-output\n                      blockID: "100001"\n                      name: "val"\n'
            '                  operator: "1"\n                  right:\n                    type: ref\n                    content:\n'
            '                      source: block-output\n                      blockID: "deleted-node"\n                      name: "x"\n'
            '          - branchKey: "false"\n            condition: {}\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "if-1"\n'
            '  - sourceNodeID: "if-1"\n    sourcePortID: "true"\n    targetNodeID: "900001"\n'
            '  - sourceNodeID: "if-1"\n    sourcePortID: "false"\n    targetNodeID: "900001"\n'
        )
        assert 'SEMANTIC-BE-017' in _be017_ids(t)
