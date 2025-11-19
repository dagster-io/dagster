import logging
import threading

import anyio
import dagster as dg
import pytest

logger = logging.getLogger(__name__)


def simple_fanout_job_def(num_fanouts: int, sleep_seconds: int):
    @dg.op(out=dg.DynamicOut())
    async def create_dynamic_outputs(context: dg.OpExecutionContext):
        """Creates a dynamic number of outputs."""
        thread = threading.current_thread()
        context.log.info(
            f"[{context.op_handle}] running in thread: {thread.name} (ident={thread.ident})"
        )

        for i in range(num_fanouts):
            yield dg.DynamicOutput(value=f"item_{i}", mapping_key=f"key_{i}")

    @dg.op
    async def process_item(context: dg.OpExecutionContext, item: str):
        """Process each item from the fan-out."""
        thread = threading.current_thread()
        context.log.info(
            f"[{context.op_handle}] running in thread: {thread.name} (ident={thread.ident})"
        )
        context.log.info(f"[{context.op_handle}] sleeping...")
        await anyio.sleep(sleep_seconds)
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

    return simple_fanout_job


@pytest.mark.parametrize(
    "num_fanouts,sleep_seconds,expected_max_seconds_duration",
    [
        (20, 3, 30),  # takes a lot less time in reality, but putting it high to avoid a flakey test
        (
            100,
            3,
            60,
        ),  # takes a lot less time in reality, but putting it high to avoid a flakey test
    ],
)
def test_async_performance_basic(
    num_fanouts: int, sleep_seconds: int, expected_max_seconds_duration: int
) -> None:
    with (
        dg.instance_for_test() as instance,
        dg.execute_job(
            dg.build_reconstructable_job(
                reconstructor_module_name=__name__,
                reconstructor_function_name="simple_fanout_job_def",
                reconstructable_args=(num_fanouts, sleep_seconds),
                reconstructable_kwargs={},
            ),
            instance=instance,
        ) as result,
    ):
        assert result.success

        run_stats = instance.get_run_stats(result.run_id)

        # Get execution time in seconds
        if run_stats.end_time and run_stats.start_time:
            duration_seconds = run_stats.end_time - run_stats.start_time
            logging.info(
                f"num_fanouts: {num_fanouts} | sleep_seconds: {sleep_seconds} | duration_seconds: {duration_seconds:.2f}"
            )
            assert duration_seconds <= expected_max_seconds_duration
