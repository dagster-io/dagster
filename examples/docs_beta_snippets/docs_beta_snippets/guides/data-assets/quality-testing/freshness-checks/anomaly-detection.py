from dagster_cloud.anomaly_detection import build_anomaly_detection_freshness_checks

import dagster as dg


@dg.observable_source_asset
def hourly_sales(): ...


freshness_checks = build_anomaly_detection_freshness_checks(
    assets=[hourly_sales], params=None
)
