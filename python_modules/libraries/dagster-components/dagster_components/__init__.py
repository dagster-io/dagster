import importlib.util

from dagster_components.core.component import (
    Component as Component,
    ComponentLoadContext as ComponentLoadContext,
    component as component,
)
from dagster_components.core.component_defs_builder import (
    build_component_defs as build_component_defs,
)
from dagster_components.core.component_scaffolder import (
    ComponentScaffolder as ComponentScaffolder,
    ComponentScaffolderUnavailableReason as ComponentScaffolderUnavailableReason,
    ComponentScaffoldRequest as ComponentScaffoldRequest,
    DefaultComponentScaffolder as DefaultComponentScaffolder,
)
from dagster_components.core.schema.base import (
    FieldResolver as FieldResolver,
    ResolvableSchema as ResolvableSchema,
)
from dagster_components.core.schema.context import ResolutionContext as ResolutionContext
from dagster_components.core.schema.metadata import ResolvableFieldInfo as ResolvableFieldInfo
from dagster_components.core.schema.objects import (
    AssetAttributesSchema as AssetAttributesSchema,
    AssetPostProcessorSchema as AssetPostProcessorSchema,
    AssetSpecSchema as AssetSpecSchema,
    OpSpecSchema as OpSpecSchema,
)
from dagster_components.scaffold import scaffold_component_yaml as scaffold_component_yaml
from dagster_components.version import __version__ as __version__

# ########################
# ##### COMPONENTS
# ########################

_has_dagster_dbt = importlib.util.find_spec("dagster_dbt") is not None
_has_dagster_sling = importlib.util.find_spec("dagster_sling") is not None

if _has_dagster_dbt:
    from dagster_components.components.dbt_project.component import (
        DbtProjectComponent as DbtProjectComponent,
    )

if _has_dagster_sling:
    from dagster_components.components.sling_replication_collection.component import (
        SlingReplicationCollectionComponent as SlingReplicationCollectionComponent,
    )

from dagster_components.components.definitions_component.component import (
    DefinitionsComponent as DefinitionsComponent,
)
from dagster_components.components.pipes_subprocess_script_collection import (
    PipesSubprocessScriptCollectionComponent as PipesSubprocessScriptCollectionComponent,
)
