# in defs/asset_one.py
import dagster as dg
from my_project.resources import AResource


@dg.asset
def asset_one(a_resource: AResource): ...
