"""Node validators — Chat/Conversation node types."""
from __future__ import annotations
from ...diagnostics.core import Checkability, Diagnostic, DiagnosticKind
from ...ast.workflow_ast import NodeAST
from ..diag_helper import diag_fe
from ..constants import (
    CHAT_NODE_TYPE_IDS, CREATE_CONVERSATION_NODE_TYPE_ID,
    UPDATE_CONVERSATION_NODE_TYPE_ID, DELETE_CONVERSATION_NODE_TYPE_ID,
    QUERY_CONVERSATION_HISTORY_NODE_TYPE_ID, CREATE_MESSAGE_NODE_TYPE_ID,
    UPDATE_MESSAGE_NODE_TYPE_ID, DELETE_MESSAGE_NODE_TYPE_ID,
    QUERY_MESSAGE_LIST_NODE_TYPE_ID, CLEAR_CONTEXT_NODE_TYPE_ID,
)

def _check_chat_node_fields(node, diagnostics: list[Diagnostic]) -> None:
    """FE-001: validate chat/conversation node required fields.

    Each chat node type has specific required parameters.
    """
    params_by_name = {p.name: p for p in node.parameters if p.name}

    # Helper to check if a required param exists and has a value
    def _require_param(param_name: str, node_label: str) -> None:
        if param_name not in params_by_name:
            diagnostics.append(diag_fe(
                'SEMANTIC-FE-001', 'violation',
                f'{node_label} requires "{param_name}" parameter',
                checkability=Checkability.OFFLINE,
                source_span=node.source_span,
            ))
        else:
            p = params_by_name[param_name]
            if not p.input_ref or not p.input_ref.name or not str(p.input_ref.name).strip():
                diagnostics.append(diag_fe(
                    'SEMANTIC-FE-001', 'violation',
                    f'{node_label} requires "{param_name}" value',
                    checkability=Checkability.OFFLINE,
                    source_span=node.source_span,
                ))

    nt = node.node_type
    label = f'Chat node "{node.title or node.node_id}"'

    if nt == CREATE_CONVERSATION_NODE_TYPE_ID:
        # create-conversation: first input required
        if not node.parameters:
            diagnostics.append(diag_fe(
                'SEMANTIC-FE-001', 'violation',
                f'{label} requires at least one input parameter',
                checkability=Checkability.OFFLINE,
                source_span=node.source_span,
            ))
    elif nt == UPDATE_CONVERSATION_NODE_TYPE_ID:
        _require_param('conversationName', label)
        _require_param('newConversationName', label)
    elif nt == DELETE_CONVERSATION_NODE_TYPE_ID:
        _require_param('conversationName', label)
    elif nt == QUERY_CONVERSATION_HISTORY_NODE_TYPE_ID:
        _require_param('conversationName', label)
    elif nt == CREATE_MESSAGE_NODE_TYPE_ID:
        _require_param('conversationName', label)
        _require_param('role', label)
        _require_param('content', label)
    elif nt == UPDATE_MESSAGE_NODE_TYPE_ID:
        _require_param('conversationName', label)
        _require_param('messageId', label)
        _require_param('newContent', label)
    elif nt == DELETE_MESSAGE_NODE_TYPE_ID:
        _require_param('conversationName', label)
        _require_param('messageId', label)
    elif nt == QUERY_MESSAGE_LIST_NODE_TYPE_ID:
        # query-message-list: first input required
        if not node.parameters:
            diagnostics.append(diag_fe(
                'SEMANTIC-FE-001', 'violation',
                f'{label} requires at least one input parameter',
                checkability=Checkability.OFFLINE,
                source_span=node.source_span,
            ))
    elif nt == CLEAR_CONTEXT_NODE_TYPE_ID:
        # clear-context: first input required
        if not node.parameters:
            diagnostics.append(diag_fe(
                'SEMANTIC-FE-001', 'violation',
                f'{label} requires at least one input parameter',
                checkability=Checkability.OFFLINE,
                source_span=node.source_span,
            ))
