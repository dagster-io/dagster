import warnings
from typing import List, Union

import pytest
from dagster import (
    AssetExecutionContext,
    AssetKey,
    AssetsDefinition,
    DailyPartitionsDefinition,
    OpExecutionContext,
    asset,
    job,
    materialize,
    op,
)
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.decorators.asset_decorator import multi_asset
from dagster._core.definitions.partition import StaticPartitionsDefinition
from dagster._core.storage.io_manager import IOManager
from dagster._core.storage.tags import (
    ASSET_PARTITION_RANGE_END_TAG,
    ASSET_PARTITION_RANGE_START_TAG,
)


def test_base_asset_execution_context() -> None:
    called = {"yup": False}

    @asset
    def an_asset(context: AssetExecutionContext):
        assert isinstance(context, AssetExecutionContext)
        called["yup"] = True

    assert materialize([an_asset]).success
    assert called["yup"]


def test_isinstance_op_execution_context_asset_execution_context() -> None:
    called = {"yup": False}

    @asset
    def an_asset(context: AssetExecutionContext):
        # we make this work for backwards compat
        assert isinstance(context, OpExecutionContext)
        assert type(context) is AssetExecutionContext
        called["yup"] = True

    assert materialize([an_asset]).success
    assert called["yup"]


def test_op_gets_actual_op_execution_context() -> None:
    called = {"yup": False}

    @op
    def an_op(context: OpExecutionContext):
        # we make this work for backwards compat
        assert isinstance(context, OpExecutionContext)
        assert type(context) is OpExecutionContext
        called["yup"] = True

    @job
    def a_job():
        an_op()

    assert a_job.execute_in_process().success
    assert called["yup"]


def test_run_id_in_asset_execution_context() -> None:
    called = {"yup": False}

    @asset
    def an_asset(context: AssetExecutionContext):
        # we make this work for backwards compat
        assert isinstance(context, OpExecutionContext)
        assert type(context) is AssetExecutionContext
        assert context.run_id
        called["yup"] = True

    assert materialize([an_asset]).success
    assert called["yup"]


def test_basic_static_partitioning() -> None:
    called = {"yup": False}

    @asset(partitions_def=StaticPartitionsDefinition(["foo", "bar"]))
    def a_partitioned_asset(context: AssetExecutionContext):
        assert context.partition_key_range.start == "bar"
        assert context.partition_key_range.end == "bar"
        called["yup"] = True

    assert materialize([a_partitioned_asset], partition_key="bar").success
    assert called["yup"]


# neither our python apis nor our default i/o manager support support partition ranges
# so I am forced to write this helper 😐
def materialize_single_run_with_partition_key_range(
    assets_def: Union[AssetsDefinition, List[AssetsDefinition]], start: str, end: str
):
    # our default io manager does not handle partition ranges
    class DevNullIOManager(IOManager):
        def handle_output(self, context, obj) -> None:
            ...

        def load_input(self, context) -> None:
            ...

    return materialize(
        [assets_def] if isinstance(assets_def, AssetsDefinition) else assets_def,
        tags={
            ASSET_PARTITION_RANGE_START_TAG: start,
            ASSET_PARTITION_RANGE_END_TAG: end,
        },
        resources={"io_manager": DevNullIOManager()},
    )


def test_basic_daily_partitioning() -> None:
    called = {"yup": False}

    @asset(partitions_def=DailyPartitionsDefinition(start_date="2020-01-01", end_date="2020-01-03"))
    def a_partitioned_asset(context: AssetExecutionContext):
        assert context.partition_key_range.start == "2020-01-01"
        assert context.partition_key_range.end == "2020-01-02"
        called["yup"] = True

    assert materialize_single_run_with_partition_key_range(
        a_partitioned_asset, start="2020-01-01", end="2020-01-02"
    ).success
    assert called["yup"]


def test_basic_daily_partitioning_two_assets() -> None:
    called = {"upstream": False, "downstream": False}
    partitions_def = DailyPartitionsDefinition(start_date="2020-01-01", end_date="2020-01-03")

    @asset(partitions_def=partitions_def)
    def upstream(context: AssetExecutionContext):
        assert context.partition_key_range.start == "2020-01-01"
        assert context.partition_key_range.end == "2020-01-02"
        called[context.asset_key.to_user_string()] = True

    @asset(deps=[upstream], partitions_def=partitions_def)
    def downstream(context: AssetExecutionContext):
        assert context.partition_key_range.start == "2020-01-01"
        assert context.partition_key_range.end == "2020-01-02"
        called[context.asset_key.to_user_string()] = True

    assert materialize_single_run_with_partition_key_range(
        [upstream, downstream], start="2020-01-01", end="2020-01-02"
    ).success

    assert called["upstream"]
    assert called["downstream"]


