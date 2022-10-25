import json
from pathlib import Path
from typing import Any

import pytest
from upath import UPath

from dagster import (
    DagsterType,
    Field,
    IOManager,
    InitResourceContext,
    InputContext,
    OutputContext,
    PythonObjectDagsterType,
    build_init_resource_context,
    build_input_context,
    build_output_context,
    io_manager,
)
from dagster._core.storage.upath_io_manager import UPathIOManager


@pytest.mark.parametrize("json_data", [0, 0.0, [0, 1, 2], {"a": 0}, [{"a": 0}, {"b": 1}, {"c": 2}]])
def test_upath_io_manager_with_json(tmp_path: Path, json_data: Any):
    class JSONIOManager(UPathIOManager):
        extension: str = ".json"

        def serialize(self, obj: Any, path: UPath, context: OutputContext):
            with path.open("wb") as file:
                file.write(json.dumps(obj).encode())

        def deserialize(self, path: UPath, context: InputContext) -> Any:
            with path.open("rb") as file:
                return json.loads(file.read())

    @io_manager(config_schema={"base_path": Field(str, is_required=False)})
    def json_io_manager(init_context: InitResourceContext):
        base_path = UPath(
            init_context.resource_config.get("base_path", init_context.instance.storage_directory())
        )
        return JSONIOManager(base_path=base_path)

    manager = json_io_manager(build_init_resource_context(config={"base_path": str(tmp_path)}))
    context = build_output_context(
        name="abc",
        step_key="123",
        dagster_type=DagsterType(type_check_fn=lambda _, value: True, name="any", typing_type=Any),
    )
    manager.handle_output(context, json_data)

    with manager.get_path(context).open("rb") as file:
        assert json.loads(file.read()) == json_data

    context = build_input_context(
        name="abc",
        upstream_output=context,
        dagster_type=DagsterType(type_check_fn=lambda _, value: True, name="any", typing_type=Any),
    )
    assert manager.load_input(context) == json_data
