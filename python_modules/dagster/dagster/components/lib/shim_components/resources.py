from typing import Optional

from dagster.components.lib.shim_components.base import ShimScaffolder
from dagster.components.scaffold.scaffold import NoParams, scaffold_with


class ResourcesScaffolder(ShimScaffolder):
    def get_text(self, filename: str, params: Optional[NoParams]) -> str:
        return """import dagster as dg
from dagster.components import definitions


@definitions
def resources() -> dg.Definitions:
    return dg.Definitions(resources={})
"""


def resources() -> None:
    """Symbol for dg scaffold to target."""
    ...


scaffold_with(ResourcesScaffolder)(resources)
