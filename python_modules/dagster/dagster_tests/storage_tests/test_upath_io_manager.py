import json
import pickle
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

import pytest
from dagster import (
    AllPartitionMapping,
    AssetIn,
    DagsterType,
    DailyPartitionsDefinition,
    Field,
    HourlyPartitionsDefinition,
    InitResourceContext,
    InputContext,
    MetadataValue,
    OpExecutionContext,
    OutputContext,
    StaticPartitionsDefinition,
    asset,
    build_init_resource_context,
    build_input_context,
    build_output_context,
    io_manager,
    materialize,
)
from dagster._check import CheckError
from dagster._core.definitions import build_assets_job
from dagster._core.storage.io_manager import IOManagerDefinition
from dagster._core.storage.upath_io_manager import UPathIOManager
from upath import UPath


class DummyIOManager(UPathIOManager):
    """This IOManager simply outputs the object path without loading or writing anything."""

    def dump_to_path(self, context: OutputContext, obj: str, path: UPath):
        pass

    def load_from_path(self, context: InputContext, path: UPath) -> str:
        return str(path)


@pytest.fixture
def dummy_io_manager(tmp_path: Path) -> IOManagerDefinition:
    @io_manager(config_schema={"base_path": Field(str, is_required=False)})
    def dummy_io_manager(init_context: InitResourceContext):
        assert init_context.instance is not None
        base_path = UPath(
            init_context.resource_config.get("base_path", init_context.instance.storage_directory())
        )
        return DummyIOManager(base_path=cast(UPath, base_path))

    io_manager_def = dummy_io_manager.configured({"base_path": str(tmp_path)})

    return io_manager_def


@pytest.fixture
def start():
    return datetime(2022, 1, 1)


@pytest.fixture
def hourly(start: datetime):
    return HourlyPartitionsDefinition(start_date=f"{start:%Y-%m-%d-%H:%M}")


@pytest.fixture
def daily(start: datetime):
    return DailyPartitionsDefinition(start_date=f"{start:%Y-%m-%d}")


@pytest.mark.parametrize("json_data", [0, 0.0, [0, 1, 2], {"a": 0}, [{"a": 0}, {"b": 1}, {"c": 2}]])
def test_upath_io_manager_with_json(tmp_path: Path, json_data: Any):
    class JSONIOManager(UPathIOManager):
        extension: str = ".json"

        def dump_to_path(self, context: OutputContext, obj: Any, path: UPath):
            with path.open("w") as file:
                json.dump(obj, file)

        def load_from_path(self, context: InputContext, path: UPath) -> Any:
            with path.open("r") as file:
                return json.load(file)

    @io_manager(config_schema={"base_path": Field(str, is_required=False)})
    def json_io_manager(init_context: InitResourceContext):
        assert init_context.instance is not None
        base_path = UPath(
            init_context.resource_config.get("base_path", init_context.instance.storage_directory())
        )
        return JSONIOManager(base_path=cast(UPath, base_path))

    manager = json_io_manager(build_init_resource_context(config={"base_path": str(tmp_path)}))
    context = build_output_context(
        name="abc",
        step_key="123",
        dagster_type=DagsterType(type_check_fn=lambda _, value: True, name="any", typing_type=Any),
    )
    manager.handle_output(context, json_data)

    with manager._get_path(context).open("r") as file:  # pylint: disable=W0212
        assert json.load(file) == json_data

    context = build_input_context(
        name="abc",
        upstream_output=context,
        dagster_type=DagsterType(type_check_fn=lambda _, value: True, name="any", typing_type=Any),
    )
    assert manager.load_input(context) == json_data


def test_upath_io_manager_with_non_any_type_annotation(tmp_path: Path):
    class MyIOManager(UPathIOManager):
        def dump_to_path(self, context: OutputContext, obj: List, path: UPath):
            with path.open("wb") as file:
                pickle.dump(obj, file)

        def load_from_path(self, context: InputContext, path: UPath) -> List:
            with path.open("rb") as file:
                return pickle.load(file)

    @io_manager(config_schema={"base_path": Field(str, is_required=False)})
    def my_io_manager(init_context: InitResourceContext):
        assert init_context.instance is not None
        base_path = UPath(
            init_context.resource_config.get("base_path", init_context.instance.storage_directory())
        )
        return MyIOManager(base_path=cast(UPath, base_path))

    manager = my_io_manager(build_init_resource_context(config={"base_path": str(tmp_path)}))

    data = [0, 1, "a", "b"]

    context = build_output_context(
        name="abc",
        step_key="123",
        dagster_type=DagsterType(
            type_check_fn=lambda _, value: isinstance(value, list),
            name="List",
            typing_type=list,
        ),
    )
    manager.handle_output(context, data)

    with manager._get_path(context).open("rb") as file:  # pylint: disable=W0212
        assert data == pickle.load(file)

    context = build_input_context(
        name="abc",
        upstream_output=context,
        dagster_type=DagsterType(
            type_check_fn=lambda _, value: isinstance(value, list),
            name="List",
            typing_type=list,
        ),
    )
    assert manager.load_input(context) == data


