import textwrap
from typing import Any

from dagster._core.definitions.decorators.job_decorator import job
from dagster.components.lib.shim_components.base import ShimScaffolder
from dagster.components.scaffold.scaffold import scaffold_with


class JobScaffolder(ShimScaffolder):
    def get_text(self, filename: str, params: Any) -> str:
        return textwrap.dedent(
            f"""\
            import dagster as dg


            @dg.job
            def {filename}():
                pass
            """
        )


scaffold_with(JobScaffolder)(job)
