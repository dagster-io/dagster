import re
from typing import Any, Mapping

from dagster import AssetKey
from dagster._annotations import public


class DagsterSlingTranslator:
    @public
    @classmethod
    def sanitize_stream_name(cls, stream_name: str) -> str:
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
                    @classmethod
                    def sanitize_stream_name(cls, stream_name: str) -> str:
                        return stream_name.replace(".", "")
        """
        return re.sub(r"[^a-zA-Z0-9_.]", "_", stream_name.replace('"', ""))

    @public
    @classmethod
    def get_asset_key(
        cls, stream_definition: Mapping[str, Any], target_prefix: str = "target"
    ) -> AssetKey:
        """A function that takes a stream definition from a Sling replication config and returns a
        Dagster AssetKey.

        The stream definition is a dictionary key/value pair where the key is the stream name and
        the value is a dictionary representing the stream definition. For example:

        stream_definition = {"public.users": {'sql': 'select all_user_id, name from public."all_Users"', 'object': 'public.all_users'}}

        By default, this returns the target_prefix concatenated with the stream name. For example, a stream
        named "public.accounts" will create an AssetKey named "target_public_accounts".

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
            target_prefix (str): The prefix to use when creating the AssetKey

        Returns:
            AssetKey: The Dagster AssetKey for the replication stream.

        Examples:
            Using a custom mapping for streams:

            class CustomSlingTranslator(DagsterSlingTranslator):
                @classmethod
                def get_asset_key_for_target(cls, stream_definition) -> AssetKey:
                    map = {"stream1": "asset1", "stream2": "asset2"}
                    return AssetKey(map[stream_name])
        """
        meta = stream_definition.get("meta", {}).get("dagster", {})
        asset_key = meta.get("asset_key")
        if asset_key and cls.sanitize_stream_name(asset_key) != asset_key:
            raise ValueError(
                f"Asset key {asset_key} for stream {stream_definition['name']} is not "
                "sanitized. Please use only alphanumeric characters and underscores."
            )
        elif asset_key:
            return AssetKey(asset_key)

        stream_name = next(iter(stream_definition.keys()))
        components = cls.sanitize_stream_name(stream_name).split(".")
        return AssetKey([target_prefix] + components)

    @public
    @classmethod
    def get_deps_asset_key(cls, stream_definition: Mapping[str, Any]) -> AssetKey:
        """A function that takes a stream name from a Sling replication config and returns a
        Dagster AssetKey for the dependencies of the replication stream.

        By default, this returns the stream name. For example, a stream
        named "public.accounts" will create an AssetKey named "target_public_accounts" and a
        dependency named "public_accounts".

        Override this function to customize how to map a Sling stream to a Dagster depenency.
        Alternatively, you can provide metadata in your Sling replication config to specify the
        Dagster AssetKey for a stream as follows:

        public.users:
           meta:
             dagster:
               deps: "sourcedb_users"

        Args:
            stream_name (str): The name of the stream.

        Returns:
            AssetKey: The Dagster AssetKey dependency for the replication stream.

        Examples:
            Using a custom mapping for streams:

            class CustomSlingTranslator(DagsterSlingTranslator):
                @classmethod
                def get_deps_asset_key(cls, stream_name: str) -> AssetKey:
                    map = {"stream1": "asset1", "stream2": "asset2"}
                    return AssetKey(map[stream_name])


        """
        meta = stream_definition.get("meta", {}).get("dagster", {})
        asset_key = meta.get("deps")
        if asset_key and cls.sanitize_stream_name(asset_key) != asset_key:
            raise ValueError(
                f"Asset key {asset_key} for stream {stream_definition['name']} is not "
                "sanitized. Please use only alphanumeric characters and underscores."
            )
        elif asset_key:
            return AssetKey(asset_key)

        stream_name = next(iter(stream_definition.keys()))
        components = cls.sanitize_stream_name(stream_name).split(".")
        return AssetKey(components)
