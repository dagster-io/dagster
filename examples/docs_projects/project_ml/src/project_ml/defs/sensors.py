import dagster as dg


@dg.run_failure_sensor
def model_failure_sensor(context: dg.RunFailureSensorContext):
    """Alert when ML pipeline jobs fail."""
    if context.dagster_run.job_name in [
        "digit_classifier_training",
        "model_deployment",
    ]:
        return dg.SkipReason("Slack integration not configured")
