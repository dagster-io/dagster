from dagster import AssetKey

from dagster_airbyte.asset_defs import AirbyteConnectionMetadata


class DagsterAirbyteTranslator:
    def get_group_name_from_connection_metadata(
        self, connection_metadata: AirbyteConnectionMetadata
    ):
        # Based on
        # connection_meta_to_group_fn: Optional[Callable[[AirbyteConnectionMetadata], Optional[str]]] = (
        #    None,
        # )
        return default_group_name_fn(connection_metadata)

    def get_asset_key(self, connection_metadata: AirbyteConnectionMetadata, table_name: str):
        # Based on
        # connection_to_asset_key_fn: Optional[Callable[[AirbyteConnectionMetadata, str], AssetKey]] = (None,)
        return default_asset_key_fn(connection_metadata, table_name)

    def get_asset_key_prefix(self, connection_metadata: AirbyteConnectionMetadata):
        # Based on
        # connection_to_asset_key_fn: Optional[Callable[[AirbyteConnectionMetadata, str], AssetKey]] = (None,)
        return default_asset_key_prefix_fn(connection_metadata)

    def get_auto_materialize_policy(self, connection_metadata: AirbyteConnectionMetadata):
        # Based on
        # connection_to_auto_materialize_policy_fn: Optional[
        #    Callable[[AirbyteConnectionMetadata], Optional[AutoMaterializePolicy]]
        # ] = (None,)
        return default_auto_materialize_policy_fn(connection_metadata)

    def get_freshness_policy(self, connection_metadata: AirbyteConnectionMetadata):
        # Based on
        # connection_to_freshness_policy_fn: Optional[
        #    Callable[[AirbyteConnectionMetadata], Optional[FreshnessPolicy]]
        # ] = (None,)
        return default_freshness_policy_fn(connection_metadata)

    def get_io_manager_key(self, connection_metadata: AirbyteConnectionMetadata):
        # Based on
        # connection_to_io_manager_key_fn: Optional[Callable[[str], Optional[str]]] = (None,)
        return default_io_manager_key_fn(connection_metadata)


def default_group_name_fn(connection_metadata: AirbyteConnectionMetadata):
    return connection_metadata.name


def default_asset_key_fn(connection_metadata: AirbyteConnectionMetadata, table_name: str):
    return AssetKey([connection_metadata.name, table_name])


def default_asset_key_prefix_fn(connection_metadata: AirbyteConnectionMetadata):
    return [connection_metadata.name]


def default_auto_materialize_policy_fn(connection_metadata: AirbyteConnectionMetadata):
    return None


def default_freshness_policy_fn(connection_metadata: AirbyteConnectionMetadata):
    return None


def default_io_manager_key_fn(connection_metadata: AirbyteConnectionMetadata):
    return "io_manager"
