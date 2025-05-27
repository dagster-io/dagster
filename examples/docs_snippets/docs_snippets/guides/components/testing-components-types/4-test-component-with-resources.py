from my_component_library.lib.component_with_resources import (
    AResource,
    ComponentWithResources,
)

import dagster as dg
from dagster.components.testing import component_defs


def test_component_with_resources() -> None:
    defs = component_defs(
        component=ComponentWithResources(), resources={"a_resource": AResource(value=2)}
    )
    assert defs.get_assets_def("an_asset")() == 2
