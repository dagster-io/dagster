from abc import abstractmethod
from typing import AbstractSet, Any, Dict, Mapping, Optional, Sequence

from dagster import MaterializeResult, asset
from dagster._core.blueprints.blueprint import Blueprint, BlueprintDefinitions
from dagster._core.execution.context.compute import AssetExecutionContext


class BaseAssetBlueprint(Blueprint):
    """A blueprint for an asset definition whose materialization function is a databricks task."""

    asset_key: str
    deps: Sequence[str] = []
    description: Optional[str] = None
    metadata: Mapping[str, Any] = {}
    group_name: Optional[str] = None
    skippable: bool = False
    code_version: Optional[str] = None
    owners: Sequence[str] = []
    tags: Mapping[str, str] = {}

    task: Dict[str, Any]
    submit_args: Optional[Mapping[str, str]] = None

    def build_defs(self) -> BlueprintDefinitions:
        @asset(
            key=self.asset_key,
            deps=self.deps,
            description=self.description,
            metadata=self.metadata,
            group_name=self.group_name,
            output_required=not self.skippable,
            code_version=self.code_version,
            owners=self.owners,
            tags=self.tags,
            required_resource_keys=self.get_required_resource_keys(),
        )
        def _asset(context: AssetExecutionContext) -> MaterializeResult:
            return self.materialize(context=context)

        return BlueprintDefinitions(assets=[_asset])

    @staticmethod
    def get_required_resource_keys() -> AbstractSet[str]:
        return set()

    @abstractmethod
    def materialize(self, context: AssetExecutionContext) -> MaterializeResult:
        raise NotImplementedError()
