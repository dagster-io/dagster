from dagster._core.definitions.decorators.sensor_decorator import sensor
from dagster.components.lib.shim_components.base import ShimScaffolder
from dagster.components.scaffold.scaffold import ScaffoldRequest, scaffold_with


class SensorScaffolder(ShimScaffolder):
    def get_text(self, request: ScaffoldRequest) -> str:
        return f"""import dagster as dg


@dg.sensor(target=None)
def {request.target_path.stem}(context: dg.SensorEvaluationContext) -> dg.SensorResult:
    return dg.SensorResult()
"""


scaffold_with(SensorScaffolder)(sensor)
