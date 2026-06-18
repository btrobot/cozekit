"""YAML source format → JSON export format converter.

Converts coze-studio's YAML source format (flat structure, string type names)
to the JSON export format (nested structure, numeric type IDs).

Design inspired by v1's TempIRAdapter — all conversion logic lives here
so the downstream builder only handles normalized data.
"""

from __future__ import annotations

from typing import Any

# ── Type name → numeric ID mapping ──────────────────────────
# Source: frontend/packages/workflow/base/src/types/node-type.ts

TYPE_NAME_TO_ID: dict[str, str] = {
    'start': '1', 'end': '2', 'llm': '3', 'plugin': '4',
    'code': '5', 'dataset': '6', 'if': '8', 'condition': '8',
    'subworkflow': '9', 'sub_workflow': '9', 'subflow': '9', 'variable': '11',
    'database': '12', 'output': '13', 'imageflow': '14',
    'text': '15', 'image_generate': '16', 'imagegenerate': '16',
    'image_reference': '17', 'question': '18', 'break': '19',
    'set_variable': '20', 'setvariable': '20', 'loop': '21',
    'intent': '22', 'drawing_board': '23', 'drawingboard': '23',
    'scene_variable': '24', 'scenevariable': '24', 'scene_chat': '25',
    'scenechat': '25', 'ltm': '26', 'dataset_write': '27',
    'datasetwrite': '27', 'batch': '28', 'continue': '29',
    'input': '30', 'comment': '31', 'variable_merge': '32',
    'variablemerge': '32', 'trigger_upsert': '34', 'triggerupsert': '34',
    'trigger_delete': '35', 'triggerdelete': '35', 'trigger_read': '36',
    'triggerread': '36', 'query_message_list': '37', 'querymessagelist': '37', 'message_list': '37',
    'clear_context': '38', 'clearcontext': '38', 'conversation_clear': '38', 'create_conversation': '39', 'conversation_create': '39',
    'createconversation': '39', 'variable_assign': '40', 'variableassign': '40',
    'database_update': '42', 'databaseupdate': '42', 'update_record': '42', 'database_query': '43',
    'databasequery': '43', 'select_record': '43', 'database_delete': '44', 'databasedelete': '44', 'delete_record': '44',
    'http': '45', 'database_create': '46', 'databasecreate': '46', 'insert_record': '46',
    'update_conversation': '51', 'updateconversation': '51', 'conversation_update': '51',
    'delete_conversation': '52', 'deleteconversation': '52', 'conversation_delete': '52',
    'query_conversation_list': '53', 'queryconversationlist': '53', 'conversation_list': '53',
    'query_conversation_history': '54', 'queryconversationhistory': '54', 'conversation_history_list': '54',
    'create_message': '55', 'message_create': '55', 'createmessage': '55',
    'update_message': '56', 'updatemessage': '56', 'message_update': '56',
    'delete_message': '57', 'deletemessage': '57', 'message_delete': '57',
    'json_stringify': '58', 'jsonstringify': '58', 'to_json': '58',
    'json_parser': '59', 'jsonparser': '59', 'from_json': '59',
    'dataset_delete': '60', 'datasetdelete': '60',
    'audio2text': '61', 'text2audio': '62',
    'video_audio_extractor': '63', 'video_frame_extractor': '64',
    'video_generation': '65', 'ltm_write': '66', 'ltmwrite': '66',
    'ltm_read': '67', 'ltmread': '67',
}

# ── Media type → assistType mapping ─────────────────────────
MEDIA_ASSIST_TYPE: dict[str, int] = {
    'image': 1, 'file': 2, 'audio': 3, 'voice': 3, 'video': 4,
}

# ── Variable type normalization ─────────────────────────────
VAR_TYPE_MAP: dict[str, str] = {
    'string': 'string', 'str': 'string',
    'integer': 'integer', 'int': 'integer',
    'float': 'float', 'number': 'float',
    'boolean': 'boolean', 'bool': 'boolean',
    'object': 'object', 'map': 'object',
    'list': 'list', 'array': 'list',
    'image': 'string', 'voice': 'string',
    'audio': 'string', 'file': 'string', 'video': 'string',
}


