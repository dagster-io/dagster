import textwrap

from dagster._core.definitions.decorators.job_decorator import job
from dagster.components.lib.shim_components.base import ShimScaffolder
from dagster.components.scaffold.scaffold import ScaffoldRequest, scaffold_with


class JobScaffolder(ShimScaffolder):
    def get_text(self, request: ScaffoldRequest) -> str:
        return textwrap.dedent(
            f"""\
            import dagster as dg


            @dg.job
            def {request.target_path.stem}():
                pass
            """
        )


scaffold_with(JobScaffolder)(job)
