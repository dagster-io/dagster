from dagster import execute_pipeline
from dagster.seven import TemporaryDirectory
from docs_snippets.overview.asset_stores.asset_store_per_output import my_pipeline


def test_asset_store_per_output():
    with TemporaryDirectory() as tmpdir:
        execute_pipeline(
            my_pipeline,
            run_config={"resources": {"asset_store": {"config": {"base_dir": tmpdir}}}},
        )
