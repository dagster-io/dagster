import math
import time

from dagster import DagsterInstance, Definitions, asset
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.partition import StaticPartitionsDefinition
from dagster._core.storage.branching.branching_io_manager import BranchingIOManager

from .utils import AssetBasedInMemoryIOManager, DefinitionsRunner

partitioning_scheme = StaticPartitionsDefinition(["A", "B", "C"])


@asset(partitions_def=partitioning_scheme)
def now_time():
    return int(math.floor(time.time() * 100))


def get_now_time_plus_N(N: int) -> AssetsDefinition:
    @asset(partitions_def=partitioning_scheme)
    def now_time_plus_N(now_time: int) -> int:
        return now_time + N

    return now_time_plus_N


@asset(partitions_def=partitioning_scheme)
def now_time_plus_20_after_plus_N(now_time_plus_N: int) -> int:
    return now_time_plus_N + 20


def test_asset_based_io_manager_with_partitions():
    @asset(partitions_def=partitioning_scheme)
    def plus_10(now_time):
        return now_time + 10

    io_manager = AssetBasedInMemoryIOManager()

    with DefinitionsRunner.ephemeral(
        Definitions(assets=[now_time, plus_10], resources={"io_manager": io_manager})
    ) as runner:
        partition_A_result = runner.materialize_all_assets(partition_key="A")
        partition_A_time_now = partition_A_result.output_for_node("now_time")
        assert isinstance(partition_A_time_now, int)

        assert not io_manager.has_value("now_time")  # no partition
        assert io_manager.has_value("now_time", partition_key="A")  # correct partition
        assert not io_manager.has_value("now_time", partition_key="B")  # incorrect partition

        assert io_manager.get_value("now_time", partition_key="A") == partition_A_time_now

        partition_B_result = runner.materialize_all_assets(partition_key="B")
        assert partition_B_result.success
        partition_B_time_now = partition_B_result.output_for_node("now_time")
        assert isinstance(partition_B_time_now, int)
        assert partition_B_time_now > partition_A_time_now

        assert not io_manager.has_value("now_time")  # no partition
        assert io_manager.has_value("now_time", partition_key="A")  # previously materialized
        assert io_manager.has_value("now_time", partition_key="B")  # just materialized

        assert io_manager.get_value("now_time", partition_key="A") == partition_A_time_now
        assert io_manager.get_value("now_time", partition_key="B") == partition_B_time_now

        assert runner.load_asset_value("now_time", partition_key="A") == partition_A_time_now
        assert runner.load_asset_value("now_time", partition_key="B") == partition_B_time_now


