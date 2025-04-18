from dagster_airlift.test.test_utils import asset_spec


def test_job_based_defs(
    airflow_instance: None,
) -> None:
    """Test that job based defs load properly."""
    from kitchen_sink.dagster_defs.job_based_defs import defs

    assert len(defs.jobs) == 19  # type: ignore
    assert len(defs.assets) == 1  # type: ignore
    for key in ["print_asset", "another_print_asset", "example1", "example2"]:
        assert asset_spec(key, defs)
