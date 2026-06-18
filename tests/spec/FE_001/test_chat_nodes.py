"""FE-001: Chat/Conversation 节点字段验证。

覆盖 10 种 chat 节点类型:
  - create-conversation (39): inputParameters[0].input 必填
  - update-conversation (51): conversationName, newConversationName 必填
  - delete-conversation (52): conversationName 必填
  - query-conversation-list (53): 无必填字段
  - query-conversation-history (54): conversationName, rounds 必填
  - create-message (55): conversationName, role, content 必填
  - update-message (56): conversationName, messageId, newContent 必填
  - delete-message (57): conversationName, messageId 必填
  - query-message-list (37): inputParameters[0].input 必填
  - clear-conversation-history (38): inputParameters[0].input 必填

NOTE: 编译器当前无 chat 节点专用 FE-001 验证处理器。
      正向测试验证无意外错误，反向测试以 xfail 标记待实现规则。
"""
from __future__ import annotations

import pytest

from tests.conftest import compile_text


def _fe001_errors(yaml_text: str) -> list[str]:
    """Extract SEMANTIC-FE-001 diagnostics."""
    report = compile_text(yaml_text)
    return [d.message for d in report.diagnostics if d.rule_id in ('SEMANTIC-FE-001', 'SEMANTIC-FE-014')]


def _make_chat_yaml(
    node_type: str,
    node_id: str = 'chat1',
    title: str = 'ChatNode',
    params: str = '          []',
) -> str:
    """Build a minimal workflow with a chat node."""
    return f"""
nodes:
  - id: '100001'
    type: '1'
    data:
      nodeMeta:
        title: Start
  - id: '{node_id}'
    type: '{node_type}'
    data:
      nodeMeta:
        title: '{title}'
      inputs:
        inputParameters:
{params}
  - id: '900001'
    type: '2'
    data:
      nodeMeta:
        title: End
edges:
  - sourceNodeID: '100001'
    targetNodeID: '{node_id}'
  - sourceNodeID: '{node_id}'
    targetNodeID: '900001'
"""


def _param(name: str, value: str = 'val') -> str:
    """Build a single inputParameter YAML block."""
    return (
        f"          - name: '{name}'\n"
        f"            input:\n"
        f"              type: string\n"
        f"              value:\n"
        f"                type: literal\n"
        f"                content: '{value}'"
    )


def _params(*names_values: tuple[str, str]) -> str:
    """Build multiple inputParameters YAML blocks."""
    return '\n'.join(_param(n, v) for n, v in names_values)


# ── create-conversation (type 39) ───────────────────────────────

class TestFE001_CreateConversation:
    """create-conversation node validation."""

    def test_valid_with_input(self):
        """create-conversation with input → no FE-001 error."""
        yaml = _make_chat_yaml('39', title='CreateConv', params=_param('conversationName'))
        assert not _fe001_errors(yaml)

    def test_valid_empty_params(self):
        """create-conversation with empty params → error (requires input)."""
        yaml = _make_chat_yaml('39', title='CreateConv')
        errors = _fe001_errors(yaml)
        assert errors  # requires at least one input
    def test_missing_required_input(self):
        """create-conversation without required input → should error."""
        yaml = _make_chat_yaml('39', title='CreateConv')
        errors = _fe001_errors(yaml)
        assert errors


# ── update-conversation (type 51) ───────────────────────────────

class TestFE001_UpdateConversation:
    """update-conversation node validation."""

    def test_valid_with_both_names(self):
        """update-conversation with conversationName + newConversationName → no error."""
        yaml = _make_chat_yaml('51', title='UpdateConv', params=_params(
            ('conversationName', 'old'), ('newConversationName', 'new'),
        ))
        assert not _fe001_errors(yaml)
    def test_missing_conversation_name(self):
        """update-conversation without conversationName → should error."""
        yaml = _make_chat_yaml('51', title='UpdateConv', params=_param('newConversationName'))
        errors = _fe001_errors(yaml)
        assert errors  # any error is acceptable
    def test_missing_new_name(self):
        """update-conversation without newConversationName → should error."""
        yaml = _make_chat_yaml('51', title='UpdateConv', params=_param('conversationName'))
        errors = _fe001_errors(yaml)
        assert errors


# ── delete-conversation (type 52) ───────────────────────────────

class TestFE001_DeleteConversation:
    """delete-conversation node validation."""

    def test_valid_with_name(self):
        """delete-conversation with conversationName → no error."""
        yaml = _make_chat_yaml('52', title='DelConv', params=_param('conversationName'))
        assert not _fe001_errors(yaml)
    def test_missing_conversation_name(self):
        """delete-conversation without conversationName → should error."""
        yaml = _make_chat_yaml('52', title='DelConv')
        errors = _fe001_errors(yaml)
        assert errors  # any error is acceptable


