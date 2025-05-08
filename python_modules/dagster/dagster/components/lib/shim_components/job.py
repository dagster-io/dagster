import textwrap
from typing import Any, Optional

from pydantic import BaseModel

from dagster._core.definitions.decorators.job_decorator import job
from dagster.components.lib.shim_components.base import ShimScaffolder
from dagster.components.scaffold.scaffold import scaffold_with


class JobScaffolder(ShimScaffolder):
    @classmethod
    def get_scaffold_params(cls) -> Optional[type[BaseModel]]:
        return None

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
