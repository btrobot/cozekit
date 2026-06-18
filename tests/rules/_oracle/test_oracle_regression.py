"""Oracle regression tests — verify compiler output matches expected baselines.

These tests verify that all rules produce the same diagnostics as the known-good
oracle baseline. They act as a regression safety net.

Source: tests/fixtures/expected/oracle_baseline.json
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.conftest import compile_fixture, FIXTURES_DIR

ORACLE_FILE = FIXTURES_DIR / 'expected' / 'oracle_baseline.json'

with open(ORACLE_FILE) as _f:
    _BASELINES = {b['fixture_id']: b for b in json.load(_f)}

FIXTURE_IDS = list(_BASELINES.keys())


class TestOracleSyntaxBaseline:
    """SYNTAX rule_ids must match oracle baseline."""

    @pytest.fixture(params=FIXTURE_IDS)
    def fixture_id(self, request):
        return request.param

    def test_syntax_rules_match(self, fixture_id):
        baseline = _BASELINES[fixture_id]
        expected = sorted(r for r in baseline['rule_ids'] if r.startswith('SYNTAX'))
        report = compile_fixture(FIXTURES_DIR / 'json' / f'{fixture_id}.json')
        actual = sorted(d.rule_id for d in report.diagnostics if d.rule_id.startswith('SYNTAX'))
        assert actual == expected, f'{fixture_id}: SYNTAX mismatch\n  expected: {expected}\n  actual:   {actual}'


class TestOracleSemanticBaseline:
    """SEMANTIC rule_ids must match oracle baseline."""

    @pytest.fixture(params=FIXTURE_IDS)
    def fixture_id(self, request):
        return request.param

    def test_semantic_rules_match(self, fixture_id):
        baseline = _BASELINES[fixture_id]
        expected = sorted(r for r in baseline['rule_ids'] if r.startswith('SEMANTIC'))
        report = compile_fixture(FIXTURES_DIR / 'json' / f'{fixture_id}.json')
        actual = sorted(d.rule_id for d in report.diagnostics if d.rule_id.startswith('SEMANTIC'))
        assert actual == expected, f'{fixture_id}: SEMANTIC mismatch\n  expected: {expected}\n  actual:   {actual}'


class TestOracleExitCode:
    """Exit code must match oracle baseline."""

    @pytest.fixture(params=FIXTURE_IDS)
    def fixture_id(self, request):
        return request.param

    def test_exit_code_matches(self, fixture_id):
        baseline = _BASELINES[fixture_id]
        report = compile_fixture(FIXTURES_DIR / 'json' / f'{fixture_id}.json')
        assert report.exit_code == baseline['exit_code'], (
            f'{fixture_id}: exit code {report.exit_code} != {baseline["exit_code"]}'
        )


class TestExportEnvelope:
    """Export envelope should be unwrapped transparently."""

    def test_export_envelope_unwrapped(self):
        import json as _json
        envelope = _json.dumps({
            'type': 'coze-workflow-export-data',
            'json': {
                'nodes': [
                    {'id': '100001', 'type': '1', 'data': {'nodeMeta': {'title': 'Start'}}},
                    {'id': '900001', 'type': '2', 'data': {'nodeMeta': {'title': 'End'}}},
                ],
                'edges': [{'sourceNodeID': '100001', 'targetNodeID': '900001'}],
            },
        })
        from tests.conftest import compile_text
        report = compile_text(envelope)
        syntax_errors = [d for d in report.diagnostics if d.rule_id.startswith('SYNTAX')]
        assert not syntax_errors, f'Export envelope should be clean: {syntax_errors}'
