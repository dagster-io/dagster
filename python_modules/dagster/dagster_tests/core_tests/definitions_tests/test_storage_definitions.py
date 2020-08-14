import pytest

from dagster import (
    ModeDefinition,
    check,
    configured,
    execute_pipeline,
    intermediate_storage,
    pipeline,
    system_storage,
)
from dagster.core.storage.object_store import InMemoryObjectStore
from dagster.core.storage.system_storage import (
    build_intermediate_storage_from_object_store,
    create_mem_system_storage_data,
)


def create_mem_system_intermediate_store(init_context):
    object_store = InMemoryObjectStore()
    return build_intermediate_storage_from_object_store(
        object_store=object_store, init_context=init_context
    )


def assert_pipeline_runs_with_storage(storage_def, storage_config):
    @pipeline(mode_defs=[ModeDefinition(system_storage_defs=[storage_def])])
    def pass_pipeline():
        pass

    result = execute_pipeline(pass_pipeline, {'storage': storage_config})
    assert result.success


def assert_pipeline_runs_with_intermediate_storage(
    intermediate_storage_def, intermediate_storage_config
):
    @pipeline(mode_defs=[ModeDefinition(intermediate_storage_defs=[intermediate_storage_def])])
    def pass_pipeline():
        pass

    result = execute_pipeline(pass_pipeline, {'intermediate_storage': intermediate_storage_config})
    assert result.success


def test_naked_system_storage():
    it = {}

    @system_storage(required_resource_keys=set())
    def no_config_storage(init_context):
        it['ran'] = True
        return create_mem_system_storage_data(init_context)

    assert_pipeline_runs_with_storage(no_config_storage, {'no_config_storage': {}})
    assert it['ran']

    it = {}
    assert_pipeline_runs_with_storage(no_config_storage, {'no_config_storage': None})
    assert it['ran']


@pytest.mark.xfail(raises=check.ParameterCheckError)
def test_system_storage_primitive_config():
    it = {}

    @system_storage(required_resource_keys=set(), config_schema=str)
    def test_storage(init_context):
        assert init_context.system_storage_config == 'secret testing value!!'
        it['ran'] = True
        return create_mem_system_storage_data(init_context)

    assert_pipeline_runs_with_storage(
        test_storage, {'test_storage': {'config': 'secret testing value!!'}}
    )
    assert it['ran']


def test_system_storage_dict_config():
    it = {}

    @system_storage(required_resource_keys=set(), config_schema={'value': str})
    def test_storage(init_context):
        assert init_context.system_storage_config['value'] == 'secret testing value!!'
        it['ran'] = True
        return create_mem_system_storage_data(init_context)

    assert_pipeline_runs_with_storage(
        test_storage, {'test_storage': {'config': {'value': 'secret testing value!!'}}}
    )
    assert it['ran']


def test_system_storage_dict_config_configured():
    it = {}

    @system_storage(required_resource_keys=set(), config_schema={'value': str})
    def test_storage(init_context):
        assert init_context.system_storage_config['value'] == 'secret testing value!!'
        it['ran'] = True
        return create_mem_system_storage_data(init_context)

    test_storage_configured = configured(test_storage)({'value': 'secret testing value!!'})

    assert_pipeline_runs_with_storage(test_storage_configured, {'test_storage': {}})
    assert it['ran']

    it = {}
    assert_pipeline_runs_with_storage(test_storage_configured, {'test_storage': None})
    assert it['ran']


def test_naked_intermediate_storage():
    it = {}

    @intermediate_storage(required_resource_keys=set())
    def no_config_intermediate_storage(init_context):
        it['ran'] = True
        return create_mem_system_intermediate_store(init_context)

    assert_pipeline_runs_with_intermediate_storage(
        no_config_intermediate_storage, {'no_config_intermediate_storage': {}}
    )
    assert it['ran']

    it = {}
    assert_pipeline_runs_with_intermediate_storage(
        no_config_intermediate_storage, {'no_config_intermediate_storage': None}
    )
    assert it['ran']


@pytest.mark.xfail(raises=check.ParameterCheckError)
def test_intermediate_storage_primitive_config():
    it = {}

    @intermediate_storage(required_resource_keys=set(), config_schema=str)
    def test_intermediate_storage(init_context):
        assert init_context.intermediate_storage_config == 'secret testing value!!'
        it['ran'] = True
        return create_mem_system_intermediate_store(init_context)

    assert_pipeline_runs_with_intermediate_storage(
        test_intermediate_storage,
        {'test_intermediate_storage': {'config': 'secret testing value!!'}},
    )
    assert it['ran']


def test_intermediate_storage_dict_config():
    it = {}

    @intermediate_storage(required_resource_keys=set(), config_schema={'value': str})
    def test_intermediate_storage(init_context):
        assert init_context.intermediate_storage_config['value'] == 'secret testing value!!'
        it['ran'] = True
        return create_mem_system_intermediate_store(init_context)

    assert_pipeline_runs_with_intermediate_storage(
        test_intermediate_storage,
        {'test_intermediate_storage': {'config': {'value': 'secret testing value!!'}}},
    )
    assert it['ran']


def test_intermediate_storage_dict_config_configured():
    it = {}

    @intermediate_storage(required_resource_keys=set(), config_schema={'value': str})
    def test_intermediate_storage(init_context):
        assert init_context.intermediate_storage_config['value'] == 'secret testing value!!'
        it['ran'] = True
        return create_mem_system_intermediate_store(init_context)

    test_intermediate_storage_configured = configured(test_intermediate_storage)(
        {'value': 'secret testing value!!'}
    )

    assert_pipeline_runs_with_intermediate_storage(
        test_intermediate_storage_configured, {'test_intermediate_storage': {}}
    )
    assert it['ran']

    it = {}
    assert_pipeline_runs_with_intermediate_storage(
        test_intermediate_storage_configured, {'test_intermediate_storage': None}
    )
    assert it['ran']
