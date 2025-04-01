from dagster import sensor

from dagster_components.lib.shim_components.base import ShimScaffolder
from dagster_components.scaffold.scaffold import scaffold_with


class SensorScaffolder(ShimScaffolder):
    def get_text(self, filename: str) -> str:
        return f"""# import dagster as dg
# 
#
# @dg.sensor(target=...)
# def {filename}(context: dg.SensorEvaluationContext): ...

"""


scaffold_with(SensorScaffolder)(sensor)
