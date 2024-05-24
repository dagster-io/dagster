"""An asset with a large number of partitions (hourly over 1 years = 8760 partitions) and a
single-run backfill policy. When backfilled, will generate a large number of `store_event` or
`store_event_batch` calls, depending on if batching is enabled. Use a DummyIOManager to avoid
unnecessary writes.
"""

from dagster import (
    AssetExecutionContext,
    BackfillPolicy,
    Definitions,
    HourlyPartitionsDefinition,
    IOManager,
    asset,
)

partitions_def = HourlyPartitionsDefinition(
    start_date="2023-01-01-00:00", end_date="2024-01-01-00:00"
)


@asset(partitions_def=partitions_def, backfill_policy=BackfillPolicy.single_run())
def foo(context: AssetExecutionContext):
    return {k: 1 for k in context.partition_keys}


class DummyIOManager(IOManager):
    def load_input(self, context, obj):
        return 1

    def handle_output(self, context, obj):
        pass


defs = Definitions(
    assets=[foo],
    resources={"io_manager": DummyIOManager()},
)
