from dagster_components import registered_component_type
from dagster_components.lib import SlingReplicationCollection


@registered_component_type(name="custom_subclass")
class CustomSubclass(SlingReplicationCollection): ...
