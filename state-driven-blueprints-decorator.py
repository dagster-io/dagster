from typing import Any, Mapping

from dagster import (
    Definitions,
    DefinitionsLoadContext,
    DefinitionSource,
    JsonMetadataValue,
    build_last_update_freshness_checks,
    defs_loader,
)

####################################################################################################
# This is code that would live inside the core Dagster library of dagster-blueprints package
####################################################################################################


class StateDrivenBlueprintsLoader:
    def __init__(self, name: str, schema):
        self._name = name
        self._schema = schema

    def build_defs(self, context: DefinitionsLoadContext) -> Definitions:
        existing_source: DefinitionSource = context.get_loaded_definition_source(self._name)
        if existing_source:
            # we end up here inside step worker and run worker

            # note that we don't want to fetch from the blueprints store in this case, because the
            # blueprints store could have been updated since the enclosing run was launched.
            blueprints = existing_source.metadata["blueprints"].value
        else:
            # we end up here inside the code server
            blueprints = context.get_blueprints_from_blueprints_store()

        return self._build_defs_from_blueprints(blueprints)

    def _build_defs_from_blueprints(self, blueprints: Mapping[str, Any]) -> Definitions:
        assets = []  # build AssetsDefinition using blueprints
        return Definitions(
            assets=assets,
            sources=[
                DefinitionSource(
                    name=self._name,
                    metadata={
                        "blueprints": JsonMetadataValue(blueprints),
                        "schema": JsonMetadataValue(self._schema),
                    },
                )
            ],
        )


####################################################################################################
# This is code that a user would write
####################################################################################################


embedded_elt_blueprints_loader = StateDrivenBlueprintsLoader(name="embedded_elt")


@defs_loader
def defs(context: DefinitionsLoadContext) -> Definitions:
    defs_from_blueprints = embedded_elt_blueprints_loader.build_defs(context)
    freshness_checks = build_last_update_freshness_checks(defs_from_blueprints.assets)

    return Definitions.merge(defs_from_blueprints, Definitions(asset_checks=freshness_checks))
