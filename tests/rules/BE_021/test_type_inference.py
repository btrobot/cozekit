"""BE-021: Type inference from ref target when source has no declared type.

When a parameter has no declared type, cozekit infers the type from the
ref target node's output declarations. This is stricter than coze-studio
which defers to runtime (UNKNOWN state).
"""
import pytest
from tests.conftest import compile_text


def _be021(yaml_text: str) -> list[str]:
    report = compile_text(yaml_text)
    return [d.message for d in report.diagnostics if d.rule_id == 'SEMANTIC-BE-021']


def _code(node_id, title, inputs=(), outputs=()):
    """Build a code node YAML snippet."""
    input_params = []
    for name, ref_node, ref_name, declared_type in inputs:
        type_line = ""
        if declared_type:
            type_line = "\n              type: " + declared_type
        input_params.append(
            "          - name: " + name + "\n"
            "            input:" + type_line + "\n"
            "              value:\n"
            "                type: ref\n"
            "                content:\n"
            "                  blockID: '" + ref_node + "'\n"
            "                  name: " + ref_name
        )
    inputs_block = '\n'.join(input_params) if input_params else '          []'

    output_block = ''
    if outputs:
        out_lines = []
        for name, otype in outputs:
            out_lines.append(
                "        - name: " + name + "\n"
                "          type: " + otype
            )
        output_block = '\n      outputs:\n' + '\n'.join(out_lines)

    return (
        "  - id: '" + node_id + "'\n"
        "    type: '5'\n"
        "    data:\n"
        "      nodeMeta:\n"
        "        title: " + title + "\n"
        "      inputs:\n"
        "        inputParameters:\n"
        + inputs_block + output_block
    )


def _wf(*node_snippets, edges):
    """Assemble a workflow YAML from node snippets and edge list."""
    edge_lines = '\n'.join(
        "  - sourceNodeID: '" + s + "'\n    targetNodeID: '" + t + "'"
        for s, t in edges
    )
    all_nodes = '\n'.join(node_snippets)
    return (
        "nodes:\n"
        "  - id: '100001'\n    type: '1'\n    data:\n      nodeMeta:\n        title: Start\n"
        + all_nodes + "\n"
        "  - id: '900001'\n    type: '2'\n    data:\n      nodeMeta:\n        title: End\n"
        "edges:\n" + edge_lines
    )


# ── Inferred type: no conflict ──────────────────────────────────

class TestTypeInference_NoConflict:
    """No declared type -> inferred from ref target -> compatible."""

    def test_inferred_list_refs_list_output(self):
        yaml = _wf(
            _code('n1', 'A', outputs=[('result', 'list')]),
            _code('n2', 'B', inputs=[('data', 'n1', 'result', None)], outputs=[('out', 'list')]),
            edges=[('100001', 'n1'), ('n1', 'n2'), ('n2', '900001')],
        )
        assert _be021(yaml) == []

    def test_inferred_string_refs_string_output(self):
        yaml = _wf(
            _code('n1', 'A', outputs=[('result', 'string')]),
            _code('n2', 'B', inputs=[('data', 'n1', 'result', None)]),
            edges=[('100001', 'n1'), ('n1', 'n2'), ('n2', '900001')],
        )
        assert _be021(yaml) == []

    def test_inferred_integer_refs_integer_output(self):
        yaml = _wf(
            _code('n1', 'A', outputs=[('count', 'integer')]),
            _code('n2', 'B', inputs=[('num', 'n1', 'count', None)]),
            edges=[('100001', 'n1'), ('n1', 'n2'), ('n2', '900001')],
        )
        assert _be021(yaml) == []


# ── Inferred type: downstream conflict ─────────────────────────