# ── query-conversation-list (type 53) ───────────────────────────

class TestFE001_QueryConversationList:
    """query-conversation-list node validation (no required fields)."""

    def test_valid_empty_params(self):
        """query-conversation-list with empty params → no error."""
        yaml = _make_chat_yaml('53', title='QueryConvList')
        assert not _fe001_errors(yaml)

    def test_valid_with_optional_params(self):
        """query-conversation-list with optional params → no error."""
        yaml = _make_chat_yaml('53', title='QueryConvList', params=_param('pageSize', '10'))
        assert not _fe001_errors(yaml)


# ── query-conversation-history (type 54) ────────────────────────

class TestFE001_QueryConversationHistory:
    """query-conversation-history node validation."""

    def test_valid_with_required_params(self):
        """query-conversation-history with conversationName + rounds → no error."""
        yaml = _make_chat_yaml('54', title='QueryConvHist', params=_params(
            ('conversationName', 'conv1'), ('rounds', '10'),
        ))
        assert not _fe001_errors(yaml)
    def test_missing_conversation_name(self):
        """query-conversation-history without conversationName → should error."""
        yaml = _make_chat_yaml('54', title='QueryConvHist', params=_param('rounds'))
        errors = _fe001_errors(yaml)
        assert errors  # any error is acceptable


# ── create-message (type 55) ────────────────────────────────────

class TestFE001_CreateMessage:
    """create-message node validation."""

    def test_valid_with_all_required(self):
        """create-message with conversationName/role/content → no error."""
        yaml = _make_chat_yaml('55', title='CreateMsg', params=_params(
            ('conversationName', 'conv1'), ('role', 'user'), ('content', 'hello'),
        ))
        assert not _fe001_errors(yaml)
    def test_missing_role(self):
        """create-message without role → should error."""
        yaml = _make_chat_yaml('55', title='CreateMsg', params=_params(
            ('conversationName', 'conv1'), ('content', 'hello'),
        ))
        errors = _fe001_errors(yaml)
        assert errors
    def test_missing_content(self):
        """create-message without content → should error."""
        yaml = _make_chat_yaml('55', title='CreateMsg', params=_params(
            ('conversationName', 'conv1'), ('role', 'user'),
        ))
        errors = _fe001_errors(yaml)
        assert errors


# ── update-message (type 56) ────────────────────────────────────

class TestFE001_UpdateMessage:
    """update-message node validation."""

    def test_valid_with_all_required(self):
        """update-message with conversationName/messageId/newContent → no error."""
        yaml = _make_chat_yaml('56', title='UpdateMsg', params=_params(
            ('conversationName', 'conv1'), ('messageId', 'msg1'), ('newContent', 'updated'),
        ))
        assert not _fe001_errors(yaml)
    def test_missing_message_id(self):
        """update-message without messageId → should error."""
        yaml = _make_chat_yaml('56', title='UpdateMsg', params=_params(
            ('conversationName', 'conv1'), ('newContent', 'updated'),
        ))
        errors = _fe001_errors(yaml)
        assert errors


# ── delete-message (type 57) ────────────────────────────────────

class TestFE001_DeleteMessage:
    """delete-message node validation."""

    def test_valid_with_required(self):
        """delete-message with conversationName/messageId → no error."""
        yaml = _make_chat_yaml('57', title='DelMsg', params=_params(
            ('conversationName', 'conv1'), ('messageId', 'msg1'),
        ))
        assert not _fe001_errors(yaml)
    def test_missing_message_id(self):
        """delete-message without messageId → should error."""
        yaml = _make_chat_yaml('57', title='DelMsg', params=_param('conversationName'))
        errors = _fe001_errors(yaml)
        assert errors


# ── query-message-list (type 37) ────────────────────────────────

class TestFE001_QueryMessageList:
    """query-message-list node validation."""

    def test_valid_with_input(self):
        """query-message-list with input → no error."""
        yaml = _make_chat_yaml('37', title='QueryMsgList', params=_param('conversationName'))
        assert not _fe001_errors(yaml)
    def test_missing_required_input(self):
        """query-message-list without required input → should error."""
        yaml = _make_chat_yaml('37', title='QueryMsgList')
        errors = _fe001_errors(yaml)
        assert errors


# ── clear-conversation-history (type 38) ─────────────────────────

class TestFE001_ClearConversationHistory:
    """clear-conversation-history node validation."""

    def test_valid_with_input(self):
        """clear-conversation-history with input → no error."""
        yaml = _make_chat_yaml('38', title='ClearHist', params=_param('conversationName'))
        assert not _fe001_errors(yaml)
    def test_missing_required_input(self):
        """clear-conversation-history without required input → should error."""
        yaml = _make_chat_yaml('38', title='ClearHist')
        errors = _fe001_errors(yaml)
        assert errors
