from datetime import datetime

import pendulum

from dagster import daily_partitioned_config, job, repository
from dagster._core.host_representation import (
    external_pipeline_data_from_def,
    external_repository_data_from_def,
)
from dagster._core.host_representation.external_data import (
    ExternalTimeWindowPartitionsDefinitionData,
)
from dagster._legacy import ModeDefinition, PresetDefinition, daily_schedule, pipeline, solid
from dagster._serdes import serialize_pp


@solid
def a_solid(_):
    pass


@pipeline(
    mode_defs=[ModeDefinition("default"), ModeDefinition("mode_one")],
    preset_defs=[
        PresetDefinition(name="plain_preset"),
        PresetDefinition(
            name="kitchen_sink_preset",
            run_config={"foo": "bar"},
            solid_selection=["a_solid"],
            mode="mode_one",
        ),
    ],
)
def a_pipeline():
    a_solid()


@daily_schedule(  # type: ignore
    pipeline_name="a_pipeline",
    start_date=datetime(year=2019, month=1, day=1),
    end_date=datetime(year=2019, month=2, day=1),
    execution_timezone="US/Central",
)
def a_schedule():
    return {}


@daily_partitioned_config(start_date=datetime(2020, 1, 1), minute_offset=15)
def my_partitioned_config(_start: datetime, _end: datetime):
    return {}


@job(config=my_partitioned_config)
def a_job():
    a_solid()


def test_external_repository_data(snapshot):
    @repository
    def repo():
        return [a_pipeline, a_schedule, a_job]

    external_repo_data = external_repository_data_from_def(repo)
    assert external_repo_data.get_external_pipeline_data("a_pipeline")
    assert external_repo_data.get_external_schedule_data("a_schedule")
    partition_set_data = external_repo_data.get_external_partition_set_data("a_schedule_partitions")
    assert partition_set_data
    assert not partition_set_data.external_partitions_data

    job_partition_set_data = external_repo_data.get_external_partition_set_data(
        "a_job_partition_set"
    )
    assert job_partition_set_data
    assert isinstance(
        job_partition_set_data.external_partitions_data, ExternalTimeWindowPartitionsDefinitionData
    )

    now = pendulum.now()

    assert (
        job_partition_set_data.external_partitions_data.get_partitions_definition().get_partitions(
            now
        )
        == my_partitioned_config.partitions_def.get_partitions(now)
    )

    snapshot.assert_match(serialize_pp(external_repo_data))


def test_external_pipeline_data(snapshot):
    snapshot.assert_match(serialize_pp(external_pipeline_data_from_def(a_pipeline)))
