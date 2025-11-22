import logging
import threading

import anyio
import dagster as dg

logger = logging.getLogger(__name__)


@dg.op(out=dg.DynamicOut())
async def create_dynamic_outputs(context: dg.OpExecutionContext):
    """Creates a dynamic number of outputs."""
    thread = threading.current_thread()
    context.log.info(
        f"[{context.op_handle}] running in thread: {thread.name} (ident={thread.ident})"
    )

    for i in range(20):
        yield dg.DynamicOutput(value=f"item_{i}", mapping_key=f"key_{i}")


@dg.op
async def process_item(context: dg.OpExecutionContext, item: str):
    """Process each item from the fan-out."""
    thread = threading.current_thread()
    context.log.info(
        f"[{context.op_handle}] running in thread: {thread.name} (ident={thread.ident})"
    )
    context.log.info(f"[{context.op_handle}] sleeping...")
    await anyio.sleep(1)
    context.log.info(f"[{context.op_handle}] completed")
    return item


@dg.op
async def collect_results(context: dg.OpExecutionContext, results: list):
    """Collect all results from the fan-out."""
    thread = threading.current_thread()
    context.log.info(
        f"[{context.op_handle}] running in thread: {thread.name} (ident={thread.ident})"
    )
    context.log.info(f"[{context.op_handle}] collected {len(results)} results")
    return results


@dg.job(executor_def=dg.async_executor)
def simple_fanout_job():
    dynamic_items = create_dynamic_outputs()
    processed = dynamic_items.map(process_item)
    collect_results(processed.collect())


def test_concurrency_limit() -> None:
    with (
        dg.instance_for_test() as instance,
        dg.execute_job(
            dg.reconstructable(simple_fanout_job),
            instance=instance,
            run_config={"execution": {"config": {"max_concurrent": 1}}},
        ) as result,
    ):
        assert result.success

        run_stats = instance.get_run_stats(result.run_id)

        # Get execution time in seconds
        if run_stats.end_time and run_stats.start_time:
            duration_seconds = run_stats.end_time - run_stats.start_time
            assert duration_seconds >= 20  # At least 20 seconds since max_concurrent=1
