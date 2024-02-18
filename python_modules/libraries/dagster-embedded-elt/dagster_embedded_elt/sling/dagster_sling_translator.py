import re

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
        """
        return re.sub(r"[^a-zA-Z0-9_.]", "_", stream_name.replace('"', ""))

    @public
    @classmethod
    def get_asset_key_for_target(cls, stream_name: str, target_prefix: str = "target") -> AssetKey:
        """A function that takes a stream name from a Sling replication config and returns a
        Dagster AssetKey.

        By default, this returns the target_prefix concatenated with the stream name. For example, a stream
        named "public.accounts" will create an AssetKey named "target_public_accounts".

        Override this function to customize how to map a Sling stream to a Dagster AssetKey.
        Alternatively, you can provide metadata in your Sling replication config to specify the
        Dagster AssetKey for a stream as follows:

        public.users:
           meta:
             dagster:
               asset_key: "mydb_users"

        Args:
            stream_name (str): The name of the stream.

        Returns:
            AssetKey: The Dagster AssetKey for the replication stream.

        Examples:
            Using a custom mapping for streams:

            class CustomSlingTranslator(DagsterSlingTranslator):
                @classmethod
                def get_asset_key_for_target(cls, stream_name: str) -> AssetKey:
                    map = {"stream1": "asset1", "stream2": "asset2"}
                    return AssetKey(map[stream_name])
        """
        components = cls.sanitize_stream_name(stream_name).split(".")
        return AssetKey([target_prefix] + components)

    @public
    @classmethod
    def get_deps_asset_key(cls, stream_name: str) -> AssetKey:
        """A function that takes a stream name from a Sling replication config and returns a
        Dagster AssetKey for the dependencies of the replication stream.

        By default, this returns the stream name. For example, a stream
        named "public.accounts" will create an AssetKey named "target_public_accounts" and a
        depenency AssetKey named "public_accounts".

        Override this function to customize how to map a Sling stream to a Dagster AssetKey.
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
        components = cls.sanitize_stream_name(stream_name).split(".")
        return AssetKey(components)
