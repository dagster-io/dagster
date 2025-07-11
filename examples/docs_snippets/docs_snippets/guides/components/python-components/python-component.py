from dagster import component_instance, ComponentLoadContext
from dagster_dbt import DbtProjectComponent

@component_instance
def load(context: ComponentLoadContext) -> DbtProjectComponent: ...
