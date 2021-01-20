import re

import pytest
from dagster import (
    ModeDefinition,
    check,
    configured,
    execute_pipeline,
    intermediate_storage,
    pipeline,
)
from dagster.core.storage.object_store import InMemoryObjectStore
from dagster.core.storage.system_storage import build_intermediate_storage_from_object_store


def test_storage_config_backcompat():
    it = {}

    @intermediate_storage(required_resource_keys=set())
    def no_config_intermediate_storage(init_context):
        it["ran"] = True
        return create_mem_system_intermediate_store(init_context)

    @pipeline(
        mode_defs=[ModeDefinition(intermediate_storage_defs=[no_config_intermediate_storage])]
    )
    def pass_pipeline():
        pass

    result = execute_pipeline(pass_pipeline, {"storage": {"no_config_intermediate_storage": None}})
    assert result.success


def create_mem_system_intermediate_store(init_context):
    object_store = InMemoryObjectStore()
    return build_intermediate_storage_from_object_store(
        object_store=object_store, init_context=init_context
    )


def assert_pipeline_runs_with_intermediate_storage(
    intermediate_storage_def, intermediate_storage_config
):
    @pipeline(mode_defs=[ModeDefinition(intermediate_storage_defs=[intermediate_storage_def])])
    def pass_pipeline():
        pass

    result = execute_pipeline(pass_pipeline, {"intermediate_storage": intermediate_storage_config})
    assert result.success


def test_naked_intermediate_storage():
    it = {}

    @intermediate_storage(required_resource_keys=set())
    def no_config_intermediate_storage(init_context):
        it["ran"] = True
        return create_mem_system_intermediate_store(init_context)

    assert_pipeline_runs_with_intermediate_storage(
        no_config_intermediate_storage, {"no_config_intermediate_storage": {}}
    )
    assert it["ran"]

    it = {}
    assert_pipeline_runs_with_intermediate_storage(
        no_config_intermediate_storage, {"no_config_intermediate_storage": None}
    )
    assert it["ran"]


@pytest.mark.xfail(raises=check.ParameterCheckError)
def test_intermediate_storage_primitive_config():
    it = {}

    @intermediate_storage(required_resource_keys=set(), config_schema=str)
    def test_intermediate_storage(init_context):
        assert init_context.intermediate_storage_config == "secret testing value!!"
        it["ran"] = True
        return create_mem_system_intermediate_store(init_context)

    assert_pipeline_runs_with_intermediate_storage(
        test_intermediate_storage,
        {"test_intermediate_storage": {"config": "secret testing value!!"}},
    )
    assert it["ran"]


def test_intermediate_storage_dict_config():
    it = {}

    @intermediate_storage(required_resource_keys=set(), config_schema={"value": str})
    def test_intermediate_storage(init_context):
        assert init_context.intermediate_storage_config["value"] == "secret testing value!!"
        it["ran"] = True
        return create_mem_system_intermediate_store(init_context)

    assert_pipeline_runs_with_intermediate_storage(
        test_intermediate_storage,
        {"test_intermediate_storage": {"config": {"value": "secret testing value!!"}}},
    )
    assert it["ran"]


def test_intermediate_storage_dict_config_configured():
    it = {}

    @intermediate_storage(required_resource_keys=set(), config_schema={"value": str})
    def test_intermediate_storage(init_context):
        assert init_context.intermediate_storage_config["value"] == "secret testing value!!"
        it["ran"] = True
        return create_mem_system_intermediate_store(init_context)

    test_intermediate_storage_configured = configured(test_intermediate_storage)(
        {"value": "secret testing value!!"}
    )

    assert_pipeline_runs_with_intermediate_storage(
        test_intermediate_storage_configured, {"test_intermediate_storage": {}}
    )
    assert it["ran"]

    it = {}
    assert_pipeline_runs_with_intermediate_storage(
        test_intermediate_storage_configured, {"test_intermediate_storage": None}
    )
    assert it["ran"]


def test_intermediate_storage_deprecation_warning():
    @pipeline
    def empty_pipeline():
        pass

    # Deprecation warning on intermediate storage config
    with pytest.warns(
        UserWarning,
        match=re.escape(
            'The "storage" and "intermediate_storage" entries in the run config are deprecated'
        ),
    ):
        execute_pipeline(empty_pipeline, run_config={"intermediate_storage": {"filesystem": {}}})

    # No warnings if no intermediate storage configured or created
    with pytest.warns(None) as record:

        execute_pipeline(empty_pipeline)

    assert len(record) == 0
