import os
import pathlib
import subprocess
import sys

import toml

ROOT_DIR = pathlib.Path(__file__).parent.parent
VIRTUAL_ENV = ROOT_DIR / ".venv"
ROOT_PYPROJECT = ROOT_DIR / "pyproject.toml"
PYTHON = sys.executable
MIGRATED_MARKER = ".uv_migrated"
import re

PROJECTS = [
    pathlib.Path(p).parent
    for p in sorted(
        """docs/dagster-ui-screenshot/setup.py
docs/sphinx/_ext/dagster-sphinx/setup.py
integration_tests/python_modules/dagster-k8s-test-infra/setup.py
python_modules/automation/setup.py
python_modules/dagit/setup.py
python_modules/dagster/setup.py
python_modules/dagster-graphql/setup.py
python_modules/dagster-pipes/setup.py
python_modules/dagster-test/setup.py
python_modules/dagster-webserver/setup.py
python_modules/libraries/dagster-airbyte/setup.py
python_modules/libraries/dagster-airflow/setup.py
python_modules/libraries/dagster-aws/setup.py
python_modules/libraries/dagster-azure/setup.py
python_modules/libraries/dagster-celery/setup.py
python_modules/libraries/dagster-celery-docker/setup.py
python_modules/libraries/dagster-celery-k8s/setup.py
python_modules/libraries/dagster-census/setup.py
python_modules/libraries/dagster-dask/setup.py
python_modules/libraries/dagster-databricks/setup.py
python_modules/libraries/dagster-datadog/setup.py
python_modules/libraries/dagster-datahub/setup.py
python_modules/libraries/dagster-dbt/setup.py
python_modules/libraries/dagster-deltalake/setup.py
python_modules/libraries/dagster-deltalake-pandas/setup.py
python_modules/libraries/dagster-deltalake-polars/setup.py
python_modules/libraries/dagster-docker/setup.py
python_modules/libraries/dagster-duckdb/setup.py
python_modules/libraries/dagster-duckdb-pandas/setup.py
python_modules/libraries/dagster-duckdb-polars/setup.py
python_modules/libraries/dagster-duckdb-pyspark/setup.py
python_modules/libraries/dagster-embedded-elt/setup.py
python_modules/libraries/dagster-fivetran/setup.py
python_modules/libraries/dagster-gcp/setup.py
python_modules/libraries/dagster-gcp-pandas/setup.py
python_modules/libraries/dagster-gcp-pyspark/setup.py
python_modules/libraries/dagster-ge/setup.py
python_modules/libraries/dagster-github/setup.py
python_modules/libraries/dagster-k8s/setup.py
python_modules/libraries/dagster-looker/setup.py
python_modules/libraries/dagster-managed-elements/setup.py
python_modules/libraries/dagster-mlflow/setup.py
python_modules/libraries/dagster-msteams/setup.py
python_modules/libraries/dagster-mysql/setup.py
python_modules/libraries/dagster-openai/setup.py
python_modules/libraries/dagster-pagerduty/setup.py
python_modules/libraries/dagster-pandas/setup.py
python_modules/libraries/dagster-pandera/setup.py
python_modules/libraries/dagster-papertrail/setup.py
python_modules/libraries/dagster-polars/setup.py
python_modules/libraries/dagster-postgres/setup.py
python_modules/libraries/dagster-powerbi/setup.py
python_modules/libraries/dagster-prometheus/setup.py
python_modules/libraries/dagster-pyspark/setup.py
python_modules/libraries/dagster-sdf/setup.py
python_modules/libraries/dagster-shell/setup.py
python_modules/libraries/dagster-slack/setup.py
python_modules/libraries/dagster-snowflake/setup.py
python_modules/libraries/dagster-snowflake-pandas/setup.py
python_modules/libraries/dagster-snowflake-pyspark/setup.py
python_modules/libraries/dagster-spark/setup.py
python_modules/libraries/dagster-ssh/setup.py
python_modules/libraries/dagster-twilio/setup.py
python_modules/libraries/dagster-wandb/setup.py
python_modules/libraries/dagstermill/setup.py""".split("\n")
    )
]


def is_dagster_package(package_name: str) -> bool:
    if "dagster" in package_name:
        return True

    elif package_name in []:
        return True

    return False


def clean_package_name(package_name: str) -> str:
    # remove extras
    package_name = package_name.split("[")[0]
    # remove versions, they usually come after symbols like ==, >=, etc
    package_name = re.split(r"[<>=]", package_name)[0]

    return package_name


def add_workspace_sources(pyproject_path: str):
    with open(pyproject_path, "r") as file:
        packages = toml.load(file)["project"]["dependencies"]

    with open(ROOT_PYPROJECT, "r") as file:
        root_pyproject = toml.load(file)

    for package in packages:
        if is_dagster_package(package):
            if "tool" not in root_pyproject:
                root_pyproject["tool"] = {}

            if "uv" not in root_pyproject["tool"]:
                root_pyproject["tool"]["uv"] = {}

            if "sources" not in root_pyproject["tool"]["uv"]:
                root_pyproject["tool"]["uv"]["sources"] = {}

            root_pyproject["tool"]["uv"]["sources"][clean_package_name(package)] = {
                "workspace": True
            }

    with open(ROOT_PYPROJECT, "w") as file:
        toml.dump(root_pyproject, file)


def cleanup_pyproject_after_pdm(file_path: str):
    # remove tool.pdb and change build backend to setuptools.build_meta

    with open(file_path, "r") as file:
        data = toml.load(file)

    if "tool" in data:
        del data["tool"]
    data["build-system"] = {
        "requires": ["hatchling"],
        "build-backend": "hatchling.build",
    }

    with open(file_path, "w") as file:
        toml.dump(data, file)


def migrate_to_uv(project_dir: pathlib.Path, run_tests: bool = False):
    project_dir = ROOT_DIR / project_dir

    # change current directory to project_dir
    os.chdir(str(project_dir))
    # convert setup.py to pyproject.toml using pdm
    subprocess.run(["pdm", "import", "-v", "setup.py"], check=True)

    # cleanup pyproject.toml
    cleanup_pyproject_after_pdm("pyproject.toml")

    add_workspace_sources(str(project_dir / "pyproject.toml"))

    # try installing the project with uv to test if it works
    subprocess.run(["uv", "pip", "install", "-e", str(project_dir)], check=True)

    if run_tests:
        subprocess.run(["pytest", "."], check=True)

    with ROOT_PYPROJECT.open("r") as file:
        root_pyproject = toml.load(file)

    project_dir.relative_to(ROOT_DIR)

    with ROOT_PYPROJECT.open("w") as file:
        toml.dump(root_pyproject, file)

    # mark project as migrated
    (project_dir / MIGRATED_MARKER).touch()


if __name__ == "__main__":
    # os.environ["PDM_IGNORE_ACTIVE_VENV"] = "false"
    # os.environ["VIRTUAL_ENV"] = str(VIRTUAL_ENV)

    os.system("uv pip install pdm")

    projects = [
        pathlib.Path(p) for p in ["python_modules/dagster-pipes", "python_modules/dagster"]
    ]  # get_projects_to_migrate()
    projects = PROJECTS

    projects = [p for p in projects if not (p / MIGRATED_MARKER).exists()]

    for project in projects:
        try:
            migrate_to_uv(project, run_tests=False)
        except Exception as e:
            print(f"Error migrating {project}: {e}")  # noqa
