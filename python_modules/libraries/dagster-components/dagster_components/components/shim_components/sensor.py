from pathlib import Path

from dagster._utils import pushd

from dagster_components import Blueprint, ScaffoldRequest
from dagster_components.blueprint import scaffold_with
from dagster_components.components.shim_components.base import ShimComponent


class SensorBlueprint(Blueprint):
    def scaffold(self, request: ScaffoldRequest, params: None) -> None:
        with pushd(str(request.target_path)):
            Path("definitions.py").write_text("""
# import dagster as dg
# 
# @dg.sensor(target=...)
# def my_sensor(context: dg.SensorEvaluationContext): ...
""")


@scaffold_with(SensorBlueprint)
class RawSensorComponent(ShimComponent):
    """Sensor component."""
