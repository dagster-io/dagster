import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from dagster import (
    AssetCheckSpec,
    AssetDep,
    AssetKey,
    AssetSpec,
    AutoMaterializePolicy,
    AutomationCondition,
    DagsterInvalidDefinitionError,
    MetadataValue,
    PartitionMapping,
)
from dagster._annotations import beta, public
from dagster._core.definitions.metadata.source_code import (
    CodeReferencesMetadataSet,
    CodeReferencesMetadataValue,
    LocalFileCodeReference,
)
from dagster._core.definitions.partitions.definition import PartitionsDefinition
from dagster._utils.tags import is_valid_tag_key
from dagster.components.resolved.base import Resolvable
from dagster_shared import check

from dagster_dbt.asset_utils import (
    DAGSTER_DBT_MANIFEST_METADATA_KEY,
    DAGSTER_DBT_PROJECT_METADATA_KEY,
    DAGSTER_DBT_TRANSLATOR_METADATA_KEY,
    DAGSTER_DBT_UNIQUE_ID_METADATA_KEY,
    default_asset_check_fn,
    default_asset_key_fn,
    default_auto_materialize_policy_fn,
    default_code_version_fn,
    default_description_fn,
    default_group_from_dbt_resource_props,
    default_metadata_from_dbt_resource_props,
    default_owners_from_dbt_resource_props,
    get_node,
    get_upstream_unique_ids,
    has_self_dependency,
)

if TYPE_CHECKING:
    from dagster_dbt.dbt_project import DbtProject


@dataclass(frozen=True)
class DagsterDbtTranslatorSettings(Resolvable):
    """Settings to enable Dagster features for your dbt project.

    Args:
        enable_asset_checks (bool): Whether to load dbt tests as Dagster asset checks.
            Defaults to True.
        enable_duplicate_source_asset_keys (bool): Whether to allow dbt sources with duplicate
            Dagster asset keys. Defaults to False.
        enable_code_references (bool): Whether to enable Dagster code references for dbt resources.
            Defaults to False.
        enable_dbt_selection_by_name (bool): Whether to enable selecting dbt resources by name,
            rather than fully qualified name. Defaults to False.
        enable_source_tests_as_checks (bool): Whether to load dbt source tests as Dagster asset checks.
            Defaults to False. If False, asset observations will be emitted for source tests.
        enable_source_metadata (bool): Whether to include metadata on AssetDep objects for dbt sources.
            If set to True, enables the ability to remap upstream asset keys based on table name. Defaults to False.
    """

    enable_asset_checks: bool = True
    enable_duplicate_source_asset_keys: bool = False
    enable_code_references: bool = False
    enable_dbt_selection_by_name: bool = False
    enable_source_tests_as_checks: bool = False
    enable_source_metadata: bool = False


