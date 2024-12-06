import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Sequence

from dagster import (
    AssetsDefinition,
    AssetSpec,
    Definitions,
    MaterializeResult,
    PipesSubprocessClient,
    multi_asset,
    AssetKey,
)
from dagster_airlift.core import (
    AirflowBasicAuthBackend,
    AirflowInstance,
    assets_with_task_mappings,
    build_defs_from_airflow_instance,
)

REQS_DIR = Path(__file__).parent.parent / "requirements"
SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"


@contextmanager
def venv_initialize(req_file: Path) -> Generator[Path, None, None]:
    """Initialize a virtual environment and install the requirements file. Yield the path to the python executable."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        subprocess.run(["uv", "venv"], cwd=tmpdirname, check=False)
        path_to_uv = Path(tmpdirname) / ".venv" / "bin" / "uv"
        subprocess.run([path_to_uv, "install", "-r", req_file], cwd=tmpdirname, check=False)
        yield Path(tmpdirname) / ".venv" / "bin" / "python"


def build_python_executable_asset(
    specs: Sequence[AssetSpec], req_file: Path, script: Path
) -> AssetsDefinition:
    @multi_asset(specs=specs)
    def run_script_in_venv(context) -> MaterializeResult:
        with venv_initialize(req_file) as python_executable:
            return (
                PipesSubprocessClient()
                .run(
                    command=[str(python_executable), str(script)],
                    context=context,
                )
                .get_materialize_result()
            )

    return run_script_in_venv


# Define some dagster assets
my_custom_report = build_python_executable_asset(
    specs=[
        AssetSpec("my_custom_report", deps=[AssetKey(["jaffle_shop", "staging", "stg_orders"])]),
    ],  # Define asset specs in terms of what you're actually creating. In this case, we're creating a report.
    req_file=REQS_DIR / "report_env.txt",
    script=SCRIPTS_DIR / "generate_report.py",
)
assets = assets_with_task_mappings(
    dag_id="operate_on_orders_data", task_mappings={"run_bespoke_in_isolated_env": [my_custom_report]}
)


airflow_instance = AirflowInstance(
    auth_backend=AirflowBasicAuthBackend(
        webserver_url="http://localhost:8080", username="admin", password="admin"
    ),
    name="airflow_instance",
)

defs = build_defs_from_airflow_instance(
    airflow_instance=airflow_instance, defs=Definitions(assets=assets)
)
