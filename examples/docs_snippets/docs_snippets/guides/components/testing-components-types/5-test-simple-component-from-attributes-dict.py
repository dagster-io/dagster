from my_component_library.simple_component import SimpleComponent

import dagster as dg
from dagster.components.testing import component_defs


def test_simple_component() -> None:
    defs = component_defs(
        component=SimpleComponent.from_attributes_dict(attributes={"value": 2})
    )
    assert defs.get_assets_def("an_asset")() == 2
