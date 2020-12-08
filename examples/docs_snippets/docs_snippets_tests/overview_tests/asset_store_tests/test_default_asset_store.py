from dagster import execute_pipeline
from dagster.seven import TemporaryDirectory
from docs_snippets.overview.asset_stores.default_asset_store import my_pipeline


def test_default_asset_store():
    with TemporaryDirectory() as tmpdir:
        execute_pipeline(
            my_pipeline,
            run_config={"resources": {"object_manager": {"config": {"base_dir": tmpdir}}}},
        )
