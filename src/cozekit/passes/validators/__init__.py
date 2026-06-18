"""Node-specific field validators.

Each module validates a group of node types. The NODE_VALIDATOR_REGISTRY
maps node_type_id -> list of validator functions.
"""
from __future__ import annotations

from ..constants import (
    LLM_NODE_TYPE_ID, CODE_NODE_TYPE_ID, QUESTION_NODE_TYPE_ID,
    IF_NODE_TYPE_ID, INTENT_NODE_TYPE_ID, HTTP_NODE_TYPE_ID,
    SET_VARIABLE_NODE_TYPE_ID, VARIABLE_ASSIGN_NODE_TYPE_ID,
    DATABASE_NODE_TYPE_IDS, IMAGE_GENERATE_NODE_TYPE_ID,
    LTM_NODE_TYPE_ID, DATASET_SEARCH_NODE_TYPE_ID, DATASET_WRITE_NODE_TYPE_ID,
    TEXT_PROCESS_NODE_TYPE_ID, VARIABLE_MERGE_NODE_TYPE_ID,
    TRIGGER_UPSERT_NODE_TYPE_ID, TRIGGER_DELETE_NODE_TYPE_ID,
    TRIGGER_READ_NODE_TYPE_ID, CHAT_NODE_TYPE_IDS,
    REQUIRE_FIRST_INPUT_NODE_TYPES, PLUGIN_NODE_TYPE_ID,
    SUBWORKFLOW_NODE_TYPE_ID,
)

from .llm import _check_llm_fields
from .question import _check_question_fields
from .database import _check_database_fields
from .http import _check_http_fields
from .variable import _check_variable_assign_fields, _check_variable_merge_fields
from .if_condition import _check_if_conditions
from .chat_nodes import _check_chat_node_fields
from .common import (
    _check_code_fields,
    _check_intent_fields,
    _check_image_generate_fields,
    _check_ltm_fields,
    _check_dataset_fields,
    _check_first_input_required,
    _check_text_process_fields,
    _check_trigger_fields,
    _check_plugin_fields,
    _check_subworkflow_fields,
)


def _build_registry() -> dict[str, list]:
    """Build the node validator registry."""
    reg: dict[str, list] = {}

    def _add(type_ids, *validators):
        for tid in (type_ids if isinstance(type_ids, (list, tuple, frozenset)) else [type_ids]):
            reg.setdefault(tid, []).extend(validators)

    _add(LLM_NODE_TYPE_ID, _check_llm_fields)
    _add(QUESTION_NODE_TYPE_ID, _check_question_fields)
    _add(CODE_NODE_TYPE_ID, _check_code_fields)  # TODO: move to common
    _add(list(DATABASE_NODE_TYPE_IDS), _check_database_fields)
    _add(HTTP_NODE_TYPE_ID, _check_http_fields)
    _add([SET_VARIABLE_NODE_TYPE_ID, VARIABLE_ASSIGN_NODE_TYPE_ID], _check_variable_assign_fields)
    _add(INTENT_NODE_TYPE_ID, _check_intent_fields)
    _add(IMAGE_GENERATE_NODE_TYPE_ID, _check_image_generate_fields)
    _add(LTM_NODE_TYPE_ID, _check_ltm_fields)
    _add([DATASET_SEARCH_NODE_TYPE_ID, DATASET_WRITE_NODE_TYPE_ID], _check_dataset_fields)
    _add(list(REQUIRE_FIRST_INPUT_NODE_TYPES), _check_first_input_required)
    _add(TEXT_PROCESS_NODE_TYPE_ID, _check_text_process_fields)
    _add([TRIGGER_UPSERT_NODE_TYPE_ID, TRIGGER_DELETE_NODE_TYPE_ID, TRIGGER_READ_NODE_TYPE_ID],
         _check_trigger_fields)
    _add(IF_NODE_TYPE_ID, _check_if_conditions)
    _add(VARIABLE_MERGE_NODE_TYPE_ID, _check_variable_merge_fields)
    _add(PLUGIN_NODE_TYPE_ID, _check_plugin_fields)
    _add(SUBWORKFLOW_NODE_TYPE_ID, _check_subworkflow_fields)
    _add(list(CHAT_NODE_TYPE_IDS), _check_chat_node_fields)

    return reg


NODE_VALIDATOR_REGISTRY: dict[str, list] = _build_registry()
