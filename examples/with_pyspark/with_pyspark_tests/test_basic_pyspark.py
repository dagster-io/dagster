from with_pyspark.definitions import defs


def test_basic_pyspark():
    res = defs.get_implicit_global_asset_job_def().execute_in_process()
    assert res.success
