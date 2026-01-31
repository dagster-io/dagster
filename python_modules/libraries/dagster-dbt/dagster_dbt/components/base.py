from abc import ABC
from collections.abc import Mapping
from typing import TYPE_CHECKING, Annotated, Any, Optional

import dagster as dg
from dagster._utils.cached_method import cached_method
from dagster.components.component.state_backed_component import StateBackedComponent
from dagster.components.resolved.core_models import OpSpec
from dagster.components.resolved.model import Resolver
from pydantic import Field

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

if TYPE_CHECKING:
    from dagster_dbt.dbt_project import DbtProject


class DagsterDbtComponentTranslatorSettings(DagsterDbtTranslatorSettings):
    """Subclass of DagsterDbtTranslatorSettings that enables code references by default."""

    enable_code_references: bool = True


class BaseDbtComponent(StateBackedComponent, dg.Resolvable, dg.Model, ABC):
    """Base class for dbt components (both local and cloud)."""

    model_config = {"arbitrary_types_allowed": True}

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

    translation_settings: DagsterDbtComponentTranslatorSettings = Field(
        default_factory=DagsterDbtComponentTranslatorSettings,
        description="Allows enabling or disabling various features for translating dbt models in to Dagster assets.",
        examples=[
            {
                "enable_source_tests_as_checks": True,
            },
        ],
    )

    @property
    @cached_method
    def translator(self) -> DagsterDbtTranslator:
        return DagsterDbtTranslator(self.translation_settings)

    @property
    def op_config_schema(self) -> Optional[type[dg.Config]]:
        return None

    @property
    def config_cls(self) -> Optional[type[dg.Config]]:
        """Internal property that returns the config schema for the op.

        Delegates to op_config_schema for backwards compatibility and consistency
        with other component types.
        """
        return self.op_config_schema

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

    def get_resource_props(self, manifest: Mapping[str, Any], unique_id: str) -> Mapping[str, Any]:
        """Given a parsed manifest and a dbt unique_id, returns the dictionary of properties
        for the corresponding dbt resource (e.g. model, seed, snapshot, source) as defined
        in your dbt project. This can be used as a convenience method when overriding the
        `get_asset_spec` method.

        Args:
            manifest (Mapping[str, Any]): The parsed manifest of the dbt project.
            unique_id (str): The unique_id of the dbt resource.

        Returns:
            Mapping[str, Any]: The dictionary of properties for the corresponding dbt resource.

        Examples:
            .. code-block:: python

                class CustomDbtProjectComponent(DbtProjectComponent):

                    def get_asset_spec(self, manifest: Mapping[str, Any], unique_id: str, project: Optional[DbtProject] = None) -> dg.AssetSpec:
                        base_spec = super().get_asset_spec(manifest, unique_id, project)
                        resource_props = self.get_resource_props(manifest, unique_id)
                        if resource_props["meta"].get("use_custom_group"):
                            return base_spec.replace_attributes(group_name="custom_group")
                        else:
                            return base_spec
        """
        return get_node(manifest, unique_id)

    def get_asset_spec(
        self, manifest: Mapping[str, Any], unique_id: str, project: Optional["DbtProject"] = None
    ) -> dg.AssetSpec:
        """Generates an AssetSpec for a given dbt node.

        This method can be overridden in a subclass to customize how dbt nodes are converted
        to Dagster asset specs. By default, it delegates to the configured DagsterDbtTranslator.

        Args:
            manifest: The dbt manifest dictionary containing information about all dbt nodes
            unique_id: The unique identifier for the dbt node (e.g., "model.my_project.my_model")
            project: The DbtProject object, if available

        Returns:
            An AssetSpec that represents the dbt node as a Dagster asset

        Example:
            Override this method to add custom tags to all dbt models:

            .. code-block:: python

                from dagster_dbt import DbtProjectComponent
                import dagster as dg

                class CustomDbtProjectComponent(DbtProjectComponent):
                    def get_asset_spec(self, manifest, unique_id, project):
                        base_spec = super().get_asset_spec(manifest, unique_id, project)
                        return base_spec.replace_attributes(
                            tags={**base_spec.tags, "custom_tag": "my_value"}
                        )
        """
        return self.translator.get_asset_spec(manifest, unique_id, project)

    def get_asset_check_spec(
        self,
        asset_spec: dg.AssetSpec,
        manifest: Mapping[str, Any],
        unique_id: str,
        project: Optional["DbtProject"] = None,
    ) -> Optional[dg.AssetCheckSpec]:
        return self.translator.get_asset_check_spec(asset_spec, manifest, unique_id, project)
