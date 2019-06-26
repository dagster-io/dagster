from dagster.core.utils import convert_airflow_datestr_to_epoch_ts

EPS = 1e-6


def test_airflow_ts():
    example = '2019-06-26T17:19:09.989485+00:00'
    res = convert_airflow_datestr_to_epoch_ts(example)
    assert (res - 1561569549.989485) < EPS
