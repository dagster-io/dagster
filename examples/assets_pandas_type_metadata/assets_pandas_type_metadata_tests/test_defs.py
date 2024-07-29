from assets_pandas_type_metadata import defs


def test_defs_can_load():
    assert defs.get_all_job_defs()
