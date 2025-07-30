export enum JobMetricNames {
  STEP_DURATION = '__dagster_execution_time_ms',
  STEP_RETRIES = '__dagster_step_retries',
  STEP_FAILURES = '__dagster_step_failures',
  RUN_SUCCESSES = '__dagster_run_successes',
  RUN_FAILURES = '__dagster_run_failures',
  RUN_DURATION = '__dagster_run_duration_ms',
  DAGSTER_CREDITS = '__dagster_dagster_credits',
  FAILED_TO_MATERIALIZE = '__dagster_failed_to_materialize',
  MATERIALIZATIONS = '__dagster_materializations',
  OBSERVATIONS = '__dagster_observations',
}

export function jobMetricNameToDisplayString(metricName: JobMetricNames) {
  switch (metricName) {
    case JobMetricNames.STEP_DURATION:
      return 'Execution time';
    case JobMetricNames.STEP_RETRIES:
      return 'Step retries';
    case JobMetricNames.STEP_FAILURES:
      return 'Step failures';
    case JobMetricNames.RUN_SUCCESSES:
      return 'Run success count';
    case JobMetricNames.RUN_FAILURES:
      return 'Run failure count';
    case JobMetricNames.RUN_DURATION:
      return 'Run duration';
    case JobMetricNames.DAGSTER_CREDITS:
      return 'Dagster credits';
    case JobMetricNames.FAILED_TO_MATERIALIZE:
      return 'Failed to materialize';
    case JobMetricNames.MATERIALIZATIONS:
      return 'Materializations';
    case JobMetricNames.OBSERVATIONS:
      return 'Observations';
    default:
      return 'Unknown metric';
  }
}
