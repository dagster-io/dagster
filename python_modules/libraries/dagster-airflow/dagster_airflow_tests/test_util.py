from dagster_airflow.operators.util import convert_airflow_datestr_to_epoch_ts

EPS = 1e-6


def test_airflow_ts():
    example = "2019-06-26T17:19:09+00:00"
    res = convert_airflow_datestr_to_epoch_ts(example)
    assert abs(res - 1561569549) < EPS

    example = "2019-01-01T00:00:00.123456+00:00"
    res = convert_airflow_datestr_to_epoch_ts(example)
    assert abs(res - 1546300800.123456) < EPS

    # Adding 1900 as a test case because we've seen this produced by Airflow
    example = "1900-01-08T00:00:00+00:00"
    res = convert_airflow_datestr_to_epoch_ts(example)
    assert abs(res - -2208384000.0) < EPS
