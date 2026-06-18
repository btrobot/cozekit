"""FE-001: Question 节点 (type 18) 字段验证。

验证规则:
  - question 必填 (问题内容不能为空)
  - options 必填 (当 answer_type=option, option_type=static)
  - options 不能重复

Tests cover:
  - Valid question in text mode
  - Valid question in option mode with options
  - Missing question content
  - Empty question content
  - Option mode without options
  - Duplicate options detected
  - Unique options no violation
  - Whitespace-only question
  - Question with very long content
"""

from tests.conftest import compile_text


def _fe001_errors(yaml_text: str) -> list[str]:
    report = compile_text(yaml_text)
    return [
        d.message for d in report.diagnostics
        if d.rule_id == 'SEMANTIC-FE-001'
    ]


def _make_question_yaml(
    question: str | None = 'What is your name?',
    answer_type: str | None = 'text',
    option_type: str | None = None,
    options: str | None = None,
) -> str:
    params = {}
    if question is not None:
        params['question'] = question
    if answer_type is not None:
        params['answer_type'] = answer_type
    if option_type is not None:
        params['option_type'] = option_type
    if options is not None:
        params['options'] = options

    qp_lines = []
    for k, v in params.items():
        if k == 'options':
            qp_lines.append(f"          options: {v}")
        else:
            qp_lines.append(f"          {k}: '{v}'")
    qp_block = '\n'.join(qp_lines) if qp_lines else '          {}'

    return f"""
nodes:
  - id: '100001'
    type: '1'
    data:
      nodeMeta:
        title: Start
  - id: 'q1'
    type: '18'
    data:
      nodeMeta:
        title: Question
      inputs:
        inputParameters: []
        questionParams:
{qp_block}
  - id: '900001'
    type: '2'
    data:
      nodeMeta:
        title: End
edges:
  - sourceNodeID: '100001'
    targetNodeID: 'q1'
  - sourceNodeID: 'q1'
    targetNodeID: '900001'
"""


# ── Positive ─────────────────────────────────────────────────────

class TestFE001_Question_Positive:
    """Valid question configurations → no FE-001 errors."""

    def test_with_question_text_mode(self):
        yaml = _make_question_yaml(question='Hello?')
        errors = _fe001_errors(yaml)
        assert not any('question' in e.lower() for e in errors)

    def test_option_mode_with_options(self):
        yaml = _make_question_yaml(
            question='Pick one',
            answer_type='option',
            option_type='static',
            options='["A", "B"]',
        )
        errors = _fe001_errors(yaml)
        assert not any('option' in e.lower() for e in errors)

    def test_question_with_long_content(self):
        """Very long question text → valid."""
        long_q = 'A' * 500
        yaml = _make_question_yaml(question=long_q)
        errors = _fe001_errors(yaml)
        assert not any('question' in e.lower() for e in errors)


# ── Negative ─────────────────────────────────────────────────────

class TestFE001_Question_Negative:
    """Invalid question configurations → FE-001 errors."""

    def test_missing_question_content(self):
        yaml = _make_question_yaml(question=None)
        errors = _fe001_errors(yaml)
        assert any('question' in e.lower() for e in errors)

    def test_empty_question_content(self):
        yaml = _make_question_yaml(question='')
        errors = _fe001_errors(yaml)
        assert any('question' in e.lower() for e in errors)

    def test_option_mode_without_options(self):
        yaml = _make_question_yaml(
            question='Pick one',
            answer_type='option',
            option_type='static',
        )
        errors = _fe001_errors(yaml)
        assert any('option' in e.lower() for e in errors)

    def test_whitespace_only_question(self):
        """Whitespace-only question → error."""
        yaml = _make_question_yaml(question='   ')
        errors = _fe001_errors(yaml)
        assert any('question' in e.lower() for e in errors)


# ── Duplicate options ───────────────────────────────────────────

class TestFE001_QuestionOptionDuplicates:
    """Option duplicate validation."""

    def test_duplicate_options_detected(self):
        """Duplicate option names → FE-001 violation."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "q1"\n    type: "18"\n    data:\n'
            '      nodeMeta:\n        title: "Q"\n'
            '      inputs:\n'
            '        questionParams:\n'
            '          question: "pick"\n'
            '          answer_type: "option"\n'
            '          option_type: "static"\n'
            '          options:\n'
            '            - name: "A"\n'
            '            - name: "A"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "q1"\n  - sourceNodeID: "q1"\n    targetNodeID: "900001"\n'
        )
        r = compile_text(t)
        fe001 = [d for d in r.diagnostics if d.rule_id == 'SEMANTIC-FE-001']
        dup = [d for d in fe001 if 'duplicate' in d.message.lower()]
        assert len(dup) >= 1

    def test_unique_options_no_violation(self):
        """Unique option names → no duplicate violation."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "q1"\n    type: "18"\n    data:\n'
            '      nodeMeta:\n        title: "Q"\n'
            '      inputs:\n'
            '        questionParams:\n'
            '          question: "pick"\n'
            '          answer_type: "option"\n'
            '          option_type: "static"\n'
            '          options:\n'
            '            - name: "A"\n'
            '            - name: "B"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "q1"\n  - sourceNodeID: "q1"\n    targetNodeID: "900001"\n'
        )
        r = compile_text(t)
        fe001 = [d for d in r.diagnostics if d.rule_id == 'SEMANTIC-FE-001']
        dup = [d for d in fe001 if 'duplicate' in d.message.lower()]
        assert len(dup) == 0

    def test_three_unique_options(self):
        """Three unique options → no violation."""
        t = (
            'nodes:\n'
            '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"\n'
            '  - id: "q1"\n    type: "18"\n    data:\n'
            '      nodeMeta:\n        title: "Q"\n'
            '      inputs:\n'
            '        questionParams:\n'
            '          question: "pick"\n'
            '          answer_type: "option"\n'
            '          option_type: "static"\n'
            '          options:\n'
            '            - name: "A"\n'
            '            - name: "B"\n'
            '            - name: "C"\n'
            '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"\n'
            'edges:\n  - sourceNodeID: "100001"\n    targetNodeID: "q1"\n  - sourceNodeID: "q1"\n    targetNodeID: "900001"\n'
        )
        r = compile_text(t)
        fe001 = [d for d in r.diagnostics if d.rule_id == 'SEMANTIC-FE-001']
        dup = [d for d in fe001 if 'duplicate' in d.message.lower()]
        assert len(dup) == 0
