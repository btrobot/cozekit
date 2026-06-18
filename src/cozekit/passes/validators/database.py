"""Node validators — Database node types."""
from __future__ import annotations
from ...diagnostics.core import Checkability, Diagnostic, DiagnosticKind
from ...ast.workflow_ast import NodeAST
from ..diag_helper import diag_fe
from ..constants import (
    DATABASE_NODE_TYPE_IDS, DATABASE_QUERY_NODE_TYPE_ID,
    QUERY_LIMIT_MIN, QUERY_LIMIT_MAX,
)

def _check_database_fields(node, diagnostics: list[Diagnostic]) -> None:
    """FE-001: validate Database node — sql required, databaseInfoList required,
    queryLimit range [1, 1000] for query nodes."""
    params_by_name = {p.name: p for p in node.node_specific_params if p.name}

    # sql is required
    sql_param = params_by_name.get('sql')
    if sql_param and sql_param.input_ref:
        sql_val = sql_param.input_ref.name
        if not sql_val or sql_val.strip() == '':
            diagnostics.append(diag_fe(
                'SEMANTIC-FE-001', 'violation',
                'Database node requires SQL statement',
                checkability=Checkability.OFFLINE,
                source_span=node.source_span,
            ))
    elif not sql_param:
        diagnostics.append(diag_fe(
            'SEMANTIC-FE-001', 'violation',
            'Database node requires SQL statement',
            checkability=Checkability.OFFLINE,
            source_span=node.source_span,
        ))

    # databaseInfoList is required (must select a database)
    db_info_param = params_by_name.get('databaseInfoList')
    if db_info_param and db_info_param.input_ref:
        db_info_val = db_info_param.input_ref.name
        # Empty list check: content is a list stored in name
        if db_info_val is not None:
            try:
                import ast as _ast
                val = _ast.literal_eval(db_info_val) if isinstance(db_info_val, str) else db_info_val
                if isinstance(val, list) and len(val) == 0:
                    diagnostics.append(diag_fe(
                        'SEMANTIC-FE-001', 'violation',
                        'Database node requires database selection',
                        checkability=Checkability.OFFLINE,
                        source_span=node.source_span,
                    ))
            except (ValueError, SyntaxError):
                pass
    elif not db_info_param:
        diagnostics.append(diag_fe(
            'SEMANTIC-FE-001', 'violation',
            'Database node requires database selection',
            checkability=Checkability.OFFLINE,
            source_span=node.source_span,
        ))

    # queryLimit range check (query node only)
    if node.node_type == DATABASE_QUERY_NODE_TYPE_ID:
        limit_param = params_by_name.get('queryLimit')
        if limit_param and limit_param.input_ref and limit_param.input_ref.ref_type == 'literal':
            try:
                limit_val = int(limit_param.input_ref.name) if limit_param.input_ref.name else None
                if limit_val is not None and (limit_val < QUERY_LIMIT_MIN or limit_val > QUERY_LIMIT_MAX):
                    diagnostics.append(diag_fe(
                        'SEMANTIC-FE-001', 'violation',
                        f'Database query limit must be between {QUERY_LIMIT_MIN} and {QUERY_LIMIT_MAX}',
                        checkability=Checkability.OFFLINE,
                        source_span=node.source_span,
                    ))
            except (ValueError, TypeError):
                pass

# ── HTTP node (type 45) ────────────────────────────────────

_HTTP_URL_MAX_LENGTH = 10000
