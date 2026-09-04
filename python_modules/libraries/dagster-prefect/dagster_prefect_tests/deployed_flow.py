"""Flow executed by a real Prefect worker in `test_pipes_deployment.py`.

Lives in its own module because a deployment names its flow by entrypoint, and the worker
imports this file in a fresh process. It deliberately takes no Pipes-specific argument: the
bootstrap payload arrives as environment variables, so `open_dagster_pipes()` needs no
configuration.
"""

from dagster_pipes import open_dagster_pipes
from prefect import flow


@flow(name="orders-summary")
def orders_summary(as_of: str = "latest") -> None:
    with open_dagster_pipes() as pipes:
        pipes.report_asset_materialization(metadata={"rows": 100, "as_of": as_of})
