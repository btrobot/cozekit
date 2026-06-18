"""AST builder — converts parsed document into WorkflowAST.

Handles nested canvases (composite nodes like loops, ifs, batches)
that contain `blocks` and `edges` inside their `data` or at node level.
"""

from __future__ import annotations

from typing import Any

from ..diagnostics.core import SourceSpan
from ..types import (
    LLM_NODE_TYPE_ID, QUESTION_NODE_TYPE_ID, VARIABLE_NODE_TYPE_ID, CODE_NODE_TYPE_ID,
    IF_NODE_TYPE_ID, LOOP_NODE_TYPE_ID, BATCH_NODE_TYPE_ID,
    HTTP_NODE_TYPE_ID, SET_VARIABLE_NODE_TYPE_ID, VARIABLE_ASSIGN_NODE_TYPE_ID,
    DATABASE_NODE_TYPE_IDS, DATABASE_QUERY_NODE_TYPE_ID,
    INTENT_NODE_TYPE_ID, IMAGE_GENERATE_NODE_TYPE_ID,
    LTM_NODE_TYPE_ID, DATASET_SEARCH_NODE_TYPE_ID, DATASET_WRITE_NODE_TYPE_ID,
    TEXT_PROCESS_NODE_TYPE_ID,
    VARIABLE_MERGE_NODE_TYPE_ID,
)
from ..transport.input_source import ParsedDocument
from ..transport.span_map import SpanMap
from .workflow_ast import (
    BranchAST,
    CanvasAST,
    ConditionAST,
    ConditionBranchAST,
    EdgeAST,
    NodeAST,
    ParameterAST,
    RefAST,
    SourceProvenance,
    WorkflowAST,
)

# Note: _COMPOSITE_TYPES is now defined using constants from constants.py
_COMPOSITE_TYPES = {
    IF_NODE_TYPE_ID: 'if',
    LOOP_NODE_TYPE_ID: 'loop',
    BATCH_NODE_TYPE_ID: 'batch',
}


