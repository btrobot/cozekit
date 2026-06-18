"""Common validators — value expression, error config, node meta.

Covers:
  - Value expression type validation (literal/ref/object_ref)
  - SettingOnError config (SEMANTIC-FE-012)
  - Node title validation (SEMANTIC-FE-009/010/011)
  - LLM temperature range (SEMANTIC-FE-001)

规则来源: coze-workflow-spec.md §2.5, §3.8, §2.6
"""
from __future__ import annotations

import pytest

from tests.conftest import compile_text


def _all_messages(t):
    return [(d.rule_id, d.message) for d in compile_text(t).diagnostics]


def _fe012_ids(t):
    return [d.rule_id for d in compile_text(t).diagnostics if d.rule_id == 'SEMANTIC-FE-012']


def _fe009_ids(t):
    return [d.rule_id for d in compile_text(t).diagnostics if d.rule_id == 'SEMANTIC-FE-009']


def _fe010_ids(t):
    return [d.rule_id for d in compile_text(t).diagnostics if d.rule_id == 'SEMANTIC-FE-010']


def _fe011_ids(t):
    return [d.rule_id for d in compile_text(t).diagnostics if d.rule_id == 'SEMANTIC-FE-011']


def _fe001_messages(t):
    return [d.message for d in compile_text(t).diagnostics if d.rule_id == 'SEMANTIC-FE-001']


# ── Value Expression Type Validation ─────────────────────────────

class TestValueExpression_Positive:
    """Valid value expressions → no errors."""

    def test_literal_type(self):
        """Literal type with string content → valid."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "n1"\n    type: "5"\n    data:\n      nodeMeta:\n        title: "Code"\n'
            '      inputs:\n        inputParameters:\n'
            '          - name: "x"\n            input:\n              type: literal\n              content: "hello"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "n1"\n'
            '  - sourceNodeID: "n1"\n    targetNodeID: "900001"\n'
        )
        pairs = _all_messages(t)
        ve_errors = [m for rid, m in pairs if 'value expression' in m.lower()]
        assert len(ve_errors) == 0

    def test_ref_type_with_blockid(self):
        """Ref type with valid blockID → valid."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "n1"\n    type: "5"\n    data:\n      nodeMeta:\n        title: "Code"\n'
            '      inputs:\n        inputParameters:\n'
            '          - name: "x"\n            input:\n              type: string\n              value:\n'
            '                type: ref\n                content:\n'
            '                  source: block-output\n                  blockID: "100001"\n                  name: "out"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "n1"\n'
            '  - sourceNodeID: "n1"\n    targetNodeID: "900001"\n'
        )
        pairs = _all_messages(t)
        be017 = [m for rid, m in pairs if rid == 'SEMANTIC-BE-017']
        assert len(be017) == 0


class TestValueExpression_Negative:
    """Invalid value expressions → errors."""

    def test_ref_empty_blockid(self):
        """Ref type with empty blockID → BE-017 (uses Coze full format)."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "n1"\n    type: "5"\n    data:\n      nodeMeta:\n        title: "Code"\n'
            '      inputs:\n        inputParameters:\n'
            '          - name: "x"\n            input:\n              type: string\n              value:\n'
            '                type: ref\n                content:\n'
            '                  source: block-output\n                  blockId: ""\n                  name: "out"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "n1"\n'
            '  - sourceNodeID: "n1"\n    targetNodeID: "900001"\n'
        )
        be017 = [rid for rid, m in _all_messages(t) if rid == 'SEMANTIC-BE-017']
        assert len(be017) >= 1

    def test_ref_nonexistent_blockid(self):
        """Ref type with non-existent blockID → BE-017."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "n1"\n    type: "5"\n    data:\n      nodeMeta:\n        title: "Code"\n'
            '      inputs:\n        inputParameters:\n'
            '          - name: "x"\n            input:\n              type: string\n              value:\n'
            '                type: ref\n                content:\n'
            '                  source: block-output\n                  blockId: "nonexistent"\n                  name: "out"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "n1"\n'
            '  - sourceNodeID: "n1"\n    targetNodeID: "900001"\n'
        )
        be017 = [rid for rid, m in _all_messages(t) if rid == 'SEMANTIC-BE-017']
        assert len(be017) >= 1


