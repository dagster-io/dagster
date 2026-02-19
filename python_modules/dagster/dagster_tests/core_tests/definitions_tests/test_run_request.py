from collections.abc import Sequence
from typing import cast

import dagster as dg
import pytest


@pytest.mark.parametrize(
    "prior_partitions,dynamic_partitions_requests,expect_success",
    [
        (["a"], [], True),
        ([], [], False),
        ([], [dg.AddDynamicPartitionsRequest("something", ["a"])], True),
        ([], [dg.AddDynamicPartitionsRequest("something_else", ["a"])], False),
        (["a"], [dg.DeleteDynamicPartitionsRequest("something", ["a"])], False),
        (["a"], [dg.DeleteDynamicPartitionsRequest("something_else", ["a"])], True),
    ],
)
def test_validate_dynamic_partitions(
    prior_partitions: Sequence[str],
    dynamic_partitions_requests: Sequence[
        dg.AddDynamicPartitionsRequest | dg.DeleteDynamicPartitionsRequest
    ],
    expect_success: bool,
):
    partitions_def = dg.DynamicPartitionsDefinition(name="something")

    @dg.job(partitions_def=partitions_def)
    def job1():
        pass

    run_request = dg.RunRequest(partition_key="a")
    with dg.instance_for_test() as instance:
        instance.add_dynamic_partitions(cast("str", partitions_def.name), prior_partitions)

        if expect_success:
            run_request.with_resolved_tags_and_config(
                target_definition=job1,
                dynamic_partitions_requests=dynamic_partitions_requests,
                dynamic_partitions_store=instance,
            )
        else:
            with pytest.raises(
                dg.DagsterUnknownPartitionError, match=r"Could not find a partition with key `a`."
            ):
                run_request.with_resolved_tags_and_config(
                    target_definition=job1,
                    dynamic_partitions_requests=dynamic_partitions_requests,
                    dynamic_partitions_store=instance,
                )
