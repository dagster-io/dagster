from dagster import _check as check
from dagster.components.lib.shim_components.base import ShimScaffolder
from dagster.components.scaffold.scaffold import scaffold_with


class ResourcesScaffolder(ShimScaffolder):
    def get_text(self, filename: str, params: None) -> str:
        check.invariant(params is None, "params")
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
