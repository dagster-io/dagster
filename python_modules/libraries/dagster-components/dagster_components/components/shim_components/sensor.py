from dagster_components.blueprint import scaffold_with
from dagster_components.components.shim_components.base import ShimBlueprint, ShimComponent


class SensorBlueprint(ShimBlueprint):
    def get_text(self) -> str:
        return """# import dagster as dg
# 
#
# @dg.sensor(target=...)
# def my_sensor(context: dg.SensorEvaluationContext): ...
"""


@scaffold_with(SensorBlueprint)
class RawSensorComponent(ShimComponent):
    """Sensor component."""
