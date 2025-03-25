from dagster_components.component.component_loader import component
from dagster_components.core.context import DefsModuleLoadContext
from dagster_components.lib.pipes_subprocess_script_collection import (
    PipesSubprocessScriptCollectionComponent,
    PipesSubprocessScriptCollectionModel,
    PipesSubprocessScriptModel,
)
from dagster_components.resolved.core_models import AssetSpecModel


@component
def load(context: DefsModuleLoadContext) -> PipesSubprocessScriptCollectionComponent:
    attributes = PipesSubprocessScriptCollectionModel(
        scripts=[
            PipesSubprocessScriptModel(
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
    return PipesSubprocessScriptCollectionComponent.load(attributes=attributes, context=context)
