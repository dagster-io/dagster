from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional

import yaml

from dagster import (
    AssetExecutionContext,
    AssetKey,
    AssetMaterialization,
    AssetsDefinition,
    AssetSpec,
    ConfigurableResource,
    _check as check,
    multi_asset,
)
from dagster._annotations import public


def replicate(replication_configuration_yaml: Path) -> Iterator[Mapping[str, Any]]:
    data = yaml.safe_load(replication_configuration_yaml.read_text())
    for table in data.get("tables"):
        # < perform replication here, and get status >
        yield {"table": table.get("name"), "status": "success"}


class ReplicationProject:
    def __init__(self, replication_configuration_yaml: str):
        self.replication_configuration_yaml = replication_configuration_yaml

    def load(self):
        return yaml.safe_load(Path(self.replication_configuration_yaml).read_text())


class ReplicationResource(ConfigurableResource):
    @public
    def run(self, context: AssetExecutionContext) -> Iterator[AssetMaterialization]:
        metadata_by_key = context.assets_def.metadata_by_key
        first_asset_metadata = next(iter(metadata_by_key.values()))

        project = check.inst(
            first_asset_metadata.get("replication_project"),
            ReplicationProject,
        )

        translator = check.inst(
            first_asset_metadata.get("replication_translator"),
            ReplicationTranslator,
        )

        results = replicate(Path(project.replication_configuration_yaml))
        for table in results:
            if table.get("status") == "SUCCESS":
                yield AssetMaterialization(
                    asset_key=translator.get_asset_key(table), metadata=table
                )


@dataclass
class ReplicationTranslator:
    @public
    def get_asset_key(self, table_definition: Mapping[str, str]) -> AssetKey:
        return AssetKey(str(table_definition.get("name")))


def custom_replication_assets(
    *,
    replication_project: ReplicationProject,
    name: Optional[str] = None,
    group_name: Optional[str] = None,
    translator: Optional[ReplicationTranslator] = None,
) -> Callable[[Callable[..., Any]], AssetsDefinition]:
    project = replication_project.load()

    translator = (
        check.opt_inst_param(translator, "translator", ReplicationTranslator)
        or ReplicationTranslator()
    )

    return multi_asset(
        name=name,
        group_name=group_name,
        specs=[
            AssetSpec(
                key=translator.get_asset_key(table),
                metadata={
                    "replication_project": project,
                    "replication_translator": translator,
                },
            )
            for table in project.get("tables")
        ],
    )