# ── SettingOnError Config (SEMANTIC-FE-012) ─────────────────────

class TestOnErrorConfig_Positive:
    """Valid error config → no FE-012."""

    def test_no_error_config(self):
        """No onErrorConfig → no error."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "900001"\n'
        )
        assert 'SEMANTIC-FE-012' not in _fe012_ids(t)

    def test_valid_json_error_config(self):
        """Valid JSON in returnJson → no FE-012 error."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "n1"\n    type: "3"\n    data:\n      nodeMeta:\n        title: "LLM"\n'
            '      onError:\n'
            '        returnJson: \'{"error": "failed"}\'\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "n1"\n'
            '  - sourceNodeID: "n1"\n    targetNodeID: "900001"\n'
        )
        assert 'SEMANTIC-FE-012' not in _fe012_ids(t)


class TestOnErrorConfig_Negative:
    """Invalid error config → FE-012 error."""

    def test_invalid_json_error_config(self):
        """Invalid JSON in returnJson → FE-012 error."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "n1"\n    type: "3"\n    data:\n      nodeMeta:\n        title: "LLM"\n'
            '      onError:\n'
            '        returnJson: \'{invalid json}\'\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "n1"\n'
            '  - sourceNodeID: "n1"\n    targetNodeID: "900001"\n'
        )
        assert 'SEMANTIC-FE-012' in _fe012_ids(t)


# ── Node Title Validation (SEMANTIC-FE-009/010/011) ──────────────

class TestNodeTitle_Positive:
    """Valid titles → no FE-009/010/011 errors."""

    def test_valid_short_title(self):
        """Short valid title → no error."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "900001"\n'
        )
        assert 'SEMANTIC-FE-009' not in _fe009_ids(t)
        assert 'SEMANTIC-FE-010' not in _fe010_ids(t)
        assert 'SEMANTIC-FE-011' not in _fe011_ids(t)

    def test_max_length_title(self):
        """Exactly 63 character title → no error."""
        title = 'a' * 63
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            f'  - id: "n1"\n    type: "5"\n    data:\n      nodeMeta:\n        title: "{title}"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "n1"\n'
            '  - sourceNodeID: "n1"\n    targetNodeID: "900001"\n'
        )
        assert 'SEMANTIC-FE-010' not in _fe010_ids(t)

    def test_chinese_title(self):
        """Chinese title → valid."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "开始"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "结束"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "900001"\n'
        )
        assert 'SEMANTIC-FE-009' not in _fe009_ids(t)


class TestNodeTitle_Negative:
    """Invalid titles → FE-009/010/011 errors."""

    def test_empty_title(self):
        """Empty title → FE-009 error."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: ""\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "900001"\n'
        )
        assert 'SEMANTIC-FE-009' in _fe009_ids(t)

    def test_title_too_long(self):
        """64 character title → FE-010 error."""
        title = 'x' * 64
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            f'  - id: "n1"\n    type: "5"\n    data:\n      nodeMeta:\n        title: "{title}"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "n1"\n'
            '  - sourceNodeID: "n1"\n    targetNodeID: "900001"\n'
        )
        assert 'SEMANTIC-FE-010' in _fe010_ids(t)

    def test_duplicate_titles(self):
        """Duplicate titles → FE-011 error (2 nodes with same title)."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "n1"\n    type: "5"\n    data:\n      nodeMeta:\n        title: "Dup"\n'
            '  - id: "n2"\n    type: "3"\n    data:\n      nodeMeta:\n        title: "Dup"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "n1"\n'
            '  - sourceNodeID: "n1"\n    targetNodeID: "n2"\n'
            '  - sourceNodeID: "n2"\n    targetNodeID: "900001"\n'
        )
        ids = _fe011_ids(t)
        assert ids.count('SEMANTIC-FE-011') == 2


# ── LLM Temperature Range (SEMANTIC-FE-001) ─────────────────────

class TestLLMTemperature:
    """LLM node temperature range validation."""

    def test_valid_temperature(self):
        """Temperature 0.7 → no error."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "n1"\n    type: "3"\n    data:\n      nodeMeta:\n        title: "LLM"\n'
            '      inputs:\n        inputParameters:\n'
            '          - name: prompt\n            input:\n              type: literal\n              content: hello\n'
            '        llmParam:\n'
            '          - name: temperature\n            input:\n              type: string\n              value:\n                type: literal\n                content: "0.7"\n'
            '          - name: modelType\n            input:\n              type: string\n              value:\n                type: literal\n                content: "gpt4"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "n1"\n'
            '  - sourceNodeID: "n1"\n    targetNodeID: "900001"\n'
        )
        errors = _fe001_messages(t)
        assert not any('temperature' in e.lower() for e in errors)

    def test_temperature_out_of_range(self):
        """Temperature 3.0 → error."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "n1"\n    type: "3"\n    data:\n      nodeMeta:\n        title: "LLM"\n'
            '      inputs:\n        inputParameters:\n'
            '          - name: prompt\n            input:\n              type: literal\n              content: hello\n'
            '        llmParam:\n'
            '          - name: temperature\n            input:\n              type: string\n              value:\n                type: literal\n                content: "3.0"\n'
            '          - name: modelType\n            input:\n              type: string\n              value:\n                type: literal\n                content: "gpt4"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "n1"\n'
            '  - sourceNodeID: "n1"\n    targetNodeID: "900001"\n'
        )
        errors = _fe001_messages(t)
        assert any('temperature' in e.lower() for e in errors)

    def test_temperature_negative(self):
        """Temperature -1 → error."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "n1"\n    type: "3"\n    data:\n      nodeMeta:\n        title: "LLM"\n'
            '      inputs:\n        inputParameters:\n'
            '          - name: prompt\n            input:\n              type: literal\n              content: hello\n'
            '        llmParam:\n'
            '          - name: temperature\n            input:\n              type: string\n              value:\n                type: literal\n                content: "-1"\n'
            '          - name: modelType\n            input:\n              type: string\n              value:\n                type: literal\n                content: "gpt4"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "n1"\n'
            '  - sourceNodeID: "n1"\n    targetNodeID: "900001"\n'
        )
        errors = _fe001_messages(t)
        assert any('temperature' in e.lower() for e in errors)

    def test_temperature_boundary_zero(self):
        """Temperature 0.0 → valid (lower boundary)."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "n1"\n    type: "3"\n    data:\n      nodeMeta:\n        title: "LLM"\n'
            '      inputs:\n        inputParameters:\n'
            '          - name: prompt\n            input:\n              type: literal\n              content: hello\n'
            '        llmParam:\n'
            '          - name: temperature\n            input:\n              type: string\n              value:\n                type: literal\n                content: "0.0"\n'
            '          - name: modelType\n            input:\n              type: string\n              value:\n                type: literal\n                content: "gpt4"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "n1"\n'
            '  - sourceNodeID: "n1"\n    targetNodeID: "900001"\n'
        )
        errors = _fe001_messages(t)
        assert not any('temperature' in e.lower() for e in errors)

    def test_temperature_boundary_two(self):
        """Temperature 2.0 → valid (upper boundary)."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "n1"\n    type: "3"\n    data:\n      nodeMeta:\n        title: "LLM"\n'
            '      inputs:\n        inputParameters:\n'
            '          - name: prompt\n            input:\n              type: literal\n              content: hello\n'
            '        llmParam:\n'
            '          - name: temperature\n            input:\n              type: string\n              value:\n                type: literal\n                content: "2.0"\n'
            '          - name: modelType\n            input:\n              type: string\n              value:\n                type: literal\n                content: "gpt4"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "n1"\n'
            '  - sourceNodeID: "n1"\n    targetNodeID: "900001"\n'
        )
        errors = _fe001_messages(t)
        assert not any('temperature' in e.lower() for e in errors)
