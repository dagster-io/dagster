from assets_dbt_python import assets_dbt_python_defs


def test_repo_can_load():
    assert assets_dbt_python_defs.get_job("everything_everywhere_job")
    assert assets_dbt_python_defs.get_job("refresh_forecast_model_job")