def test_basic_partitioning_workflow():
    now_time_plus_10 = get_now_time_plus_N(10)
    prod_io_manager = AssetBasedInMemoryIOManager()
    dev_io_manager = AssetBasedInMemoryIOManager()

    prod_defs = Definitions(
        assets=[now_time, now_time_plus_10, now_time_plus_20_after_plus_N],
        resources={
            "io_manager": prod_io_manager,
        },
    )

    dev_defs_t0 = Definitions(
        assets=[now_time, get_now_time_plus_N(10), now_time_plus_20_after_plus_N],
        resources={
            "io_manager": BranchingIOManager(
                parent_io_manager=prod_io_manager, branch_io_manager=dev_io_manager
            )
        },
    )

    dev_defs_t1 = Definitions(
        # at t1 the developer changes the business logic from +10 to +15
        assets=[now_time, get_now_time_plus_N(15), now_time_plus_20_after_plus_N],
        resources={
            "io_manager": BranchingIOManager(
                parent_io_manager=prod_io_manager, branch_io_manager=dev_io_manager
            )
        },
    )

    with DagsterInstance.ephemeral() as dev_instance, DagsterInstance.ephemeral() as prod_instance:
        # Simulate a full prod run. All partitions are full
        prod_runner = DefinitionsRunner(prod_defs, prod_instance)
        prod_runner.materialize_all_assets(partition_key="A")
        prod_runner.materialize_all_assets(partition_key="B")
        prod_runner.materialize_all_assets(partition_key="C")

        for asset_key in ["now_time", "now_time_plus_N", "now_time_plus_20_after_plus_N"]:
            for partition_key in ["A", "B", "C"]:
                assert prod_io_manager.has_value(asset_key, partition_key)

        prod_now_time_A = prod_runner.load_asset_value("now_time", partition_key="A")
        assert isinstance(prod_now_time_A, int)

        prod_now_time_B = prod_runner.load_asset_value("now_time", partition_key="B")
        assert isinstance(prod_now_time_B, int)

        # For partition A:
        # now_time => now_time_plus_N => now_time_plus_20_after_plus_N
        # At t(0), N = 10.
        #   - Materialize now_time_plus_N:A in dev.
        #   - Verify value was computed and it was not sourced from prod.

        #
        dev_runner_t0 = DefinitionsRunner(dev_defs_t0, dev_instance)

        # this is currently plus 10. Same value as prod
        dev_runner_t0.materialize_asset("now_time_plus_N", partition_key="A")

        # now_time still same. dev_runner_t0 is reading from prod
        assert dev_runner_t0.load_asset_value(
            "now_time", partition_key="A"
        ) == prod_runner.load_asset_value("now_time", partition_key="A")

        # note that this worked without having a value in the dev_io_manager, meaning it read from prod
        assert not dev_io_manager.has_value("now_time", partition_key="A")

        # now_time_plus_N has been remataerialized in the dev branch but still with same logic
        assert dev_runner_t0.load_asset_value(
            "now_time_plus_N", partition_key="A"
        ) == prod_runner.load_asset_value("now_time_plus_N", partition_key="A")

        assert (
            dev_runner_t0.load_asset_value("now_time_plus_N", partition_key="A")
            == prod_now_time_A + 10
        )

        # At t(1), N = 15 (equivalent to business logic updated).
        #   - Materialize now_time_plus_N:A in dev.
        #   - Verify value is updated in dev (to +15) but still the old value in prod
        #   - Materialize now_time_plus_20_after_plus_N:A in dev
        #   - Confirm that it read from dev (+15 and then +20)
        #   - Verify that old prod is still +10 +20

        # Now the programmer has updated business logic. This is represented by dev_runner_t1
        dev_runner_t1 = DefinitionsRunner(dev_defs_t1, dev_instance)

        # Now it is plus 15.
        dev_runner_t1.materialize_asset("now_time_plus_N", partition_key="A")

        # now time is still the same. dev_runner loading from prod
        assert dev_runner_t1.load_asset_value(
            "now_time", partition_key="A"
        ) == prod_runner.load_asset_value("now_time", partition_key="A")

        # branch io manager has new value. parent does not
        assert dev_runner_t1.load_asset_value(
            "now_time_plus_N", partition_key="A"
        ) != prod_runner.load_asset_value("now_time_plus_N", partition_key="A")

        # we can also verify that values are different against the i/o managers directly
        assert dev_io_manager.get_value(
            "now_time_plus_N", partition_key="A"
        ) != prod_io_manager.get_value("now_time_plus_N", partition_key="A")

        # dev i/o still has never materialized now_time:A. has read from prod
        assert not dev_io_manager.has_value("now_time", partition_key="A")

        # we have only materialized partition A. B and C untouched
        assert not dev_io_manager.has_value("now_time_plus_N", partition_key="B")
        assert not dev_io_manager.has_value("now_time_plus_N", partition_key="C")

        dev_runner_t1.materialize_asset("now_time_plus_20_after_plus_N", partition_key="A")
        # confirm that this read from the materialized asset in dev (time_now + 15)
        assert dev_runner_t1.load_asset_value(
            "now_time_plus_20_after_plus_N", partition_key="A"
        ) == (prod_now_time_A + 15 + 20)

        # prod still has old value
        assert prod_runner.load_asset_value("now_time_plus_20_after_plus_N", partition_key="A") == (
            prod_now_time_A + 10 + 20
        )

        # - Now we will test in a different partition
        #   - Read through dev from now_time_plus_N:B. Confirm that it is +10 from prod now_time:B
        #   - Materialize now_time:B in dev. Confirm that it is greater than now_time:B in prod
        #   - Materialize now_time_plus_N:B in dev. Confirm that is read now_time:B in dev.
        assert (
            dev_runner_t1.load_asset_value("now_time_plus_N", partition_key="B")
            == prod_now_time_B + 10
        )

        # materialized new now_time:B in dev
        dev_runner_t1.materialize_asset("now_time", partition_key="B")

        # we haven't materialized now_tine_plus_N:B yet, so still has old value
        assert (
            dev_runner_t1.load_asset_value("now_time_plus_N", partition_key="B")
            == prod_now_time_B + 10
        )

        dev_now_time_B = dev_runner_t1.load_asset_value("now_time", partition_key="B")
        assert isinstance(dev_now_time_B, int)
        assert dev_now_time_B > prod_now_time_B

        dev_runner_t1.materialize_asset("now_time_plus_N", partition_key="B")
        assert (
            dev_runner_t1.load_asset_value("now_time_plus_N", partition_key="B")
            == dev_now_time_B + 15
        )
