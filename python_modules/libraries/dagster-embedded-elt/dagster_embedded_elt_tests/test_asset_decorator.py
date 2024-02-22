import pytest
from dagster import AssetKey
from dagster_embedded_elt.sling import (
    SlingReplicationParam,
    sling_assets,
)


@pytest.mark.parametrize(
    "replication_params",
    ["base_replication_config", "base_replication_config_path", "os_fspath"],
    indirect=True,
)
def test_replication_argument(replication_params: SlingReplicationParam):
    @sling_assets(replication_config=replication_params)
    def my_sling_assets():
        ...

    assert my_sling_assets.keys == {
        AssetKey.from_user_string(key)
        for key in [
            "target/public/accounts",
            "target/public/users",
            "target/departments",
            "target/public/transactions",
            "target/public/all_users",
        ]
    }
