import os
from pathlib import Path

from dagster import AssetCheckResult, AssetCheckSeverity, AssetKey, Definitions, asset_check
from dagster_airlift.core import AirflowInstance, BasicAuthBackend, build_defs_from_airflow_instance


# Attach a check to the DAG representation asset, which will be executed by Dagster
# any time the DAG is run in Airflow
@asset_check(asset=AssetKey(["airflow_instance_one", "dag", "rebuild_customers_list"]))
def validate_exported_csv() -> AssetCheckResult:
    csv_path = Path(os.environ["TUTORIAL_EXAMPLE_DIR"]) / "customers.csv"

    if not csv_path.exists():
        return AssetCheckResult(passed=False, description=f"Export CSV {csv_path} does not exist")

    rows = len(csv_path.read_text().split("\n"))
    if rows < 2:
        return AssetCheckResult(
            passed=False,
            description=f"Export CSV {csv_path} is empty",
            severity=AssetCheckSeverity.WARN,
        )

    return AssetCheckResult(
        passed=True,
        description=f"Export CSV {csv_path} exists",
        metadata={"rows": rows},
    )


defs = Definitions.merge(
    build_defs_from_airflow_instance(
        airflow_instance=AirflowInstance(
            # other backends available (e.g. MwaaSessionAuthBackend)
            auth_backend=BasicAuthBackend(
                webserver_url="http://localhost:8080",
                username="admin",
                password="admin",
            ),
            name="airflow_instance_one",
        )
    ),
    Definitions(asset_checks=[validate_exported_csv]),
)
