from assets_pandas_type_metadata.definitions import defs


def test_defs_can_load():
    assert defs.resolve_all_job_defs()
