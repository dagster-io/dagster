import re

import pytest
from dagster.core.definitions import intermediate_storage, pipeline, solid
from dagster.core.definitions.mode import ModeDefinition
from dagster.core.execution.api import execute_pipeline, reexecute_pipeline
from dagster.core.instance import DagsterInstance
from dagster.core.storage.object_store import InMemoryObjectStore
from dagster.core.storage.system_storage import (
    build_intermediate_storage_from_object_store,
    io_manager_from_intermediate_storage,
)
from dagster_tests.general_tests.utils_tests.utils import assert_no_warnings


def test_intermediate_storage_def_to_io_manager_def():
    called = {}

    @intermediate_storage()
    def no_config_intermediate_storage(init_context):
        called["ran"] = True
        object_store = InMemoryObjectStore()
        return build_intermediate_storage_from_object_store(
            object_store=object_store, init_context=init_context
        )

    @solid
    def return_one(_):
        return 1

    @pipeline(
        mode_defs=[
            ModeDefinition(
                resource_defs={
                    "io_manager": io_manager_from_intermediate_storage(
                        no_config_intermediate_storage
                    )
                }
            )
        ]
    )
    def foo():
        return_one()

    assert execute_pipeline(foo).success


def test_intermediate_storage_deprecation_warning():
    @solid
    def return_one(_):
        return 1

    @pipeline
    def foo():
        return_one()

    with assert_no_warnings():
        execute_pipeline(foo)

    with pytest.warns(
        UserWarning,
        match=re.escape(
            "Intermediate Storages are deprecated in 0.10.0 and will be removed in a future release."
        ),
    ):
        execute_pipeline(foo, run_config={"intermediate_storage": {"filesystem": {}}})


def test_intermediate_storage_reexecution():
    @solid
    def return_one(_):
        return 1

    @solid
    def plus_one(_, one):
        return one + 1

    @pipeline
    def foo():
        plus_one(return_one())

    run_config = {"intermediate_storage": {"filesystem": {}}}

    instance = DagsterInstance.ephemeral()
    result = execute_pipeline(foo, run_config=run_config, instance=instance)
    assert result.success
    reexecution_result = reexecute_pipeline(
        foo, run_config=run_config, parent_run_id=result.run_id, instance=instance
    )
    assert reexecution_result.success

    partial_reexecution_result = reexecute_pipeline(
        foo,
        run_config=run_config,
        step_selection=["plus_one"],
        parent_run_id=result.run_id,
        instance=instance,
    )
    assert partial_reexecution_result.success


def test_intermediate_storage_event_message():
    @solid
    def return_one(_):
        return 1

    @solid
    def plus_one(_, one):
        return one + 1

    @pipeline
    def foo():
        plus_one(return_one())

    run_config = {"intermediate_storage": {"filesystem": {}}}

    result = execute_pipeline(foo, run_config=run_config)

    for i in filter(lambda i: i.is_handled_output, result.event_list):
        assert "output manager" not in i.message

    for i in filter(lambda i: i.is_loaded_input, result.event_list):
        assert "input manager" not in i.message
