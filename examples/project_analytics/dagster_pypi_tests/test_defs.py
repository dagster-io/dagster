from dagster_pypi.definitions import defs


def test_def_can_load():
    assert defs.get_job_def("dagster_pypi_job")
