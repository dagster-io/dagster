import math
import time
from typing import Any, Dict, List, cast

from dagster import (
    AssetExecutionContext,
    AssetIn,
    AssetsDefinition,
    DagsterInstance,
    Definitions,
    In,
    StaticPartitionMapping,
    StaticPartitionsDefinition,
    asset,
    job,
    op,
)
from dagster._core.execution.context.compute import OpExecutionContext
from dagster._core.storage.branching.branching_io_manager import BranchingIOManager

from dagster_tests.storage_tests.branching_io_manager_tests.utils import (
    AssetBasedInMemoryIOManager,
    DefinitionsRunner,
)

partitioning_scheme = StaticPartitionsDefinition(["A", "B", "C"])
secondary_partitioning_scheme = StaticPartitionsDefinition(["1", "2", "3"])
tertiary_partitioning_scheme = StaticPartitionsDefinition(["ab", "bc", "ca"])

primary_secondary_partition_mapping = StaticPartitionMapping({"A": "1", "B": "2", "C": "3"})
primary_tertiary_partition_mapping = StaticPartitionMapping(
    {
        "A": ["ab", "ca"],
        "B": ["bc", "ab"],
        "C": ["bc", "ca"],
    }
)


@asset(partitions_def=partitioning_scheme)
def now_time():
    return int(math.floor(time.time() * 100))


@asset(
    partitions_def=secondary_partitioning_scheme,
    ins={
        "now_time": AssetIn(key="now_time", partition_mapping=primary_secondary_partition_mapping)
    },
)
def now_time_times_two(now_time: int) -> int:
    return now_time * 2


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


def test_partition_mapping_workflow() -> Any:
    prod_io_manager = AssetBasedInMemoryIOManager()
    dev_io_manager = AssetBasedInMemoryIOManager()

    prod_defs = Definitions(
        assets=[now_time, now_time_times_two],
        resources={
            "io_manager": prod_io_manager,
        },
    )

    dev_defs = Definitions(
        assets=[now_time, now_time_times_two],
        resources={
            "io_manager": BranchingIOManager(
                parent_io_manager=prod_io_manager, branch_io_manager=dev_io_manager
            )
        },
    )

    with DagsterInstance.ephemeral() as dev_instance, DagsterInstance.ephemeral() as prod_instance:
        # Simulate a full prod run. All partitions are full
        prod_runner = DefinitionsRunner(prod_defs, prod_instance)
        prod_runner.materialize_asset("now_time", partition_key="A")
        prod_runner.materialize_asset("now_time", partition_key="B")
        prod_runner.materialize_asset("now_time", partition_key="C")

        prod_runner.materialize_asset("now_time_times_two", partition_key="1")
        prod_runner.materialize_asset("now_time_times_two", partition_key="2")
        prod_runner.materialize_asset("now_time_times_two", partition_key="3")

        for partition_key in ["A", "B", "C"]:
            assert prod_io_manager.has_value("now_time", partition_key)

        for partition_key in ["1", "2", "3"]:
            assert prod_io_manager.has_value("now_time_times_two", partition_key)

        dev_runner = DefinitionsRunner(dev_defs, dev_instance)

        dev_runner.materialize_asset("now_time_times_two", partition_key="2")

        assert dev_runner.load_asset_value(
            "now_time", partition_key="A"
        ) == prod_runner.load_asset_value("now_time", partition_key="A")

        assert not dev_io_manager.has_value("now_time", partition_key="A")

        # now_time_plus_N has been remataerialized in the dev branch but still with same logic
        assert dev_runner.load_asset_value(
            "now_time_times_two", partition_key="2"
        ) == prod_runner.load_asset_value("now_time_times_two", partition_key="2")

        assert dev_io_manager.has_value("now_time_times_two", partition_key="2")


# Asset factory which produces a partitioned asset w/ each partition having a different seeded value
def get_base_values(seed_values: List[int]) -> AssetsDefinition:
    assert len(seed_values) == 3
    seed_value_dict = {
        "A": seed_values[0],
        "B": seed_values[1],
        "C": seed_values[2],
    }

    @asset(partitions_def=partitioning_scheme)
    def base_values(context: AssetExecutionContext) -> int:
        return seed_value_dict[context.partition_key]

    return base_values


# Asset with a many-to-one mapping from input partitions to output partitions
# e.g. to materialize partition "ab" in the output asset, we need as input partitions "A" and "B" of
# now_time
@asset(
    partitions_def=tertiary_partitioning_scheme,
    ins={
        "upstream_values": AssetIn(
            key="base_values", partition_mapping=primary_tertiary_partition_mapping
        )
    },
)
def average_upstream(upstream_values: Dict[str, int]) -> int:
    return sum(upstream_values.values()) // len(upstream_values)


