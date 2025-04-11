from resource_docs.resources import AResource

import dagster as dg

defs = dg.Definitions(
    resources={"a_resource": AResource(name="foo")},
)
