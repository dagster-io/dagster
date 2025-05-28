export enum AssetCatalogMetricNames {
  ASSET_CHECK_ERRORS = '__dagster_asset_check_errors',
  ASSET_CHECK_WARNINGS = '__dagster_asset_check_warnings',
  ASSET_CHECK_SUCCESS_RATE = '__dagster_asset_check_success_rate',
  ASSET_SUCCESS_RATE = '__dagster_asset_success_rate',
  MATERIALIZATIONS = '__dagster_materializations',
  STEP_DURATION = '__dagster_execution_time_ms',
  FAILED_TO_MATERIALIZE = '__dagster_failed_to_materialize',
  STEP_RETRIES = '__dagster_step_retries',
  FRESHNESS_FAILURES = '__dagster_freshness_failures',
  FRESHNESS_WARNINGS = '__dagster_freshness_warnings',
  FRESHNESS_PASS_RATE = '__dagster_freshness_pass_rate',
  // Custom metrics
  DBT_EXECUTION_DURATION = 'Execution Duration',
  ROW_COUNT = 'row_count',
}

export function metricNameToDisplayString(metricName: AssetCatalogMetricNames) {
  switch (metricName) {
    case AssetCatalogMetricNames.ASSET_CHECK_ERRORS:
      return 'Check errors';
    case AssetCatalogMetricNames.ASSET_CHECK_WARNINGS:
      return 'Check warnings';
    case AssetCatalogMetricNames.ASSET_SUCCESS_RATE:
      return 'Success rate';
    case AssetCatalogMetricNames.ASSET_CHECK_SUCCESS_RATE:
      return 'Check success rate';
    case AssetCatalogMetricNames.MATERIALIZATIONS:
      return 'Materializations';
    case AssetCatalogMetricNames.STEP_DURATION:
      return 'Execution time';
    case AssetCatalogMetricNames.FAILED_TO_MATERIALIZE:
      return 'Failures';
    case AssetCatalogMetricNames.STEP_RETRIES:
      return 'Step retries';
    case AssetCatalogMetricNames.DBT_EXECUTION_DURATION:
      return 'DBT execution duration';
    case AssetCatalogMetricNames.ROW_COUNT:
      return 'Row count';
    case AssetCatalogMetricNames.FRESHNESS_FAILURES:
      return 'Freshness failures';
    case AssetCatalogMetricNames.FRESHNESS_WARNINGS:
      return 'Freshness warnings';
    default:
      return 'Unknown metric';
  }
}
