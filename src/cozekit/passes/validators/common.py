"""Node-specific field validators — common/small node types."""
from __future__ import annotations
from ...diagnostics.core import Checkability, Diagnostic, DiagnosticKind
from ...ast.workflow_ast import NodeAST
from ..diag_helper import diag_fe
from ..constants import (
    INTENT_NODE_TYPE_ID, IMAGE_GENERATE_NODE_TYPE_ID, LTM_NODE_TYPE_ID,
    DATASET_SEARCH_NODE_TYPE_ID, DATASET_WRITE_NODE_TYPE_ID,
    TEXT_PROCESS_NODE_TYPE_ID, VARIABLE_MERGE_NODE_TYPE_ID,
    TRIGGER_UPSERT_NODE_TYPE_ID, TRIGGER_DELETE_NODE_TYPE_ID,
    TRIGGER_READ_NODE_TYPE_ID, PLUGIN_NODE_TYPE_ID, SUBWORKFLOW_NODE_TYPE_ID,
    REQUIRE_FIRST_INPUT_NODE_TYPES, ALLOWED_BLOCK_INPUT_VALUE_TYPES,
    CODE_NODE_TYPE_ID,
)

def _check_intent_fields(node, diagnostics: list[Diagnostic]) -> None:
    """FE-001: validate Intent node — first input is required."""
    if not node.parameters:
        diagnostics.append(diag_fe(
            'SEMANTIC-FE-001', 'violation',
            'Intent node requires at least one input parameter',
            checkability=Checkability.OFFLINE,
            source_span=node.source_span,
        ))
    else:
        first = node.parameters[0]
        if not first.input_ref or not first.input_ref.name or first.input_ref.name.strip() == '':
            diagnostics.append(diag_fe(
                'SEMANTIC-FE-001', 'violation',
                'Intent node requires first input value',
                checkability=Checkability.OFFLINE,
                source_span=node.source_span,
            ))

# ── Image Generate node (type 16) ──────────────────────────
def _check_image_generate_fields(node, diagnostics: list[Diagnostic]) -> None:
    """FE-001: validate Image Generate node — model is required."""
    params_by_name = {p.name: p for p in node.node_specific_params if p.name}

    model_param = params_by_name.get('model')
    if model_param and model_param.input_ref:
        model_val = model_param.input_ref.name
        if not model_val or model_val.strip() == '':
            diagnostics.append(diag_fe(
                'SEMANTIC-FE-001', 'violation',
                'Image Generate node requires model selection',
                checkability=Checkability.OFFLINE,
                source_span=node.source_span,
            ))
    elif not model_param:
        diagnostics.append(diag_fe(
            'SEMANTIC-FE-001', 'violation',
            'Image Generate node requires model selection',
            checkability=Checkability.OFFLINE,
            source_span=node.source_span,
        ))

# ── LTM node (type 26) ────────────────────────────────────

def _check_ltm_fields(node, diagnostics: list[Diagnostic]) -> None:
    """FE-001: validate LTM node — first input is required."""
    if not node.parameters:
        diagnostics.append(diag_fe(
            'SEMANTIC-FE-001', 'violation',
            'LTM node requires at least one input parameter',
            checkability=Checkability.OFFLINE,
            source_span=node.source_span,
        ))
    else:
        first = node.parameters[0]
        if not first.input_ref or not first.input_ref.name or first.input_ref.name.strip() == '':
            diagnostics.append(diag_fe(
                'SEMANTIC-FE-001', 'violation',
                'LTM node requires first input value',
                checkability=Checkability.OFFLINE,
                source_span=node.source_span,
            ))

# ── Dataset nodes (types 6/27) ─────────────────────────────

def _check_dataset_fields(node, diagnostics: list[Diagnostic]) -> None:
    """FE-001: validate Dataset node — knowledge base and required inputs."""
    params_by_name = {p.name: p for p in node.node_specific_params if p.name}

    knowledge_param = params_by_name.get('knowledge')
    if knowledge_param and knowledge_param.input_ref:
        knowledge_val = knowledge_param.input_ref.name
        if not knowledge_val or knowledge_val.strip() == '':
            diagnostics.append(diag_fe(
                'SEMANTIC-FE-001', 'violation',
                'Dataset node requires knowledge base selection',
                checkability=Checkability.OFFLINE,
                source_span=node.source_span,
            ))
    elif not knowledge_param:
        diagnostics.append(diag_fe(
            'SEMANTIC-FE-001', 'violation',
            'Dataset node requires knowledge base selection',
            checkability=Checkability.OFFLINE,
            source_span=node.source_span,
        ))

    # Dataset search (type 6): Query inputParameter is required
    if node.node_type == DATASET_SEARCH_NODE_TYPE_ID:
        input_names = {p.name for p in node.parameters}
        if 'Query' not in input_names:
            diagnostics.append(diag_fe(
                'SEMANTIC-FE-001', 'violation',
                'Dataset search node requires Query input parameter',
                checkability=Checkability.OFFLINE,
                source_span=node.source_span,
            ))

    # Dataset write (type 27): knowledge inputParameter is required
    if node.node_type == DATASET_WRITE_NODE_TYPE_ID:
        input_names = {p.name for p in node.parameters}
        if 'knowledge' not in input_names:
            diagnostics.append(diag_fe(
                'SEMANTIC-FE-001', 'violation',
                'Dataset write node requires knowledge input parameter',
                checkability=Checkability.OFFLINE,
                source_span=node.source_span,
            ))

