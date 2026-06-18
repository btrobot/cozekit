"""Tests for YAML source format converter."""

from __future__ import annotations

import pytest
from cozekit.transport.yaml_source_converter import YamlSourceConverter, TYPE_NAME_TO_ID


@pytest.fixture
def converter():
    return YamlSourceConverter()


# ── Format Detection Tests ──────────────────────────────────

class TestIsYamlSourceFormat:
    """Test YAML source format detection."""

    def test_detects_schema_version(self, converter):
        doc = {'schema_version': '1.0.0', 'nodes': [], 'edges': []}
        assert converter.is_yaml_source_format(doc) is True

    def test_detects_name_field(self, converter):
        doc = {'name': 'test_workflow', 'nodes': [], 'edges': []}
        assert converter.is_yaml_source_format(doc) is True

    def test_detects_mode_field(self, converter):
        doc = {'mode': 'workflow', 'nodes': [], 'edges': []}
        assert converter.is_yaml_source_format(doc) is True

    def test_detects_string_type(self, converter):
        doc = {'nodes': [{'id': '1', 'type': 'start'}], 'edges': []}
        assert converter.is_yaml_source_format(doc) is True

    def test_rejects_numeric_type(self, converter):
        doc = {'nodes': [{'id': '1', 'type': '1'}], 'edges': []}
        assert converter.is_yaml_source_format(doc) is False

    def test_rejects_empty_doc(self, converter):
        doc = {}
        assert converter.is_yaml_source_format(doc) is False

    def test_rejects_non_dict(self, converter):
        assert converter.is_yaml_source_format(None) is False
        assert converter.is_yaml_source_format([]) is False


# ── Type Mapping Tests ──────────────────────────────────────

class TestTypeMapping:
    """Test type name to ID mapping."""

    @pytest.mark.parametrize("name,expected_id", [
        ('start', '1'),
        ('end', '2'),
        ('llm', '3'),
        ('plugin', '4'),
        ('code', '5'),
        ('if', '8'),
        ('condition', '8'),
        ('loop', '21'),
        ('batch', '28'),
        ('http', '45'),
        ('comment', '31'),
        ('text', '15'),
        ('variable_merge', '32'),
        ('image_generate', '16'),
        ('output', '13'),
        ('question', '18'),
        ('intent', '22'),
        ('database', '12'),
    ])
    def test_maps_common_types(self, converter, name, expected_id):
        assert converter._resolve_type_id(name) == expected_id

    def test_preserves_numeric_type(self, converter):
        assert converter._resolve_type_id('1') == '1'
        assert converter._resolve_type_id('45') == '45'

    def test_case_insensitive(self, converter):
        assert converter._resolve_type_id('LLM') == '3'
        assert converter._resolve_type_id('Plugin') == '4'

    def test_unknown_type_passthrough(self, converter):
        assert converter._resolve_type_id('unknown_type') == 'unknown_type'


# ── Node Conversion Tests ───────────────────────────────────

class TestNodeConversion:
    """Test node structure conversion."""

    def test_converts_basic_node(self, converter):
        yaml_node = {
            'id': '100001',
            'type': 'start',
            'title': '开始',
            'icon': 'https://example.com/icon.png',
            'description': 'Start node',
            'position': {'x': 100, 'y': 200},
        }
        result = converter._adapt_node(yaml_node)
        
        assert result['id'] == '100001'
        assert result['type'] == '1'
        assert result['meta']['position'] == {'x': 100, 'y': 200}
        assert result['data']['nodeMeta']['title'] == '开始'
        assert result['data']['nodeMeta']['icon'] == 'https://example.com/icon.png'
        assert result['data']['nodeMeta']['description'] == 'Start node'

    def test_converts_llm_node_with_params(self, converter):
        yaml_node = {
            'id': '123456',
            'type': 'llm',
            'title': 'LLM',
            'parameters': {
                'modelType': 'gpt-4',
                'prompt': 'Hello',
                'temperature': 0.7,
            }
        }
        result = converter._adapt_node(yaml_node)
        
        assert result['type'] == '3'
        # All params go into data.inputs as direct keys
        inputs = result['data']['inputs']
        assert 'modelType' in inputs or 'prompt' in inputs

    def test_converts_outputs(self, converter):
        yaml_node = {
            'id': '100001',
            'type': 'start',
            'parameters': {
                'node_outputs': {
                    'url': {'type': 'string', 'required': True},
                    'count': {'type': 'integer', 'required': False},
                }
            }
        }
        result = converter._adapt_node(yaml_node)
        
        assert len(result['data']['outputs']) == 2
        outputs = {o['name']: o for o in result['data']['outputs']}
        assert outputs['url']['type'] == 'string'
        assert outputs['url']['required'] is True

    def test_preserves_blocks(self, converter):
        yaml_node = {
            'id': '21',
            'type': 'loop',
            'blocks': [{'id': 'block1'}],
        }
        result = converter._adapt_node(yaml_node)
        assert len(result['blocks']) == 1
        assert result['blocks'][0]['id'] == 'block1'


