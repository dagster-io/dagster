import dagster as dg


@dg.sensor(target=...)
def sensor_name(context: dg.SensorEvaluationContext) -> dg.SensorResult: ...
