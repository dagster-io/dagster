from pathlib import Path

from dagster._utils import pushd

from dagster_components import Scaffolder, ScaffoldRequest
from dagster_components.components.shim_components.base import ShimComponent
from dagster_components.scaffoldable.decorator import scaffoldable


class ScheduleScaffolder(Scaffolder):
    def scaffold(self, request: ScaffoldRequest, params: None) -> None:
        with pushd(str(request.target_path)):
            Path("definitions.py").write_text("""
# import dagster as dg
# 
# @dg.schedule(cron_schedule=..., target=...)
# def my_schedule(context: dg.ScheduleEvaluationContext): ...

""")


@scaffoldable(ScheduleScaffolder)
class RawScheduleComponent(ShimComponent):
    """Schedule component."""
