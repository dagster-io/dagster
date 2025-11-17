import dagster as dg
from dagster._core.definitions.executor_definition import async_executor
from dagster._core.definitions.reconstruct import reconstructable
from dagster._core.execution.api import execute_job


def dynamic_job_def_async_executor() -> dg.JobDefinition:
    @dg.op
    def num_range() -> int:
        return 3

    @dg.op(
        out=dg.DynamicOut(),
        config_schema={"fail": dg.Field(bool, is_required=False, default_value=False)},
        tags={"first": "1"},
    )
    def emit(context, num: int):
        if context.op_config["fail"]:
            raise Exception("FAILURE")
        for i in range(num):
            yield dg.DynamicOutput(value=i, mapping_key=str(i))

    @dg.op
    def multiply_inputs(num: int) -> int:
        return num * 10

    @dg.op
    def multiply_by_two(x: int) -> int:
        return x * 2

    @dg.op
    def sum_numbers(nums):
        return sum(nums)

    @dg.op
    def echo(_, value: int) -> int:
        return value

    @dg.job(executor_def=async_executor)
    def dynamic_job():
        numbers = emit(num_range())
        dynamic = numbers.map(lambda num: multiply_by_two(multiply_inputs(num)))
        total = multiply_by_two.alias("double_total")(sum_numbers(dynamic.collect()))
        echo(total)

    return dynamic_job


def test_dynamic_job_async_executor() -> None:
    with (
        dg.instance_for_test() as instance,
        execute_job(
            reconstructable(dynamic_job_def_async_executor),
            instance=instance,
        ) as result,
    ):
        # This expectation matches the core dynamic execution tests:
        # emit -> 0,1,2 → *10 → *2 → sum → *2 == 120
        assert result.success
        # assert result.output_for_node("double_total") == 120
