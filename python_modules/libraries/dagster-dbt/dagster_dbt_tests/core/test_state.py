from dagster import AssetExecutionContext, Definitions, define_asset_job
from dagster_dbt import DbtCliResource, DbtManifestAssetSelection, dbt_assets

from ..conftest import MODIFIED_TEST_PROJECT_DIR, TEST_PROJECT_DIR


def test_state_modified_selection() -> None:
    prod_manifest = MODIFIED_TEST_PROJECT_DIR + "/manifest.json"

    @dbt_assets(manifest=prod_manifest)
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(
            [
                "run",
                "--defer",
                "--state",
                TEST_PROJECT_DIR,
            ],
            context=context,
        ).stream()

    defs = Definitions(
        assets=[my_dbt_assets],
        jobs=[
            define_asset_job(
                "dbt_state_modified",
                selection=DbtManifestAssetSelection.build(
                    manifest=prod_manifest,
                    select="state:modified",
                    state_path=TEST_PROJECT_DIR,
                ),
            ),
        ],
        resources={"dbt": DbtCliResource(project_dir=MODIFIED_TEST_PROJECT_DIR)},
    )

    job = defs.get_job_def("dbt_state_modified")

    result = job.execute_in_process()
    assert result.success
    assert {
        mat.asset_key.to_user_string()
        for mat in result.asset_materializations_for_node("my_dbt_assets")
    } == {
        "sort_cold_cereals_by_calories",  # modified relative to base
        "names",  # added relative to base
    }
