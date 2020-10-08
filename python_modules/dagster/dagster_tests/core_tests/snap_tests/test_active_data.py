from datetime import datetime

from dagster import ModeDefinition, PresetDefinition, daily_schedule, pipeline, repository, solid
from dagster.core.host_representation import (
    external_pipeline_data_from_def,
    external_repository_data_from_def,
)
from dagster.serdes import serialize_pp


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


@daily_schedule(
    pipeline_name="a_pipeline",
    start_date=datetime(year=2019, month=1, day=1),
    end_date=datetime(year=2019, month=2, day=1),
    execution_timezone="US/Central",
)
def a_schedule():
    return {}


def test_external_repository_data(snapshot):
    @repository
    def repo():
        return [a_pipeline, a_schedule]

    external_repo_data = external_repository_data_from_def(repo)
    assert external_repo_data.get_external_pipeline_data("a_pipeline")
    assert external_repo_data.get_external_schedule_data("a_schedule")
    assert external_repo_data.get_external_partition_set_data("a_schedule_partitions")
    snapshot.assert_match(serialize_pp(external_repo_data))


def test_external_pipeline_data(snapshot):
    snapshot.assert_match(serialize_pp(external_pipeline_data_from_def(a_pipeline)))
