from typing import List, Union

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
    #     assert context.partition_key_range.start == "2020-01-01"
    #     assert context.partition_key_range.end == "2020-01-02"

    # monthly_partitions_def = MonthlyPartitionsDefinition(start_date="2020-01-01", end_date="2020-03-01")

    # @asset(partitions_def=monthly_partitions_def, deps=[AssetDep(daily_partitioned_asset)])
    # def downstream_monthly_partitioned_asset(context: AssetExecutionContext):
    #     pass

    # materialize_single_run_with_partition_key_range([daily_partitioned_asset, downstream_monthly_partitioned_asset], start="2020-01-01", end="2020-02-01")