class ASTBuilder:
    """Build WorkflowAST from a transport-normalized ParsedDocument."""

    def build(self, document: ParsedDocument) -> WorkflowAST:
        raw = document.raw_document
        source_file = document.source_file
        provenance = SourceProvenance(source_file=source_file)
        span_map = document.span_map

        if not isinstance(raw, dict):
            return WorkflowAST(provenance=provenance)

        root_canvas = self._build_canvas(
            raw, source_file, canvas_path=(), span_map=span_map,
        )
        all_canvases = [root_canvas] + self._collect_subcanvases(root_canvas)
        return WorkflowAST(
            root_canvas=root_canvas,
            canvases=tuple(all_canvases),
            provenance=provenance,
        )

    def _build_canvas(
        self,
        raw: dict,
        source_file: str | None,
        canvas_path: tuple[str | int, ...],
        span_map: SpanMap | None = None,
    ) -> CanvasAST:
        nodes, non_object_count = self._extract_nodes(
            raw, source_file, canvas_path, span_map=span_map,
        )
        edges = self._extract_edges(
            raw, source_file, canvas_path, span_map=span_map,
        )
        parameters = self._extract_top_level_parameters(raw, source_file)
        return CanvasAST(
            nodes=tuple(nodes),
            edges=tuple(edges),
            parameters=tuple(parameters),
            canvas_path=canvas_path,
            provenance=SourceProvenance(source_file=source_file),
            non_object_node_count=non_object_count,
        )

    def _collect_subcanvases(self, canvas: CanvasAST) -> list[CanvasAST]:
        """Recursively collect subcanvases from composite nodes."""
        result = []
        for node in canvas.nodes:
            if node.blocks:
                sub_path = node.canvas_path + (node.node_id,)
                sub_canvas = CanvasAST(
                    canvas_id=node.node_id,
                    nodes=node.blocks,
                    edges=node.nested_edges,  # already typed EdgeAST
                    canvas_path=sub_path,
                    provenance=node.provenance,
                )
                result.append(sub_canvas)
                result.extend(self._collect_subcanvases(sub_canvas))
        return result

    def _extract_nodes(
        self,
        raw: dict,
        source_file: str | None,
        canvas_path: tuple[str | int, ...],
        span_map: SpanMap | None = None,
    ) -> tuple[list[NodeAST], int]:
        nodes_raw = raw.get('nodes', [])
        if not isinstance(nodes_raw, list):
            return [], 0
        result = []
        non_object_count = 0
        for i, n in enumerate(nodes_raw):
            if not isinstance(n, dict):
                non_object_count += 1
                continue
            try:
                result.append(self._extract_single_node(
                    n, source_file, canvas_path,
                    span_map=span_map, yaml_prefix=('nodes', str(i)),
                ))
            except Exception:
                # Skip malformed node, continue with remaining nodes
                non_object_count += 1
        return result, non_object_count

    def _extract_single_node(
        self,
        n: dict,
        source_file: str | None,
        canvas_path: tuple[str | int, ...],
        span_map: SpanMap | None = None,
        yaml_prefix: tuple[str, ...] = (),
    ) -> NodeAST:
        """Extract a single node dict into a fully-typed NodeAST."""
        node_id = str(n.get('id', ''))
        node_type = str(n.get('type', ''))
        data = n.get('data', {}) if isinstance(n.get('data'), dict) else {}
        meta = data.get('nodeMeta', {}) if isinstance(data, dict) else {}
        title = meta.get('title') if isinstance(meta, dict) else None

        # Look up source span for this node mapping
        source_span = span_map.lookup_path(yaml_prefix) if span_map and yaml_prefix else None

        # Extract input parameters from data.inputs.inputParameters
        inputs_obj = data.get('inputs', {}) if isinstance(data, dict) else {}
        inputs_obj = inputs_obj if isinstance(inputs_obj, dict) else {}
        input_params_raw = inputs_obj.get('inputParameters', [])
        var_params_raw = inputs_obj.get('variableParameters', [])
        branches_raw = inputs_obj.get('branches', [])

        # Extract node-specific parameters (e.g., llmParam for LLM nodes)
        node_specific_params_raw = self._extract_node_specific_params_raw(
            node_type, inputs_obj, data,
        )

        params = self._extract_parameters(
            input_params_raw if isinstance(input_params_raw, list) else [],
            source_file,
        )
        var_params = self._extract_parameters(
            var_params_raw if isinstance(var_params_raw, list) else [],
            source_file,
        )
        branches = self._extract_branches(
            branches_raw if isinstance(branches_raw, list) else [],
            source_file,
        )
        node_specific_params = self._extract_parameters(
            node_specific_params_raw,
            source_file,
        )

        # Extract blocks as typed NodeAST objects
        blocks_raw, _ = self._get_blocks_raw(n, data)
        sub_path = canvas_path + (node_id,)
        blocks = tuple(
            self._extract_single_node(
                b, source_file, sub_path,
                span_map=span_map,
                yaml_prefix=self._lookup_block_yaml_prefix(
                    span_map, yaml_prefix, i,
                ),
            )
            for i, b in enumerate(blocks_raw) if isinstance(b, dict)
        )

        # Extract nested edges as typed EdgeAST objects
        _, edges_raw = self._get_blocks_raw(n, data)
        nested_edges = tuple(
            EdgeAST(
                source_node_id=str(e.get('sourceNodeID', '')),
                target_node_id=str(e.get('targetNodeID', '')),
                source_port_id=e.get('sourcePortID'),
                target_port_id=e.get('targetPortID'),
                canvas_path=sub_path,
                provenance=SourceProvenance(source_file=source_file),
                source_span=self._lookup_nested_edge_span(
                    span_map, yaml_prefix, i,
                ),
            )
            for i, e in enumerate(edges_raw) if isinstance(e, dict)
        )

        composite_kind = _COMPOSITE_TYPES.get(node_type)
        raw_blocks = n.get('blocks') or (data.get('blocks') if isinstance(data, dict) else None)
        has_blocks = bool(raw_blocks) and len(raw_blocks) > 0

        # Extract global var info for Variable nodes
        global_var_name = None
        global_var_type = None
        global_var_schema = None
        global_var_item_type = None
        on_error_config = None
        if node_type == VARIABLE_NODE_TYPE_ID:
            inputs_obj_gv = data.get('inputs', {}) if isinstance(data, dict) else {}
            inputs_obj_gv = inputs_obj_gv if isinstance(inputs_obj_gv, dict) else {}
            global_var_name = inputs_obj_gv.get('name') or inputs_obj_gv.get('variableName')
            global_var_type = inputs_obj_gv.get('type') or inputs_obj_gv.get('variableType')
            global_var_name = str(global_var_name) if global_var_name is not None else None
            global_var_type = str(global_var_type) if global_var_type is not None else None
            global_var_schema = inputs_obj_gv.get('schema') if isinstance(inputs_obj_gv.get('schema'), dict) else None
            global_var_item_type = None
            if global_var_schema and global_var_type in ('list', 'array'):
                global_var_item_type = global_var_schema.get('type')

        # Extract on_error_config for all nodes
        if isinstance(data, dict):
            on_error_config = data.get('onError')

        outputs = self._extract_outputs(data, source_file)

        return NodeAST(
            node_id=node_id,
            node_type=node_type,
            title=title if isinstance(title, str) else None,
            parameters=tuple(params),
            variable_parameters=tuple(var_params),
            node_specific_params=tuple(node_specific_params),
            branches=tuple(branches),
            blocks=blocks,
            nested_edges=nested_edges,
            has_blocks_key=has_blocks,
            composite_kind=composite_kind,
            _has_shape_issue=has_blocks and composite_kind is None,
            has_data='data' in n,
            is_valid_object=isinstance(n, dict),
            global_var_name=global_var_name,
            global_var_type=global_var_type,
            global_var_schema=global_var_schema,
            global_var_item_type=global_var_item_type,
            on_error_config=on_error_config,
            outputs=outputs,
            canvas_path=canvas_path,
            provenance=SourceProvenance(source_file=source_file),
            source_span=source_span,
        )

    @staticmethod
    def _extract_node_specific_params_raw(
        node_type: str,
        inputs_obj: dict,
        data: dict,
    ) -> list:
        """Extract node-specific parameters based on node type.

        Returns raw parameter dicts for the given node type.
        Normalizes heterogeneous structures into a uniform list of
        {name, input: {type, value: {type, content}}} dicts so that
        the semantic pass can use a uniform params_by_name pattern.
        """
        # ── LLM nodes (type 3): extract llmParam ──────────────
        if node_type == LLM_NODE_TYPE_ID:
            llm_params = inputs_obj.get('llmParam', [])
            return llm_params if isinstance(llm_params, list) else []

        # ── Code nodes (type 5): extract codeParam ────────────
        if node_type == CODE_NODE_TYPE_ID:
            code_params = inputs_obj.get('codeParam', [])
            if isinstance(code_params, list) and code_params:
                return code_params
            # Fallback: code might be stored directly (YAML source format)
            code_val = inputs_obj.get('code', '')
            # Handle already-structured value from YAML converter
            if isinstance(code_val, dict) and 'content' in code_val:
                return [{'name': 'code', 'input': {'type': 'string', 'value': code_val}}]
            return [{'name': 'code', 'input': {'type': 'string', 'value': {'type': 'literal', 'content': code_val or ''}}}]

        # ── Question nodes (type 18): extract questionParams ──
        if node_type == QUESTION_NODE_TYPE_ID:
            q_params = inputs_obj.get('questionParams', {})
            if isinstance(q_params, dict):
                return _dict_to_param_list(q_params)
            return []

        # ── HTTP nodes (type 45): extract url ─────────────────
        if node_type == HTTP_NODE_TYPE_ID:
            result = []
            api_info = inputs_obj.get('apiInfo', {})
            if isinstance(api_info, dict):
                url = api_info.get('url', '')
                result.append({
                    'name': 'url',
                    'input': {'type': 'string', 'value': {'type': 'literal', 'content': url or ''}},
                })
            # Extract auth info for VAL-HTTP-AUTH-001
            auth = inputs_obj.get('auth', {})
            if isinstance(auth, dict):
                auth_open = auth.get('authOpen', False)
                auth_type = auth.get('authType', '')
                result.append({
                    'name': '_auth_open',
                    'input': {'type': 'boolean', 'value': {'type': 'literal', 'content': str(auth_open)}},
                })
                result.append({
                    'name': '_auth_type',
                    'input': {'type': 'string', 'value': {'type': 'literal', 'content': str(auth_type)}},
                })
                # Extract auth data fields
                auth_data = auth.get('authData', {})
                if isinstance(auth_data, dict):
                    for auth_field in ('basicAuthData', 'bearerTokenData', 'customData'):
                        field_data = auth_data.get(auth_field, {})
                        if isinstance(field_data, list):
                            for item in field_data:
                                if isinstance(item, dict):
                                    name = item.get('name', '')
                                    inp = item.get('input', {})
                                    if isinstance(inp, dict):
                                        raw_val = inp.get('value', {})
                                    else:
                                        raw_val = inp
                                    if isinstance(raw_val, dict):
                                        val = raw_val.get('content', '')
                                    else:
                                        val = raw_val if raw_val else ''
                                    result.append({
                                        'name': f'_auth_{auth_field}_{name}',
                                        'input': {'type': 'string', 'value': {'type': 'literal', 'content': str(val) if val else ''}},
                                    })
            return result

        # ── Variable Assign nodes (types 20, 40) ──────────────
        if node_type in (SET_VARIABLE_NODE_TYPE_ID, VARIABLE_ASSIGN_NODE_TYPE_ID):
            # These use inputParameters with left/right structure
            # Already extracted into node.parameters by the main extraction.
            # Return empty here; validation checks node.parameters directly.
            return []

        # ── Database nodes (types 12, 42, 43, 44, 46) ────────
        if node_type in DATABASE_NODE_TYPE_IDS:
            result = []
            sql = inputs_obj.get('sql', '')
            result.append({
                'name': 'sql',
                'input': {'type': 'string', 'value': {'type': 'literal', 'content': sql or ''}},
            })
            db_info_list = inputs_obj.get('databaseInfoList', [])
            result.append({
                'name': 'databaseInfoList',
                'input': {'type': 'list', 'value': {'type': 'literal', 'content': db_info_list}},
            })
            # Query node has selectParam.limit
            if node_type == DATABASE_QUERY_NODE_TYPE_ID:
                select_param = inputs_obj.get('selectParam', {})
                if isinstance(select_param, dict):
                    limit_val = select_param.get('limit', '')
                    result.append({
                        'name': 'queryLimit',
                        'input': {'type': 'integer', 'value': {'type': 'literal', 'content': str(limit_val) if limit_val != '' else ''}},
                    })
            return result

        # ── Intent nodes (type 22) ────────────────────────────
        if node_type == INTENT_NODE_TYPE_ID:
            # First input must be present — checked via node.parameters
            return []

        # ── Image Generate nodes (type 16) ────────────────────
        if node_type == IMAGE_GENERATE_NODE_TYPE_ID:
            result = []
            model_setting = inputs_obj.get('modelSetting', {})
            if isinstance(model_setting, dict):
                model = model_setting.get('model', '')
                result.append({
                    'name': 'model',
                    'input': {'type': 'string', 'value': {'type': 'literal', 'content': str(model) if model else ''}},
                })
            return result

        # ── LTM nodes (type 26) ───────────────────────────────
        if node_type == LTM_NODE_TYPE_ID:
            # First input must be present — checked via node.parameters
            return []

        # ── Dataset nodes (types 6, 27) ───────────────────────
        if node_type in (DATASET_SEARCH_NODE_TYPE_ID, DATASET_WRITE_NODE_TYPE_ID):
            result = []
            # Knowledge base selection
            knowledge = inputs_obj.get('knowledge', '')
            if not knowledge:
                # Also check inputParameters for knowledge
                inp_params = inputs_obj.get('inputParameters', [])
                if isinstance(inp_params, list):
                    for p in inp_params:
                        if isinstance(p, dict) and p.get('name') == 'knowledge':
                            knowledge = p.get('input', {}).get('value', {}).get('content', '') if isinstance(p.get('input'), dict) else ''
                            break
            result.append({
                'name': 'knowledge',
                'input': {'type': 'string', 'value': {'type': 'literal', 'content': knowledge or ''}},
            })
            return result

        # ── Text Process nodes (type 15) ──────────────────────
        if node_type == TEXT_PROCESS_NODE_TYPE_ID:
            result = []
            method = inputs_obj.get('method', '')
            if isinstance(method, dict) and 'type' in method and 'content' in method:
                method_content = method
            else:
                method_content = {'type': 'literal', 'content': str(method) if method else ''}
            result.append({
                'name': 'method',
                'input': {'type': 'string', 'value': method_content},
            })
            concat = inputs_obj.get('concatResult', '')
            if isinstance(concat, dict) and 'type' in concat and 'content' in concat:
                concat_content = concat
            else:
                concat_content = {'type': 'literal', 'content': str(concat) if concat else ''}
            result.append({
                'name': 'concatResult',
                'input': {'type': 'string', 'value': concat_content},
            })
            return result

        # ── Variable Merge nodes (type 32) ────────────────────
        if node_type == VARIABLE_MERGE_NODE_TYPE_ID:
            merge_groups = inputs_obj.get('mergeGroups', [])
            if merge_groups:
                return [{'name': 'mergeGroups', 'input': {'type': 'list', 'value': {'type': 'literal', 'content': merge_groups}}}]
            return []

        # Default: empty
        return []


    def _extract_outputs(
        self, data: dict, source_file: str | None,
        span_map: SpanMap | None = None,
        yaml_prefix: tuple[str, ...] = (),
    ) -> tuple:
        """Extract outputs tree from data.outputs."""
        from .workflow_ast import OutputVarAST
        raw = data.get('outputs', [])
        if not isinstance(raw, list):
            return ()
        return tuple(self._extract_output_var(o, source_file) for o in raw if isinstance(o, dict))

    def _extract_output_var(self, item: dict, source_file: str | None):
        """Recursively extract a single output variable."""
        from .workflow_ast import OutputVarAST
        children_raw = item.get('children', [])
        children = tuple(
            self._extract_output_var(c, source_file)
            for c in children_raw if isinstance(c, dict)
        ) if isinstance(children_raw, list) else ()

        # Extract type: prefer top-level "type", fall back to "input.type"
        # (coze-studio format puts type inside the input value expression)
        var_type = item.get('type')
        if not var_type:
            inp = item.get('input')
            if isinstance(inp, dict):
                var_type = inp.get('type')

        return OutputVarAST(
            name=item.get('name'),
            var_type=var_type,
            required=bool(item.get('required', False)),
            default_value=item.get('defaultValue'),
            children=children,
            source_span=None,
        )

    def _get_blocks_raw(self, node_raw: dict, data: dict) -> tuple[list, list]:
        """Get raw blocks and edges from node or data."""
        blocks_raw = node_raw.get('blocks', [])
        edges_raw = node_raw.get('edges', [])
        if not blocks_raw and isinstance(data, dict):
            blocks_raw = data.get('blocks', [])
        if not edges_raw and isinstance(data, dict):
            edges_raw = data.get('edges', [])
        return (
            blocks_raw if isinstance(blocks_raw, list) else [],
            edges_raw if isinstance(edges_raw, list) else [],
        )

    @staticmethod
    def _lookup_block_yaml_prefix(
        span_map: SpanMap | None,
        node_yaml_prefix: tuple[str, ...],
        block_index: int,
    ) -> tuple[str, ...]:
        """Compute YAML path prefix for a block, checking node-level then data-level.

        Blocks may appear directly on the node dict ('blocks' key) or
        nested under data ('data' -> 'blocks').  Try node-level first.
        """
        if span_map is None:
            return ()
        node_path = node_yaml_prefix + ('blocks', str(block_index))
        if span_map.lookup_path(node_path) is not None:
            return node_yaml_prefix + ('blocks',)
        return node_yaml_prefix + ('data', 'blocks',)

    @staticmethod
    def _lookup_nested_edge_span(
        span_map: SpanMap | None,
        node_yaml_prefix: tuple[str, ...],
        edge_index: int,
    ) -> SourceSpan | None:
        """Look up span for a nested edge, checking node-level then data-level."""
        if span_map is None:
            return None
        node_path = node_yaml_prefix + ('edges', str(edge_index))
        span = span_map.lookup_path(node_path)
        if span is not None:
            return span
        data_path = node_yaml_prefix + ('data', 'edges', str(edge_index))
        return span_map.lookup_path(data_path)

    def _extract_edges(
        self,
        raw: dict,
        source_file: str | None,
        canvas_path: tuple[str | int, ...],
        span_map: SpanMap | None = None,
    ) -> list[EdgeAST]:
        edges_raw = raw.get('edges', [])
        if not isinstance(edges_raw, list):
            return []
        result = []
        for i, e in enumerate(edges_raw):
            if not isinstance(e, dict):
                continue
            try:
                result.append(EdgeAST(
                    source_node_id=str(e.get('sourceNodeID', '')),
                    target_node_id=str(e.get('targetNodeID', '')),
                    source_port_id=e.get('sourcePortID'),
                    target_port_id=e.get('targetPortID'),
                    canvas_path=canvas_path,
                    provenance=SourceProvenance(source_file=source_file),
                    source_span=span_map.lookup_path(('edges', str(i))) if span_map else None,
                ))
            except Exception:
                # Skip malformed edge, continue with remaining edges
                pass
        return result

    def _extract_top_level_parameters(
        self, raw: dict, source_file: str | None
    ) -> list[ParameterAST]:
        params_raw = raw.get('parameters', [])
        if not isinstance(params_raw, list):
            return []
        return self._extract_parameters(params_raw, source_file)


    @staticmethod
    def _extract_ref_from_field(fld: dict) -> RefAST | None:
        """Extract a RefAST from a value expression field dict.

        Handles: {"type": ..., "value": {"type": "ref", "content": {...}}}
        and:     {"type": ..., "value": {"type": "literal", "content": "..."}}
        """
        if not isinstance(fld, dict):
            return None
        val = fld.get('value')
        if not isinstance(val, dict):
            return None
        vc = val.get('content')
        if isinstance(vc, dict):
            return RefAST(
                ref_type=str(val.get('type')) if val.get('type') else None,
                source=vc.get('source'),
                block_id=vc.get('blockID') if vc.get('blockID') is not None else vc.get('blockId'),
                name=vc.get('name'),
                path=tuple(vc.get('path') or ()),
            )
        if vc is not None:
            return RefAST(
                ref_type=str(val.get('type')) if val.get('type') else 'literal',
                name=str(vc),
            )
        return None

    def _extract_parameters(
        self, inputs: list, source_file: str | None
    ) -> list[ParameterAST]:
        """Extract parameters from inputParameters list.

        Handles two formats:
        1. Coze-studio format: {name: varName, left: {value: ...}, input/right: {value: ...}}
           Each entry represents one variable assignment. ``left_ref`` and ``right_ref``
           are populated on the ParameterAST so the validator can check both sides.
        2. Cozekit internal format: {name: "left", input: {value: ...}} + {name: "right", ...}
           Each entry is a separate parameter named "left" or "right".
        3. Simple format: {name, type/leftType, inputRef/leftRef: {...}}
        """
        if not isinstance(inputs, list):
            return []
        params = []
        for inp in inputs:
            if not isinstance(inp, dict):
                continue

            name = inp.get('name', '')
            left_type = None

            # Extract left_type from 'left' or 'input' field (before ref extraction)
            for _lt_key in ('left', 'input'):
                _lt_fld = inp.get(_lt_key)
                if isinstance(_lt_fld, dict):
                    lt = _lt_fld.get('type')
                    if isinstance(lt, str) and lt not in ('ref', 'object_ref', 'literal'):
                        left_type = lt
                        break

            # Detect coze-studio format: entry has both "left" and "input"/"right"
            # as dicts with "value" subfield, and name is NOT "left" (cozekit internal)
            left_field = inp.get('left')
            right_field = inp.get('right') or inp.get('input')
            left_has_value = isinstance(left_field, dict) and 'value' in left_field
            right_has_value = isinstance(right_field, dict) and 'value' in right_field

            if left_has_value and right_has_value and name != 'left':
                # Coze-studio format: populate left_ref and right_ref
                left_ref = self._extract_ref_from_field(left_field)
                right_ref = self._extract_ref_from_field(right_field)
                params.append(ParameterAST(
                    name=name if isinstance(name, str) else None,
                    left_type=left_type if isinstance(left_type, str) else None,
                    input_ref=right_ref,  # backward compat: input_ref = value side
                    left_ref=left_ref,
                    right_ref=right_ref,
                    provenance=SourceProvenance(source_file=source_file),
                ))
                continue

            # Standard extraction: find first matching field
            ref = None
            for key in ('input', 'left', 'right'):
                fld = inp.get(key)
                if isinstance(fld, dict):
                    if not name:
                        name_candidate = fld.get('name')
                        if isinstance(name_candidate, str):
                            name = name_candidate
                    val = fld.get('value')
                    if isinstance(val, dict):
                        vc = val.get('content')
                        if isinstance(vc, dict):
                            ref = RefAST(
                                ref_type=str(val.get('type')) if val.get('type') else None,
                                source=vc.get('source'),
                                block_id=vc.get('blockID') if vc.get('blockID') is not None else vc.get('blockId'),
                                name=vc.get('name'),
                                path=tuple(vc.get('path') or ()),
                            )
                            break
                        elif vc is not None:
                            ref = RefAST(
                                ref_type=str(val.get('type')) if val.get('type') else 'literal',
                                name=str(vc),
                            )
                            break

            # Fallback: try inputRef/leftRef (simple format)
            if ref is None:
                input_ref = inp.get('inputRef') or inp.get('leftRef')
                if isinstance(input_ref, dict):
                    ref = RefAST(
                        ref_type=input_ref.get('type'),
                        source=input_ref.get('source'),
                        block_id=input_ref.get('blockID') if input_ref.get('blockID') is not None else input_ref.get('blockId'),
                        name=input_ref.get('name'),
                    )

            params.append(ParameterAST(
                name=name if isinstance(name, str) else None,
                left_type=left_type if isinstance(left_type, str) else None,
                input_ref=ref,
                provenance=SourceProvenance(source_file=source_file),
            ))
        return params

    def _extract_branches(
        self, branches_raw: list, source_file: str | None
    ) -> list[BranchAST]:
        """Extract branches with typed conditions."""
        if not isinstance(branches_raw, list):
            return []
        result = []
        for b in branches_raw:
            if not isinstance(b, dict):
                continue
            branch_key = b.get('branchKey') or b.get('id')
            condition = self._extract_condition(b.get('condition'))
            result.append(BranchAST(
                branch_key=str(branch_key) if branch_key is not None else None,
                condition=condition,
                provenance=SourceProvenance(source_file=source_file),
            ))
        return result

    def _extract_condition(self, cond_raw: Any) -> ConditionAST | None:
        """Extract condition into typed ConditionAST."""
        if not isinstance(cond_raw, dict):
            return None
        conditions = cond_raw.get('conditions', [])
        if not isinstance(conditions, list) or not conditions:
            return None
        branches = []
        for c in conditions:
            if not isinstance(c, dict):
                continue
            left = self._extract_condition_param(c.get('left'))
            right = self._extract_condition_param(c.get('right'))
            operator = c.get('operator')
            branches.append(ConditionBranchAST(
                left=left,
                operator=str(operator) if operator else None,
                right=right,
            ))
        return ConditionAST(branches=tuple(branches))

    def _extract_condition_param(self, block_input: Any) -> ParameterAST | None:
        """Extract a condition operand into ParameterAST.

        Handles two formats:
        1. Simple: {type: "ref", content: "{{var}}"}  or  {type: "literal", content: "value"}
        2. Nested: {input: {value: {type: "ref", content: {source: ..., blockID: ...}}}}
        """
        if not isinstance(block_input, dict):
            return None
        name = block_input.get('name', '')
        ref = None

        # Format 1: simple {type, content} at top level
        direct_type = block_input.get('type')
        direct_content = block_input.get('content')
        if direct_type and direct_content is not None:
            if isinstance(direct_content, dict):
                ref = RefAST(
                    ref_type=str(direct_type),
                    source=direct_content.get('source'),
                    block_id=direct_content.get('blockID') if direct_content.get('blockID') is not None else direct_content.get('blockId'),
                    name=direct_content.get('name'),
                    path=tuple(direct_content.get('path') or ()),
                )
            else:
                ref = RefAST(
                    ref_type=str(direct_type),
                    name=str(direct_content) if direct_content else '',
                )

        # Format 2: nested {input: {value: {type, content}}}
        if ref is None:
            for key in ('input', 'left', 'right'):
                fld = block_input.get(key)
                if isinstance(fld, dict):
                    if not name:
                        nc = fld.get('name')
                        if isinstance(nc, str):
                            name = nc
                    val = fld.get('value')
                    if isinstance(val, dict):
                        vc = val.get('content')
                        if isinstance(vc, dict):
                            ref = RefAST(
                                ref_type=str(val.get('type')) if val.get('type') else None,
                                source=vc.get('source'),
                                block_id=vc.get('blockID') if vc.get('blockID') is not None else vc.get('blockId'),
                                name=vc.get('name'),
                                path=tuple(vc.get('path') or ()),
                            )
                            break
                        elif vc is not None:
                            # Literal value (string, number, etc.)
                            ref = RefAST(
                                ref_type=str(val.get('type')) if val.get('type') else 'literal',
                                name=str(vc),
                            )
                            break
        left_type = None
        left = block_input.get('left')
        if isinstance(left, dict):
            raw_lt = left.get('type')
            if isinstance(raw_lt, str):
                left_type = raw_lt
        return ParameterAST(
            name=str(name) if name else None,
            left_type=left_type,
            input_ref=ref,
        )

def _dict_to_param_list(d: dict) -> list[dict]:
    """Convert a flat dict to a normalized parameter list.

    Handles special keys like 'options' (list), scalar string values,
    and nested dicts.
    """
    result = []
    for key, value in d.items():
        if key == 'options' and isinstance(value, list):
            result.append({
                'name': 'options',
                'input': {'type': 'list', 'value': {'type': 'literal', 'content': value}},
            })
        elif isinstance(value, str):
            result.append({
                'name': key,
                'input': {'type': 'string', 'value': {'type': 'literal', 'content': value}},
            })
        elif isinstance(value, (int, float, bool)):
            result.append({
                'name': key,
                'input': {'type': 'number', 'value': {'type': 'literal', 'content': str(value)}},
            })
        elif isinstance(value, dict):
            # Nested dict — store as-is for complex structures
            result.append({
                'name': key,
                'input': {'type': 'object', 'value': {'type': 'literal', 'content': value}},
            })
    return result