def _check_first_input_required(node, diagnostics: list[Diagnostic]) -> None:
    """FE-001: Intent/LTM/JsonStringify nodes require first inputParameter value."""
    if not node.parameters:
        diagnostics.append(diag_fe(
            'SEMANTIC-FE-001', 'violation',
            f'Node "{node.title or node.node_id}" requires at least one input parameter',
            checkability=Checkability.OFFLINE,
            source_span=node.source_span,
        ))
    else:
        first = node.parameters[0]
        if not first.input_ref or not first.input_ref.name or not str(first.input_ref.name).strip():
            diagnostics.append(diag_fe(
                'SEMANTIC-FE-001', 'violation',
                f'Node "{node.title or node.node_id}" requires first input value',
                checkability=Checkability.OFFLINE,
                source_span=node.source_span,
            ))

def _check_text_process_fields(node, diagnostics: list[Diagnostic]) -> None:
    """FE-001: TextProcess node requires content for concat mode."""
    params_by_name = {p.name: p for p in node.node_specific_params if p.name}
    method = params_by_name.get('method')
    method_val = method.input_ref.name if method and method.input_ref else 'concat'
    if method_val != 'split':
        concat = params_by_name.get('concatResult')
        if not concat or not concat.input_ref or not str(concat.input_ref.name).strip():
            diagnostics.append(diag_fe(
                'SEMANTIC-FE-001', 'violation',
                'TextProcess node requires content for concat mode',
                checkability=Checkability.OFFLINE,
                source_span=node.source_span,
            ))

def _check_trigger_fields(node, diagnostics: list[Diagnostic]) -> None:
    """FE-001: Trigger nodes require userId; upsert also requires triggerName."""
    input_names = {p.name for p in node.parameters}
    if 'userId' not in input_names:
        diagnostics.append(diag_fe(
            'SEMANTIC-FE-001', 'violation',
            'Trigger node requires userId input parameter',
            checkability=Checkability.OFFLINE,
            source_span=node.source_span,
        ))
    if node.node_type == TRIGGER_UPSERT_NODE_TYPE_ID:
        if 'triggerName' not in input_names:
            diagnostics.append(diag_fe(
                'SEMANTIC-FE-001', 'violation',
                'Trigger upsert node requires triggerName input parameter',
                checkability=Checkability.OFFLINE,
                source_span=node.source_span,
            ))

def _check_plugin_fields(node, diagnostics: list[Diagnostic]) -> None:
    """FE-001: Plugin node (type 4) static validation.

    Validates:
    - inputParameters have valid value expression format
    Note: Whether inputs are required depends on API definition (runtime).
    """
    # Check inputParameters format
    for param in node.parameters:
        if param.input_ref and param.input_ref.ref_type:
            if param.input_ref.ref_type not in ALLOWED_BLOCK_INPUT_VALUE_TYPES:
                diagnostics.append(diag_fe(
                    'SEMANTIC-FE-001', 'violation',
                    f'Plugin node inputParameter "{param.name}" has invalid value type "{param.input_ref.ref_type}"',
                    checkability=Checkability.OFFLINE,
                    source_span=node.source_span,
                ))

def _check_subworkflow_fields(node, diagnostics: list[Diagnostic]) -> None:
    """FE-001: SubWorkflow node (type 9) static validation.

    Validates:
    - inputParameters have valid value expression format
    Note: Whether inputs are required depends on sub-workflow definition (runtime).
    """
    # Check inputParameters format
    for param in node.parameters:
        if param.input_ref and param.input_ref.ref_type:
            if param.input_ref.ref_type not in ALLOWED_BLOCK_INPUT_VALUE_TYPES:
                diagnostics.append(diag_fe(
                    'SEMANTIC-FE-001', 'violation',
                    f'SubWorkflow node inputParameter "{param.name}" has invalid value type "{param.input_ref.ref_type}"',
                    checkability=Checkability.OFFLINE,
                    source_span=node.source_span,
                ))

# ── Chat/Conversation nodes ─────────────────────────────────


def _check_code_fields(node, diagnostics: list[Diagnostic]) -> None:
    """FE-001: validate Code node — code content is required."""
    params_by_name = {p.name: p for p in node.node_specific_params if p.name}

    code_param = params_by_name.get('code')
    if code_param and code_param.input_ref:
        code_val = code_param.input_ref.name
        if not code_val or code_val.strip() == '':
            diagnostics.append(diag_fe(
                'SEMANTIC-FE-001', 'violation',
                'Code node requires code content',
                checkability=Checkability.OFFLINE,
                source_span=node.source_span,
            ))
    elif not code_param:
        diagnostics.append(diag_fe(
            'SEMANTIC-FE-001', 'violation',
            'Code node requires code content',
            checkability=Checkability.OFFLINE,
            source_span=node.source_span,
        ))

# ── Database nodes (types 12/42/43/44/46) ──────────────────