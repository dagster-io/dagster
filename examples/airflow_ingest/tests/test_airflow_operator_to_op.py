from airflow_ingest.airflow_operator_to_op import my_http_job


def test_http_op():
    assert my_http_job.execute_in_process()
