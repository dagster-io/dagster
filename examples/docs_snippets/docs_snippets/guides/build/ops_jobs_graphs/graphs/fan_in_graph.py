# start_marker


import dagster as dg


@dg.op
def return_one() -> int:
    return 1


@dg.op
def sum_fan_in(nums: list[int]) -> int:
    return sum(nums)


@dg.graph
def fan_in():
    fan_outs = [return_one.alias(f"return_one_{i}")() for i in range(0, 10)]
    sum_fan_in(fan_outs)


# end_marker
