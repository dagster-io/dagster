from dagster._core.libraries import DagsterLibraryRegistry

from dagster_components.core.component import (
    Component as Component,
    ComponentLoadContext as ComponentLoadContext,
    ComponentRegistry as ComponentRegistry,
    component as component,
)
from dagster_components.core.component_defs_builder import (
    build_defs_from_toplevel_components_folder as build_defs_from_toplevel_components_folder,
)
from dagster_components.version import __version__ as __version__

DagsterLibraryRegistry.register("dagster-components", __version__)
