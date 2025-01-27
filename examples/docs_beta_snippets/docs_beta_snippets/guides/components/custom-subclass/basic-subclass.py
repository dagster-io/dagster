from dagster_components import component_type
from dagster_components.lib import SlingReplicationCollection


@component_type(name="custom_subclass")
class CustomSubclass(SlingReplicationCollection): ...
