from with_pyspark.repository import make_and_filter_data_job


def test_basic_pyspark():
    res = make_and_filter_data_job.execute_in_process()
    assert res.success
