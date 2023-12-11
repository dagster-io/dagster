import json
import os
from unittest.mock import MagicMock, patch

import pendulum
import pytest
from dagster import DagsterInstance, materialize
from dagster._check import CheckError

from assets_dynamic_partitions import adhoc_partition_load, duckdb_io_manager
from assets_dynamic_partitions.assets import releases_metadata, releases_partitions_def


def test_adhoc_partition_load_no_partition():
    with pytest.raises(CheckError):
        adhoc_partition_load.execute_in_process(
            run_config={
                "ops": {
                    "dynamic_partition_loader": {
                        "inputs": {
                            "asset_key": {
                                "value": "test_asset_key",
                            },
                            "partition_key": {"value": "test_partition_id"},
                        }
                    }
                }
            }
        )


def test_adhoc_partition_load():
    old_environ = dict(os.environ)
    os.environ.update({"GITHUB_USER_NAME": "username", "GITHUB_ACCESS_TOKEN": "token"})
    try:
        instance = DagsterInstance.ephemeral()
        with patch("requests.get") as mock:
            mock.return_value = MagicMock(
                ok=True,
                content=json.dumps(
                    {
                        "tarball_url": "test_tarball_url",
                        "zipball_url": "test_zipball_url",
                        "id": "test_id",
                        "author": {"login": "test_author_login"},
                        "published_at": str(pendulum.now()),
                    }
                ),
            )
            instance.add_dynamic_partitions(releases_partitions_def.name, ["1.1.0"])
            assert materialize(
                [releases_metadata],
                instance=instance,
                partition_key="1.1.0",
                resources={
                    "warehouse": duckdb_io_manager.configured({"database": "releases.duckdb"})
                },
            ).success

            assert instance.has_dynamic_partition(releases_partitions_def.name, "1.1.0")

            res = adhoc_partition_load.execute_in_process(
                instance=instance,
                run_config={
                    "ops": {
                        "dynamic_partition_loader": {
                            "inputs": {
                                "asset_key": {
                                    "value": "releases_metadata",
                                },
                                "partition_key": {"value": "1.1.0"},
                            }
                        }
                    }
                },
            )

    finally:
        os.environ.clear()
        os.environ.update(old_environ)
