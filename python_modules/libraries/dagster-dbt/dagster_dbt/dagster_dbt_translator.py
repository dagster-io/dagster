from dataclasses import dataclass
from typing import Any, Mapping, Optional

from dagster import AssetKey, AutoMaterializePolicy, FreshnessPolicy
from dagster._annotations import public
from dagster._core.definitions.events import (
    CoercibleToAssetKeyPrefix,
    check_opt_coercible_to_asset_key_prefix_param,
)

from .asset_utils import (
    default_asset_key_fn,
    default_auto_materialize_policy_fn,
    default_description_fn,
    default_freshness_policy_fn,
    default_group_from_dbt_resource_props,
    default_metadata_from_dbt_resource_props,
)


@dataclass(frozen=True)
class DagsterDbtTranslatorSettings:
    """Settings to enable Dagster features for your dbt project.

    Args:
        enable_asset_checks (bool): Whether to load dbt tests as Dagster asset checks.
            Defaults to False.
    """

    enable_asset_checks: bool = False


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

    @classmethod
    @public
    def get_asset_key(cls, dbt_resource_props: Mapping[str, Any]) -> AssetKey:
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
                    @classmethod
                    def get_asset_key(cls, dbt_resource_props: Mapping[str, Any]) -> AssetKey:
                        return super().get_asset_key(dbt_resource_props).with_prefix("prefix")

            Adding a prefix to the default asset key generated for each dbt resource, but only for dbt sources:

            .. code-block:: python

                from typing import Any, Mapping

                from dagster import AssetKey
                from dagster_dbt import DagsterDbtTranslator


                class CustomDagsterDbtTranslator(DagsterDbtTranslator):
                    @classmethod
                    def get_asset_key(cls, dbt_resource_props: Mapping[str, Any]) -> AssetKey:
                        asset_key = super().get_asset_key(dbt_resource_props)

                        if dbt_resource_props["resource_type"] == "source":
                            asset_key = asset_key.with_prefix("my_prefix")

                        return asset_key
        """
        return default_asset_key_fn(dbt_resource_props)

    @classmethod
    @public
    def get_description(cls, dbt_resource_props: Mapping[str, Any]) -> str:
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
                    @classmethod
                    def get_description(cls, dbt_resource_props: Mapping[str, Any]) -> str:
                        return "custom description"
        """
        return default_description_fn(dbt_resource_props)

    @classmethod
    @public
    def get_metadata(cls, dbt_resource_props: Mapping[str, Any]) -> Mapping[str, Any]:
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
                    @classmethod
                    def get_metadata(cls, dbt_resource_props: Mapping[str, Any]) -> Mapping[str, Any]:
                        return {"custom": "metadata"}
        """
        return default_metadata_from_dbt_resource_props(dbt_resource_props)

    @classmethod
    @public
    def get_group_name(cls, dbt_resource_props: Mapping[str, Any]) -> Optional[str]:
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
                    @classmethod
                    def get_group_name(cls, dbt_resource_props: Mapping[str, Any]) -> Optional[str]:
                        return "custom_group_prefix" + dbt_resource_props.get("config", {}).get("group")
        """
        return default_group_from_dbt_resource_props(dbt_resource_props)

    @classmethod
    @public
    def get_freshness_policy(
        cls, dbt_resource_props: Mapping[str, Any]
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
                    @classmethod
                    def get_freshness_policy(cls, dbt_resource_props: Mapping[str, Any]) -> Optional[FreshnessPolicy]:
                        return FreshnessPolicy(maximum_lag_minutes=60)

            Set a custom freshness policy for dbt resources with a specific tag:

            .. code-block:: python

                from typing import Any, Mapping

                from dagster_dbt import DagsterDbtTranslator


                class CustomDagsterDbtTranslator(DagsterDbtTranslator):
                    @classmethod
                    def get_freshness_policy(cls, dbt_resource_props: Mapping[str, Any]) -> Optional[FreshnessPolicy]:
                        freshness_policy = None
                        if "my_custom_tag" in dbt_resource_props.get("tags", []):
                            freshness_policy = FreshnessPolicy(maximum_lag_minutes=60)

                        return freshness_policy
        """
        return default_freshness_policy_fn(dbt_resource_props)

    @classmethod
    @public
    def get_auto_materialize_policy(
        cls, dbt_resource_props: Mapping[str, Any]
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
                    @classmethod
                    def get_auto_materialize_policy(cls, dbt_resource_props: Mapping[str, Any]) -> Optional[AutoMaterializePolicy]:
                        return AutoMaterializePolicy.eager()

            Set a custom auto-materialize policy for dbt resources with a specific tag:

            .. code-block:: python

                from typing import Any, Mapping

                from dagster_dbt import DagsterDbtTranslator


                class CustomDagsterDbtTranslator(DagsterDbtTranslator):
                    @classmethod
                    def get_auto_materialize_policy(cls, dbt_resource_props: Mapping[str, Any]) -> Optional[AutoMaterializePolicy]:
                        auto_materialize_policy = None
                        if "my_custom_tag" in dbt_resource_props.get("tags", []):
                            auto_materialize_policy = AutoMaterializePolicy.eager()

                        return auto_materialize_policy

        """
        return default_auto_materialize_policy_fn(dbt_resource_props)


class KeyPrefixDagsterDbtTranslator(DagsterDbtTranslator):
    """A DagsterDbtTranslator that applies prefixes to the asset keys generated from dbt resources.

    Attributes:
        asset_key_prefix (Optional[Union[str, Sequence[str]]]): A prefix to apply to all dbt models,
            seeds, snapshots, etc. This will *not* apply to dbt sources.
        source_asset_key_prefix (Optional[Union[str, Sequence[str]]]): A prefix to apply to all dbt
            sources.
    """

    def __init__(
        self,
        asset_key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
        source_asset_key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
        *args,
        **kwargs,
    ):
        self._asset_key_prefix = (
            check_opt_coercible_to_asset_key_prefix_param(asset_key_prefix, "asset_key_prefix")
            or []
        )
        self._source_asset_key_prefix = (
            check_opt_coercible_to_asset_key_prefix_param(
                source_asset_key_prefix, "source_asset_key_prefix"
            )
            or []
        )

        super().__init__(*args, **kwargs)

    @public
    def get_asset_key(self, dbt_resource_props: Mapping[str, Any]) -> AssetKey:
        base_key = default_asset_key_fn(dbt_resource_props)
        if dbt_resource_props["resource_type"] == "source":
            return base_key.with_prefix(self._source_asset_key_prefix)
        else:
            return base_key.with_prefix(self._asset_key_prefix)


@dataclass
class DbtManifestWrapper:
    manifest: Mapping[str, Any]
