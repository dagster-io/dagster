from dagster_dbt.rpc.utils import fmt_rpc_logs


def test_fmt_rpc_logs(rpc_logs):
    expected = {
        10: "2020-03-10T18:19:06.726848Z - DEBUG - finished collecting timing info",
        20: "2020-03-10T18:19:06.727723Z - INFO - 11:19:06 | 1 of 1 OK snapshotted snapshots_david_wallace.dagster.daily_fulfillment_forecast_snapshot [\x1b[32mSUCCESS 0\x1b[0m in 11.92s]",
    }
    fmttd_rpc_logs = fmt_rpc_logs(rpc_logs)
    assert expected == fmttd_rpc_logs
