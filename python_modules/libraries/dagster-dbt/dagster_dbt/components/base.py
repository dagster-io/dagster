from abc import ABC
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Annotated, Any, Optional

import dagster as dg
from dagster._utils.cached_method import cached_method
from dagster.components.component.state_backed_component import StateBackedComponent
from dagster.components.resolved.core_models import OpSpec
from dagster.components.resolved.model import Resolver

from dagster_dbt.asset_utils import (
    DAGSTER_DBT_EXCLUDE_METADATA_KEY,
    DAGSTER_DBT_SELECT_METADATA_KEY,
    DAGSTER_DBT_SELECTOR_METADATA_KEY,
    DBT_DEFAULT_EXCLUDE,
    DBT_DEFAULT_SELECT,
    DBT_DEFAULT_SELECTOR,
    get_node,
)
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator, DagsterDbtTranslatorSettings
from dagster_dbt.dbt_manifest_asset_selection import DbtManifestAssetSelection

if TYPE_CHECKING:
    from dagster_dbt.dbt_project import DbtProject


@dataclass(frozen=True)
class DagsterDbtComponentTranslatorSettings(DagsterDbtTranslatorSettings):
    """Subclass of DagsterDbtTranslatorSettings that enables code references by default."""

    enable_code_references: bool = True


@dataclass(kw_only=True)
class BaseDbtComponent(StateBackedComponent, dg.Resolvable, ABC):
    """Base class for dbt components (both local and cloud)."""

    op: Annotated[
        Optional[OpSpec],
        Resolver.default(
            description="Op related arguments to set on the generated @dbt_assets",
            examples=[
                {
                    "name": "some_op",
                    "tags": {"tag1": "value"},
                    "backfill_policy": {"type": "single_run"},
                },
            ],
        ),
    ] = None
    select: Annotated[
        str,
        Resolver.default(
            description="The dbt selection string for models you want to include.",
            examples=["tag:dagster"],
        ),
    ] = DBT_DEFAULT_SELECT
    exclude: Annotated[
        str,
        Resolver.default(
            description="The dbt selection string for models you want to exclude.",
            examples=["tag:skip_dagster"],
        ),
    ] = DBT_DEFAULT_EXCLUDE
    selector: Annotated[
        str,
        Resolver.default(
            description="The dbt selector for models you want to include.",
            examples=["custom_selector"],
        ),
    ] = DBT_DEFAULT_SELECTOR
    translation_settings: Annotated[
        Optional[DagsterDbtComponentTranslatorSettings],
        Resolver.default(
            description="Allows enabling or disabling various features for translating dbt models in to Dagster assets.",
            examples=[
                {
                    "enable_source_tests_as_checks": True,
                },
            ],
        ),
    ] = field(default_factory=lambda: DagsterDbtComponentTranslatorSettings())

    @property
    @cached_method
    def translator(self) -> DagsterDbtTranslator:
        return DagsterDbtTranslator(self.translation_settings)

    def _get_op_spec(self, op_name: Optional[str] = None) -> OpSpec:
        if op_name is None:
            op_name = self.op.name if self.op else None

        default = self.op or OpSpec(name=op_name or "dbt_assets")
        return default.model_copy(
            update=dict(
                tags={
                    **(default.tags or {}),
                    **({DAGSTER_DBT_SELECT_METADATA_KEY: self.select} if self.select else {}),
                    **({DAGSTER_DBT_EXCLUDE_METADATA_KEY: self.exclude} if self.exclude else {}),
                    **({DAGSTER_DBT_SELECTOR_METADATA_KEY: self.selector} if self.selector else {}),
                }
            )
        )

    def get_asset_selection(
        self, select: str, exclude: str = DBT_DEFAULT_EXCLUDE, manifest_path: Optional[str] = None
    ) -> DbtManifestAssetSelection:
        if manifest_path is None:
            raise NotImplementedError(
                "Subclasses must provide manifest_path or override get_asset_selection"
            )

        return DbtManifestAssetSelection.build(
            manifest=manifest_path,
            dagster_dbt_translator=self.translator,
            select=select,
            exclude=exclude,
        )

    def get_resource_props(self, manifest: Mapping[str, Any], unique_id: str) -> Mapping[str, Any]:
        """Given a parsed manifest and a dbt unique_id, returns the dictionary of properties."""
        return get_node(manifest, unique_id)

    def get_asset_spec(
        self, manifest: Mapping[str, Any], unique_id: str, project: Optional["DbtProject"] = None
    ) -> dg.AssetSpec:
        """Generates an AssetSpec for a given dbt node."""
        return self.translator.get_asset_spec(manifest, unique_id, project)

    def get_asset_check_spec(
        self,
        asset_spec: dg.AssetSpec,
        manifest: Mapping[str, Any],
        unique_id: str,
        project: Optional["DbtProject"] = None,
    ) -> Optional[dg.AssetCheckSpec]:
        return self.translator.get_asset_check_spec(asset_spec, manifest, unique_id, project)
