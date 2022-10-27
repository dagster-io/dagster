import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, List, Optional

import pandas
import pendulum
import pytest
from upath import UPath

from dagster import (
    AllPartitionMapping,
    AssetIn,
    AssetKey,
    AssetMaterialization,
    DagsterType,
    DailyPartitionsDefinition,
    Field,
    HourlyPartitionsDefinition,
    IOManager,
    InitResourceContext,
    InputContext,
    OpExecutionContext,
    OutputContext,
    PartitionKeyRange,
    PartitionMapping,
    PartitionsDefinition,
    PythonObjectDagsterType,
    StaticPartitionsDefinition,
    asset,
    build_init_resource_context,
    build_input_context,
    build_output_context,
    io_manager,
    materialize,
)
from dagster._core.definitions import AssetGroup, build_assets_job
from dagster._core.storage.upath_io_manager import UPathIOManagerBase


@pytest.mark.parametrize("json_data", [0, 0.0, [0, 1, 2], {"a": 0}, [{"a": 0}, {"b": 1}, {"c": 2}]])
def test_upath_io_manager_with_json(tmp_path: Path, json_data: Any):
    class JSONIOManager(UPathIOManagerBase):
        extension: str = ".json"

        def dump_to_path(self, obj: Any, path: UPath, context: OutputContext):
            with path.open("wb") as file:
                file.write(json.dumps(obj).encode())

        def load_from_path(self, path: UPath, context: InputContext) -> Any:
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


def test_upath_io_manager_multiple_partitions(tmp_path: Path):
    class DummyIOManager(UPathIOManagerBase):
        def dump_to_path(self, obj: str, path: UPath, context: OutputContext):
            return str(path)

        def load_from_path(self, path: UPath, context: InputContext) -> str:
            return str(path)

    @io_manager(config_schema={"base_path": Field(str, is_required=False)})
    def dummy_io_manager(init_context: InitResourceContext):
        base_path = UPath(
            init_context.resource_config.get("base_path", init_context.instance.storage_directory())
        )
        return DummyIOManager(base_path=base_path)

    io_manager_def = dummy_io_manager.configured({"base_path": str(tmp_path)})
    upstream_partitions_def = HourlyPartitionsDefinition(start_date="2020-01-01-00:00")
    downstream_partitions_def = DailyPartitionsDefinition(start_date="2020-01-01")

    @asset(partitions_def=upstream_partitions_def)
    def upstream_asset(context: OpExecutionContext) -> str:
        return context.partition_key

    @asset(
        partitions_def=downstream_partitions_def,
    )
    def downstream_asset(context: OpExecutionContext, upstream_asset: List[str]) -> List[str]:
        return upstream_asset

    # period = pendulum.period(pendulum.DateTime(2022, 1, 1), pendulum.DateTime(2022, 1, 2))
    #
    # upstream_asset_datas = []
    # for dt in period.range("hours", amount=24):
    #     result = materialize([upstream_asset], partition_key=dt.strftime(upstream_partitions_def.fmt), resources={
    #         "io_manager": io_manager_def
    #     })
    #     upstream_asset_datas.append(result._get_output_for_handle("upstream_asset", "result"))

    result = materialize(
        [*upstream_asset.to_source_assets(), downstream_asset],
        partition_key="2022-01-01",
        resources={"io_manager": io_manager_def},
    )
    downstream_asset_data = result._get_output_for_handle("downstream_asset", "result")
    assert len(downstream_asset_data) == 24, "downstream day should map to upstream 24 hours"
    # assert downstream_asset_data == upstream_asset_datas
