from dagster_cloud.anomaly_detection import build_anomaly_detection_freshness_checks

hourly_sales = ...

freshness_checks = build_anomaly_detection_freshness_checks(
    assets=[hourly_sales], params=None
)
