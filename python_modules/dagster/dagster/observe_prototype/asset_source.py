from dagster_shared.serdes import whitelist_for_serdes

from dagster._core.definitions.assets.graph.remote_asset_graph import RemoteConnectionAssetNode
from dagster._record import record
from dagster._serdes import deserialize_value


@whitelist_for_serdes
@record
class SnowflakeConnectionAssets:
    asset_nodes: list[RemoteConnectionAssetNode]


class SnowflakeConnectionExternalAssetFactory:
    def create_nodes(self) -> list[RemoteConnectionAssetNode]:
        with open("snowflake_connection_assets.json") as f:
            data = f.read()
            return deserialize_value(data, SnowflakeConnectionAssets).asset_nodes