# ── Edge Conversion Tests ───────────────────────────────────

class TestEdgeConversion:
    """Test edge format conversion."""

    def test_converts_source_target(self, converter):
        yaml_edge = {'source_node': '100001', 'target_node': '186714'}
        result = converter._adapt_edge(yaml_edge)
        
        assert result['sourceNodeID'] == '100001'
        assert result['targetNodeID'] == '186714'

    def test_preserves_camelcase(self, converter):
        yaml_edge = {'sourceNodeID': '100001', 'targetNodeID': '186714'}
        result = converter._adapt_edge(yaml_edge)
        
        assert result['sourceNodeID'] == '100001'
        assert result['targetNodeID'] == '186714'

    def test_converts_source_port(self, converter):
        yaml_edge = {
            'source_node': '100001',
            'target_node': '186714',
            'source_port': 'port1',
        }
        result = converter._adapt_edge(yaml_edge)
        
        assert result['sourcePortID'] == 'port1'


# ── Parameter Conversion Tests ──────────────────────────────

class TestParameterConversion:
    """Test parameter conversion."""

    def test_converts_scalar_params(self, converter):
        params = {
            'modelType': 'gpt-4',
            'temperature': 0.7,
            'maxTokens': 1000,
        }
        inputs, outputs = converter._adapt_parameters(params)
        
        # Scalar params go directly into inputs (not inputParameters)
        assert 'modelType' in inputs
        assert 'temperature' in inputs
        assert 'maxTokens' in inputs

    def test_excludes_node_outputs(self, converter):
        params = {
            'modelType': 'gpt-4',
            'node_outputs': {'out': {'type': 'string'}},
        }
        inputs, outputs = converter._adapt_parameters(params)
        
        assert 'modelType' in inputs
        assert 'node_outputs' not in inputs  # node_outputs goes to outputs
        assert len(outputs) == 1

    def test_converts_dict_param(self, converter):
        params = {
            'config': {'key': 'value', 'nested': {'a': 1}},
        }
        inputs, outputs = converter._adapt_parameters(params)
        
        # Dict param goes directly into inputs
        assert 'config' in inputs


# ── Full Document Conversion Tests ──────────────────────────

class TestFullConversion:
    """Test full document conversion."""

    def test_converts_simple_workflow(self, converter):
        yaml_doc = {
            'schema_version': '1.0.0',
            'name': 'test',
            'nodes': [
                {'id': '100001', 'type': 'start', 'title': '开始'},
                {'id': '900001', 'type': 'end', 'title': '结束'},
            ],
            'edges': [
                {'source_node': '100001', 'target_node': '900001'},
            ],
        }
        result = converter.convert(yaml_doc)
        
        assert result['nodes'][0]['type'] == '1'
        assert result['nodes'][1]['type'] == '2'
        assert result['edges'][0]['sourceNodeID'] == '100001'

    def test_passthrough_json_format(self, converter):
        json_doc = {
            'nodes': [
                {'id': '100001', 'type': '1', 'meta': {}, 'data': {}},
            ],
            'edges': [],
        }
        result = converter.convert(json_doc)
        assert result is json_doc  # Same object, not converted

    def test_preserves_versions(self, converter):
        yaml_doc = {
            'nodes': [{'id': '1', 'type': 'start'}],
            'edges': [],
            'versions': {'app': '1.0'},
        }
        result = converter.convert(yaml_doc)
        assert result.get('versions') == {'app': '1.0'}
