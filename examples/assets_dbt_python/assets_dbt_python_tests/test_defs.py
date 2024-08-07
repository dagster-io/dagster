from dagster._core.test_utils import environ


def test_def_can_load():
    with environ({"DAGSTER_IS_DEV_CLI": "1"}):
        from assets_dbt_python.definitions import defs

        assert defs.get_job_def("everything_everywhere_job")
        assert defs.get_job_def("refresh_forecast_model_job")
