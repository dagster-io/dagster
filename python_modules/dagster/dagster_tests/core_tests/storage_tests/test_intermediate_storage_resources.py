import pytest
from dagster import (
    DagsterInvalidDefinitionError,
    ModeDefinition,
    ResourceDefinition,
    execute_pipeline,
    intermediate_storage,
    pipeline,
)
from dagster.core.storage.object_store import InMemoryObjectStore
from dagster.core.storage.system_storage import build_intermediate_storage_from_object_store


def create_mem_system_intermediate_store(init_context):
    object_store = InMemoryObjectStore()
    return build_intermediate_storage_from_object_store(
        object_store=object_store, init_context=init_context
    )


def test_naked_intermediate_storage():
    called = {}

    @intermediate_storage(required_resource_keys=set())
    def no_config_storage(init_context):
        called["called"] = True
        return create_mem_system_intermediate_store(init_context)

    @pipeline(mode_defs=[ModeDefinition(intermediate_storage_defs=[no_config_storage])])
    def pass_pipeline():
        pass

    assert execute_pipeline(
        pass_pipeline, run_config={"intermediate_storage": {"no_config_storage": {}}}
    ).success

    assert called["called"]

    # This also works with None because storage is a selector and you can indicate your
    # "selection" by the presence of the key
    assert execute_pipeline(
        pass_pipeline, run_config={"intermediate_storage": {"no_config_storage": None}}
    ).success


def test_resource_requirements_pass():
    called = {}

    @intermediate_storage(required_resource_keys={"yup"})
    def storage_with_req(init_context):
        assert hasattr(init_context.resources, "yup")
        assert not hasattr(init_context.resources, "not_required")
        assert not hasattr(init_context.resources, "kjdkfjdkfje")
        called["called"] = True
        return create_mem_system_intermediate_store(init_context)

    @pipeline(
        mode_defs=[
            ModeDefinition(
                resource_defs={
                    "yup": ResourceDefinition.none_resource(),
                    "not_required": ResourceDefinition.none_resource(),
                },
                intermediate_storage_defs=[storage_with_req],
            )
        ]
    )
    def resource_req_pass_pipeline():
        pass

    assert execute_pipeline(
        resource_req_pass_pipeline, run_config={"intermediate_storage": {"storage_with_req": {}}}
    ).success

    assert called["called"]

    # This also works with None because storage is a selector and you can indicate your
    # "selection" by the presence of the key
    assert execute_pipeline(
        resource_req_pass_pipeline, run_config={"intermediate_storage": {"storage_with_req": None}}
    ).success


def test_resource_requirements_fail():
    @intermediate_storage(required_resource_keys={"yup"})
    def storage_with_req(init_context):
        return create_mem_system_intermediate_store(init_context)

    with pytest.raises(DagsterInvalidDefinitionError) as exc_info:

        @pipeline(
            mode_defs=[
                ModeDefinition(
                    resource_defs={"nope": ResourceDefinition.none_resource()},
                    intermediate_storage_defs=[storage_with_req],
                )
            ]
        )
        def _resource_req_pass_pipeline():
            pass

    assert str(exc_info.value) == (
        "Resource 'yup' is required by intermediate storage 'storage_with_req', but "
        "is not provided by mode 'default'."
    )
