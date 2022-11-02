from dagster import job, logger, resource
from dagster._core.snap import PipelineSnapshot
from dagster._serdes import deserialize_json_to_dagster_namedtuple, serialize_dagster_namedtuple


def test_mode_snap(snapshot):
    @resource(config_schema={"foo": str})
    def a_resource(_):
        pass

    @resource(description="resource_description")
    def no_config_resource(_):
        pass

    @logger(config_schema={"bar": str})
    def a_logger(_):
        pass

    @logger(description="logger_description")
    def no_config_logger(_):
        pass

    @job(
        resource_defs={
            "some_resource": a_resource,
            "no_config_resource": no_config_resource,
        },
        logger_defs={
            "some_logger": a_logger,
            "no_config_logger": no_config_logger,
        },
    )
    def a_job():
        pass

    pipeline_snapshot = PipelineSnapshot.from_pipeline_def(a_job)
    assert len(pipeline_snapshot.mode_def_snaps) == 1
    mode_def_snap = pipeline_snapshot.mode_def_snaps[0]

    snapshot.assert_match(serialize_dagster_namedtuple(mode_def_snap))

    assert mode_def_snap == deserialize_json_to_dagster_namedtuple(
        serialize_dagster_namedtuple(mode_def_snap)
    )
