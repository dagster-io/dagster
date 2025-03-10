from pathlib import Path

from dagster._utils import pushd

from dagster_components import Scaffolder, ScaffoldRequest
from dagster_components.components.shim_components.base import ShimComponent
from dagster_components.scaffolder import scaffolder


class SensorScaffolder(Scaffolder):
    def scaffold(self, request: ScaffoldRequest, params: None) -> None:
        with pushd(str(request.target_path)):
            Path("definitions.py").write_text("""
# import dagster as dg
# 
# @dg.sensor(target=...)
# def my_sensor(context: dg.SensorEvaluationContext): ...
""")


@scaffolder(SensorScaffolder)
class RawSensorComponent(ShimComponent):
    """Sensor component."""
