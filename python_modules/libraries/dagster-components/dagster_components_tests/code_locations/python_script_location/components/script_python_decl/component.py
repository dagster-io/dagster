from dagster_components import AssetAttributesModel, ComponentLoadContext
from dagster_components.core.component import component_loader
from dagster_components.lib import PipesSubprocessScriptCollection
from dagster_components.lib.pipes_subprocess_script_collection import (
    PipesSubprocessScriptCollectionParams,
    PipesSubprocessScriptParams,
)


@component_loader
def load(context: ComponentLoadContext) -> PipesSubprocessScriptCollection:
    params = PipesSubprocessScriptCollectionParams(
        scripts=[
            PipesSubprocessScriptParams(
                path="cool_script.py",
                assets=[
                    AssetAttributesModel(
                        key="cool_script",
                        automation_condition="{{ automation_condition.eager() }}",
                    ),
                ],
            ),
        ]
    )
    return PipesSubprocessScriptCollection.load(params=params, context=context)
