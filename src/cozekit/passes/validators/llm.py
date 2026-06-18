"""Node validators — LLM node (type 3)."""
from __future__ import annotations
from ...diagnostics.core import Checkability, Diagnostic, DiagnosticKind
from ...ast.workflow_ast import NodeAST
from ..diag_helper import diag_fe
from ..constants import (
    LLM_NODE_TYPE_ID, TEMPERATURE_MIN, TEMPERATURE_MAX, MAX_TOKENS_MIN,
)

def _check_llm_fields(node, diagnostics: list[Diagnostic]) -> None:
    """FE-001: validate LLM node fields."""
    # Build lookup for node_specific_params
    params_by_name = {}
    for p in node.node_specific_params:
        if p.name:
            params_by_name[p.name] = p

    # modelType is required
    if 'modelType' not in params_by_name:
        diagnostics.append(diag_fe(
            'SEMANTIC-FE-001',
            'violation',
            'LLM node requires modelType parameter',
            checkability=Checkability.OFFLINE,
            source_span=node.source_span,
        ))

    # temperature range check (0-2)
    temp_param = params_by_name.get('temperature')
    if temp_param and temp_param.input_ref and temp_param.input_ref.ref_type == 'literal':
        try:
            temp_val = float(temp_param.input_ref.name) if temp_param.input_ref.name else None
            if temp_val is not None and (temp_val < TEMPERATURE_MIN or temp_val > TEMPERATURE_MAX):
                diagnostics.append(diag_fe(
                    'SEMANTIC-FE-001',
                    'violation',
                    'LLM node temperature must be between 0 and 2',
                    checkability=Checkability.OFFLINE,
                    source_span=node.source_span,
                ))
        except (ValueError, TypeError):
            pass

    # maxTokens > 0 check
    max_tokens_param = params_by_name.get('maxTokens')
    if max_tokens_param and max_tokens_param.input_ref and max_tokens_param.input_ref.ref_type == 'literal':
        try:
            val = int(max_tokens_param.input_ref.name) if max_tokens_param.input_ref.name else None
            if val is not None and val <= 0:
                diagnostics.append(diag_fe(
                    'SEMANTIC-FE-001',
                    'violation',
                    'LLM node maxTokens must be a positive integer',
                    checkability=Checkability.OFFLINE,
                    source_span=node.source_span,
                ))
        except (ValueError, TypeError):
            pass

    # prompt / systemPrompt: at least one must be non-empty.
    # In coze-studio, prompt is only required when model.is_up_required === true,
    # which is a runtime property we cannot determine at compile time.
    # systemPrompt is always valid as the sole prompt source.
    prompt_param = params_by_name.get('prompt')
    system_prompt_param = params_by_name.get('systemPrompt')

    prompt_val = ''
    if prompt_param and prompt_param.input_ref:
        prompt_val = str(prompt_param.input_ref.name or '').strip()

    system_prompt_val = ''
    if system_prompt_param and system_prompt_param.input_ref:
        system_prompt_val = str(system_prompt_param.input_ref.name or '').strip()

    if not prompt_val and not system_prompt_val:
        diagnostics.append(diag_fe(
            'SEMANTIC-FE-001',
            'violation',
            'LLM node requires at least one of prompt or systemPrompt to be non-empty',
            checkability=Checkability.OFFLINE,
            source_span=node.source_span,
        ))
