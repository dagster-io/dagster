import inspect
import json
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, cast

import dagster as dg
import fsspec
import pytest
from dagster import (
    AssetExecutionContext,
    InitResourceContext,
    InputContext,
    MetadataValue,
    OpExecutionContext,
    OutputContext,
)
from dagster._core.definitions.partitions.definition import (
    DailyPartitionsDefinition,
    HourlyPartitionsDefinition,
)
from dagster._core.events import HandledOutputData
from fsspec.asyn import AsyncFileSystem
from pydantic import (
    Field as PydanticField,
    PrivateAttr,
)
from upath import UPath


class DummyIOManager(dg.UPathIOManager):
    """This IOManager simply outputs the object path without loading or writing anything."""

    def dump_to_path(self, context: OutputContext, obj: str, path: UPath):
        pass

    def load_from_path(self, context: InputContext, path: UPath) -> str:
        return str(path)


class PickleIOManager(dg.UPathIOManager):
    def dump_to_path(self, context: OutputContext, obj: list, path: UPath):
        with path.open("wb") as file:
            pickle.dump(obj, file)

    def load_from_path(self, context: InputContext, path: UPath) -> list:
        with path.open("rb") as file:
            return pickle.load(file)


@pytest.fixture
def dummy_io_manager(tmp_path: Path) -> dg.IOManagerDefinition:
    @dg.io_manager(config_schema={"base_path": dg.Field(str, is_required=False)})
    def dummy_io_manager(init_context: InitResourceContext):
        assert init_context.instance is not None
        base_path = UPath(
            init_context.resource_config.get("base_path", init_context.instance.storage_directory())
        )
        return DummyIOManager(base_path=cast("UPath", base_path))

    io_manager_def = dummy_io_manager.configured({"base_path": str(tmp_path)})

    return io_manager_def


@pytest.fixture
def start():
    return datetime(2022, 1, 1)


@pytest.fixture
def hourly(start: datetime):
    return dg.HourlyPartitionsDefinition(start_date=f"{start:%Y-%m-%d-%H:%M}")


@pytest.fixture
def daily(start: datetime):
    return dg.DailyPartitionsDefinition(start_date=f"{start:%Y-%m-%d}")


@pytest.mark.parametrize("json_data", [0, 0.0, [0, 1, 2], {"a": 0}, [{"a": 0}, {"b": 1}, {"c": 2}]])
def test_upath_io_manager_with_json(tmp_path: Path, json_data: Any):
    class JSONIOManager(dg.UPathIOManager):
        extension: str = ".json"  # pyright: ignore[reportIncompatibleVariableOverride]

        def dump_to_path(self, context: OutputContext, obj: Any, path: UPath):
            with path.open("w") as file:
                json.dump(obj, file)

        def load_from_path(self, context: InputContext, path: UPath) -> Any:
            with path.open("r") as file:
                return json.load(file)

    @dg.io_manager(config_schema={"base_path": dg.Field(str, is_required=False)})
    def json_io_manager(init_context: InitResourceContext):
        assert init_context.instance is not None
        base_path = UPath(
            init_context.resource_config.get("base_path", init_context.instance.storage_directory())
        )
        return JSONIOManager(base_path=cast("UPath", base_path))

    manager = json_io_manager(dg.build_init_resource_context(config={"base_path": str(tmp_path)}))
    context = dg.build_output_context(
        name="abc",
        step_key="123",
        dagster_type=dg.DagsterType(
            type_check_fn=lambda _, value: True, name="any", typing_type=Any
        ),
    )
    manager.handle_output(context, json_data)

    with manager._get_path(context).open("r") as file:  # noqa: SLF001
        assert json.load(file) == json_data

    context = dg.build_input_context(
        name="abc",
        upstream_output=context,
        dagster_type=dg.DagsterType(
            type_check_fn=lambda _, value: True, name="any", typing_type=Any
        ),
    )
    assert manager.load_input(context) == json_data


