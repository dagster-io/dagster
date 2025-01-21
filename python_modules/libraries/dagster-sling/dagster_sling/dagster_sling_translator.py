import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any, Callable, Optional

from dagster import AssetKey, AssetSpec, AutoMaterializePolicy, FreshnessPolicy, MetadataValue
from dagster._annotations import public, superseded
from dagster._utils.warnings import supersession_warning


@dataclass
class DagsterSlingTranslator:
    target_prefix: str = "target"

    @public
    def get_asset_spec(self, stream_definition: Mapping[str, Any]) -> AssetSpec:
        """A function that takes a stream definition from a Sling replication config and returns a
        Dagster AssetSpec.

        The stream definition is a dictionary key/value pair where the key is the stream name and
        the value is a dictionary representing the Sling Replication Stream Config.
        """
        return AssetSpec(
            key=self._resolve_back_compat_method(
                "get_asset_key", self._default_asset_key_fn, stream_definition
            ),
            deps=self._resolve_back_compat_method(
                "get_deps_asset_key", self._default_deps_fn, stream_definition
            ),
            description=self._resolve_back_compat_method(
                "get_description", self._default_description_fn, stream_definition
            ),
            metadata=self._resolve_back_compat_method(
                "get_metadata", self._default_metadata_fn, stream_definition
            ),
            tags=self._resolve_back_compat_method(
                "get_tags", self._default_tags_fn, stream_definition
            ),
            kinds=self._resolve_back_compat_method(
                "get_kinds", self._default_kinds_fn, stream_definition
            ),
            group_name=self._resolve_back_compat_method(
                "get_group_name", self._default_group_name_fn, stream_definition
            ),
            freshness_policy=self._resolve_back_compat_method(
                "get_freshness_policy", self._default_freshness_policy_fn, stream_definition
            ),
            auto_materialize_policy=self._resolve_back_compat_method(
                "get_auto_materialize_policy",
                self._default_auto_materialize_policy_fn,
                stream_definition,
            ),
        )

    def _resolve_back_compat_method(
        self,
        method_name: str,
        default_fn: Callable[[Mapping[str, Any]], Any],
        stream_definition: Mapping[str, Any],
    ):
        method = getattr(type(self), method_name)
        base_method = getattr(DagsterSlingTranslator, method_name)
        if method is not base_method:  # user defined this
            supersession_warning(
                subject=method_name,
                additional_warn_text=(
                    f"Instead of overriding DagsterSlingTranslator.{method_name}(), "
                    f"override DagsterSlingTranslator.get_asset_spec()."
                ),
            )
            return method(self, stream_definition)
        else:
            return default_fn(stream_definition)

    @public
    def sanitize_stream_name(self, stream_name: str) -> str:
        """A function that takes a stream name from a Sling replication config and returns a
        sanitized name for the stream.

        By default, this removes any non-alphanumeric characters from the stream name and replaces
        them with underscores, while removing any double quotes.

        Args:
            stream_name (str): The name of the stream.

        Examples:
            Using a custom stream name sanitizer:

            .. code-block:: python

                class CustomSlingTranslator(DagsterSlingTranslator):
                    def sanitize_stream_name(self, stream_name: str) -> str:
                        return stream_name.replace(".", "")
        """
        return re.sub(r"[^a-zA-Z0-9_.]", "_", stream_name.replace('"', "").lower())

    @superseded(
        additional_warn_text="Use `DagsterSlingTranslator.get_asset_spec(...).key` instead.",
    )
    @public
    def get_asset_key(self, stream_definition: Mapping[str, Any]) -> AssetKey:
        """A function that takes a stream definition from a Sling replication config and returns a
        Dagster AssetKey.

        The stream definition is a dictionary key/value pair where the key is the stream name and
        the value is a dictionary representing the Sling Replication Stream Config.

        For example:

        .. code-block:: python

            stream_definition = {"public.users":
                {'sql': 'select all_user_id, name from public."all_Users"',
                'object': 'public.all_users'}
            }

        By default, this returns the class's target_prefix parameter concatenated with the stream name.
        A stream named "public.accounts" will create an AssetKey named "target_public_accounts".

        Override this function to customize how to map a Sling stream to a Dagster AssetKey.

        Alternatively, you can provide metadata in your Sling replication config to specify the
        Dagster AssetKey for a stream as follows:

        .. code-block:: yaml

            public.users:
               meta:
                 dagster:
                   asset_key: "mydb_users"

        Args:
            stream_definition (Mapping[str, Any]): A dictionary representing the stream definition

        Returns:
            AssetKey: The Dagster AssetKey for the replication stream.

        Examples:
            Using a custom mapping for streams:

            .. code-block:: python

                class CustomSlingTranslator(DagsterSlingTranslator):
                    def get_asset_spec(self, stream_definition: Mapping[str, Any]) -> AssetKey:
                        default_spec = super().get_asset_spec(stream_definition)
                        map = {"stream1": "asset1", "stream2": "asset2"}
                        return default_spec.replace_attributes(key=AssetKey(map[stream_definition["name"]]))
        """
        return self._default_asset_key_fn(stream_definition)

    def _default_asset_key_fn(self, stream_definition: Mapping[str, Any]) -> AssetKey:
        """A function that takes a stream definition from a Sling replication config and returns a
        Dagster AssetKey.

        The stream definition is a dictionary key/value pair where the key is the stream name and
        the value is a dictionary representing the Sling Replication Stream Config.

        For example:

        .. code-block:: python

            stream_definition = {"public.users":
                {'sql': 'select all_user_id, name from public."all_Users"',
                'object': 'public.all_users'}
            }

        This returns the class's target_prefix parameter concatenated with the stream name.
        A stream named "public.accounts" will create an AssetKey named "target_public_accounts".

        Alternatively, you can provide metadata in your Sling replication config to specify the
        Dagster AssetKey for a stream as follows:

        .. code-block:: yaml

            public.users:
               meta:
                 dagster:
                   asset_key: "mydb_users"

        Args:
            stream_definition (Mapping[str, Any]): A dictionary representing the stream definition

        Returns:
            AssetKey: The Dagster AssetKey for the replication stream.

        Examples:
            Using a custom mapping for streams:

            .. code-block:: python

                class CustomSlingTranslator(DagsterSlingTranslator):
                    def get_asset_spec(self, stream_definition: Mapping[str, Any]) -> AssetKey:
                        default_spec = super().get_asset_spec(stream_definition)
                        map = {"stream1": "asset1", "stream2": "asset2"}
                        return default_spec.replace_attributes(key=AssetKey(map[stream_definition["name"]]))
        """
        config = stream_definition.get("config", {}) or {}
        object_key = config.get("object")
        meta = config.get("meta", {})
        asset_key = meta.get("dagster", {}).get("asset_key")

        if asset_key:
            if self.sanitize_stream_name(asset_key) != asset_key:
                raise ValueError(
                    f"Asset key {asset_key} for stream {stream_definition['name']} is not "
                    "sanitized. Please use only alphanumeric characters and underscores."
                )
            return AssetKey(asset_key.split("."))

        # You can override the Sling Replication default object with an object key
        stream_name = object_key or stream_definition["name"]
        sanitized_components = self.sanitize_stream_name(stream_name).split(".")
        return AssetKey([self.target_prefix] + sanitized_components)

    @superseded(
        additional_warn_text=(
            "Iterate over `DagsterSlingTranslator.get_asset_spec(...).deps` to access `AssetDep.asset_key` instead."
        ),
    )
    @public
    def get_deps_asset_key(self, stream_definition: Mapping[str, Any]) -> Iterable[AssetKey]:
        """A function that takes a stream definition from a Sling replication config and returns a
        Dagster AssetKey for each dependency of the replication stream.

        By default, this returns the stream name. For example, a stream named "public.accounts"
        will create an AssetKey named "target_public_accounts" and a dependency named "public_accounts".

        Override this function to customize how to map a Sling stream to a Dagster dependency.
        Alternatively, you can provide metadata in your Sling replication config to specify the
        Dagster AssetKey for a stream as follows:

        .. code-block:: yaml

            public.users:
                meta:
                    dagster:
                        deps: "sourcedb_users"

        Args:
            stream_definition (Mapping[str, Any]): A dictionary representing the stream definition

        Returns:
            Iterable[AssetKey]: A list of Dagster AssetKey for each dependency of the replication stream.
        """
        return self._default_deps_fn(stream_definition)

    def _default_deps_fn(self, stream_definition: Mapping[str, Any]) -> Iterable[AssetKey]:
        """A function that takes a stream definition from a Sling replication config and returns a
        Dagster AssetKey for each dependency of the replication stream.

        This returns the stream name. For example, a stream named "public.accounts"
        will create an AssetKey named "target_public_accounts" and a dependency named "public_accounts".

        Alternatively, you can provide metadata in your Sling replication config to specify the
        Dagster AssetKey for a stream as follows:

        .. code-block:: yaml

            public.users:
                meta:
                    dagster:
                        deps: "sourcedb_users"

        Args:
            stream_definition (Mapping[str, Any]): A dictionary representing the stream definition

        Returns:
            Iterable[AssetKey]: A list of Dagster AssetKey for each dependency of the replication stream.
        """
        config = stream_definition.get("config", {}) or {}
        meta = config.get("meta", {})
        deps = meta.get("dagster", {}).get("deps")
        deps_out = []
        if deps and isinstance(deps, str):
            deps = [deps]
        if deps:
            assert isinstance(deps, list)
            for asset_key in deps:
                if self.sanitize_stream_name(asset_key) != asset_key:
                    raise ValueError(
                        f"Deps Asset key {asset_key} for stream {stream_definition['name']} is not "
                        "sanitized. Please use only alphanumeric characters and underscores."
                    )
                deps_out.append(AssetKey(asset_key.split(".")))
            return deps_out

        stream_name = stream_definition["name"]
        components = self.sanitize_stream_name(stream_name).split(".")
        return [AssetKey(components)]

    @superseded(
        additional_warn_text="Use `DagsterSlingTranslator.get_asset_spec(...).description` instead.",
    )
    @public
    def get_description(self, stream_definition: Mapping[str, Any]) -> Optional[str]:
        """Retrieves the description for a given stream definition.

        This method checks the provided stream definition for a description. It first looks
        for an "sql" key in the configuration and returns its value if found. If not, it looks
        for a description in the metadata under the "dagster" key.

        Parameters:
            stream_definition (Mapping[str, Any]): A dictionary representing the stream definition,
            which includes configuration details.

        Returns:
            Optional[str]: The description of the stream if found, otherwise None.
        """
        return self._default_description_fn(stream_definition)

    def _default_description_fn(self, stream_definition: Mapping[str, Any]) -> Optional[str]:
        """Retrieves the description for a given stream definition.

        This method checks the provided stream definition for a description. It first looks
        for an "sql" key in the configuration and returns its value if found. If not, it looks
        for a description in the metadata under the "dagster" key.

        Parameters:
            stream_definition (Mapping[str, Any]): A dictionary representing the stream definition,
            which includes configuration details.

        Returns:
            Optional[str]: The description of the stream if found, otherwise None.
        """
        config = stream_definition.get("config", {}) or {}
        if "sql" in config:
            return config["sql"]
        meta = config.get("meta", {})
        description = meta.get("dagster", {}).get("description")
        return description

    @superseded(
        additional_warn_text="Use `DagsterSlingTranslator.get_asset_spec(...).metadata` instead.",
    )
    @public
    def get_metadata(self, stream_definition: Mapping[str, Any]) -> Mapping[str, Any]:
        """Retrieves the metadata for a given stream definition.

        This method extracts the configuration from the provided stream definition and returns
        it as a JSON metadata value.

        Parameters:
            stream_definition (Mapping[str, Any]): A dictionary representing the stream definition,
            which includes configuration details.

        Returns:
            Mapping[str, Any]: A dictionary containing the stream configuration as JSON metadata.
        """
        return self._default_metadata_fn(stream_definition)

    def _default_metadata_fn(self, stream_definition: Mapping[str, Any]) -> Mapping[str, Any]:
        """Retrieves the metadata for a given stream definition.

        This method extracts the configuration from the provided stream definition and returns
        it as a JSON metadata value.

        Parameters:
            stream_definition (Mapping[str, Any]): A dictionary representing the stream definition,
            which includes configuration details.

        Returns:
            Mapping[str, Any]: A dictionary containing the stream configuration as JSON metadata.
        """
        return {"stream_config": MetadataValue.json(stream_definition.get("config", {}))}

    @superseded(
        additional_warn_text="Use `DagsterSlingTranslator.get_asset_spec(...).tags` instead.",
    )
    @public
    def get_tags(self, stream_definition: Mapping[str, Any]) -> Mapping[str, Any]:
        """Retrieves the tags for a given stream definition.

        This method returns an empty dictionary, indicating that no tags are associated with
        the stream definition by default. This method can be overridden to provide custom tags.

        Parameters:
            stream_definition (Mapping[str, Any]): A dictionary representing the stream definition,
            which includes configuration details.

        Returns:
            Mapping[str, Any]: An empty dictionary.
        """
        return self._default_tags_fn(stream_definition)

    def _default_tags_fn(self, stream_definition: Mapping[str, Any]) -> Mapping[str, Any]:
        """Retrieves the tags for a given stream definition.

        This method returns an empty dictionary, indicating that no tags are associated with
        the stream definition by default. This method can be overridden to provide custom tags.

        Parameters:
            stream_definition (Mapping[str, Any]): A dictionary representing the stream definition,
            which includes configuration details.

        Returns:
            Mapping[str, Any]: An empty dictionary.
        """
        return {}

    @superseded(
        additional_warn_text="Use `DagsterSlingTranslator.get_asset_spec(...).kinds` instead.",
    )
    @public
    def get_kinds(self, stream_definition: Mapping[str, Any]) -> set[str]:
        """Retrieves the kinds for a given stream definition.

        This method returns "sling" by default. This method can be overridden to provide custom kinds.

        Parameters:
            stream_definition (Mapping[str, Any]): A dictionary representing the stream definition,
            which includes configuration details.

        Returns:
            Set[str]: A set containing kinds for the stream's assets.
        """
        return self._default_kinds_fn(stream_definition)

    def _default_kinds_fn(self, stream_definition: Mapping[str, Any]) -> set[str]:
        """Retrieves the kinds for a given stream definition.

        This method returns "sling" by default. This method can be overridden to provide custom kinds.

        Parameters:
            stream_definition (Mapping[str, Any]): A dictionary representing the stream definition,
            which includes configuration details.

        Returns:
            Set[str]: A set containing kinds for the stream's assets.
        """
        return {"sling"}

    @superseded(
        additional_warn_text="Use `DagsterSlingTranslator.get_asset_spec(...).group_name` instead.",
    )
    @public
    def get_group_name(self, stream_definition: Mapping[str, Any]) -> Optional[str]:
        """Retrieves the group name for a given stream definition.

        This method checks the provided stream definition for a group name in the metadata
        under the "dagster" key.

        Parameters:
            stream_definition (Mapping[str, Any]): A dictionary representing the stream definition,
            which includes configuration details.

        Returns:
            Optional[str]: The group name if found, otherwise None.
        """
        return self._default_group_name_fn(stream_definition)

    def _default_group_name_fn(self, stream_definition: Mapping[str, Any]) -> Optional[str]:
        """Retrieves the group name for a given stream definition.

        This method checks the provided stream definition for a group name in the metadata
        under the "dagster" key.

        Parameters:
            stream_definition (Mapping[str, Any]): A dictionary representing the stream definition,
            which includes configuration details.

        Returns:
            Optional[str]: The group name if found, otherwise None.
        """
        config = stream_definition.get("config", {}) or {}
        meta = config.get("meta", {})
        return meta.get("dagster", {}).get("group")

    @superseded(
        additional_warn_text="Use `DagsterSlingTranslator.get_asset_spec(...).freshness_policy` instead.",
    )
    @public
    def get_freshness_policy(
        self, stream_definition: Mapping[str, Any]
    ) -> Optional[FreshnessPolicy]:
        """Retrieves the freshness policy for a given stream definition.

        This method checks the provided stream definition for a specific configuration
        indicating a freshness policy. If the configuration is found, it constructs and
        returns a FreshnessPolicy object based on the provided parameters. Otherwise,
        it returns None.

        Parameters:
            stream_definition (Mapping[str, Any]): A dictionary representing the stream definition,
            which includes configuration details.

        Returns:
            Optional[FreshnessPolicy]: A FreshnessPolicy object if the configuration is found,
            otherwise None.
        """
        return self._default_freshness_policy_fn(stream_definition)

    def _default_freshness_policy_fn(
        self, stream_definition: Mapping[str, Any]
    ) -> Optional[FreshnessPolicy]:
        """Retrieves the freshness policy for a given stream definition.

        This method checks the provided stream definition for a specific configuration
        indicating a freshness policy. If the configuration is found, it constructs and
        returns a FreshnessPolicy object based on the provided parameters. Otherwise,
        it returns None.

        Parameters:
            stream_definition (Mapping[str, Any]): A dictionary representing the stream definition,
            which includes configuration details.

        Returns:
            Optional[FreshnessPolicy]: A FreshnessPolicy object if the configuration is found,
            otherwise None.
        """
        config = stream_definition.get("config", {}) or {}
        meta = config.get("meta", {})
        freshness_policy_config = meta.get("dagster", {}).get("freshness_policy")
        if freshness_policy_config:
            return FreshnessPolicy(
                maximum_lag_minutes=float(freshness_policy_config["maximum_lag_minutes"]),
                cron_schedule=freshness_policy_config.get("cron_schedule"),
                cron_schedule_timezone=freshness_policy_config.get("cron_schedule_timezone"),
            )

    @superseded(
        additional_warn_text="Use `DagsterSlingTranslator.get_asset_spec(...).auto_materialize_policy` instead.",
    )
    @public
    def get_auto_materialize_policy(
        self, stream_definition: Mapping[str, Any]
    ) -> Optional[AutoMaterializePolicy]:
        """Defines the auto-materialize policy for a given stream definition.

        This method checks the provided stream definition for a specific configuration
        indicating an auto-materialize policy. If the configuration is found, it returns
        an eager auto-materialize policy. Otherwise, it returns None.

        Parameters:
            stream_definition (Mapping[str, Any]): A dictionary representing the stream definition,
            which includes configuration details.

        Returns:
            Optional[AutoMaterializePolicy]: An eager auto-materialize policy if the configuration
            is found, otherwise None.
        """
        return self._default_auto_materialize_policy_fn(stream_definition)

    def _default_auto_materialize_policy_fn(
        self, stream_definition: Mapping[str, Any]
    ) -> Optional[AutoMaterializePolicy]:
        """Defines the auto-materialize policy for a given stream definition.

        This method checks the provided stream definition for a specific configuration
        indicating an auto-materialize policy. If the configuration is found, it returns
        an eager auto-materialize policy. Otherwise, it returns None.

        Parameters:
            stream_definition (Mapping[str, Any]): A dictionary representing the stream definition,
            which includes configuration details.

        Returns:
            Optional[AutoMaterializePolicy]: An eager auto-materialize policy if the configuration
            is found, otherwise None.
        """
        config = stream_definition.get("config", {}) or {}
        meta = config.get("meta", {})
        auto_materialize_policy_config = "auto_materialize_policy" in meta.get("dagster", {})
        if auto_materialize_policy_config:
            return AutoMaterializePolicy.eager()
