"""BE-010: Extended branch port validation.

Additional scenarios beyond the basic If test in test_branch_ports.py:
  - Both ports connected → valid
  - Missing true port → error
  - Missing false port → error
  - Both ports missing → error

NOTE: The compiler validates If node branch ports (true/false) but does not
currently validate Intent or Question node ports as branch ports. Those are
validated at the FE layer (FE-006/007 for subcanvas ports).

规则来源: backend-rules.json BE-validateConnections-002, coze-workflow-spec.md §3.6.2
"""
from __future__ import annotations

from tests.conftest import compile_text


def _be010_ids(t):
    return [d.rule_id for d in compile_text(t).diagnostics if d.rule_id == 'SEMANTIC-BE-010']


def _make_if_workflow(true_connected: bool, false_connected: bool) -> str:
    """Build a workflow with an If node, optionally connecting true/false ports."""
    edges = ['  - sourceNodeID: "100001"\n    targetNodeID: "if-1"']
    if true_connected:
        edges.append('  - sourceNodeID: "if-1"\n    sourcePortID: "true"\n    targetNodeID: "900001"')
    if false_connected:
        edges.append('  - sourceNodeID: "if-1"\n    sourcePortID: "false"\n    targetNodeID: "900001"')
    edges_str = '\n'.join(edges)
    return (
        'nodes:\n'
        '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
        '  - id: "if-1"\n    type: "8"\n    data:\n      nodeMeta:\n        title: "If"\n'
        '      inputs:\n        branches:\n'
        '          - branchKey: "true"\n            condition: {}\n'
        '          - branchKey: "false"\n            condition: {}\n'
        '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
        f'edges:\n{edges_str}\n'
    )


class TestBE010_Extended_Positive:
    """Valid branch port configurations → no BE-010."""

    def test_both_ports_connected(self):
        """Both true and false ports connected → no error."""
        t = _make_if_workflow(true_connected=True, false_connected=True)
        assert 'SEMANTIC-BE-010' not in _be010_ids(t)


class TestBE010_Extended_Negative:
    """Invalid branch port configurations → BE-010 error."""

    def test_missing_true_port(self):
        """Only false port connected → BE-010 for missing true."""
        t = _make_if_workflow(true_connected=False, false_connected=True)
        assert 'SEMANTIC-BE-010' in _be010_ids(t)

    def test_missing_false_port(self):
        """Only true port connected → BE-010 for missing false."""
        t = _make_if_workflow(true_connected=True, false_connected=False)
        assert 'SEMANTIC-BE-010' in _be010_ids(t)

    def test_both_ports_missing(self):
        """Neither port connected → BE-010 for both."""
        t = _make_if_workflow(true_connected=False, false_connected=False)
        ids = _be010_ids(t)
        assert len(ids) >= 1
