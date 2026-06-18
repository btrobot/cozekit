"""Shared constants for all compiler passes.

Node type definitions are in cozekit.types (canonical leaf module).
This file re-exports them for backward compatibility and adds
validation-specific constants (limits, patterns, operators).
"""

from __future__ import annotations

import re

# Re-export everything from types.py for backward compatibility
from ..types import *  # noqa: F401,F403
from ..types import NodeType  # explicit for type checkers

# ── Validation rule constants ──────────────────────────────────
TITLE_MAX_LENGTH = 63
TEMPERATURE_MIN = 0.0
TEMPERATURE_MAX = 2.0
MAX_TOKENS_MIN = 1
QUERY_LIMIT_MIN = 1
QUERY_LIMIT_MAX = 1000

# ── Parameter name pattern ──────────────────────────────────────
PARAM_NAME_PATTERN = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')

# Allowed value types for variable declarations and block inputs
ALLOWED_VARIABLE_TYPES = frozenset({
    'string', 'integer', 'float', 'boolean', 'object', 'list',
})
ALLOWED_BLOCK_INPUT_VALUE_TYPES = frozenset({'literal', 'ref', 'object_ref'})
ALLOWED_REF_SOURCES = frozenset({
    'block-output', 'global_variable_app', 'global_variable_system', 'global_variable_user',
})


# Node types that require at least one inputParameter
REQUIRE_INPUT_PARAMS_NODE_TYPES = frozenset({
    END_NODE_TYPE_ID,
    OUTPUT_NODE_TYPE_ID,
    IMAGE_CANVAS_NODE_TYPE_ID,
})

# Node types that require first inputParameter to have a value
REQUIRE_FIRST_INPUT_NODE_TYPES = frozenset({
    INTENT_NODE_TYPE_ID,
    LTM_NODE_TYPE_ID,
    JSON_STRINGIFY_NODE_TYPE_ID,
})

# Output variable name validation (matches coze-studio outputTreeMetaValidator)
OUTPUT_NAME_PATTERN = re.compile(
    r'^(?!.*\b(true|false|and|AND|or|OR|not|NOT|null|nil|If|Switch)\b)'
    r'[a-zA-Z_][a-zA-Z_$0-9]*$'
)
OUTPUT_RESERVED_NAMES = frozenset({
    'true', 'false', 'and', 'AND', 'or', 'OR',
    'not', 'NOT', 'null', 'nil', 'If', 'Switch',
})

# Condition operator IDs (from coze-studio ConditionType enum)
CONDITION_OP_EQUAL = '1'
CONDITION_OP_NOT_EQUAL = '2'
CONDITION_OP_LENGTH_GT = '3'
CONDITION_OP_LENGTH_GT_EQUAL = '4'
CONDITION_OP_LENGTH_LT = '5'
CONDITION_OP_LENGTH_LT_EQUAL = '6'
CONDITION_OP_CONTAINS = '7'
CONDITION_OP_NOT_CONTAINS = '8'
CONDITION_OP_NULL = '9'
CONDITION_OP_NOT_NULL = '10'
CONDITION_OP_TRUE = '11'
CONDITION_OP_FALSE = '12'
CONDITION_OP_GT = '13'
CONDITION_OP_GT_EQUAL = '14'
CONDITION_OP_LT = '15'
CONDITION_OP_LT_EQUAL = '16'

# Unary operators where right operand is not required
UNARY_CONDITION_OPERATORS = frozenset({
    CONDITION_OP_NULL,
    CONDITION_OP_NOT_NULL,
    CONDITION_OP_TRUE,
    CONDITION_OP_FALSE,
})