class DagsterDbtTranslator:
    """Holds a set of methods that derive Dagster asset definition metadata given a representation
    of a dbt resource (models, tests, sources, etc).

    This class is exposed so that methods can be overriden to customize how Dagster asset metadata
    is derived.
    """

    def __init__(self, settings: Optional[DagsterDbtTranslatorSettings] = None):
        """Initialize the translator.

        Args:
            settings (Optional[DagsterDbtTranslatorSettings]): Settings for the translator.
        """
        self._settings = settings or DagsterDbtTranslatorSettings()

    @property
    def settings(self) -> DagsterDbtTranslatorSettings:
        if not hasattr(self, "_settings"):
            self._settings = DagsterDbtTranslatorSettings()

        return self._settings

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

                class CustomDagsterDbtTranslator(DagsterDbtTranslator):

                    def get_asset_spec(self, manifest: Mapping[str, Any], unique_id: str, project: Optional[DbtProject]) -> dg.AssetSpec:
                        base_spec = super().get_asset_spec(manifest, unique_id, project)
                        resource_props = self.get_resource_props(manifest, unique_id)
                        if resource_props["meta"].get("use_custom_group"):
                            return base_spec.replace_attributes(group_name="custom_group")
                        else:
                            return base_spec
        """
        return get_node(manifest, unique_id)

    def get_asset_spec(
        self,
        manifest: Mapping[str, Any],
        unique_id: str,
        project: Optional["DbtProject"],
    ) -> AssetSpec:
        """Returns an AssetSpec representing a specific dbt resource."""
        # memoize resolution for a given manifest & unique_id
        # since we recursively call get_asset_spec for dependencies
        memo_id = (id(manifest), unique_id, id(project))

        # Don't initialize this in the constructor in case a subclass does not call __init__
        if not hasattr(self, "_resolved_specs"):
            self._resolved_specs = {}

        if memo_id in self._resolved_specs:
            return self._resolved_specs[memo_id]

        group_props = {group["name"]: group for group in manifest.get("groups", {}).values()}
        resource_props = self.get_resource_props(manifest, unique_id)

        # calculate the dependencies for the asset
        upstream_ids = get_upstream_unique_ids(manifest, resource_props)
        deps: list[AssetDep] = []
        for upstream_id in upstream_ids:
            spec = self.get_asset_spec(manifest, upstream_id, project)
            partition_mapping = self.get_partition_mapping(
                resource_props, self.get_resource_props(manifest, upstream_id)
            )

            deps.append(
                AssetDep(
                    asset=spec.key,
                    partition_mapping=partition_mapping,
                    metadata=spec.metadata
                    if self.settings.enable_source_metadata and upstream_id.startswith("source")
                    else None,
                )
            )

        self_partition_mapping = self.get_partition_mapping(resource_props, resource_props)
        if self_partition_mapping and has_self_dependency(resource_props):
            deps.append(
                AssetDep(
                    asset=self.get_asset_key(resource_props),
                    partition_mapping=self_partition_mapping,
                )
            )

        resource_group_props = group_props.get(resource_props.get("group") or "")
        if resource_group_props:
            owners_resource_props = {
                **resource_props,
                # this overrides the group key in resource_props, which is bad as
                # this key is not always empty and this dictionary generally differs
                # in structure from other inputs, but this is necessary for backcompat
                **({"group": resource_group_props} if resource_group_props else {}),
            }
        else:
            owners_resource_props = resource_props

        spec = AssetSpec(
            key=self.get_asset_key(resource_props),
            deps=deps,
            description=self.get_description(resource_props),
            metadata=self.get_metadata(resource_props),
            skippable=True,
            group_name=self.get_group_name(resource_props),
            code_version=self.get_code_version(resource_props),
            automation_condition=self.get_automation_condition(resource_props),
            owners=self.get_owners(owners_resource_props),
            tags=self.get_tags(resource_props),
            kinds={"dbt", manifest.get("metadata", {}).get("adapter_type", "dbt")},
            partitions_def=self.get_partitions_def(resource_props),
        )

        # add integration-specific metadata to the spec
        spec = spec.merge_attributes(
            metadata={
                DAGSTER_DBT_MANIFEST_METADATA_KEY: DbtManifestWrapper(manifest=manifest),
                DAGSTER_DBT_TRANSLATOR_METADATA_KEY: self,
                DAGSTER_DBT_UNIQUE_ID_METADATA_KEY: resource_props["unique_id"],
                **({DAGSTER_DBT_PROJECT_METADATA_KEY: project} if project else {}),
            }
        )

        # Add dbt Core project_id for tracking/debugging
        project_id = manifest.get("metadata", {}).get("project_id")
        if project_id:
            spec = spec.merge_attributes(
                metadata={"dagster_dbt/project_id": MetadataValue.text(project_id)}
            )

        if self.settings.enable_code_references:
            if not project:
                raise DagsterInvalidDefinitionError(
                    "enable_code_references requires a DbtProject to be supplied"
                    " to the @dbt_assets decorator."
                )

            spec = spec.replace_attributes(
                metadata=_attach_sql_model_code_reference(
                    existing_metadata=spec.metadata,
                    dbt_resource_props=resource_props,
                    project=project,
                )
            )

        self._resolved_specs[memo_id] = spec

        return self._resolved_specs[memo_id]

    def get_asset_check_spec(
        self,
        asset_spec: AssetSpec,
        manifest: Mapping[str, Any],
        unique_id: str,
        project: Optional["DbtProject"],
    ) -> Optional[AssetCheckSpec]:
        return default_asset_check_fn(
            manifest=manifest,
            dagster_dbt_translator=self,
            asset_key=asset_spec.key,
            test_unique_id=unique_id,
            project=project,
        )

    @public
    def get_asset_key(self, dbt_resource_props: Mapping[str, Any]) -> AssetKey:
        """A function that takes a dictionary representing properties of a dbt resource, and
        returns the Dagster asset key that represents that resource.

        Note that a dbt resource is unrelated to Dagster's resource concept, and simply represents
        a model, seed, snapshot or source in a given dbt project. You can learn more about dbt
        resources and the properties available in this dictionary here:
        https://docs.getdbt.com/reference/artifacts/manifest-json#resource-details

        This method can be overridden to provide a custom asset key for a dbt resource.

        Args:
            dbt_resource_props (Mapping[str, Any]): A dictionary representing the dbt resource.

        Returns:
            AssetKey: The Dagster asset key for the dbt resource.

        Examples:
            Adding a prefix to the default asset key generated for each dbt resource:

            .. code-block:: python

                from typing import Any, Mapping

                from dagster import AssetKey
                from dagster_dbt import DagsterDbtTranslator


                class CustomDagsterDbtTranslator(DagsterDbtTranslator):
                    def get_asset_key(self, dbt_resource_props: Mapping[str, Any]) -> AssetKey:
                        return super().get_asset_key(dbt_resource_props).with_prefix("prefix")

            Adding a prefix to the default asset key generated for each dbt resource, but only for dbt sources:

            .. code-block:: python

                from typing import Any, Mapping

                from dagster import AssetKey
                from dagster_dbt import DagsterDbtTranslator


                class CustomDagsterDbtTranslator(DagsterDbtTranslator):
                    def get_asset_key(self, dbt_resource_props: Mapping[str, Any]) -> AssetKey:
                        asset_key = super().get_asset_key(dbt_resource_props)

                        if dbt_resource_props["resource_type"] == "source":
                            asset_key = asset_key.with_prefix("my_prefix")

                        return asset_key
        """
        return default_asset_key_fn(dbt_resource_props)

    @public
    @beta(emit_runtime_warning=False)
    def get_partition_mapping(
        self,
        dbt_resource_props: Mapping[str, Any],
        dbt_parent_resource_props: Mapping[str, Any],
    ) -> Optional[PartitionMapping]:
        """A function that takes two dictionaries: the first, representing properties of a dbt
        resource; and the second, representing the properties of a parent dependency to the first
        dbt resource. The function returns the Dagster partition mapping for the dbt dependency.

        Note that a dbt resource is unrelated to Dagster's resource concept, and simply represents
        a model, seed, snapshot or source in a given dbt project. You can learn more about dbt
        resources and the properties available in this dictionary here:
        https://docs.getdbt.com/reference/artifacts/manifest-json#resource-details

        This method can be overridden to provide a custom partition mapping for a dbt dependency.

        Args:
            dbt_resource_props (Mapping[str, Any]):
                A dictionary representing the dbt child resource.
            dbt_parent_resource_props (Mapping[str, Any]):
                A dictionary representing the dbt parent resource, in relationship to the child.

        Returns:
            Optional[PartitionMapping]:
                The Dagster partition mapping for the dbt resource. If None is returned, the
                default partition mapping will be used.
        """
        return None

    @public
    def get_description(self, dbt_resource_props: Mapping[str, Any]) -> str:
        """A function that takes a dictionary representing properties of a dbt resource, and
        returns the Dagster description for that resource.

        Note that a dbt resource is unrelated to Dagster's resource concept, and simply represents
        a model, seed, snapshot or source in a given dbt project. You can learn more about dbt
        resources and the properties available in this dictionary here:
        https://docs.getdbt.com/reference/artifacts/manifest-json#resource-details

        This method can be overridden to provide a custom description for a dbt resource.

        Args:
            dbt_resource_props (Mapping[str, Any]): A dictionary representing the dbt resource.

        Returns:
            str: The description for the dbt resource.

        Examples:
            .. code-block:: python

                from typing import Any, Mapping

                from dagster_dbt import DagsterDbtTranslator


                class CustomDagsterDbtTranslator(DagsterDbtTranslator):
                    def get_description(self, dbt_resource_props: Mapping[str, Any]) -> str:
                        return "custom description"
        """
        return default_description_fn(dbt_resource_props)

    @public
    def get_metadata(self, dbt_resource_props: Mapping[str, Any]) -> Mapping[str, Any]:
        """A function that takes a dictionary representing properties of a dbt resource, and
        returns the Dagster metadata for that resource.

        Note that a dbt resource is unrelated to Dagster's resource concept, and simply represents
        a model, seed, snapshot or source in a given dbt project. You can learn more about dbt
        resources and the properties available in this dictionary here:
        https://docs.getdbt.com/reference/artifacts/manifest-json#resource-details

        This method can be overridden to provide a custom metadata for a dbt resource.

        Args:
            dbt_resource_props (Mapping[str, Any]): A dictionary representing the dbt resource.

        Returns:
            Mapping[str, Any]: A dictionary representing the Dagster metadata for the dbt resource.

        Examples:
            .. code-block:: python

                from typing import Any, Mapping

                from dagster_dbt import DagsterDbtTranslator


                class CustomDagsterDbtTranslator(DagsterDbtTranslator):
                    def get_metadata(self, dbt_resource_props: Mapping[str, Any]) -> Mapping[str, Any]:
                        return {"custom": "metadata"}
        """
        return default_metadata_from_dbt_resource_props(dbt_resource_props)

    @public
    def get_tags(self, dbt_resource_props: Mapping[str, Any]) -> Mapping[str, str]:
        """A function that takes a dictionary representing properties of a dbt resource, and
        returns the Dagster tags for that resource.

        Note that a dbt resource is unrelated to Dagster's resource concept, and simply represents
        a model, seed, snapshot or source in a given dbt project. You can learn more about dbt
        resources and the properties available in this dictionary here:
        https://docs.getdbt.com/reference/artifacts/manifest-json#resource-details

        dbt tags are strings, but Dagster tags are key-value pairs. To bridge this divide, the dbt
        tag string is used as the Dagster tag key, and the Dagster tag value is set to the empty
        string, "".

        Any dbt tags that don't match Dagster's supported tag key format (e.g. they contain
        unsupported characters) will be ignored.

        This method can be overridden to provide custom tags for a dbt resource.

        Args:
            dbt_resource_props (Mapping[str, Any]): A dictionary representing the dbt resource.

        Returns:
            Mapping[str, str]: A dictionary representing the Dagster tags for the dbt resource.

        Examples:
            .. code-block:: python

                from typing import Any, Mapping

                from dagster_dbt import DagsterDbtTranslator


                class CustomDagsterDbtTranslator(DagsterDbtTranslator):
                    def get_tags(self, dbt_resource_props: Mapping[str, Any]) -> Mapping[str, str]:
                        return {"custom": "tag"}
        """
        tags = dbt_resource_props.get("tags", [])
        return {tag: "" for tag in tags if is_valid_tag_key(tag)}

    @public
    def get_group_name(self, dbt_resource_props: Mapping[str, Any]) -> Optional[str]:
        """A function that takes a dictionary representing properties of a dbt resource, and
        returns the Dagster group name for that resource.

        Note that a dbt resource is unrelated to Dagster's resource concept, and simply represents
        a model, seed, snapshot or source in a given dbt project. You can learn more about dbt
        resources and the properties available in this dictionary here:
        https://docs.getdbt.com/reference/artifacts/manifest-json#resource-details

        This method can be overridden to provide a custom group name for a dbt resource.

        Args:
            dbt_resource_props (Mapping[str, Any]): A dictionary representing the dbt resource.

        Returns:
            Optional[str]: A Dagster group name.

        Examples:
            .. code-block:: python

                from typing import Any, Mapping

                from dagster_dbt import DagsterDbtTranslator


                class CustomDagsterDbtTranslator(DagsterDbtTranslator):
                    def get_group_name(self, dbt_resource_props: Mapping[str, Any]) -> Optional[str]:
                        return "custom_group_prefix" + dbt_resource_props.get("config", {}).get("group")
        """
        return default_group_from_dbt_resource_props(dbt_resource_props)

    @public
    def get_code_version(self, dbt_resource_props: Mapping[str, Any]) -> Optional[str]:
        """A function that takes a dictionary representing properties of a dbt resource, and
        returns the Dagster code version for that resource.

        Note that a dbt resource is unrelated to Dagster's resource concept, and simply represents
        a model, seed, snapshot or source in a given dbt project. You can learn more about dbt
        resources and the properties available in this dictionary here:
        https://docs.getdbt.com/reference/artifacts/manifest-json#resource-details

        This method can be overridden to provide a custom code version for a dbt resource.

        Args:
            dbt_resource_props (Mapping[str, Any]): A dictionary representing the dbt resource.

        Returns:
            Optional[str]: A Dagster code version.

        Examples:
            .. code-block:: python

                from typing import Any, Mapping

                from dagster_dbt import DagsterDbtTranslator


                class CustomDagsterDbtTranslator(DagsterDbtTranslator):
                    def get_code_version(self, dbt_resource_props: Mapping[str, Any]) -> Optional[str]:
                        return dbt_resource_props["checksum"]["checksum"]
        """
        return default_code_version_fn(dbt_resource_props)

    @public
    def get_owners(self, dbt_resource_props: Mapping[str, Any]) -> Optional[Sequence[str]]:
        """A function that takes a dictionary representing properties of a dbt resource, and
        returns the Dagster owners for that resource.

        Note that a dbt resource is unrelated to Dagster's resource concept, and simply represents
        a model, seed, snapshot or source in a given dbt project. You can learn more about dbt
        resources and the properties available in this dictionary here:
        https://docs.getdbt.com/reference/artifacts/manifest-json#resource-details

        This method can be overridden to provide custom owners for a dbt resource.

        Args:
            dbt_resource_props (Mapping[str, Any]): A dictionary representing the dbt resource.

        Returns:
            Optional[Sequence[str]]: A set of Dagster owners.

        Examples:
            .. code-block:: python

                from typing import Any, Mapping

                from dagster_dbt import DagsterDbtTranslator


                class CustomDagsterDbtTranslator(DagsterDbtTranslator):
                    def get_owners(self, dbt_resource_props: Mapping[str, Any]) -> Optional[Sequence[str]]:
                        return ["user@owner.com", "team:team@owner.com"]
        """
        return default_owners_from_dbt_resource_props(dbt_resource_props)

    @public
    @beta(emit_runtime_warning=False)
    def get_auto_materialize_policy(
        self, dbt_resource_props: Mapping[str, Any]
    ) -> Optional[AutoMaterializePolicy]:
        """A function that takes a dictionary representing properties of a dbt resource, and
        returns the Dagster :py:class:`dagster.AutoMaterializePolicy` for that resource.

        Note that a dbt resource is unrelated to Dagster's resource concept, and simply represents
        a model, seed, snapshot or source in a given dbt project. You can learn more about dbt
        resources and the properties available in this dictionary here:
        https://docs.getdbt.com/reference/artifacts/manifest-json#resource-details

        This method can be overridden to provide a custom auto-materialize policy for a dbt resource.

        Args:
            dbt_resource_props (Mapping[str, Any]): A dictionary representing the dbt resource.

        Returns:
            Optional[AutoMaterializePolicy]: A Dagster auto-materialize policy.

        Examples:
            Set a custom auto-materialize policy for all dbt resources:

            .. code-block:: python

                from typing import Any, Mapping

                from dagster_dbt import DagsterDbtTranslator


                class CustomDagsterDbtTranslator(DagsterDbtTranslator):
                    def get_auto_materialize_policy(self, dbt_resource_props: Mapping[str, Any]) -> Optional[AutoMaterializePolicy]:
                        return AutoMaterializePolicy.eager()

            Set a custom auto-materialize policy for dbt resources with a specific tag:

            .. code-block:: python

                from typing import Any, Mapping

                from dagster_dbt import DagsterDbtTranslator


                class CustomDagsterDbtTranslator(DagsterDbtTranslator):
                    def get_auto_materialize_policy(self, dbt_resource_props: Mapping[str, Any]) -> Optional[AutoMaterializePolicy]:
                        auto_materialize_policy = None
                        if "my_custom_tag" in dbt_resource_props.get("tags", []):
                            auto_materialize_policy = AutoMaterializePolicy.eager()

                        return auto_materialize_policy

        """
        return default_auto_materialize_policy_fn(dbt_resource_props)

    @public
    @beta(emit_runtime_warning=False)
    def get_automation_condition(
        self, dbt_resource_props: Mapping[str, Any]
    ) -> Optional[AutomationCondition]:
        """A function that takes a dictionary representing properties of a dbt resource, and
        returns the Dagster :py:class:`dagster.AutoMaterializePolicy` for that resource.

        Note that a dbt resource is unrelated to Dagster's resource concept, and simply represents
        a model, seed, snapshot or source in a given dbt project. You can learn more about dbt
        resources and the properties available in this dictionary here:
        https://docs.getdbt.com/reference/artifacts/manifest-json#resource-details

        This method can be overridden to provide a custom AutomationCondition for a dbt resource.

        Args:
            dbt_resource_props (Mapping[str, Any]): A dictionary representing the dbt resource.

        Returns:
            Optional[AutoMaterializePolicy]: A Dagster auto-materialize policy.

        Examples:
            Set a custom AutomationCondition for all dbt resources:

            .. code-block:: python

                from typing import Any, Mapping

                from dagster_dbt import DagsterDbtTranslator


                class CustomDagsterDbtTranslator(DagsterDbtTranslator):
                    def get_automation_condition(self, dbt_resource_props: Mapping[str, Any]) -> Optional[AutomationCondition]:
                        return AutomationCondition.eager()

            Set a custom AutomationCondition for dbt resources with a specific tag:

            .. code-block:: python

                from typing import Any, Mapping

                from dagster_dbt import DagsterDbtTranslator


                class CustomDagsterDbtTranslator(DagsterDbtTranslator):
                    def get_automation_condition(self, dbt_resource_props: Mapping[str, Any]) -> Optional[AutomationCondition]:
                        automation_condition = None
                        if "my_custom_tag" in dbt_resource_props.get("tags", []):
                            automation_condition = AutomationCondition.eager()

                        return automation_condition

        """
        auto_materialize_policy = self.get_auto_materialize_policy(dbt_resource_props)
        return (
            auto_materialize_policy.to_automation_condition() if auto_materialize_policy else None
        )

    def get_partitions_def(
        self, dbt_resource_props: Mapping[str, Any]
    ) -> Optional[PartitionsDefinition]:
        """[INTERNAL] A function that takes a dictionary representing properties of a dbt resource, and
        returns the Dagster :py:class:`dagster.PartitionsDefinition` for that resource.

        This method can be overridden to provide a custom PartitionsDefinition for a dbt resource.

        Args:
            dbt_resource_props (Mapping[str, Any]): A dictionary representing the dbt resource.

        Returns:
            Optional[PartitionsDefinition]: A Dagster partitions definition.

        Examples:
            Set a custom AutomationCondition for dbt resources with a specific tag:

            .. code-block:: python

                from typing import Any, Mapping

                from dagster import DailyPartitionsDefinition
                from dagster_dbt import DagsterDbtTranslator


                class CustomDagsterDbtTranslator(DagsterDbtTranslator):
                    def get_partitions_def(self, dbt_resource_props: Mapping[str, Any]) -> Optional[PartitionsDefinition]:
                        if "my_custom_tag" in dbt_resource_props.get("tags", []):
                            return DailyPartitionsDefinition(start_date="2022-01-01")
                        else:
                            return None
        """
        return None


@dataclass
class DbtManifestWrapper:
    """Wrapper around parsed DBT manifest json to provide convenient and efficient access."""

    manifest: Mapping[str, Any]


def validate_translator(dagster_dbt_translator: DagsterDbtTranslator) -> DagsterDbtTranslator:
    return check.inst_param(
        dagster_dbt_translator,
        "dagster_dbt_translator",
        DagsterDbtTranslator,
        additional_message=(
            "Ensure that the argument is an instantiated class that subclasses"
            " DagsterDbtTranslator."
        ),
    )


def validate_opt_translator(
    dagster_dbt_translator: Optional[DagsterDbtTranslator],
) -> Optional[DagsterDbtTranslator]:
    return check.opt_inst_param(
        dagster_dbt_translator,
        "dagster_dbt_translator",
        DagsterDbtTranslator,
        additional_message=(
            "Ensure that the argument is an instantiated class that subclasses"
            " DagsterDbtTranslator."
        ),
    )


def _attach_sql_model_code_reference(
    existing_metadata: Mapping[str, Any],
    dbt_resource_props: Mapping[str, Any],
    project: "DbtProject",
) -> Mapping[str, Any]:
    """Pulls the SQL model location for a dbt resource and attaches it as a code reference to the
    existing metadata.
    """
    existing_references_meta = CodeReferencesMetadataSet.extract(existing_metadata)
    references = (
        existing_references_meta.code_references.code_references
        if existing_references_meta.code_references
        else []
    )

    if "original_file_path" not in dbt_resource_props:
        raise DagsterInvalidDefinitionError(
            "Cannot attach SQL model code reference because 'original_file_path' is not present"
            " in the dbt resource properties."
        )

    # attempt to get root_path, which is removed from manifests in newer dbt versions
    relative_path = Path(dbt_resource_props["original_file_path"])
    abs_path = project.project_dir.joinpath(relative_path).resolve()

    return {
        **existing_metadata,
        **CodeReferencesMetadataSet(
            code_references=CodeReferencesMetadataValue(
                code_references=[
                    *references,
                    LocalFileCodeReference(file_path=os.fspath(abs_path)),
                ],
            )
        ),
    }
