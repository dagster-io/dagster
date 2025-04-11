# in defs/asset_one.py
from my_project.resources import AResource

import dagster as dg


@dg.asset
def asset_one(a_resource: AResource): ...