def test_basic_daily_partitioning_multi_asset() -> None:
    partitions_def = DailyPartitionsDefinition(start_date="2020-01-01", end_date="2020-01-03")
    called = {"yup": False}

    @multi_asset(
        specs=[AssetSpec("asset_one"), AssetSpec("asset_two")], partitions_def=partitions_def
    )
    def a_multi_asset(context: AssetExecutionContext):
        assert context.selected_asset_keys == {AssetKey("asset_one"), AssetKey("asset_two")}
        assert context.partition_key_range.start == "2020-01-01"
        assert context.partition_key_range.end == "2020-01-02"
        called["yup"] = True

    assert materialize_single_run_with_partition_key_range(
        a_multi_asset, start="2020-01-01", end="2020-01-02"
    ).success
    assert called["yup"]


def test_handle_partition_mapping() -> None:
    ...
    # TODO
    # daily_partitions_def = DailyPartitionsDefinition(start_date="2020-01-01", end_date="2020-03-01")

    # @asset(partitions_def=daily_partitions_def)
    # def daily_partitioned_asset(context: AssetExecutionContext):
    #     raise Exception("not executed")
    #     assert context.partition_key_range.start == "2020-01-01"
    #     assert context.partition_key_range.end == "2020-01-02"

    # monthly_partitions_def = MonthlyPartitionsDefinition(start_date="2020-01-01", end_date="2020-03-01")

    # @asset(partitions_def=monthly_partitions_def, deps=[daily_partitioned_asset])
    # def downstream_monthly_partitioned_asset(context: AssetExecutionContext):
    #     print(context.partition_key_range_for_asset_key(AssetKey("daily_partitioned_asset")))

    # materialize_single_run_with_partition_key_range([downstream_monthly_partitioned_asset], start="2020-01-01", end="2020-02-01")


def test_time_window_methods() -> None:
    called = {"yup": False}

    @asset(partitions_def=DailyPartitionsDefinition(start_date="2020-01-01", end_date="2020-01-03"))
    def a_partitioned_asset(context: AssetExecutionContext):
        ptw = context.op_execution_context.partition_time_window
        assert ptw.start.day == 1
        assert ptw.end.day == 2
        called["yup"] = True

    # time windows do not work on ranges
    # assert materialize_single_run_with_partition_key_range(
    #     a_partitioned_asset, start="2020-01-01", end="2020-01-01"
    # ).success
    assert materialize([a_partitioned_asset], partition_key="2020-01-01").success
    assert called["yup"]


@pytest.fixture
def error_on_warning():
    # I couldn't get these to fire otherwise ¯\_(ツ)_/¯
    # turn off any outer warnings filters, e.g. ignores that are set in pyproject.toml
    warnings.resetwarnings()
    warnings.filterwarnings("error")


def test_io_manager_oriented_warning(error_on_warning) -> None:
    called = {"yup": False}

    @asset(partitions_def=DailyPartitionsDefinition(start_date="2020-01-01", end_date="2020-01-03"))
    def a_partitioned_asset(context: AssetExecutionContext):
        with pytest.raises(DeprecationWarning) as exc_info:
            assert context.asset_partition_key_for_output("result") == "2020-01-01"

        expected = (
            "AssetExecutionContext.asset_partition_key_for_output is deprecated and will be removed"
            " in 1.7. You have called method asset_partition_key_for_output on"
            " AssetExecutionContext that is oriented around I/O managers. If you not using I/O"
            " managers we suggest you use partition_key_range instead. If you are using I/O"
            " managers the method still exists at"
            " op_execution_context.asset_partition_key_for_output."
        )

        assert expected in str(exc_info.value)

        called["yup"] = True

    assert materialize([a_partitioned_asset], partition_key="2020-01-01").success
    assert called["yup"]


def test_generic_op_execution_context_warning(error_on_warning) -> None:
    called = {"yup": False}

    @asset
    def an_asset(context: AssetExecutionContext):
        assert isinstance(context, AssetExecutionContext)

        with pytest.raises(DeprecationWarning) as exc_info:
            assert context.file_manager is None

        expected = (
            "AssetExecutionContext.file_manager is deprecated and will be removed in 1.7. You have"
            " called the deprecated method file_manager on AssetExecutionContext. Use the"
            " underlying OpExecutionContext instead by calling op_execution_context.file_manager."
        )

        assert expected in str(exc_info.value)

        called["yup"] = True

    assert materialize([an_asset]).success
    assert called["yup"]


def test_alternative_available_warning(error_on_warning) -> None:
    called = {"yup": False}

    @asset
    def an_asset(context: AssetExecutionContext):
        assert isinstance(context, AssetExecutionContext)

        with pytest.raises(DeprecationWarning) as exc_info:
            assert context.has_tag("foobar") is False

        expected = (
            "AssetExecutionContext.has_tag is deprecated and will be removed in 1.7. "
            "Instead use dagster_run.has_tag instead."
        )
        assert expected in str(exc_info.value)

        called["yup"] = True

    assert materialize([an_asset]).success
    assert called["yup"]
