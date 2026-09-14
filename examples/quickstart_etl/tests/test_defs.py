from quickstart_etl.definitions import defs


def test_def_can_load():
    assert defs().resolve_job_def("all_assets_job")
