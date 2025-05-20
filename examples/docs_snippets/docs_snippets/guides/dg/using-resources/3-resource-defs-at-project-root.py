from my_project.resources import AResource

import dagster as dg
from dagster.components import definitions


@definitions
def defs() -> dg.Definitions:
    return dg.Definitions(
        resources={"a_resource": AResource(name="foo")},
    )
