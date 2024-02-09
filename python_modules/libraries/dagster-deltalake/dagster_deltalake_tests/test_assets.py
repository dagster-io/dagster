import os
import uuid

# import contextmanager
from contextlib import contextmanager

import pyarrow as pa
from dagster import DagsterInstance, build_resources
from dagster._core.definitions.observe import observe
from dagster_deltalake import DeltaTableResource
from dagster_deltalake.asset import observe_table_last_modified_time
from dagster_deltalake.config import LocalConfig
from deltalake import write_deltalake


@contextmanager
def ephemeral_deltalake_table(tmp_path: str):
    table_name = "test_table_" + str(uuid.uuid4()).replace("-", "_").lower()
    table_path = os.path.join(tmp_path, table_name)
    with build_resources(
        {"delta_table": DeltaTableResource(url=table_path, storage_options=LocalConfig())}
    ) as resources:
        write_deltalake(
            table_path,
            pa.table({"a": [1, 2, 3], "b": [5, 6, 7]}),
            storage_options=resources.delta_table.storage_options.dict(),
        )
        # Add a few rows to the table.
        for i in range(3):
            write_deltalake(
                table_path,
                pa.table({"a": [4], "b": [8]}),
                storage_options=resources.delta_table.storage_options.dict(),
                mode="append",
            )
        yield table_name, table_path


def test_observe_table(tmp_path: str):
    with ephemeral_deltalake_table(tmp_path) as (table_name, table_path):
        instance = DagsterInstance.ephemeral()
        result = observe(
            [observe_table_last_modified_time],
            instance=instance,
            resources={
                "delta_table": DeltaTableResource(url=table_path, storage_options=LocalConfig())
            },
        )
        observations = result.asset_observations_for_node(observe_table_last_modified_time.op.name)
        assert len(observations) == 1
        observation = observations[0]
        assert observation.tags["dagster/data_version"] is not None
        # Interpret the data version as a timestamp
        # Convert from a string in the format 2024-02-09 00:41:29.829000 to a timestamp
        timestamp = float(observation.tags["dagster/data_version"])
        assert timestamp is not None
        all_timestamps = [timestamp]
        # Check the other available timestamps
        with build_resources(
            resources={
                "delta_table": DeltaTableResource(url=table_path, storage_options=LocalConfig())
            }
        ) as resources:
            table = resources.delta_table.load()
            history = table.history()
            for entry in history:
                all_timestamps.append(entry["timestamp"])

        # Ensure we retrieved the last available timestamp
        assert max(all_timestamps) == timestamp