def test_multi_partition_mapping_workflow() -> Any:
    prod_io_manager = AssetBasedInMemoryIOManager()
    dev_io_manager = AssetBasedInMemoryIOManager()

    prod_defs = Definitions(
        assets=[get_base_values([10, 20, 30]), average_upstream],
        resources={
            "io_manager": prod_io_manager,
        },
    )

    dev_defs = Definitions(
        assets=[get_base_values([50, 100, 150]), average_upstream],
        resources={
            "io_manager": BranchingIOManager(
                parent_io_manager=prod_io_manager, branch_io_manager=dev_io_manager
            )
        },
    )

    with DagsterInstance.ephemeral() as dev_instance, DagsterInstance.ephemeral() as prod_instance:
        # Simulate a full prod run. All partitions are full
        prod_runner = DefinitionsRunner(prod_defs, prod_instance)
        prod_runner.materialize_asset("base_values", partition_key="A")
        prod_runner.materialize_asset("base_values", partition_key="B")
        prod_runner.materialize_asset("base_values", partition_key="C")

        prod_runner.materialize_asset("average_upstream", partition_key="ab")
        prod_runner.materialize_asset("average_upstream", partition_key="bc")
        prod_runner.materialize_asset("average_upstream", partition_key="ca")

        for partition_key in ["A", "B", "C"]:
            assert prod_io_manager.has_value("base_values", partition_key)

        for partition_key in ["ab", "bc", "ca"]:
            assert prod_io_manager.has_value("average_upstream", partition_key)

        # Verify that, since we haven't materialized the upstream asset in dev, we are reading from
        # the values generated in prod
        assert prod_io_manager.get_value("base_values", partition_key="A") == 10
        assert not dev_io_manager.has_value("base_values", partition_key="A")

        assert prod_io_manager.get_value("average_upstream", partition_key="ab") == 15
        assert not dev_io_manager.has_value("average_upstream", partition_key="ab") == 15

        dev_runner = DefinitionsRunner(dev_defs, dev_instance)

        # First, we try rematerializing the averages in dev. Since we haven't materialized the
        # upstream asset, we should be reading from prod, and the values should be the same
        dev_runner.materialize_asset("average_upstream", partition_key="ab")
        assert dev_io_manager.has_value("average_upstream", partition_key="ab")
        assert dev_io_manager.get_value("average_upstream", partition_key="ab") == 15

        # Now, we materialize the upstream asset in dev, but only a single partition
        # The branching IO manager logic will only read from the upstream asset in dev if all
        # upstream partitions are materialized in dev, so the average will be unchanged
        dev_runner.materialize_asset("base_values", partition_key="A")
        assert dev_io_manager.has_value("base_values", partition_key="A")
        assert dev_io_manager.get_value("base_values", partition_key="A") == 50

        dev_runner.materialize_asset("average_upstream", partition_key="ab")
        assert dev_io_manager.get_value("average_upstream", partition_key="ab") == 15

        # Now, we materialize the upstream asset in dev for the "B" partition. Since we have
        # materialized all needed upstream partitions in dev, the branching IO manager logic
        # will read from the upstream asset in dev, and the average will be updated
        dev_runner.materialize_asset("base_values", partition_key="B")
        assert dev_io_manager.has_value("base_values", partition_key="B")
        assert dev_io_manager.get_value("base_values", partition_key="B") == 100

        dev_runner.materialize_asset("average_upstream", partition_key="ab")
        assert dev_io_manager.get_value("average_upstream", partition_key="ab") == 75


@op
def fixed_value_op(context: OpExecutionContext) -> int:
    if context.partition_key == "A":
        return 10
    elif context.partition_key == "B":
        return 20
    elif context.partition_key == "C":
        return 30
    else:
        raise Exception("Invalid partition key")


@op(ins={"input_value": In(int)})
def divide_input_by_two(input_value: int) -> int:
    return input_value // 2


@job(partitions_def=partitioning_scheme)
def my_math_job():
    divide_input_by_two(fixed_value_op())


def test_job_op_usecase_partitioned() -> Any:
    with DefinitionsRunner.ephemeral(
        Definitions(
            jobs=[my_math_job],
            resources={
                "io_manager": BranchingIOManager(
                    parent_io_manager=AssetBasedInMemoryIOManager(),
                    branch_io_manager=AssetBasedInMemoryIOManager(),
                )
            },
        ),
    ) as runner:
        result = (
            cast(DefinitionsRunner, runner)
            .defs.get_job_def("my_math_job")
            .execute_in_process(instance=runner.instance, partition_key="A")
        )
        assert result.success
        assert result.output_for_node("divide_input_by_two") == 5

        result = (
            cast(DefinitionsRunner, runner)
            .defs.get_job_def("my_math_job")
            .execute_in_process(instance=runner.instance, partition_key="B")
        )
        assert result.success
        assert result.output_for_node("divide_input_by_two") == 10
