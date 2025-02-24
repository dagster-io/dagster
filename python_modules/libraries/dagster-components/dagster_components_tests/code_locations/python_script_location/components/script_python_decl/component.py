from dagster_components import ComponentLoadContext
from dagster_components.core.component import component
from dagster_components.core.schema.objects import AssetSpecSchema
from dagster_components.lib import PipesSubprocessScriptCollection
from dagster_components.lib.pipes_subprocess_script_collection import (
    PipesSubprocessScriptCollectionSchema,
    PipesSubprocessScriptSchema,
)


@component
def load(context: ComponentLoadContext) -> PipesSubprocessScriptCollection:
    attributes = PipesSubprocessScriptCollectionSchema(
        scripts=[
            PipesSubprocessScriptSchema(
                path="cool_script.py",
                assets=[
                    AssetSpecSchema(
                        key="cool_script",
                        automation_condition="{{ automation_condition.eager() }}",
                    ),
                ],
            ),
        ]
    )
    return PipesSubprocessScriptCollection.load(attributes=attributes, context=context)
