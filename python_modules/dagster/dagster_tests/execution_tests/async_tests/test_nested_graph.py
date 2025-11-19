import anyio
import dagster as dg


@dg.op
def provide_input() -> int:
    return 1


@dg.op
async def async_inner_op(context: dg.OpExecutionContext, x: int) -> int:
    context.log.info("async_inner_op starting")
    await anyio.sleep(0.01)
    return x + 1


@dg.op
def sync_inner_op(x: int) -> int:
    return x * 2


@dg.graph
def inner_graph(x: int) -> int:
    return sync_inner_op(async_inner_op(x))


@dg.op
def downstream(context: dg.OpExecutionContext, y: int) -> int:
    context.log.info("downstream got %s", y)
    return y + 10


@dg.job(executor_def=dg.async_executor)
def nested_graph_async_job():
    result = inner_graph(provide_input())
    downstream(result)


def test_async_executor_with_nested_graph():
    with (
        dg.instance_for_test() as instance,
        dg.execute_job(
            dg.reconstructable(nested_graph_async_job),
            instance=instance,
        ) as result,
    ):
        assert result.success
        assert result.output_for_node("downstream") == ((1 + 1) * 2) + 10
