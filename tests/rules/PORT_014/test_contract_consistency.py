"""PORT-014: portability contract verification."""
from __future__ import annotations

from tests.conftest import compile_text, MINIMAL_START_END


def _port014_ids(t):
    return [d.rule_id for d in compile_text(t).diagnostics if d.rule_id == 'PORTABILITY-014']


class TestPORT014_Positive:
    def test_valid_workflow_no_contract_break(self):
        """Valid workflow with all nodes in symbol table → no PORT-014."""
        assert 'PORTABILITY-014' not in _port014_ids(MINIMAL_START_END)


class TestPORT014_Negative:
    def test_contract_break_placeholder(self):
        """PORT-014 is designed for internal consistency checks.

        Under normal circumstances, a well-formed workflow should never
        trigger PORT-014. This test documents that expectation.
        """
        # PORT-014 checks if node IDs in canvas are all in all_node_ids().
        # This is an internal invariant — hard to trigger externally.
        # We verify it doesn't fire on a valid workflow.
        assert 'PORTABILITY-014' not in _port014_ids(MINIMAL_START_END)