def test_upath_io_manager_multiple_time_partitions(
    daily: DailyPartitionsDefinition,
    hourly: HourlyPartitionsDefinition,
    start: datetime,
    dummy_io_manager: DummyIOManager,
):
    @asset(partitions_def=hourly)
    def upstream_asset(context: OpExecutionContext) -> str:
        return context.partition_key

    @asset(
        partitions_def=daily,
    )
    def downstream_asset(upstream_asset: Dict[str, str]) -> Dict[str, str]:
        return upstream_asset

    result = materialize(
        [*upstream_asset.to_source_assets(), downstream_asset],
        partition_key=start.strftime(daily.fmt),
        resources={"io_manager": dummy_io_manager},
    )
    downstream_asset_data = result.output_for_node("downstream_asset", "result")
    assert len(downstream_asset_data) == 24, "downstream day should map to upstream 24 hours"


def test_upath_io_manager_multiple_static_partitions(dummy_io_manager: DummyIOManager):
    upstream_partitions_def = StaticPartitionsDefinition(["A", "B"])

    @asset(partitions_def=upstream_partitions_def)
    def upstream_asset(context: OpExecutionContext) -> str:
        return context.partition_key

    @asset(ins={"upstream_asset": AssetIn(partition_mapping=AllPartitionMapping())})
    def downstream_asset(upstream_asset: Dict[str, str]) -> Dict[str, str]:
        return upstream_asset

    my_job = build_assets_job(
        "my_job",
        assets=[upstream_asset, downstream_asset],
        resource_defs={"io_manager": dummy_io_manager},  # type: ignore[dict-item]
    )
    result = my_job.execute_in_process(partition_key="A")
    downstream_asset_data = result.output_for_node("downstream_asset", "result")
    assert set(downstream_asset_data.keys()) == {"A", "B"}


def test_upath_io_manager_static_partitions_with_dot():
    partitions_def = StaticPartitionsDefinition(["0.0-to-1.0", "1.0-to-2.0"])

    dumped_path: Optional[UPath] = None

    class TrackingIOManager(UPathIOManager):
        def dump_to_path(self, context: OutputContext, obj: List, path: UPath):
            nonlocal dumped_path
            dumped_path = path

        def load_from_path(self, context: InputContext, path: UPath):
            pass

    @io_manager(config_schema={"base_path": Field(str, is_required=False)})
    def tracking_io_manager(init_context: InitResourceContext):
        assert init_context.instance is not None
        base_path = UPath(
            init_context.resource_config.get("base_path", init_context.instance.storage_directory())
        )
        return TrackingIOManager(base_path=base_path)

    @asset(partitions_def=partitions_def)
    def my_asset(context: OpExecutionContext) -> str:
        return context.partition_key

    my_job = build_assets_job(
        "my_job",
        assets=[my_asset],
        resource_defs={"io_manager": tracking_io_manager},
    )
    my_job.execute_in_process(partition_key="0.0-to-1.0")

    assert dumped_path is not None
    assert "0.0-to-1.0" == dumped_path.name


def test_upath_io_manager_with_extension_static_partitions_with_dot():
    partitions_def = StaticPartitionsDefinition(["0.0-to-1.0", "1.0-to-2.0"])

    dumped_path: Optional[UPath] = None

    class TrackingIOManager(UPathIOManager):
        extension = ".ext"

        def dump_to_path(self, context: OutputContext, obj: List, path: UPath):
            nonlocal dumped_path
            dumped_path = path

        def load_from_path(self, context: InputContext, path: UPath):
            pass

    @io_manager(config_schema={"base_path": Field(str, is_required=False)})
    def tracking_io_manager(init_context: InitResourceContext):
        assert init_context.instance is not None
        base_path = UPath(
            init_context.resource_config.get("base_path", init_context.instance.storage_directory())
        )
        return TrackingIOManager(base_path=base_path)

    @asset(partitions_def=partitions_def)
    def my_asset(context: OpExecutionContext) -> str:
        return context.partition_key

    my_job = build_assets_job(
        "my_job",
        assets=[my_asset],
        resource_defs={"io_manager": tracking_io_manager},
    )
    my_job.execute_in_process(partition_key="0.0-to-1.0")

    assert dumped_path is not None
    assert "0.0-to-1.0.ext" == dumped_path.name
    assert ".ext" == dumped_path.suffix


