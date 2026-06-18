"""Type name aliases for commercial Coze exports and ana2 compiler output."""
from cozekit.transport.yaml_source_converter import TYPE_NAME_TO_ID


class TestCommercialTypeAliases:
    """Coze commercial YAML export uses reversed snake_case names."""

    def test_conversation_create(self):
        assert TYPE_NAME_TO_ID['conversation_create'] == '39'

    def test_message_create(self):
        assert TYPE_NAME_TO_ID['message_create'] == '55'

    def test_subflow(self):
        assert TYPE_NAME_TO_ID['subflow'] == '9'

    def test_both_orders_resolve_same_id_conversation(self):
        assert TYPE_NAME_TO_ID['conversation_create'] == TYPE_NAME_TO_ID['create_conversation']

    def test_both_orders_resolve_same_id_message(self):
        assert TYPE_NAME_TO_ID['message_create'] == TYPE_NAME_TO_ID['create_message']

    def test_subflow_aliases(self):
        assert TYPE_NAME_TO_ID['subflow'] == TYPE_NAME_TO_ID['subworkflow'] == TYPE_NAME_TO_ID['sub_workflow']


class TestAna2CompilerAliases:
    """ana2 compiler uses {noun}_{verb} convention for chat/database nodes."""

    def test_message_update(self):
        assert TYPE_NAME_TO_ID['message_update'] == '56'

    def test_message_delete(self):
        assert TYPE_NAME_TO_ID['message_delete'] == '57'

    def test_message_list(self):
        assert TYPE_NAME_TO_ID['message_list'] == '37'

    def test_conversation_update(self):
        assert TYPE_NAME_TO_ID['conversation_update'] == '51'

    def test_conversation_delete(self):
        assert TYPE_NAME_TO_ID['conversation_delete'] == '52'

    def test_conversation_list(self):
        assert TYPE_NAME_TO_ID['conversation_list'] == '53'

    def test_conversation_history_list(self):
        assert TYPE_NAME_TO_ID['conversation_history_list'] == '54'

    def test_conversation_clear(self):
        assert TYPE_NAME_TO_ID['conversation_clear'] == '38'

    def test_select_record(self):
        assert TYPE_NAME_TO_ID['select_record'] == '43'

    def test_insert_record(self):
        assert TYPE_NAME_TO_ID['insert_record'] == '46'

    def test_update_record(self):
        assert TYPE_NAME_TO_ID['update_record'] == '42'

    def test_delete_record(self):
        assert TYPE_NAME_TO_ID['delete_record'] == '44'

    def test_to_json(self):
        assert TYPE_NAME_TO_ID['to_json'] == '58'

    def test_from_json(self):
        assert TYPE_NAME_TO_ID['from_json'] == '59'


class TestAliasConsistency:
    """All aliases for the same ID must resolve identically."""

    def test_id_9_all_subworkflow_aliases(self):
        ids = {TYPE_NAME_TO_ID[k] for k in ('subworkflow', 'sub_workflow', 'subflow')}
        assert ids == {'9'}

    def test_id_39_all_conversation_create_aliases(self):
        ids = {TYPE_NAME_TO_ID[k] for k in ('create_conversation', 'conversation_create', 'createconversation')}
        assert ids == {'39'}

    def test_id_55_all_message_create_aliases(self):
        ids = {TYPE_NAME_TO_ID[k] for k in ('create_message', 'message_create', 'createmessage')}
        assert ids == {'55'}

    def test_id_43_all_database_query_aliases(self):
        ids = {TYPE_NAME_TO_ID[k] for k in ('database_query', 'databasequery', 'select_record')}
        assert ids == {'43'}

    def test_id_46_all_database_create_aliases(self):
        ids = {TYPE_NAME_TO_ID[k] for k in ('database_create', 'databasecreate', 'insert_record')}
        assert ids == {'46'}
