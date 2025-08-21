from collections.abc import Sequence
from dataclasses import dataclass
from typing import Annotated, Literal, Optional, Union

from dagster_shared.record import as_dict, record

from dagster._core.definitions.asset_checks.asset_check_factories.metadata_bounds_checks import (
    build_metadata_bounds_checks,
)
from dagster._core.definitions.asset_checks.asset_check_factories.schema_change_checks import (
    build_column_schema_change_checks,
)
from dagster._core.definitions.asset_checks.asset_check_spec import AssetCheckSeverity
from dagster._core.definitions.asset_checks.asset_checks_definition import AssetChecksDefinition
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.definitions_class import Definitions
from dagster.components.component.component import Component
from dagster.components.core.context import ComponentLoadContext
from dagster.components.resolved.base import Resolvable
from dagster.components.resolved.context import ResolutionContext
from dagster.components.resolved.core_models import ResolvedAssetKey
from dagster.components.resolved.model import Resolver


def _resolve_asset_check_severity(context: ResolutionContext, model) -> AssetCheckSeverity:
    severity_str = context.resolve_value(model, as_type=str)
    return AssetCheckSeverity(severity_str)


ResolvedAssetCheckSeverity = Annotated[
    AssetCheckSeverity,
    Resolver(
        _resolve_asset_check_severity,
        model_field_type=str,
        description="The severity of the asset check.",
    ),
]


@record
class ColumnSchemaChangeParams(Resolvable):
    type: Literal["column_schema_change"]
    severity: ResolvedAssetCheckSeverity = AssetCheckSeverity.WARN

    def build_checks(self, key: AssetKey) -> Sequence[AssetChecksDefinition]:
        return build_column_schema_change_checks(
            assets=[key], **{k: v for k, v in as_dict(self).items() if k != "type"}
        )


@record
class MetadataBoundsParams(Resolvable):
    type: Literal["metadata_bounds"]
    metadata_key: str
    severity: ResolvedAssetCheckSeverity = AssetCheckSeverity.WARN
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    exclusive_min: bool = False
    exclusive_max: bool = False

    def build_checks(self, key: AssetKey) -> Sequence[AssetChecksDefinition]:
        return build_metadata_bounds_checks(
            assets=[key], **{k: v for k, v in as_dict(self).items() if k != "type"}
        )


def resolve_check_params(
    context: ResolutionContext, model
) -> Union[ColumnSchemaChangeParams, MetadataBoundsParams]:
    if model.type == "column_schema_change":
        return ColumnSchemaChangeParams.resolve_from_model(context, model)
    elif model.type == "metadata_bounds":
        return MetadataBoundsParams.resolve_from_model(context, model)
    else:
        raise ValueError(f"Invalid check type: {model.type}")


# Doesn't work for union right now
ResolvedMetadataCheckParams = Annotated[
    Union[ColumnSchemaChangeParams, MetadataBoundsParams],
    Resolver(
        resolve_check_params,
        model_field_type=Union[ColumnSchemaChangeParams.model(), MetadataBoundsParams.model()],
    ),
]


@dataclass
class MetadataCheck(Resolvable):
    key: ResolvedAssetKey
    params: ResolvedMetadataCheckParams

    def build_checks(self) -> Sequence[AssetChecksDefinition]:
        return self.params.build_checks(self.key)


@dataclass
class MetadataChecksComponent(Component, Resolvable):
    checks: Sequence[MetadataCheck]

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        return Definitions(
            asset_checks=[
                check for metadata_check in self.checks for check in metadata_check.build_checks()
            ]
        )
