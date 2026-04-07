import dagster as dg

from project_multi_workspace_databricks.definitions import defs


def test_defs_load():
    assert isinstance(defs, dg.Definitions)


def test_kafka_sensors_defined():
    repo = defs.get_repository_def()
    sensor_names = {s.name for s in repo.sensor_defs}
    assert "watch_kafka_replica_0" in sensor_names
    assert "watch_kafka_replica_1" in sensor_names
