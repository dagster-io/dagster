from collections.abc import Sequence
from typing import Union, cast

import pytest
from dagster import (
    AddDynamicPartitionsRequest,
    DeleteDynamicPartitionsRequest,
    DynamicPartitionsDefinition,
    RunRequest,
    job,
)
from dagster._core.errors import DagsterUnknownPartitionError
from dagster._core.test_utils import instance_for_test


@pytest.mark.parametrize(
    "prior_partitions,dynamic_partitions_requests,expect_success",
    [
        (["a"], [], True),
        ([], [], False),
        ([], [AddDynamicPartitionsRequest("something", ["a"])], True),
        ([], [AddDynamicPartitionsRequest("something_else", ["a"])], False),
        (["a"], [DeleteDynamicPartitionsRequest("something", ["a"])], False),
        (["a"], [DeleteDynamicPartitionsRequest("something_else", ["a"])], True),
    ],
)
def test_validate_dynamic_partitions(
    prior_partitions: Sequence[str],
    dynamic_partitions_requests: Sequence[
        Union[AddDynamicPartitionsRequest, DeleteDynamicPartitionsRequest]
    ],
    expect_success: bool,
):
    partitions_def = DynamicPartitionsDefinition(name="something")

    @job(partitions_def=partitions_def)
    def job1():
        pass

    run_request = RunRequest(partition_key="a")
    with instance_for_test() as instance:
        instance.add_dynamic_partitions(cast(str, partitions_def.name), prior_partitions)

        if expect_success:
            run_request.with_resolved_tags_and_config(
                target_definition=job1,
                dynamic_partitions_requests=dynamic_partitions_requests,
                dynamic_partitions_store=instance,
            )
        else:
            with pytest.raises(
                DagsterUnknownPartitionError, match="Could not find a partition with key `a`."
            ):
                run_request.with_resolved_tags_and_config(
                    target_definition=job1,
                    dynamic_partitions_requests=dynamic_partitions_requests,
                    dynamic_partitions_store=instance,
                )
