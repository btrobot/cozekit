"""PORT-003/004: transport envelope type validation."""
from __future__ import annotations

import json

from tests.conftest import compile_text


def _compile_with_text(source_text):
    from cozekit.compiler_v2_api import compile_text as ct
    return ct(source_text)


def _port_ids(report):
    return [d.rule_id for d in report.diagnostics
            if d.rule_id in ('PORTABILITY-003', 'PORTABILITY-004')]


class TestPORT003_004_Positive:
    def test_valid_export_envelope(self):
        """Valid export envelope with json as dict → no PORT-003/004."""
        inner = {
            'nodes': [
                {'id': '100001', 'type': '1', 'data': {'nodeMeta': {'title': 'Start'}}},
                {'id': '900001', 'type': '2', 'data': {'nodeMeta': {'title': 'End'}}},
            ],
            'edges': [{'sourceNodeID': '100001', 'targetNodeID': '900001'}],
        }
        envelope = json.dumps({
            'type': 'coze-workflow-export-data',
            'json': inner,
        })
        r = _compile_with_text(envelope)
        assert _port_ids(r) == []

    def test_valid_clipboard_envelope(self):
        """Valid clipboard envelope with json as dict → no PORT-003/004."""
        inner = {
            'nodes': [
                {'id': '100001', 'type': '1', 'data': {'nodeMeta': {'title': 'Start'}}},
                {'id': '900001', 'type': '2', 'data': {'nodeMeta': {'title': 'End'}}},
            ],
            'edges': [{'sourceNodeID': '100001', 'targetNodeID': '900001'}],
        }
        envelope = json.dumps({
            'type': 'coze-workflow-clipboard-data',
            'json': inner,
        })
        r = _compile_with_text(envelope)
        assert _port_ids(r) == []


class TestPORT003_004_Negative:
    def test_export_envelope_with_string_json(self):
        """Export envelope with json as string (not dict) → PORT-003."""
        inner_str = json.dumps({
            'nodes': [
                {'id': '100001', 'type': '1', 'data': {'nodeMeta': {'title': 'Start'}}},
                {'id': '900001', 'type': '2', 'data': {'nodeMeta': {'title': 'End'}}},
            ],
            'edges': [{'sourceNodeID': '100001', 'targetNodeID': '900001'}],
        })
        envelope = json.dumps({
            'type': 'coze-workflow-export-data',
            'json': inner_str,
        })
        r = _compile_with_text(envelope)
        assert 'PORTABILITY-003' in _port_ids(r)

    def test_clipboard_envelope_with_string_json(self):
        """Clipboard envelope with json as string → PORT-004."""
        inner_str = json.dumps({
            'nodes': [
                {'id': '100001', 'type': '1', 'data': {'nodeMeta': {'title': 'Start'}}},
                {'id': '900001', 'type': '2', 'data': {'nodeMeta': {'title': 'End'}}},
            ],
            'edges': [{'sourceNodeID': '100001', 'targetNodeID': '900001'}],
        })
        envelope = json.dumps({
            'type': 'coze-workflow-clipboard-data',
            'json': inner_str,
        })
        r = _compile_with_text(envelope)
        assert 'PORTABILITY-004' in _port_ids(r)
