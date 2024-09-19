from abc import abstractmethod
from typing import AbstractSet, Any, Mapping, Optional, Sequence

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.assets import unique_id_from_asset_and_check_keys
from dagster._core.definitions.decorators.asset_decorator import multi_asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.execution.context.compute import AssetExecutionContext
from dagster._model import DagsterModel

from dagster_blueprints.blueprint import Blueprint


class AssetSpecModel(DagsterModel):
    key: str
    deps: Sequence[str] = []
    description: Optional[str] = None
    metadata: Mapping[str, Any] = {}
    group_name: Optional[str] = None
    skippable: bool = False
    code_version: Optional[str] = None
    owners: Sequence[str] = []
    tags: Mapping[str, str] = {}

    def to_asset_spec(self) -> AssetSpec:
        return AssetSpec(
            **{
                **self.__dict__,
                "key": AssetKey.from_user_string(self.key),
            },
        )


class BlueprintAssetsDefinition(Blueprint):
    """A blueprint that produces an AssetsDefinition."""

    assets: Sequence[AssetSpecModel]

    def build_defs(self) -> Definitions:
        specs = [spec_model.to_asset_spec() for spec_model in self.assets]

        @multi_asset(
            name=f"assets_{unique_id_from_asset_and_check_keys([spec.key for spec in specs])}",
            specs=specs,
            required_resource_keys=self.get_required_resource_keys(),
        )
        def _assets(context: AssetExecutionContext):
            return self.materialize(context=context)

        return Definitions(assets=[_assets])

    @staticmethod
    def get_required_resource_keys() -> AbstractSet[str]:
        return set()

    @abstractmethod
    def materialize(self, context: AssetExecutionContext):
        raise NotImplementedError()
