"""I/O validators — output names, input tree, exception JSON, global array.

TODO: consider splitting FE/BE rules into separate files if this grows beyond 300 lines.

These functions validate I/O structure: output variable names,
input parameter trees, exception JSON format, and global array types.
"""
from __future__ import annotations

import re

from ..diagnostics.core import Checkability, Diagnostic
from .context import PassContext
from .diag_helper import make_diag
from .constants import (
    START_NODE_TYPE_ID,
    END_NODE_TYPE_ID,
    OUTPUT_NAME_PATTERN,
    OUTPUT_RESERVED_NAMES,
)


# _diag_fe is now imported from diag_helper (W1 refactor)
from .diag_helper import diag_fe as _diag_fe

# ── Type mapping for default value validation ──
_VAR_TYPE_TO_JSON_TYPE: dict[str, str | tuple[str, ...]] = {
    'string': 'str',
    'integer': ('int', 'float'),
    'number': ('int', 'float'),
    'float': ('int', 'float'),
    'boolean': 'bool',
    'object': 'dict',
    'list': 'list',
    'time': 'str',
}



def check_output_names(ctx: PassContext, diagnostics: list[Diagnostic]) -> None:
    """FE-013: output variable name validation."""
    for canvas in ctx.sema.canvases():
        for node in canvas.nodes:
            if not node.outputs:
                continue
            validate_output_tree(node.outputs, diagnostics, node)

def validate_output_tree(outputs, diagnostics, node):
    """Recursively validate output variable names, types, and uniqueness."""
    seen_names: set[str] = set()
    for out in outputs:
        name = out.name
        if isinstance(name, bool):
            # YAML true/false → Python True/False; treat as reserved
            diagnostics.append(_diag_fe(
                'SEMANTIC-FE-013', 'violation',
                f'output variable name "{str(name).lower()}" is a reserved word',
                checkability=Checkability.OFFLINE,
                source_span=node.source_span,
            ))
            if out.children:
                validate_output_tree(out.children, diagnostics, node)
            continue
        if not isinstance(name, str):
            name = str(name) if name is not None else ''
        if not name or not name.strip():
            diagnostics.append(_diag_fe(
                'SEMANTIC-FE-013', 'violation',
                'output variable name is required',
                checkability=Checkability.OFFLINE,
                source_span=node.source_span,
            ))
        elif name in OUTPUT_RESERVED_NAMES:
            diagnostics.append(_diag_fe(
                'SEMANTIC-FE-013', 'violation',
                f'output variable name "{out.name}" is a reserved word',
                checkability=Checkability.OFFLINE,
                source_span=node.source_span,
            ))
        elif not OUTPUT_NAME_PATTERN.match(name):
            diagnostics.append(_diag_fe(
                'SEMANTIC-FE-013', 'violation',
                f'output variable name "{out.name}" has invalid format',
                checkability=Checkability.OFFLINE,
                source_span=node.source_span,
            ))
        # SPEC-OUT-006: sibling names must be unique
        if name and name.strip() and name in seen_names:
            diagnostics.append(_diag_fe(
                'SEMANTIC-FE-013', 'violation',
                f'duplicate output variable name "{name}" among siblings',
                checkability=Checkability.OFFLINE,
                source_span=node.source_span,
            ))
        elif name and name.strip():
            seen_names.add(name)
        # Type required (§4.4.2)
        if not out.var_type:
            diagnostics.append(_diag_fe(
                'SEMANTIC-FE-013', 'violation',
                f'output variable "{name or "(unnamed)"}" is missing required "type" field',
                checkability=Checkability.OFFLINE,
                source_span=node.source_span,
            ))
        # VAL-JSON-SCHEMA-001: defaultValue must match declared type
        if out.default_value and isinstance(out.default_value, str) and out.default_value.strip():
            check_default_value_schema(out, diagnostics, node)
        if out.children:
            validate_output_tree(out.children, diagnostics, node)

# (module-level _VAR_TYPE_TO_JSON_TYPE is used below)

def check_default_value_schema(out, diagnostics: list[Diagnostic], node,
    ) -> None:
    """VAL-JSON-SCHEMA-001: validate defaultValue against declared type.

    Per SPEC-OUT-007, JSON validity and type compatibility are checked for
    JSON/object/list types.  For string/time types, plain string default
    values like "Default" are accepted without JSON parsing.  For typed
    scalars (integer, number, float, boolean), defaultValue must be valid
    JSON matching the declared type.
    """
    import json
    dv = out.default_value
    if not dv or not isinstance(dv, str) or not dv.strip():
        return

    vtype = out.var_type
    if not vtype:
        return

    vtype_lower = vtype.lower()

    # String/time types accept plain string defaultValues (e.g. "Default")
    # without JSON parsing — per coze-studio real data conventions.
    if vtype_lower in ('string', 'time'):
        return

    # JSON/object/list and typed scalars require valid JSON defaultValue
    try:
        parsed = json.loads(dv)
    except (json.JSONDecodeError, ValueError):
        diagnostics.append(_diag_fe(
            'SEMANTIC-FE-013', 'violation',
            f'output variable "{out.name}" defaultValue is not valid JSON',
            checkability=Checkability.OFFLINE,
            source_span=node.source_span,
        ))
        return

    # Check type compatibility
    expected = _VAR_TYPE_TO_JSON_TYPE.get(vtype_lower)
    if not expected:
        return
    json_type = type(parsed).__name__
    if isinstance(expected, tuple):
        if json_type not in expected:
            diagnostics.append(_diag_fe(
                'SEMANTIC-FE-013', 'violation',
                f'output variable "{out.name}" defaultValue type "{json_type}" '
                f'does not match declared type "{vtype}" (expected {"/".join(expected)})',
                checkability=Checkability.OFFLINE,
                source_span=node.source_span,
            ))
    else:
        if json_type != expected:
            diagnostics.append(_diag_fe(
                'SEMANTIC-FE-013', 'violation',
                f'output variable "{out.name}" defaultValue type "{json_type}" '
                f'does not match declared type "{vtype}" (expected {expected})',
                checkability=Checkability.OFFLINE,
                source_span=node.source_span,
            ))

