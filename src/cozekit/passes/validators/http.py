"""Node validators — HTTP node (type 45)."""
from __future__ import annotations

_HTTP_URL_MAX_LENGTH = 10000

from ...diagnostics.core import Checkability, Diagnostic, DiagnosticKind
from ...ast.workflow_ast import NodeAST
from ..diag_helper import diag_fe
from ..constants import HTTP_NODE_TYPE_ID

def _check_http_fields(node, diagnostics: list[Diagnostic]) -> None:
    """FE-001: validate HTTP node — URL is required, max length."""
    params_by_name = {p.name: p for p in node.node_specific_params if p.name}

    url_param = params_by_name.get('url')
    if url_param and url_param.input_ref:
        url_val = url_param.input_ref.name
        if not url_val or url_val.strip() == '':
            diagnostics.append(diag_fe(
                'SEMANTIC-FE-001', 'violation',
                'HTTP node requires URL',
                checkability=Checkability.OFFLINE,
                source_span=node.source_span,
            ))
        elif len(url_val) > _HTTP_URL_MAX_LENGTH:
            diagnostics.append(diag_fe(
                'SEMANTIC-FE-001', 'violation',
                f'HTTP node URL exceeds {_HTTP_URL_MAX_LENGTH} characters',
                checkability=Checkability.OFFLINE,
                source_span=node.source_span,
            ))
    elif not url_param:
        diagnostics.append(diag_fe(
            'SEMANTIC-FE-001', 'violation',
            'HTTP node requires URL',
            checkability=Checkability.OFFLINE,
            source_span=node.source_span,
        ))
    # VAL-HTTP-AUTH-001: auth field validation
    _check_http_auth(node, diagnostics)
    # VAL-HTTP-EXPR-STRING-001: expression string validation
    _check_http_expression_strings(node, diagnostics)


# Auth type → required field prefix in authData
_AUTH_TYPE_TO_FIELD: dict[str, str] = {
    'BASIC_AUTH': 'basicAuthData',
    'BEARER_AUTH': 'bearerTokenData',
    'CUSTOM_AUTH': 'customData',
}

def _check_http_auth(node, diagnostics: list[Diagnostic]) -> None:
    """VAL-HTTP-AUTH-001: when authOpen, auth fields for active type must be non-empty."""
    params_by_name = {p.name: p for p in node.node_specific_params if p.name}
    auth_open_param = params_by_name.get('_auth_open')
    if not auth_open_param:
        return
    auth_open_val = auth_open_param.input_ref.name if auth_open_param.input_ref else ''
    if auth_open_val.lower() not in ('true', '1'):
        return
    auth_type_param = params_by_name.get('_auth_type')
    auth_type = auth_type_param.input_ref.name if auth_type_param and auth_type_param.input_ref else ''
    if not auth_type:
        return
    field_prefix = _AUTH_TYPE_TO_FIELD.get(auth_type)
    if not field_prefix:
        return
    # Check that at least one auth data field has a value
    has_value = False
    for p in node.node_specific_params:
        if p.name and p.name.startswith(f'_auth_{field_prefix}_'):
            if p.input_ref and p.input_ref.name and p.input_ref.name.strip():
                has_value = True
                break
    if not has_value:
        diagnostics.append(diag_fe(
            'SEMANTIC-FE-001', 'violation',
            f'HTTP node auth is enabled ({auth_type}) but auth credentials are empty',
            checkability=Checkability.OFFLINE,
            source_span=node.source_span,
        ))

def _check_http_expression_strings(node, diagnostics: list[Diagnostic]) -> None:
    """VAL-HTTP-EXPR-STRING-001: check for malformed {{...}} expressions in URL."""
    import re
    params_by_name = {p.name: p for p in node.node_specific_params if p.name}
    url_param = params_by_name.get('url')
    if not url_param or not url_param.input_ref:
        return
    url_val = url_param.input_ref.name or ''
    # Check for unclosed {{ or }}
    opens = len(re.findall(r'\{\{', url_val))
    closes = len(re.findall(r'\}\}', url_val))
    if opens != closes:
        diagnostics.append(diag_fe(
            'SEMANTIC-FE-001', 'violation',
            'HTTP node URL contains malformed expression (unmatched {{ or }})',
            checkability=Checkability.OFFLINE,
            source_span=node.source_span,
        ))
        return
    # Check for empty expressions {{}}
    if re.search(r'\{\{\s*\}\}', url_val):
        diagnostics.append(diag_fe(
            'SEMANTIC-FE-001', 'violation',
            'HTTP node URL contains empty expression {{}}',
            checkability=Checkability.OFFLINE,
            source_span=node.source_span,
        ))

# ── Variable Assign nodes (types 20/40) ────────────────────
