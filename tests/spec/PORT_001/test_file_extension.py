"""PORT-001: transport envelope file extension validation."""
from __future__ import annotations

from pathlib import Path

from tests.conftest import compile_text, compile_fixture


def _port001_ids(report):
    return [d.rule_id for d in report.diagnostics if d.rule_id == 'PORTABILITY-001']


class TestPORT001_Positive:
    def test_json_extension_accepted(self):
        """File ending in .json → no PORT-001."""
        from cozekit.compiler_v2_api import compile_text as ct
        r = ct(
            'nodes:\n  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "900001"\n',
            source_file='workflow.json',
        )
        assert 'PORTABILITY-001' not in [d.rule_id for d in r.diagnostics]

    def test_flow_extension_accepted(self):
        """File ending in .flow → no PORT-001."""
        from cozekit.compiler_v2_api import compile_text as ct
        r = ct(
            'nodes:\n  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "900001"\n',
            source_file='workflow.flow',
        )
        assert 'PORTABILITY-001' not in [d.rule_id for d in r.diagnostics]


class TestPORT001_Negative:
    def test_txt_extension_rejected(self):
        """File ending in .txt → PORT-001."""
        from cozekit.compiler_v2_api import compile_text as ct
        r = ct(
            'nodes:\n  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "900001"\n',
            source_file='workflow.txt',
        )
        assert 'PORTABILITY-001' in [d.rule_id for d in r.diagnostics]
