from dagster_components import ComponentLoadContext
from dagster_components.core.component import component
from dagster_components.core.schema.objects import AssetSpecModel
from dagster_components.lib import PipesSubprocessScriptCollection
from dagster_components.lib.pipes_subprocess_script_collection import (
    PipesSubprocessScriptCollectionParams,
    PipesSubprocessScriptParams,
)


@component
def load(context: ComponentLoadContext) -> PipesSubprocessScriptCollection:
    params = PipesSubprocessScriptCollectionParams(
        scripts=[
            PipesSubprocessScriptParams(
                path="cool_script.py",
                assets=[
                    AssetSpecModel(
                        key="cool_script",
                        automation_condition="{{ automation_condition.eager() }}",
                    ),
                ],
            ),
        ]
    )
    return PipesSubprocessScriptCollection.load(params=params, context=context)
