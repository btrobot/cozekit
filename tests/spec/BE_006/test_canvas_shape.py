"""BE-006: canvas shape validation."""
from __future__ import annotations

from tests.conftest import compile_text, MINIMAL_START_END


def _be006_ids(t):
    return [d.rule_id for d in compile_text(t).diagnostics if d.rule_id == 'SEMANTIC-BE-006']


class TestBE006_Positive:
    def test_valid_workflow_no_shape_issue(self):
        """Valid workflow with nodes and edges → no BE-006."""
        assert 'SEMANTIC-BE-006' not in _be006_ids(MINIMAL_START_END)


class TestBE006_Negative:
    def test_empty_workflow_triggers_shape(self):
        """Empty workflow → BE-006 (no canvas or bad shape)."""
        t = 'nodes: []\nedges: []\n'
        ids = _be006_ids(t)
        assert len(ids) >= 1
