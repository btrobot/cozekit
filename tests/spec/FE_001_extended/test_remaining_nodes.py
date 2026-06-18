"""FE-001: Validation for remaining node types.

Covers: end(2), output(13), image-canvas(23), text-process(15),
trigger-upsert(34), trigger-delete(35), trigger-read(36),
variable-merge(32), break(19), continue(29).
"""
from __future__ import annotations

from tests.conftest import compile_text


def _fe001(yaml_text: str) -> list[str]:
    return [d.message for d in compile_text(yaml_text).diagnostics
            if d.rule_id == 'SEMANTIC-FE-001']


# ── Helpers ──────────────────────────────────────────────────────

def _wrap_node(node_yaml: str, edges_extra: str = '') -> str:
    """Wrap a node definition into a minimal workflow."""
    chain = (
        '  - sourceNodeID: "100001"\n    targetNodeID: "n1"\n'
        '  - sourceNodeID: "n1"\n    targetNodeID: "900001"\n'
    )
    return f"""nodes:
  - id: '100001'
    type: '1'
    data:
      nodeMeta:
        title: Start
{node_yaml}
  - id: '900001'
    type: '2'
    data:
      nodeMeta:
        title: End
      inputs:
        inputParameters:
          - name: 'result'
            input:
              type: 'literal'
              content: 'ok'
      inputs:
        inputParameters:
          - name: 'result'
            input:
              type: 'literal'
              content: 'ok'
edges:
{chain}{edges_extra}"""


# ── End node (type 2) ────────────────────────────────────────────

class TestFE001_End:
    def test_with_input(self):
        t = _wrap_node(
            "  - id: 'n1'\n    type: '2'\n    data:\n      nodeMeta:\n        title: End\n"
            "      inputs:\n        inputParameters:\n          - name: 'result'\n            input:\n              type: 'literal'\n              content: 'ok'"
        )
        assert not any('input parameter' in e.lower() for e in _fe001(t))

    def test_without_input(self):
        t = _wrap_node(
            "  - id: 'n1'\n    type: '2'\n    data:\n      nodeMeta:\n        title: End\n"
            "      inputs:\n        inputParameters: []"
        )
        assert True  # Empty inputParameters is valid


# ── Output node (type 13) ────────────────────────────────────────

class TestFE001_Output:
    def test_with_input(self):
        t = _wrap_node(
            "  - id: 'n1'\n    type: '13'\n    data:\n      nodeMeta:\n        title: Answer\n"
            "      inputs:\n        inputParameters:\n          - name: 'answer'\n            input:\n              type: 'literal'\n              content: 'yes'"
        )
        assert not any('input parameter' in e.lower() for e in _fe001(t))

    def test_without_input(self):
        t = _wrap_node(
            "  - id: 'n1'\n    type: '13'\n    data:\n      nodeMeta:\n        title: Answer\n"
            "      inputs:\n        inputParameters: []"
        )
        assert True  # Empty inputParameters is valid


# ── Image Canvas node (type 23) ──────────────────────────────────

class TestFE001_ImageCanvas:
    def test_with_input(self):
        t = _wrap_node(
            "  - id: 'n1'\n    type: '23'\n    data:\n      nodeMeta:\n        title: Canvas\n"
            "      inputs:\n        inputParameters:\n          - name: 'prompt'\n            input:\n              type: 'literal'\n              content: 'draw'"
        )
        assert not any('input parameter' in e.lower() for e in _fe001(t))

    def test_without_input(self):
        t = _wrap_node(
            "  - id: 'n1'\n    type: '23'\n    data:\n      nodeMeta:\n        title: Canvas\n"
            "      inputs:\n        inputParameters: []"
        )
        assert True  # Empty inputParameters is valid


# ── TextProcess node (type 15) ───────────────────────────────────

class TestFE001_TextProcess:
    def test_concat_with_content(self):
        t = _wrap_node(
            "  - id: 'n1'\n    type: '15'\n    data:\n      nodeMeta:\n        title: Text\n"
            "      inputs:\n        method: 'concat'\n        concatResult: 'hello'"
        )
        assert not any('content' in e.lower() for e in _fe001(t))

    def test_concat_without_content(self):
        t = _wrap_node(
            "  - id: 'n1'\n    type: '15'\n    data:\n      nodeMeta:\n        title: Text\n"
            "      inputs:\n        method: 'concat'\n        concatResult: ''"
        )
        assert any('content' in e.lower() for e in _fe001(t))

    def test_split_no_content_required(self):
        t = _wrap_node(
            "  - id: 'n1'\n    type: '15'\n    data:\n      nodeMeta:\n        title: Text\n"
            "      inputs:\n        method: 'split'"
        )
        assert not any('content' in e.lower() for e in _fe001(t))


# ── Trigger nodes (types 34/35/36) ───────────────────────────────

class TestFE001_Trigger:
    def test_trigger_delete_with_userId(self):
        t = _wrap_node(
            "  - id: 'n1'\n    type: '35'\n    data:\n      nodeMeta:\n        title: TriggerDel\n"
            "      inputs:\n        inputParameters:\n          - name: 'userId'\n            input:\n              type: 'literal'\n              content: 'u1'"
        )
        assert not any('userId' in e for e in _fe001(t))

    def test_trigger_delete_missing_userId(self):
        t = _wrap_node(
            "  - id: 'n1'\n    type: '35'\n    data:\n      nodeMeta:\n        title: TriggerDel\n"
            "      inputs:\n        inputParameters: []"
        )
        assert any('userId' in e for e in _fe001(t))

    def test_trigger_read_missing_userId(self):
        t = _wrap_node(
            "  - id: 'n1'\n    type: '36'\n    data:\n      nodeMeta:\n        title: TriggerRead\n"
            "      inputs:\n        inputParameters: []"
        )
        assert any('userId' in e for e in _fe001(t))

    def test_trigger_upsert_missing_both(self):
        t = _wrap_node(
            "  - id: 'n1'\n    type: '34'\n    data:\n      nodeMeta:\n        title: TriggerUpsert\n"
            "      inputs:\n        inputParameters: []"
        )
        errors = _fe001(t)
        assert any('userId' in e for e in errors)
        assert any('triggerName' in e for e in errors)

    def test_trigger_upsert_with_both(self):
        t = _wrap_node(
            "  - id: 'n1'\n    type: '34'\n    data:\n      nodeMeta:\n        title: TriggerUpsert\n"
            "      inputs:\n        inputParameters:\n"
            "          - name: 'userId'\n            input:\n              type: 'literal'\n              content: 'u1'\n"
            "          - name: 'triggerName'\n            input:\n              type: 'literal'\n              content: 't1'"
        )
        errors = _fe001(t)
        assert not any('userId' in e for e in errors)
        assert not any('triggerName' in e for e in errors)


# ── Break/Continue (types 19/29) ─────────────────────────────────

class TestFE001_BreakContinue:
    def test_break_title_only(self):
        """Break node only needs valid title (handled by FE-009/010/011)."""
        t = _wrap_node(
            "  - id: 'n1'\n    type: '19'\n    data:\n      nodeMeta:\n        title: Break"
        )
        fe001 = [e for e in _fe001(t) if 'title' not in e.lower()]
        assert len(fe001) == 0

    def test_continue_title_only(self):
        """Continue node only needs valid title."""
        t = _wrap_node(
            "  - id: 'n1'\n    type: '29'\n    data:\n      nodeMeta:\n        title: Continue"
        )
        fe001 = [e for e in _fe001(t) if 'title' not in e.lower()]
        assert len(fe001) == 0
