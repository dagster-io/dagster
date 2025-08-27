import dagster as dg
from dagster._core.snap import JobSnap
from dagster._core.snap.mode import ModeDefSnap


def test_mode_snap(snapshot):
    @dg.resource(config_schema={"foo": str})
    def a_resource(_):
        pass

    @dg.resource(description="resource_description")
    def no_config_resource(_):
        pass

    @dg.logger(config_schema={"bar": str})  # pyright: ignore[reportArgumentType]
    def a_logger(_):
        pass

    @dg.logger(description="logger_description")  # pyright: ignore[reportCallIssue]
    def no_config_logger(_):
        pass

    @dg.job(
        resource_defs={
            "some_resource": a_resource,
            "no_config_resource": no_config_resource,
        },
        logger_defs={  # pyright: ignore[reportArgumentType]
            "some_logger": a_logger,
            "no_config_logger": no_config_logger,
        },
    )
    def a_job():
        pass

    job_snapshot = JobSnap.from_job_def(a_job)
    assert len(job_snapshot.mode_def_snaps) == 1
    mode_def_snap = job_snapshot.mode_def_snaps[0]

    snapshot.assert_match(dg.serialize_value(mode_def_snap))

    assert mode_def_snap == dg.deserialize_value(dg.serialize_value(mode_def_snap), ModeDefSnap)
