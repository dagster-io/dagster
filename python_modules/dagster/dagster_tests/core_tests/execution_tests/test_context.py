import dagster._check as check
import pytest
from dagster import OpExecutionContext, asset, job, op
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.materialize import materialize_to_memory
from dagster._core.definitions.op_definition import OpDefinition
from dagster._core.definitions.partition_key_range import PartitionKeyRange
from dagster._core.definitions.time_window_partitions import DailyPartitionsDefinition
from dagster._core.execution.context.system import TypeCheckContext
from dagster._core.storage.dagster_run import DagsterRun
from dagster._core.storage.tags import (
    ASSET_PARTITION_RANGE_END_TAG,
    ASSET_PARTITION_RANGE_START_TAG,
)
from dagster._core.types.dagster_type import DagsterType


def test_op_execution_context():
    @op
    def ctx_op(context: OpExecutionContext):
        check.inst(context.run, DagsterRun)
        assert context.job_name == "foo"
        assert context.job_def.name == "foo"
        check.inst(context.job_def, JobDefinition)
        assert context.op_config is None
        check.inst(context.op_def, OpDefinition)

    @job
    def foo():
        ctx_op()

    assert foo.execute_in_process().success


class Catch:
    def __call__(self, context: TypeCheckContext, _) -> bool:
        self.partition_key = context.partition_key
        self.partition_key_range = context.partition_key_range
        return True


@pytest.fixture
def catch() -> Catch:
    return Catch()


def test_type_check_context_has_partition_key(catch: Catch):
    first_partition_key = "1970-01-01"
    partition_def = DailyPartitionsDefinition(start_date=first_partition_key)

    DummyDagsterType = DagsterType(name="DummyDagsterType", type_check_fn=catch)

    @asset(partitions_def=partition_def, dagster_type=DummyDagsterType)
    def asset01():
        ...

    materialize_to_memory([asset01], partition_key=first_partition_key)

    assert catch.partition_key == first_partition_key


def test_type_check_context_no_partition_key(catch: Catch):
    DummyDagsterType = DagsterType(name="DummyDagsterType", type_check_fn=catch)

    @asset(dagster_type=DummyDagsterType)
    def asset01():
        ...

    materialize_to_memory([asset01])

    assert catch.partition_key is None


def test_type_check_context_has_partition_key_range(catch: Catch):
    first_partition_key = "1970-01-01"
    partition_def = DailyPartitionsDefinition(start_date=first_partition_key)

    DummyDagsterType = DagsterType(name="DummyDagsterType", type_check_fn=catch)

    @asset(partitions_def=partition_def, dagster_type=DummyDagsterType)
    def asset01():
        ...

    materialize_to_memory(
        [asset01],
        tags={
            ASSET_PARTITION_RANGE_START_TAG: first_partition_key,
            ASSET_PARTITION_RANGE_END_TAG: first_partition_key,
        },
    )

    assert catch.partition_key_range == PartitionKeyRange(first_partition_key, first_partition_key)
