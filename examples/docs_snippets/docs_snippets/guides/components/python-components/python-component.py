import dagster as dg
from dagster_dbt import DbtProjectComponent

@dg.component_instance
def load(context: dg.ComponentLoadContext) -> DbtProjectComponent: ...
