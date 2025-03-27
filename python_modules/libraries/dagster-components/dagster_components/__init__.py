from dagster_shared.libraries import DagsterLibraryRegistry
from dagster_shared.serdes.objects import LibraryObjectKey as LibraryObjectKey

from dagster_components.component.component import Component as Component
from dagster_components.component.component_loader import component as component
from dagster_components.component.component_scaffolder import (
    DefaultComponentScaffolder as DefaultComponentScaffolder,
)
from dagster_components.component_scaffolding import (
    scaffold_component_yaml as scaffold_component_yaml,
)
from dagster_components.core.context import ComponentLoadContext as ComponentLoadContext
from dagster_components.core.load_defs import (
    build_component_defs as build_component_defs,
    load_defs as load_defs,
)
from dagster_components.resolved.base import Resolvable as Resolvable
from dagster_components.resolved.context import ResolutionContext as ResolutionContext
from dagster_components.resolved.core_models import (
    AssetAttributesModel as AssetAttributesModel,
    AssetPostProcessorModel as AssetPostProcessorModel,
    AssetSpecModel as AssetSpecModel,
    OpSpecModel as OpSpecModel,
)
from dagster_components.resolved.metadata import ResolvableFieldInfo as ResolvableFieldInfo
from dagster_components.resolved.model import (
    ResolvableModel as ResolvableModel,
    ResolvedFrom as ResolvedFrom,
    ResolvedKwargs as ResolvedKwargs,
    Resolver as Resolver,
)
from dagster_components.scaffold.scaffold import (
    Scaffolder as Scaffolder,
    ScaffolderUnavailableReason as ScaffolderUnavailableReason,
    ScaffoldRequest as ScaffoldRequest,
)
from dagster_components.version import __version__ as __version__

DagsterLibraryRegistry.register("dagster-components", __version__)
