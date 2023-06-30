from pathlib import Path

from dagster import Definitions

from dagster_dbt import DbtCli, DbtManifest, dbt_assets

dbt_project_dir = Path(__file__).parent.joinpath("..", "jaffle_shop")
dbt_manifest_path = dbt_project_dir.joinpath("target", "manifest.json")
dbt_manifest = DbtManifest.read(path=dbt_manifest_path)


@dbt_assets(manifest=dbt_manifest)
def build_dbt_project(dbt: DbtCli):
    yield from dbt.cli(["build"], manifest=dbt_manifest).stream()


schedules = [
    dbt_manifest.build_schedule(
        job_name="materialize_dbt_models",
        cron_schedule="0 0 0 * *",
    )
]

defs = Definitions(
    assets=[build_dbt_project],
    schedules=schedules,
    resources={
        "dbt": DbtCli(
            project_dir=dbt_project_dir.as_posix(),
        ),
    },
)
