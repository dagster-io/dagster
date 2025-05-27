from dagster.components.lib.shim_components.base import ShimScaffolder
from dagster.components.scaffold.scaffold import ScaffoldRequest, scaffold_with


class ResourcesScaffolder(ShimScaffolder):
    def get_text(self, request: ScaffoldRequest) -> str:
        return """import dagster as dg


@dg.definitions
def resources() -> dg.Definitions:
    return dg.Definitions(resources={})
"""


def resources() -> None:
    """Symbol for dg scaffold to target."""
    ...


scaffold_with(ResourcesScaffolder)(resources)
