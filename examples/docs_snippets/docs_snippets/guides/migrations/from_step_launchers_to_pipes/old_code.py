from typing import Any

import dagster as dg
from dagster_aws.emr import emr_pyspark_step_launcher
from pyspark.sql import DataFrame

from my_lib import MyPysparkIOManager, calculate_metric, get_data_frame  # type: ignore

# the upstream asset will serve as an example of writing a Spark DataFrame


@dg.asset(io_manager_key="pyspark_io_manager")
def upstream(pyspark_step_launcher: dg.ResourceParam[Any]) -> DataFrame:
    return get_data_frame()


# the downstream asset will serve as an example of reading a Spark DataFrame
# and logging metadata to Dagster


@dg.asset(io_manager_key="pyspark_io_manager")
def downstream(
    context: dg.AssetExecutionContext,
    upstream: DataFrame,
    pyspark_step_launcher: dg.ResourceParam[Any],
) -> None:
    my_metric = calculate_metric(upstream)
    context.add_output_metadata({"my_metric": my_metric})
    return


definitions = dg.Definitions(
    assets=[upstream, downstream],
    resources={
        "pyspark_step_launcher": emr_pyspark_step_launcher,
        "pyspark_io_manager": MyPysparkIOManager(),
    },
)
