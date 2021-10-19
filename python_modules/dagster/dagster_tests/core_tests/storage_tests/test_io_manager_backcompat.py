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
