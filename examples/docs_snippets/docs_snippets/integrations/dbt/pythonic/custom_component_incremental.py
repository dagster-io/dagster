import json
from collections.abc import Iterator

from dagster_dbt import DbtCliResource, DbtProjectComponent

import dagster as dg


# start_custom_component_incremental
class IncrementalDbtProjectComponent(DbtProjectComponent):
    """Custom DbtProjectComponent that handles incremental models with partitions.

    This is the recommended approach for migrating incremental model logic.
    """

    def execute(
        self, context: dg.AssetExecutionContext, dbt: DbtCliResource
    ) -> Iterator:
        time_window = context.partition_time_window
        dbt_vars = {
            "start_date": time_window.start.strftime("%Y-%m-%d"),
            "end_date": time_window.end.strftime("%Y-%m-%d"),
        }

        yield from dbt.cli(
            ["build", "--vars", json.dumps(dbt_vars)], context=context
        ).stream()


# end_custom_component_incremental
