from my_project.resources import AResource

import dagster as dg


# highlight-start
@dg.definitions
def defs() -> dg.Definitions:
    return dg.Definitions(
        resources={"a_resource": AResource(name="foo")},
    )
#highlight-end