def test_upath_io_manager_with_non_any_type_annotation(tmp_path: Path):
    class MyIOManager(dg.UPathIOManager):
        def dump_to_path(self, context: OutputContext, obj: list, path: UPath):
            with path.open("wb") as file:
                pickle.dump(obj, file)

        def load_from_path(self, context: InputContext, path: UPath) -> list:
            with path.open("rb") as file:
                return pickle.load(file)

    @dg.io_manager(config_schema={"base_path": dg.Field(str, is_required=False)})
    def my_io_manager(init_context: InitResourceContext):
        assert init_context.instance is not None
        base_path = UPath(
            init_context.resource_config.get("base_path", init_context.instance.storage_directory())
        )
        return MyIOManager(base_path=cast("UPath", base_path))

    manager = my_io_manager(dg.build_init_resource_context(config={"base_path": str(tmp_path)}))

    data = [0, 1, "a", "b"]

    context = dg.build_output_context(
        name="abc",
        step_key="123",
        dagster_type=dg.DagsterType(
            type_check_fn=lambda _, value: isinstance(value, list),
            name="List",
            typing_type=list,
        ),
    )
    manager.handle_output(context, data)

    with manager._get_path(context).open("rb") as file:  # noqa: SLF001
        assert data == pickle.load(file)

    context = dg.build_input_context(
        name="abc",
        upstream_output=context,
        dagster_type=dg.DagsterType(
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
    @dg.asset(partitions_def=hourly)
    def upstream_asset(context: AssetExecutionContext) -> str:
        return context.partition_key

    @dg.asset(
        partitions_def=daily,
    )
    def downstream_asset(upstream_asset: dict[str, str]) -> dict[str, str]:
        return upstream_asset

    result = dg.materialize(
        [*upstream_asset.to_source_assets(), downstream_asset],
        partition_key=start.strftime(daily.fmt),
        resources={"io_manager": dummy_io_manager},
    )
    downstream_asset_data = result.output_for_node("downstream_asset", "result")
    assert len(downstream_asset_data) == 24, "downstream day should map to upstream 24 hours"


def test_upath_io_manager_multiple_static_partitions(dummy_io_manager: DummyIOManager):
    upstream_partitions_def = dg.StaticPartitionsDefinition(["A", "B"])

    @dg.asset(partitions_def=upstream_partitions_def)
    def upstream_asset(context: AssetExecutionContext) -> str:
        return context.partition_key

    @dg.asset(ins={"upstream_asset": dg.AssetIn(partition_mapping=dg.AllPartitionMapping())})
    def downstream_asset(upstream_asset: dict[str, str]) -> dict[str, str]:
        return upstream_asset

    result = dg.materialize(
        assets=[upstream_asset, downstream_asset],
        resources={"io_manager": dummy_io_manager},
        partition_key="A",
    )
    downstream_asset_data = result.output_for_node("downstream_asset", "result")
    assert set(downstream_asset_data.keys()) == {"A", "B"}


def test_upath_io_manager_load_multiple_inputs(dummy_io_manager: DummyIOManager):
    upstream_partitions_def = dg.MultiPartitionsDefinition(
        {
            "a": dg.StaticPartitionsDefinition(["a", "b"]),
            "1": dg.StaticPartitionsDefinition(["1"]),
        }
    )

    @dg.asset(partitions_def=upstream_partitions_def)
    def upstream_asset(context: AssetExecutionContext) -> str:
        return context.partition_key

    @dg.asset
    def downstream_asset(upstream_asset):
        return upstream_asset

    result = dg.materialize(
        assets=[upstream_asset, downstream_asset],
        resources={"io_manager": dummy_io_manager},
        partition_key=dg.MultiPartitionKey({"a": "a", "1": "1"}),
    )
    downstream_asset_data = result.output_for_node("downstream_asset", "result")
    assert set(downstream_asset_data.keys()) == {"1|a", "1|b"}


def test_upath_io_manager_multiple_partitions_from_non_partitioned_run(tmp_path: Path):
    my_io_manager = PickleIOManager(UPath(tmp_path))

    upstream_partitions_def = dg.StaticPartitionsDefinition(["A", "B"])

    @dg.asset(partitions_def=upstream_partitions_def, io_manager_def=my_io_manager)
    def upstream_asset(context: AssetExecutionContext) -> str:
        return context.partition_key

    @dg.asset(
        ins={"upstream_asset": dg.AssetIn(partition_mapping=dg.AllPartitionMapping())},
        io_manager_def=my_io_manager,
    )
    def downstream_asset(upstream_asset: dict[str, str]) -> dict[str, str]:
        return upstream_asset

    for partition_key in ["A", "B"]:
        dg.materialize(
            [upstream_asset],
            partition_key=partition_key,
        )

    result = dg.materialize([upstream_asset.to_source_asset(), downstream_asset])

    downstream_asset_data = result.output_for_node("downstream_asset", "result")
    assert set(downstream_asset_data.keys()) == {"A", "B"}


def test_upath_io_manager_static_partitions_with_dot():
    partitions_def = dg.StaticPartitionsDefinition(["0.0-to-1.0", "1.0-to-2.0"])

    dumped_path: UPath | None = None

    class TrackingIOManager(dg.UPathIOManager):
        def dump_to_path(self, context: OutputContext, obj: list, path: UPath):
            nonlocal dumped_path
            dumped_path = path

        def load_from_path(self, context: InputContext, path: UPath):
            pass

    @dg.io_manager(config_schema={"base_path": dg.Field(str, is_required=False)})
    def tracking_io_manager(init_context: InitResourceContext):
        assert init_context.instance is not None
        base_path = UPath(
            init_context.resource_config.get("base_path", init_context.instance.storage_directory())
        )
        return TrackingIOManager(base_path=base_path)

    @dg.asset(partitions_def=partitions_def)
    def my_asset(context: AssetExecutionContext) -> str:
        return context.partition_key

    dg.materialize(
        assets=[my_asset],
        resources={"io_manager": tracking_io_manager},
        partition_key="0.0-to-1.0",
    )

    assert dumped_path is not None
    assert "0.0-to-1.0" == dumped_path.name


def test_upath_io_manager_with_extension_static_partitions_with_dot():
    partitions_def = dg.StaticPartitionsDefinition(["0.0-to-1.0", "1.0-to-2.0"])

    dumped_path: UPath | None = None

    class TrackingIOManager(dg.UPathIOManager):
        extension = ".ext"

        def dump_to_path(self, context: OutputContext, obj: list, path: UPath):
            nonlocal dumped_path
            dumped_path = path

        def load_from_path(self, context: InputContext, path: UPath):
            pass

    @dg.io_manager(config_schema={"base_path": dg.Field(str, is_required=False)})
    def tracking_io_manager(init_context: InitResourceContext):
        assert init_context.instance is not None
        base_path = UPath(
            init_context.resource_config.get("base_path", init_context.instance.storage_directory())
        )
        return TrackingIOManager(base_path=base_path)

    @dg.asset(partitions_def=partitions_def)
    def my_asset(context: AssetExecutionContext) -> str:
        return context.partition_key

    dg.materialize(
        assets=[my_asset],
        resources={"io_manager": tracking_io_manager},
        partition_key="0.0-to-1.0",
    )

    assert dumped_path is not None
    assert "0.0-to-1.0.ext" == dumped_path.name
    assert ".ext" == dumped_path.suffix


def test_partitioned_io_manager_preserves_single_partition_dependency(
    daily: DailyPartitionsDefinition, dummy_io_manager: DummyIOManager
):
    @dg.asset(partitions_def=daily)
    def upstream_asset():
        return 42

    @dg.asset(partitions_def=daily)
    def daily_asset(upstream_asset: str):
        return upstream_asset

    result = dg.materialize(
        [upstream_asset, daily_asset],
        partition_key="2022-01-01",
        resources={"io_manager": dummy_io_manager},
    )
    assert result.output_for_node("daily_asset").endswith("2022-01-01")


def test_skip_type_check_for_multiple_partitions_with_no_type_annotation(
    start: datetime,
    daily: DailyPartitionsDefinition,
    hourly: HourlyPartitionsDefinition,
    dummy_io_manager: DummyIOManager,
):
    @dg.asset(partitions_def=hourly)
    def upstream_asset(context: AssetExecutionContext) -> str:
        return context.partition_key

    @dg.asset(
        partitions_def=daily,
    )
    def downstream_asset(upstream_asset):
        return upstream_asset

    result = dg.materialize(
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
    @dg.asset(partitions_def=hourly)
    def upstream_asset(context: AssetExecutionContext) -> str:
        return context.partition_key

    @dg.asset(
        partitions_def=daily,
    )
    def downstream_asset(upstream_asset: Any):
        return upstream_asset

    result = dg.materialize(
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

    class MetadataIOManager(dg.UPathIOManager):
        def dump_to_path(self, context: OutputContext, obj: Any, path: UPath):
            return

        def load_from_path(self, context: InputContext, path: UPath) -> Any:
            return

        def get_metadata(self, context: OutputContext, obj: Any) -> dict[str, dg.MetadataValue]:
            return {"length": MetadataValue.int(get_length(obj))}

    @dg.io_manager(config_schema={"base_path": dg.Field(str, is_required=False)})
    def metadata_io_manager(init_context: InitResourceContext):
        assert init_context.instance is not None
        base_path = UPath(
            init_context.resource_config.get("base_path", init_context.instance.storage_directory())
        )
        return MetadataIOManager(base_path=cast("UPath", base_path))

    manager = metadata_io_manager(
        dg.build_init_resource_context(config={"base_path": str(tmp_path)})
    )

    @dg.asset
    def my_asset() -> Any:
        return json_data

    result = dg.materialize(
        [my_asset],
        resources={"io_manager": manager},
    )
    handled_output_data = next(
        iter(filter(lambda evt: evt.is_handled_output, result.all_node_events))
    ).event_specific_data
    assert isinstance(handled_output_data, HandledOutputData)
    assert handled_output_data.metadata["length"] == MetadataValue.int(get_length(json_data))


class AsyncJSONIOManager(dg.ConfigurableIOManager, dg.UPathIOManager):
    base_dir: str = PydanticField(None, description="Base directory for storing files.")  # type: ignore

    _base_path: UPath = PrivateAttr()

    def setup_for_execution(self, context: InitResourceContext) -> None:
        self._base_path = UPath(self.base_dir)

    def dump_to_path(self, context: OutputContext, obj: Any, path: UPath):
        with path.open("w") as file:
            json.dump(obj, file)

    async def load_from_path(self, context: InputContext, path: UPath) -> Any:
        fs = self.get_async_filesystem(path)

        if inspect.iscoroutinefunction(fs.open_async):
            # S3FileSystem has this interface
            file = await fs.open_async(str(path), "rb")
            data = await file.read()
        else:
            # AsyncLocalFileSystem has this interface
            async with fs.open_async(str(path), "rb") as file:
                data = await file.read()

        return json.loads(data)

    @staticmethod
    def get_async_filesystem(path: "Path") -> AsyncFileSystem:
        """A helper method, is useful inside an async `load_from_path`.
        The returned `fsspec` FileSystem will have async IO methods.
        https://filesystem-spec.readthedocs.io/en/latest/async.html.
        """
        import morefs.asyn_local

        if isinstance(path, UPath):
            so = path.fs.storage_options.copy()
            cls = type(path.fs)
            if cls is fsspec.implementations.local.LocalFileSystem:
                cls = morefs.asyn_local.AsyncLocalFileSystem
            so["asynchronous"] = True
            return cls(**so)
        elif isinstance(path, Path):
            return morefs.asyn_local.AsyncLocalFileSystem()
        else:
            raise dg.DagsterInvariantViolationError(
                f"Path type {type(path)} is not supported by the UPathIOManager"
            )


@pytest.mark.parametrize("json_data", [0, 0.0, [0, 1, 2], {"a": 0}, [{"a": 0}, {"b": 1}, {"c": 2}]])
def test_upath_io_manager_async_load_from_path(tmp_path: Path, json_data: Any):
    manager = AsyncJSONIOManager(base_dir=str(tmp_path))

    @dg.asset(io_manager_def=manager)
    def non_partitioned_asset():
        return json_data

    result = dg.materialize([non_partitioned_asset])

    assert result.output_for_node("non_partitioned_asset") == json_data

    @dg.asset(partitions_def=dg.StaticPartitionsDefinition(["a", "b"]), io_manager_def=manager)
    def partitioned_asset(context: OpExecutionContext):
        return context.partition_key

    result = dg.materialize([partitioned_asset], partition_key="a")

    assert result.output_for_node("partitioned_asset") == "a"


def test_upath_io_manager_async_multiple_time_partitions(
    tmp_path: Path,
    daily: DailyPartitionsDefinition,
    start: datetime,
):
    manager = AsyncJSONIOManager(base_dir=str(tmp_path))

    @dg.asset(partitions_def=daily, io_manager_def=manager)
    def upstream_asset(context: AssetExecutionContext) -> str:
        return context.partition_key

    @dg.asset(
        partitions_def=daily,
        io_manager_def=manager,
        ins={
            "upstream_asset": dg.AssetIn(
                partition_mapping=dg.TimeWindowPartitionMapping(start_offset=-1)
            )
        },
    )
    def downstream_asset(upstream_asset: dict[str, str]):
        return upstream_asset

    for days in range(2):
        dg.materialize(
            [upstream_asset],
            partition_key=(start + timedelta(days=days)).strftime(daily.fmt),
        )

    result = dg.materialize(
        [upstream_asset.to_source_asset(), downstream_asset],
        partition_key=(start + timedelta(days=1)).strftime(daily.fmt),
    )
    downstream_asset_data = result.output_for_node("downstream_asset", "result")
    assert len(downstream_asset_data) == 2, "downstream day should map to 2 upstream days"


def test_upath_io_manager_async_fail_on_missing_partitions(
    tmp_path: Path,
    daily: DailyPartitionsDefinition,
    start: datetime,
):
    manager = AsyncJSONIOManager(base_dir=str(tmp_path))

    @dg.asset(partitions_def=daily, io_manager_def=manager)
    def upstream_asset(context: AssetExecutionContext) -> str:
        return context.partition_key

    @dg.asset(
        partitions_def=daily,
        io_manager_def=manager,
        ins={
            "upstream_asset": dg.AssetIn(
                partition_mapping=dg.TimeWindowPartitionMapping(start_offset=-1)
            )
        },
    )
    def downstream_asset(upstream_asset: dict[str, str]):
        return upstream_asset

    dg.materialize(
        [upstream_asset],
        partition_key=start.strftime(daily.fmt),
    )

    with pytest.raises(RuntimeError):
        dg.materialize(
            [upstream_asset.to_source_asset(), downstream_asset],
            partition_key=(start + timedelta(days=4)).strftime(daily.fmt),
        )


def test_upath_io_manager_async_allow_missing_partitions(
    tmp_path: Path,
    daily: DailyPartitionsDefinition,
    start: datetime,
):
    manager = AsyncJSONIOManager(base_dir=str(tmp_path))

    @dg.asset(partitions_def=daily, io_manager_def=manager)
    def upstream_asset(context: AssetExecutionContext) -> str:
        return context.partition_key

    @dg.asset(
        partitions_def=daily,
        io_manager_def=manager,
        ins={
            "upstream_asset": dg.AssetIn(
                partition_mapping=dg.TimeWindowPartitionMapping(start_offset=-1),
                metadata={"allow_missing_partitions": True},
            )
        },
    )
    def downstream_asset(upstream_asset: dict[str, str]):
        return upstream_asset

    dg.materialize(
        [upstream_asset],
        partition_key=start.strftime(daily.fmt),
    )

    result = dg.materialize(
        [upstream_asset.to_source_asset(), downstream_asset],
        partition_key=(start + timedelta(days=1)).strftime(daily.fmt),
    )
    downstream_asset_data = result.output_for_node("downstream_asset", "result")
    assert len(downstream_asset_data) == 1, "1 partition should be missing"


def test_upath_can_transition_from_non_partitioned_to_partitioned(
    tmp_path: Path, daily: DailyPartitionsDefinition, start: datetime
):
    my_io_manager = PickleIOManager(UPath(tmp_path))

    @dg.asset
    def my_asset():  # type: ignore
        return 1

    assert dg.materialize([my_asset], resources={"io_manager": my_io_manager}).success

    @dg.asset(partitions_def=daily)
    def my_asset():
        return 1

    assert dg.materialize(
        [my_asset], resources={"io_manager": my_io_manager}, partition_key=start.strftime(daily.fmt)
    ).success
