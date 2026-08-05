from my_project.defs.aresource import AResource  # ty: ignore[unresolved-import]

import dagster as dg


@dg.asset
def asset_one(a_resource: AResource): ...
