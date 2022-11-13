from dagster._core.definitions.definitions_fn import get_dagster_definitions_in_module


def test_repo_can_load():
    import assets_dbt_python

    defs = get_dagster_definitions_in_module(assets_dbt_python)
    assert defs.get_job("everything_everywhere_job")
    assert defs.get_job("refresh_forecast_model_job")
