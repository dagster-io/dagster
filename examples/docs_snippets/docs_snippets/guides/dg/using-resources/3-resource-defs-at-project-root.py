import dagster as dg
from resource_docs.resources import AResource

defs = dg.Definitions(
    resources={"a_resource": AResource(name="foo")},
)
