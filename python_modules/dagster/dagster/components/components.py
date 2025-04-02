from dagster.components.core.defs_module import DefsFolderComponent as DefsFolderComponent
from dagster.components.lib.definitions_component import (
    DefinitionsComponent as DefinitionsComponent,
)
from dagster.components.lib.pipes_subprocess_script_collection import (
    PipesSubprocessScriptCollectionComponent as PipesSubprocessScriptCollectionComponent,
)

# These just modify the exsiting Dagster decorators
from dagster.components.lib.shim_components.asset import asset as asset
from dagster.components.lib.shim_components.schedule import schedule as schedule
from dagster.components.lib.shim_components.sensor import sensor as sensor