class TestTypeInference_DownstreamConflict:
    """No declared type on B -> inferred from A -> conflicts with declared type on C."""

    def test_inferred_list_vs_declared_string(self):
        yaml = _wf(
            _code('n1', 'A', outputs=[('result', 'list')]),
            _code('n2', 'B', inputs=[('data', 'n1', 'result', None)], outputs=[('out', 'list')]),
            _code('n3', 'C', inputs=[('text', 'n2', 'out', 'string')]),
            edges=[('100001', 'n1'), ('n1', 'n2'), ('n2', 'n3'), ('n3', '900001')],
        )
        errors = _be021(yaml)
        assert len(errors) == 1
        assert 'string' in errors[0] and 'list' in errors[0]

    def test_inferred_object_vs_declared_string(self):
        yaml = _wf(
            _code('n1', 'A', outputs=[('data', 'object')]),
            _code('n2', 'B', inputs=[('input', 'n1', 'data', None)], outputs=[('out', 'object')]),
            _code('n3', 'C', inputs=[('text', 'n2', 'out', 'string')]),
            edges=[('100001', 'n1'), ('n1', 'n2'), ('n2', 'n3'), ('n3', '900001')],
        )
        errors = _be021(yaml)
        assert len(errors) == 1
        assert 'string' in errors[0] and 'object' in errors[0]

    def test_no_false_positive_compatible_chain(self):
        yaml = _wf(
            _code('n1', 'A', outputs=[('result', 'list')]),
            _code('n2', 'B', inputs=[('data', 'n1', 'result', None)], outputs=[('out', 'list')]),
            _code('n3', 'C', inputs=[('items', 'n2', 'out', 'list')]),
            edges=[('100001', 'n1'), ('n1', 'n2'), ('n2', 'n3'), ('n3', '900001')],
        )
        assert _be021(yaml) == []


# ── Mixed: declared vs inferred coexist ─────────────────────────

class TestTypeInference_MixedDeclared:
    """Some inputs declared, some inferred."""

    def test_declared_compatible_inferred_compatible(self):
        yaml = _wf(
            _code('n1', 'A', outputs=[('str_out', 'string'), ('list_out', 'list')]),
            _code('n2', 'B', inputs=[
                ('a', 'n1', 'str_out', 'string'),
                ('b', 'n1', 'list_out', None),
            ]),
            edges=[('100001', 'n1'), ('n1', 'n2'), ('n2', '900001')],
        )
        assert _be021(yaml) == []

    def test_declared_conflict_inferred_ok(self):
        yaml = _wf(
            _code('n1', 'A', outputs=[('str_out', 'string'), ('list_out', 'list')]),
            _code('n2', 'B', inputs=[
                ('a', 'n1', 'str_out', 'integer'),
                ('b', 'n1', 'list_out', None),
            ]),
            edges=[('100001', 'n1'), ('n1', 'n2'), ('n2', '900001')],
        )
        errors = _be021(yaml)
        assert len(errors) == 1
        assert 'integer' in errors[0] and 'string' in errors[0]


# ── Edge cases ──────────────────────────────────────────────────

class TestTypeInference_EdgeCases:
    """Missing targets, missing outputs, global variables."""

    def test_missing_ref_target_skipped(self):
        yaml = _wf(
            _code('n1', 'A', inputs=[('data', 'nonexistent', 'output', None)]),
            edges=[('100001', 'n1'), ('n1', '900001')],
        )
        assert _be021(yaml) == []

    def test_missing_output_name_skipped(self):
        yaml = _wf(
            _code('n1', 'A', outputs=[('result', 'list')]),
            _code('n2', 'B', inputs=[('data', 'n1', 'nonexistent', None)]),
            edges=[('100001', 'n1'), ('n1', 'n2'), ('n2', '900001')],
        )
        assert _be021(yaml) == []

    def test_no_outputs_on_target_skipped(self):
        yaml = _wf(
            _code('n1', 'A', inputs=[('data', '100001', 'some_field', None)]),
            edges=[('100001', 'n1'), ('n1', '900001')],
        )
        assert _be021(yaml) == []

    def test_inferred_no_crash_on_complex_chain(self):
        """Deep chain with mixed declared/inferred types doesn't crash."""
        yaml = _wf(
            _code('n1', 'A', outputs=[('a', 'list'), ('b', 'string'), ('c', 'integer')]),
            _code('n2', 'B', inputs=[
                ('x', 'n1', 'a', None),       # inferred list
                ('y', 'n1', 'b', None),       # inferred string
                ('z', 'n1', 'c', None),       # inferred integer
            ], outputs=[('out_a', 'list'), ('out_b', 'string'), ('out_c', 'integer')]),
            _code('n3', 'C', inputs=[
                ('p', 'n2', 'out_a', 'list'),     # declared list vs inferred list -> ok
                ('q', 'n2', 'out_b', 'string'),   # declared string vs inferred string -> ok
                ('r', 'n2', 'out_c', 'integer'),  # declared integer vs inferred integer -> ok
            ]),
            edges=[('100001', 'n1'), ('n1', 'n2'), ('n2', 'n3'), ('n3', '900001')],
        )
        assert _be021(yaml) == []
