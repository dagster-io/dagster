from pathlib import Path

from dagster._utils import pushd

from dagster_components import Blueprint, ScaffoldRequest
from dagster_components.blueprint import scaffold_with
from dagster_components.components.shim_components.base import ShimComponent


class ScheduleBlueprint(Blueprint):
    def scaffold(self, request: ScaffoldRequest, params: None) -> None:
        with pushd(str(request.target_path)):
            Path("definitions.py").write_text("""
# import dagster as dg
# 
# @dg.schedule(cron_schedule=..., target=...)
# def my_schedule(context: dg.ScheduleEvaluationContext): ...

""")


@scaffold_with(ScheduleBlueprint)
class RawScheduleComponent(ShimComponent):
    """Schedule component."""
