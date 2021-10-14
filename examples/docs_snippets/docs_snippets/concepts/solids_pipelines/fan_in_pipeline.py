# start_marker

from typing import List

from dagster import pipeline, solid


@solid
def return_one() -> int:
    return 1


@solid
def sum_fan_in(nums: List[int]) -> int:
    return sum(nums)


@pipeline
def fan_in_pipeline():
    fan_outs = []
    for i in range(0, 10):
        fan_outs.append(return_one.alias(f"return_one_{i}")())
    sum_fan_in(fan_outs)


# end_marker
