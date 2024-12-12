import importlib.util

_has_dagster_dbt = importlib.util.find_spec("dagster_dbt") is not None
_has_dagster_embedded_elt = importlib.util.find_spec("dagster_embedded_elt") is not None

if _has_dagster_dbt:
    from dagster_components.lib.dbt_project import DbtProjectComponent as DbtProjectComponent

if _has_dagster_embedded_elt:
    from dagster_components.lib.sling_replication import (
        SlingReplicationComponent as SlingReplicationComponent,
    )

from dagster_components.lib.pipes_subprocess_script_collection import (
    PipesSubprocessScriptCollection as PipesSubprocessScriptCollection,
)
