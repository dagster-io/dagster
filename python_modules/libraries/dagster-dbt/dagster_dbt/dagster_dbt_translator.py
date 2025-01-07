from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Optional

from dagster import (
    AssetKey,
    AutoMaterializePolicy,
    AutomationCondition,
    FreshnessPolicy,
    PartitionMapping,
    _check as check,
)
from dagster._annotations import beta, public
from dagster._core.definitions.partition import PartitionsDefinition
from dagster._utils.tags import is_valid_tag_key

from dagster_dbt.asset_utils import (
    default_asset_key_fn,
    default_auto_materialize_policy_fn,
    default_code_version_fn,
    default_description_fn,
    default_freshness_policy_fn,
    default_group_from_dbt_resource_props,
    default_metadata_from_dbt_resource_props,
    default_owners_from_dbt_resource_props,
)


@dataclass(frozen=True)
class DagsterDbtTranslatorSettings:
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
    """

    enable_asset_checks: bool = True
    enable_duplicate_source_asset_keys: bool = False
    enable_code_references: bool = False
    enable_dbt_selection_by_name: bool = False


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
    def get_freshness_policy(
        self, dbt_resource_props: Mapping[str, Any]
    ) -> Optional[FreshnessPolicy]:
        """A function that takes a dictionary representing properties of a dbt resource, and
        returns the Dagster :py:class:`dagster.FreshnessPolicy` for that resource.

        Note that a dbt resource is unrelated to Dagster's resource concept, and simply represents
        a model, seed, snapshot or source in a given dbt project. You can learn more about dbt
        resources and the properties available in this dictionary here:
        https://docs.getdbt.com/reference/artifacts/manifest-json#resource-details

        This method can be overridden to provide a custom freshness policy for a dbt resource.

        Args:
            dbt_resource_props (Mapping[str, Any]): A dictionary representing the dbt resource.

        Returns:
            Optional[FreshnessPolicy]: A Dagster freshness policy.

        Examples:
            Set a custom freshness policy for all dbt resources:

            .. code-block:: python

                from typing import Any, Mapping

                from dagster_dbt import DagsterDbtTranslator


                class CustomDagsterDbtTranslator(DagsterDbtTranslator):
                    def get_freshness_policy(self, dbt_resource_props: Mapping[str, Any]) -> Optional[FreshnessPolicy]:
                        return FreshnessPolicy(maximum_lag_minutes=60)

            Set a custom freshness policy for dbt resources with a specific tag:

            .. code-block:: python

                from typing import Any, Mapping

                from dagster_dbt import DagsterDbtTranslator


                class CustomDagsterDbtTranslator(DagsterDbtTranslator):
                    def get_freshness_policy(self, dbt_resource_props: Mapping[str, Any]) -> Optional[FreshnessPolicy]:
                        freshness_policy = None
                        if "my_custom_tag" in dbt_resource_props.get("tags", []):
                            freshness_policy = FreshnessPolicy(maximum_lag_minutes=60)

                        return freshness_policy
        """
        return default_freshness_policy_fn(dbt_resource_props)

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