def test_partitioned_io_manager_preserves_single_partition_dependency(
    daily: DailyPartitionsDefinition, dummy_io_manager: DummyIOManager
):
    @asset(partitions_def=daily)
    def upstream_asset():
        return 42

    @asset(partitions_def=daily)
    def daily_asset(upstream_asset: str):
        return upstream_asset

    result = materialize(
        [upstream_asset, daily_asset],
        partition_key="2022-01-01",
        resources={"io_manager": dummy_io_manager},
    )
    assert result.output_for_node("daily_asset").endswith("2022-01-01")


def test_user_forgot_dict_type_annotation_for_multiple_partitions(
    start: datetime,
    daily: DailyPartitionsDefinition,
    hourly: HourlyPartitionsDefinition,
    dummy_io_manager: DummyIOManager,
):
    @asset(partitions_def=hourly)
    def upstream_asset(context: OpExecutionContext) -> str:
        return context.partition_key

    @asset(partitions_def=daily)
    def downstream_asset(upstream_asset: str) -> str:
        return upstream_asset

    with pytest.raises(
        CheckError,
        match="the type annotation on the op input is not a dict",
    ):
        materialize(
            [*upstream_asset.to_source_assets(), downstream_asset],
            partition_key=start.strftime(daily.fmt),
            resources={"io_manager": dummy_io_manager},
        )


def test_skip_type_check_for_multiple_partitions_with_no_type_annotation(
    start: datetime,
    daily: DailyPartitionsDefinition,
    hourly: HourlyPartitionsDefinition,
    dummy_io_manager: DummyIOManager,
):
    @asset(partitions_def=hourly)
    def upstream_asset(context: OpExecutionContext) -> str:
        return context.partition_key

    @asset(
        partitions_def=daily,
    )
    def downstream_asset(upstream_asset):
        return upstream_asset

    result = materialize(
        [*upstream_asset.to_source_assets(), downstream_asset],
        partition_key=start.strftime(daily.fmt),
        resources={"io_manager": dummy_io_manager},
    )
    assert isinstance(result.output_for_node("downstream_asset"), dict)


def test_skip_type_check_for_multiple_partitions_with_any_type(
    start: datetime,
    daily: DailyPartitionsDefinition,
    hourly: HourlyPartitionsDefinition,
    dummy_io_manager: DummyIOManager,
):
    @asset(partitions_def=hourly)
    def upstream_asset(context: OpExecutionContext) -> str:
        return context.partition_key

    @asset(
        partitions_def=daily,
    )
    def downstream_asset(upstream_asset: Any):
        return upstream_asset

    result = materialize(
        [*upstream_asset.to_source_assets(), downstream_asset],
        partition_key=start.strftime(daily.fmt),
        resources={"io_manager": dummy_io_manager},
    )
    assert isinstance(result.output_for_node("downstream_asset"), dict)


@pytest.mark.parametrize("json_data", [0, 0.0, [0, 1, 2], {"a": 0}, [{"a": 0}, {"b": 1}, {"c": 2}]])
def test_upath_io_manager_custom_metadata(tmp_path: Path, json_data: Any):
    def get_length(obj: Any) -> int:
        try:
            return len(obj)
        except TypeError:
            return 0

    class MetadataIOManager(UPathIOManager):
        def dump_to_path(self, context: OutputContext, obj: Any, path: UPath):
            return

        def load_from_path(self, context: InputContext, path: UPath) -> Any:
            return

        def get_metadata(
            self, context: OutputContext, obj: Any  # pylint: disable=unused-argument
        ) -> Dict[str, MetadataValue]:
            return {"length": MetadataValue.int(get_length(obj))}

    @io_manager(config_schema={"base_path": Field(str, is_required=False)})
    def metadata_io_manager(init_context: InitResourceContext):
        assert init_context.instance is not None
        base_path = UPath(
            init_context.resource_config.get("base_path", init_context.instance.storage_directory())
        )
        return MetadataIOManager(base_path=cast(UPath, base_path))

    manager = metadata_io_manager(build_init_resource_context(config={"base_path": str(tmp_path)}))

    @asset
    def my_asset() -> Any:
        return json_data

    result = materialize(
        [my_asset],
        resources={"io_manager": manager},
    )
    handled_output_events = list(filter(lambda evt: evt.is_handled_output, result.all_node_events))

    assert handled_output_events[0].event_specific_data.metadata_entries[  # type: ignore[index,union-attr]
        1
    ].value.value == get_length(
        json_data
    )
