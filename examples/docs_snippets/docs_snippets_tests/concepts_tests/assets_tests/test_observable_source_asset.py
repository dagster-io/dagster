from dagster import repository
from dagster._core.definitions.assets_job import build_assets_job
from docs_snippets.concepts.assets.observable_source_assets import foo_source_asset


def test_observable_source_asset():
    @repository
    def repo():
        return [foo_source_asset]

    job_def = build_assets_job("test_job", [], [foo_source_asset])
    result = job_def.execute_in_process()
    assert result.success
