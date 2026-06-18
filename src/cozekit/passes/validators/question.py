"""Node validators — Question node (type 18)."""
from __future__ import annotations
from ...diagnostics.core import Checkability, Diagnostic, DiagnosticKind
from ...ast.workflow_ast import NodeAST
from ..diag_helper import diag_fe
from ..constants import QUESTION_NODE_TYPE_ID

def _check_question_fields(node, diagnostics: list[Diagnostic]) -> None:
    """FE-001: validate Question node fields."""
    # Build lookup for node_specific_params
    params_by_name = {}
    for p in node.node_specific_params:
        if p.name:
            params_by_name[p.name] = p

    # question is required
    question_param = params_by_name.get('question')
    if question_param and question_param.input_ref:
        question_val = question_param.input_ref.name
        if not question_val or question_val.strip() == '':
            diagnostics.append(diag_fe(
                'SEMANTIC-FE-001',
                'violation',
                'Question node requires question content',
                checkability=Checkability.OFFLINE,
                source_span=node.source_span,
            ))
    elif not question_param:
        diagnostics.append(diag_fe(
            'SEMANTIC-FE-001',
            'violation',
            'Question node requires question content',
            checkability=Checkability.OFFLINE,
            source_span=node.source_span,
        ))

    # Check options when answer_type is 'option' and option_type is 'static'
    answer_type_param = params_by_name.get('answer_type')
    option_type_param = params_by_name.get('option_type')
    
    answer_type = answer_type_param.input_ref.name if answer_type_param and answer_type_param.input_ref else None
    option_type = option_type_param.input_ref.name if option_type_param and option_type_param.input_ref else None
    
    if answer_type == 'option' and option_type == 'static':
        # Check options exist and are not empty
        options_param = params_by_name.get('options')
        if options_param and options_param.input_ref:
            # options are stored as a list in the name field (serialized)
            # Check for duplicate option names
            _check_question_option_duplicates(
                options_param, diagnostics, node,
            )
        else:
            diagnostics.append(diag_fe(
                'SEMANTIC-FE-001',
                'violation',
                'Question node requires options when answer_type is option',
                checkability=Checkability.OFFLINE,
                source_span=node.source_span,
            ))

def _check_question_option_duplicates(options_param, diagnostics, node):
    """FE-001: Question options must not be empty or contain duplicates.

    Matches coze-studio questionOptionValidator (nonEmptyUniqueArray).
    """
    import ast as _ast
    raw = options_param.input_ref.name if options_param and options_param.input_ref else None
    if not raw:
        return
    try:
        parsed = _ast.literal_eval(raw)
    except (ValueError, SyntaxError):
        return
    if not isinstance(parsed, list):
        return
    seen = set()
    for i, item in enumerate(parsed):
        if not isinstance(item, dict):
            continue
        name = item.get('name', '')
        # Empty option content check
        if not name or not name.strip():
            diagnostics.append(diag_fe(
                'SEMANTIC-FE-001', 'violation',
                f'Question node option {i + 1} content cannot be empty',
                checkability=Checkability.OFFLINE,
                source_span=node.source_span,
            ))
            continue
        # Duplicate check
        if name in seen:
            diagnostics.append(diag_fe(
                'SEMANTIC-FE-001', 'violation',
                f'Question node has duplicate option: "{name}"',
                checkability=Checkability.OFFLINE,
                source_span=node.source_span,
            ))
        else:
            seen.add(name)


# ── Code node (type 5) ─────────────────────────────────────
