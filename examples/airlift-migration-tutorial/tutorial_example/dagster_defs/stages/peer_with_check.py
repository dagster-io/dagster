import os
from pathlib import Path

import dagster as dg
import dagster_airlift.core as dg_airlift_core


# highlight-start
# Attach a check to the DAG representation asset, which will be executed by Dagster
# any time the DAG is run in Airflow
@dg.asset_check(asset=dg.AssetKey(["airflow_instance_one", "dag", "rebuild_customers_list"]))
def validate_exported_csv() -> dg.AssetCheckResult:
    csv_path = Path(os.environ["TUTORIAL_EXAMPLE_DIR"]) / "customers.csv"

    if not csv_path.exists():
        return dg.AssetCheckResult(
            passed=False, description=f"Export CSV {csv_path} does not exist"
        )

    rows = len(csv_path.read_text().split("\n"))
    if rows < 2:
        return dg.AssetCheckResult(
            passed=False,
            description=f"Export CSV {csv_path} is empty",
            severity=dg.AssetCheckSeverity.WARN,
        )

    return dg.AssetCheckResult(
        passed=True,
        description=f"Export CSV {csv_path} exists",
        metadata={"rows": rows},
    )


# highlight-end


defs = dg_airlift_core.build_defs_from_airflow_instance(
    airflow_instance=dg_airlift_core.AirflowInstance(
        # other backends available (e.g. MwaaSessionAuthBackend)
        auth_backend=dg_airlift_core.AirflowBasicAuthBackend(
            webserver_url="http://localhost:8080",
            username="admin",
            password="admin",
        ),
        name="airflow_instance_one",
    ),
    # highlight-start
    # Pass a Definitions object containing the relevant check, so that it is attached to the DAG
    # asset.
    defs=dg.Definitions(asset_checks=[validate_exported_csv]),
    # highlight-end
)
