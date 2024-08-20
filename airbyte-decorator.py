from datetime import datetime, timedelta
from typing import Any, Callable, Mapping, Optional

from dagster import (
    AssetExecutionContext,
    Definitions,
    DefinitionsLoadContext,
    DefinitionSource,
    DefinitionsReloadRequest,
    JsonMetadataValue,
    SensorResult,
    build_last_update_freshness_checks,
    defs_loader,
    sensor,
)

####################################################################################################
# This is code that would live inside the dagster-airbyte library
####################################################################################################


class AirbyteWorkspace:
    def __init__(self, name: str):
        self._name = name

    def build_defs(
        self, context: DefinitionsLoadContext, execution_fn: Optional[Callable] = None
    ) -> Definitions:
        existing_source: DefinitionSource = context.get_loaded_definition_source(self._name)
        if existing_source:
            # we end up here inside step worker and run worker
            airbyte_workspace_info = existing_source.metadata["dagster_airbyte/workspace"].value
        else:
            # we end up here inside the code server
            airbyte_workspace_info = self._fetch_workspace_info()

        return self._build_defs_from_workspace_info(airbyte_workspace_info, execution_fn)

    def _build_defs_from_workspace_info(
        self, workspace_info: Mapping[str, Any], execution_fn: Optional[Callable]
    ) -> Definitions:
        if execution_fn is None:

            def _default_execution_fn(context):
                yield from self.sync(context).stream()

            execution_fn = _default_execution_fn

        assets = []  # build AssetsDefinition using execution_fn
        return Definitions(
            assets=assets,
            sources=[
                DefinitionSource(
                    name=self._name,
                    metadata={"dagster_airbyte/workspace": JsonMetadataValue(workspace_info)},
                )
            ],
        )

    def _fetch_workspace_info(self):
        """Fetches data from Airbyte that can be used to construct a set of asset definitions."""
        return {}

    def sync(self, context: AssetExecutionContext):
        pass


####################################################################################################
# This is code that a user would write
####################################################################################################


workspace = AirbyteWorkspace(name="workspace1")


@sensor()
def my_reload_code_location_sensor(context):
    last_reload = datetime.strptime(context.cursor, "%Y-%m-%d %H:%M:%S.%f")
    if datetime.now() - last_reload > timedelta(minutes=5):
        return SensorResult(
            definitions_reload_requests=[DefinitionsReloadRequest.self()],
            cursor=str(datetime.now()),
        )


@defs_loader
def defs(context: DefinitionsLoadContext) -> Definitions:
    airbyte_defs = workspace.build_defs(context)
    freshness_checks = build_last_update_freshness_checks(airbyte_defs.assets)

    return Definitions.merge(
        airbyte_defs,
        Definitions(asset_checks=freshness_checks, sensors=[my_reload_code_location_sensor]),
    )