def check_input_tree(ctx: PassContext, diagnostics: list[Diagnostic]) -> None:
    """FE-014: generic input parameter validation for all nodes.

    Validates (matches coze-studio inputTreeValidator):
    - Name is non-empty
    - Name format matches identifier pattern
    - Value is non-empty (input_ref required)
    - Sibling names are unique

    Also validates variable_parameters for loop nodes.
    """
    # Nodes that don't have regular input parameters
    _SKIP_TYPES = frozenset({
        START_NODE_TYPE_ID,  # Start has no inputs
    })

    for canvas in ctx.sema.canvases():
        for node in canvas.nodes:
            if node.node_type in _SKIP_TYPES:
                continue
            # Validate regular parameters
            all_params = list(node.parameters)
            # Also include variable_parameters for loop nodes
            if node.variable_parameters:
                all_params.extend(node.variable_parameters)
            if not all_params:
                continue
            seen_names: set[str] = set()
            for param in all_params:
                pname = param.name
                # Name non-empty
                if not pname or not pname.strip():
                    diagnostics.append(_diag_fe(
                        'SEMANTIC-FE-014', 'violation',
                        f'input parameter name is required on node "{node.title or node.node_id}"',
                        checkability=Checkability.OFFLINE,
                        source_span=node.source_span,
                    ))
                    continue
                # Name format (same regex as output names per coze-studio VARIABLE_NAME_REGEX)
                if not OUTPUT_NAME_PATTERN.match(pname):
                    diagnostics.append(_diag_fe(
                        'SEMANTIC-FE-014', 'violation',
                        f'input parameter name "{pname}" has invalid format on node "{node.title or node.node_id}"',
                        checkability=Checkability.OFFLINE,
                        source_span=node.source_span,
                    ))
                # Sibling name uniqueness
                if pname in seen_names:
                    diagnostics.append(_diag_fe(
                        'SEMANTIC-FE-014', 'violation',
                        f'duplicate input parameter name "{pname}" on node "{node.title or node.node_id}"',
                        checkability=Checkability.OFFLINE,
                        source_span=node.source_span,
                    ))
                else:
                    seen_names.add(pname)
                # Value non-empty (input_ref must exist and have content)
                # For ref types: name or path must be present
                # For literal types: name must be present (stored in name field)
                # Skip for parameters with left_ref (VariableAssign uses left/right)
                if not param.left_ref:
                    has_value = False
                    if param.input_ref:
                        if param.input_ref.ref_type == 'ref' and (param.input_ref.name or param.input_ref.path):
                            has_value = True
                        elif param.input_ref.ref_type and param.input_ref.name:
                            has_value = True
                    if not has_value:
                        diagnostics.append(_diag_fe(
                            'SEMANTIC-FE-014', 'violation',
                            f'input parameter "{pname}" requires a value on node "{node.title or node.node_id}"',
                            checkability=Checkability.OFFLINE,
                            source_span=node.source_span,
                        ))

    # FE-012: Exception JSON parseability
def check_exception_json(ctx: PassContext, diagnostics: list[Diagnostic]) -> None:
    """FE-012: setting-on-error RETURN JSON must be parseable."""
    import json
    for canvas in ctx.sema.canvases():
        for node in canvas.nodes:
            if node.on_error_config:
                return_json = node.on_error_config.get('returnJson')
                if return_json and isinstance(return_json, str):
                    try:
                        json.loads(return_json)
                    except json.JSONDecodeError:
                        diagnostics.append(_diag_fe(
                            'SEMANTIC-FE-012', 'violation',
                            'setting-on-error RETURN JSON is not parseable',
                            checkability=Checkability.OFFLINE,
                            source_span=node.source_span,
                        ))

# BE-021: Global array element type matching
def check_global_array_element_type(ctx: PassContext, diagnostics: list[Diagnostic]) -> None:
    """BE-021: global list variable element type must match metadata."""
    for canvas in ctx.sema.canvases():
        for node in canvas.nodes:
            if node.global_var_type in ('list', 'array') and node.global_var_item_type:
                # Check assignments to this variable
                for other_node in canvas.nodes:
                    for idx, param in enumerate(other_node.parameters):
                        resolved = ctx.sema.resolved_ref_for(other_node.node_id, idx)
                        if resolved and resolved.is_global and resolved.name == node.global_var_name:
                            # For now, just check that item type is specified
                            # Full type checking would need type system extension
                            pass