class YamlSourceConverter:
    """Convert YAML source format to JSON export format.

    All conversion logic lives here so the builder only handles
    normalized data. Inspired by v1's TempIRAdapter.
    """

    def convert(self, doc: dict) -> dict:
        if not self.is_yaml_source_format(doc):
            return doc
        nodes = [self._adapt_node(n) for n in doc.get('nodes', []) if isinstance(n, dict)]
        edges = [self._adapt_edge(e) for e in doc.get('edges', []) if isinstance(e, dict)]
        result: dict[str, Any] = {'nodes': nodes, 'edges': edges}
        if 'versions' in doc:
            result['versions'] = doc['versions']
        return result

    def is_yaml_source_format(self, doc: dict) -> bool:
        if not isinstance(doc, dict):
            return False
        if any(k in doc for k in ('schema_version', 'name', 'mode', 'description')):
            return True
        nodes = doc.get('nodes', [])
        if nodes and isinstance(nodes[0], dict):
            node_type = nodes[0].get('type', '')
            if isinstance(node_type, str) and not node_type.isdigit():
                return True
        return False

    # ── Node conversion ──────────────────────────────────────

    def _adapt_node(self, node: dict) -> dict:
        """Convert a YAML source node to JSON export format."""
        type_name = node.get('type', '')
        type_id = self._resolve_type_id(type_name)

        # Title — auto-fill for comment nodes
        title = node.get('title', '')
        if (not isinstance(title, str) or not title) and type_name == 'comment':
            title = f"comment_{node.get('id', 'unknown')}"

        # nodeMeta
        node_meta: dict[str, Any] = {
            'title': title or '',
            'icon': node.get('icon') or '',
            'description': node.get('description') or '',
        }

        # meta
        meta: dict[str, Any] = {}
        if isinstance(node.get('position'), dict):
            meta['position'] = dict(node['position'])
        if isinstance(node.get('canvas_position'), dict):
            meta['canvasPosition'] = dict(node['canvas_position'])

        # Parameters → data.inputs + data.outputs
        params = node.get('parameters') if isinstance(node.get('parameters'), dict) else {}
        inputs, outputs = self._adapt_parameters(params)

        # Build data
        data: dict[str, Any] = {'nodeMeta': node_meta}
        if inputs:
            data['inputs'] = inputs
        if outputs:
            data['outputs'] = outputs

        # Start node: extract trigger_parameters from outputs
        if type_id == '1' and outputs:
            data['trigger_parameters'] = [
                {k: v for k, v in o.items() if k in ('name', 'type', 'required', 'assistType', 'schema')}
                for o in outputs
            ]

        # Build result
        result: dict[str, Any] = {
            'id': str(node.get('id', '')),
            'type': type_id,
            'meta': meta,
            'data': data,
        }

        if node.get('version') is not None:
            result['version'] = str(node['version'])
        if node.get('size') is not None:
            data['size'] = node['size']

        # Composite nodes: YAML 'nodes' → JSON 'blocks'
        if isinstance(node.get('nodes'), list):
            result['blocks'] = [
                self._adapt_node(c) for c in node['nodes'] if isinstance(c, dict)
            ]
        elif isinstance(node.get('blocks'), list):
            result['blocks'] = [
                self._adapt_node(b) if isinstance(b, dict) and 'type' in b else b
                for b in node['blocks']
            ]

        # Nested edges
        if isinstance(node.get('edges'), list):
            result['edges'] = [self._adapt_edge(e) for e in node['edges'] if isinstance(e, dict)]

        return result

    # ── Parameter conversion ─────────────────────────────────

    def _adapt_parameters(self, params: dict) -> tuple[dict, list]:
        """Convert YAML parameters to JSON inputs + outputs."""
        inputs: dict[str, Any] = {}
        outputs: list[dict[str, Any]] = []

        # node_inputs → inputParameters
        node_inputs = params.get('node_inputs')
        if isinstance(node_inputs, list):
            inputs['inputParameters'] = [
                self._adapt_input_param(item)
                for item in node_inputs if isinstance(item, dict)
            ]

        # node_outputs → outputs
        node_outputs = params.get('node_outputs')
        if isinstance(node_outputs, dict):
            outputs = [
                self._adapt_variable(name, spec)
                for name, spec in node_outputs.items()
                if isinstance(name, str) and isinstance(spec, dict)
            ]

        # All other params → data.inputs (with recursive normalization)
        for key, value in params.items():
            if key in ('node_inputs', 'node_outputs'):
                continue
            inputs[key] = self._adapt_generic(value)

        # Post-process: expand node-specific list structures
        self._expand_text_process_params(inputs)

        return inputs, outputs

    def _adapt_input_param(self, item: dict) -> dict:
        """Convert a node_input item to inputParameters format."""
        result: dict[str, Any] = {'name': str(item.get('name', ''))}
        # Preserve left/right fields for variable_assign nodes
        for side_key in ('left', 'right'):
            side_val = item.get(side_key)
            if isinstance(side_val, dict):
                result[side_key] = self._adapt_block_input(side_val)
        inp = item.get('input')
        if isinstance(inp, dict):
            result['input'] = self._adapt_block_input(inp)
        elif inp is not None:
            result['input'] = self._adapt_block_input({'value': inp})
        return result

    # ── Generic recursive conversion (from v1) ───────────────

    def _adapt_generic(self, value: Any) -> Any:
        """Recursively convert all nested value expressions.

        This is the core mechanism that eliminates builder patches.
        Walks the entire structure and converts:
        - {path, ref_node} → {type: "ref", content: {source, blockID, name}}
        - {type: "literal", content} → pass through
        - input/left/right/variables fields → _adapt_block_input
        - Everything else → recursive descent
        """
        if value is None:
            return value
        if isinstance(value, list):
            return [self._adapt_generic(item) for item in value]
        if isinstance(value, dict):
            # Value expression: {path, ref_node} or {type, content}
            if self._looks_like_ref(value):
                return self._adapt_ref(value)
            if value.get('type') in ('literal', 'ref', 'object_ref') and 'content' in value:
                return self._normalize_typed_value(value)
            # Structured input fields
            result: dict[str, Any] = {}
            for k, child in value.items():
                if k in ('input', 'left', 'right'):
                    result[k] = self._adapt_block_input(child) if isinstance(child, dict) else child
                elif k == 'variables' and isinstance(child, list):
                    result[k] = [self._adapt_block_input(item) if isinstance(item, dict) else item for item in child]
                elif k == 'value':
                    if isinstance(child, dict):
                        if self._looks_like_ref(child):
                            result[k] = self._adapt_ref(child)
                        elif child.get('type') in ('literal', 'ref', 'object_ref') and 'content' in child:
                            result[k] = self._normalize_typed_value(child)
                        else:
                            result[k] = self._adapt_generic(child)
                    elif child is None:
                        result[k] = {'type': 'literal', 'content': ''}
                    else:
                        result[k] = self._adapt_value_expr(child)
                else:
                    result[k] = self._adapt_generic(child)
            return result
        return value

    def _looks_like_ref(self, value: Any) -> bool:
        """Check if value is a YAML ref expression {path, ref_node}."""
        return isinstance(value, dict) and 'ref_node' in value and 'path' in value

    def _adapt_ref(self, raw: dict) -> dict:
        """Convert {path, ref_node} to {type: "ref", content: {source, blockID, name}}."""
        path = raw.get('path')
        ref_node = raw.get('ref_node', '')
        content: dict[str, Any] = {
            'source': 'block-output',
            'blockID': str(ref_node or ''),
        }
        if isinstance(path, str) and path:
            content['name'] = path
        elif isinstance(path, list):
            content['path'] = path
        result: dict[str, Any] = {'type': 'ref', 'content': content}
        if 'rawMeta' in raw:
            result['rawMeta'] = raw['rawMeta']
        return result

    def _normalize_typed_value(self, raw: dict) -> dict:
        """Normalize a typed value {type, content} — ensure content is properly structured."""
        vtype = raw.get('type')
        content = raw.get('content')
        result: dict[str, Any] = {'type': vtype}
        if vtype == 'literal':
            result['content'] = content
        elif isinstance(content, dict):
            normalized = dict(content)
            if normalized.get('source') is None:
                normalized['source'] = 'block-output'
            if normalized.get('blockID') is not None:
                normalized['blockID'] = str(normalized['blockID'])
            result['content'] = normalized
        else:
            result['content'] = content
        if 'rawMeta' in raw:
            result['rawMeta'] = raw['rawMeta']
        return result

    def _adapt_block_input(self, raw: Any) -> dict:
        """Convert a block input (value with type/schema) to normalized format."""
        if not isinstance(raw, dict):
            if raw is None:
                return {'type': 'string'}
            return {'type': self._infer_type(raw), 'value': self._adapt_generic(raw)}

        # Condition-style input: {input: {value: ...}} or {left: ..., right: ...}
        if 'input' in raw and isinstance(raw.get('input'), dict):
            result = {}
            for k, child in raw.items():
                if k == 'input' and isinstance(child, dict):
                    result[k] = self._adapt_block_input(child)
                else:
                    result[k] = self._adapt_generic(child)
            return result

        # Has explicit type/schema/value structure
        if any(k in raw for k in ('type', 'value', 'schema', 'assistType', 'items', 'properties')):
            result: dict[str, Any] = {}
            raw_type = raw.get('type')
            if raw_type is not None:
                result['type'] = VAR_TYPE_MAP.get(str(raw_type), str(raw_type))
            if 'value' in raw:
                result['value'] = self._adapt_value_expr(raw['value'])
            if 'schema' in raw:
                result['schema'] = self._adapt_generic(raw['schema'])
            if 'items' in raw:
                result['items'] = self._adapt_generic(raw['items'])
            if 'properties' in raw:
                result['properties'] = self._adapt_generic(raw['properties'])
            if 'required' in raw:
                result['required'] = raw['required']
            if 'assistType' in raw:
                result['assistType'] = raw['assistType']
            if 'name' in raw:
                result['name'] = raw['name']
            return result

        # Plain value — wrap as typed value expression
        if raw is None:
            return {'type': 'string'}
        adapted_value = self._adapt_value_expr(raw)
        return {'type': self._infer_type(raw), 'value': adapted_value}

    # ── Variable/output conversion ───────────────────────────

    def _adapt_variable(self, name: str, spec: dict) -> dict:
        """Convert a node_output variable spec to JSON export format."""
        raw_type = spec.get('type', 'string')
        var_type = VAR_TYPE_MAP.get(str(raw_type), 'string')
        result: dict[str, Any] = {
            'name': name,
            'type': var_type,
        }
        if spec.get('required') is not None:
            result['required'] = bool(spec['required'])
        if spec.get('description') not in (None, ''):
            result['description'] = spec['description']
        assist_type = MEDIA_ASSIST_TYPE.get(str(raw_type))
        if assist_type is not None:
            result['assistType'] = assist_type
        # Schema for object/list types
        schema = self._adapt_variable_schema(spec)
        if schema is not None:
            result['schema'] = schema
        # Default value
        default_value = spec.get('value')
        if default_value is not None and not self._looks_like_ref(default_value):
            result['defaultValue'] = default_value
        return result

    def _adapt_variable_schema(self, spec: dict) -> Any:
        """Extract and normalize schema from a variable spec."""
        raw_type = VAR_TYPE_MAP.get(str(spec.get('type', 'string')), 'string')
        if raw_type == 'object':
            properties = spec.get('properties')
            if isinstance(properties, dict):
                return [self._adapt_variable(n, c) for n, c in properties.items() if isinstance(n, str) and isinstance(c, dict)]
            existing = spec.get('schema')
            if isinstance(existing, list):
                return existing
            return []
        if raw_type == 'list':
            items = spec.get('items')
            if isinstance(items, dict):
                item_type = VAR_TYPE_MAP.get(str(items.get('type', 'string')), 'string')
                res: dict[str, Any] = {'type': item_type}
                nested = self._adapt_variable_schema(items)
                if nested is not None and item_type in ('object', 'list'):
                    res['schema'] = nested
                return res
            existing = spec.get('schema')
            if isinstance(existing, (dict, list)):
                return existing
            return {'type': 'string'}
        return None

    # ── Node-specific expansions ──────────────────────────────

    def _expand_text_process_params(self, inputs: dict) -> None:
        """Expand concatParams list into individual params."""
        concat_params = inputs.get("concatParams")
        if not isinstance(concat_params, list):
            return
        for item in concat_params:
            if isinstance(item, dict) and "name" in item:
                name = item["name"]
                inp = item.get("input", {})
                if isinstance(inp, dict) and "value" in inp:
                    inputs[name] = inp["value"]
                elif isinstance(inp, dict):
                    inputs[name] = inp

    def _expand_condition_branches(self, inputs: dict) -> None:
        """Normalize condition branch values from YAML ref format."""
        branches = inputs.get("branches")
        if not isinstance(branches, list):
            return
        for branch in branches:
            if not isinstance(branch, dict):
                continue
            cond = branch.get("condition")
            if not isinstance(cond, dict):
                continue
            conditions = cond.get("conditions")
            if not isinstance(conditions, list):
                continue
            for c in conditions:
                if not isinstance(c, dict):
                    continue
                for key in ("left", "right"):
                    side = c.get(key)
                    if isinstance(side, dict):
                        inp = side.get("input")
                        if isinstance(inp, dict) and "value" in inp:
                            inp["value"] = self._adapt_value_expr(inp["value"])

    # ── Edge conversion ──────────────────────────────────────

    def _adapt_edge(self, edge: dict) -> dict:
        """Convert YAML edge to JSON export format."""
        result: dict[str, Any] = {}
        if 'source_node' in edge:
            result['sourceNodeID'] = str(edge['source_node'])
        elif 'sourceNodeID' in edge:
            result['sourceNodeID'] = str(edge['sourceNodeID'])
        if 'target_node' in edge:
            result['targetNodeID'] = str(edge['target_node'])
        elif 'targetNodeID' in edge:
            result['targetNodeID'] = str(edge['targetNodeID'])
        if 'source_port' in edge:
            result['sourcePortID'] = str(edge['source_port'])
        elif 'sourcePortID' in edge:
            result['sourcePortID'] = str(edge['sourcePortID'])
        if 'target_port' in edge:
            result['targetPortID'] = str(edge['target_port'])
        elif 'targetPortID' in edge:
            result['targetPortID'] = str(edge['targetPortID'])
        return result

    # ── Utilities ────────────────────────────────────────────

    def _resolve_type_id(self, type_name: str) -> str:
        if not type_name:
            return type_name
        if type_name.isdigit():
            return type_name
        return TYPE_NAME_TO_ID.get(type_name.lower(), type_name)

    def _adapt_value_expr(self, raw: Any) -> dict:
        """Convert any raw value to {type, content} format."""
        if raw is None:
            return {'type': 'literal', 'content': ''}
        if isinstance(raw, dict):
            if self._looks_like_ref(raw):
                return self._adapt_ref(raw)
            if raw.get('type') in ('literal', 'ref', 'object_ref') and 'content' in raw:
                return self._normalize_typed_value(raw)
            return {'type': 'literal', 'content': raw}
        return {'type': 'literal', 'content': raw}
    
    def _infer_type(self, value: Any) -> str:
        if isinstance(value, bool):
            return 'boolean'
        if isinstance(value, int):
            return 'integer'
        if isinstance(value, float):
            return 'number'
        if isinstance(value, list):
            return 'list'
        if isinstance(value, dict):
            return 'object'
        return 'string'
