import dagster as dg


@dg.sensor(target=None)
def sensor(context: dg.SensorEvaluationContext) -> dg.SensorResult:
    return dg.SensorResult()
