import dagster as dg
import pytest
from dagster._check import CheckError
from dagster._core.instance import DagsterInstance


@dg.op
def do_something():
    pass


@dg.job
def do_something_job():
    do_something()


def test_sensor_result_one_run_request():
    @dg.sensor(job=do_something_job)
    def test_sensor(_):
        return dg.SensorResult(run_requests=[dg.RunRequest(run_key="foo")])

    with dg.instance_for_test() as instance:
        ctx = dg.build_sensor_context(
            instance=instance,
        )
        sensor_data = test_sensor.evaluate_tick(ctx)
        assert len(sensor_data.run_requests) == 1  # pyright: ignore[reportArgumentType]
        assert sensor_data.run_requests[0].run_key == "foo"  # pyright: ignore[reportOptionalSubscript]
        assert not sensor_data.skip_message
        assert not sensor_data.dagster_run_reactions
        assert not sensor_data.cursor


def test_sensor_result_skip_reason():
    skip_reason = dg.SkipReason("I'm skipping")

    @dg.sensor(job=do_something_job)  # pyright: ignore[reportArgumentType]
    def test_sensor(_):
        return [
            dg.SensorResult(skip_reason=skip_reason),
        ]

    with dg.instance_for_test() as instance:
        ctx = dg.build_sensor_context(
            instance=instance,
        )
        sensor_data = test_sensor.evaluate_tick(ctx)
        assert not sensor_data.run_requests
        assert sensor_data.skip_message == skip_reason.skip_message
        assert not sensor_data.dagster_run_reactions
        assert not sensor_data.cursor


def test_sensor_result_string_skip_reason():
    skip_reason = "I'm skipping"

    @dg.sensor(job=do_something_job)  # pyright: ignore[reportArgumentType]
    def test_sensor(_):
        return [
            dg.SensorResult(skip_reason=skip_reason),
        ]

    with dg.instance_for_test() as instance:
        ctx = dg.build_sensor_context(
            instance=instance,
        )
        sensor_data = test_sensor.evaluate_tick(ctx)
        assert not sensor_data.run_requests
        assert sensor_data.skip_message == skip_reason
        assert not sensor_data.dagster_run_reactions
        assert not sensor_data.cursor


def test_invalid_skip_reason_invocations():
    @dg.sensor(job=do_something_job)  # pyright: ignore[reportArgumentType]
    def multiple_sensor_results(_):
        return [
            dg.SensorResult(skip_reason=dg.SkipReason("I'm skipping")),
            dg.SensorResult(skip_reason=dg.SkipReason("I'm skipping")),
        ]

    @dg.sensor(job=do_something_job)
    def sensor_result_w_other_objects(_):
        return [
            dg.SensorResult(run_requests=[dg.RunRequest(run_key="foo")]),
            dg.RunRequest(run_key="foo"),
        ]

    @dg.sensor(job=do_something_job)  # pyright: ignore[reportArgumentType]
    def invalid_sensor_result(_):
        return [
            dg.SensorResult(
                run_requests=[dg.RunRequest(run_key="foo")], skip_reason=dg.SkipReason("aklsdj")
            ),
        ]

    with dg.instance_for_test() as instance:
        ctx = dg.build_sensor_context(
            instance=instance,
        )

        with pytest.raises(
            CheckError,
            match=(
                r"When a SensorResult is returned from a sensor, it must be the only object"
                " returned."
            ),
        ):
            multiple_sensor_results.evaluate_tick(ctx)

        with pytest.raises(
            CheckError,
            match=(
                r"When a SensorResult is returned from a sensor, it must be the only object"
                " returned."
            ),
        ):
            sensor_result_w_other_objects.evaluate_tick(ctx)

        with pytest.raises(
            CheckError,
            match="Expected a single skip reason or one or more run requests",
        ):
            invalid_sensor_result.evaluate_tick(ctx)


def test_update_cursor():
    @dg.sensor(job=do_something_job)  # pyright: ignore[reportArgumentType]
    def test_sensor(_):
        return [
            dg.SensorResult([dg.RunRequest("foo")], cursor="foo"),
        ]

    with dg.instance_for_test() as instance:
        ctx = dg.build_sensor_context(
            instance=instance,
        )
        result = test_sensor.evaluate_tick(ctx)
        assert result.cursor == "foo"


def test_update_cursor_and_sensor_result_cursor():
    @dg.sensor(job=do_something_job)  # pyright: ignore[reportArgumentType]
    def test_sensor(context):
        context.update_cursor("bar")
        return [
            dg.SensorResult([dg.RunRequest("foo")], cursor="foo"),
        ]

    with dg.instance_for_test() as instance:
        ctx = dg.build_sensor_context(
            instance=instance,
        )
        with pytest.raises(
            dg.DagsterInvariantViolationError,
            match=r"cannot be set if context.update_cursor()",
        ):
            test_sensor.evaluate_tick(ctx)


def test_sensor_result_asset_sensor():
    observed = {}

    @dg.op
    def my_table_materialization():
        yield dg.AssetMaterialization("my_table")
        yield dg.Output(1)

    @dg.job
    def my_table_job():
        my_table_materialization()

    @dg.asset_sensor(asset_key=dg.AssetKey("my_table"), job=do_something_job)
    def my_asset_sensor(context, asset_event):
        observed["cursor"] = context.cursor
        return dg.SensorResult([dg.RunRequest("foo")])

    @dg.asset_sensor(asset_key=dg.AssetKey("my_table"), job=do_something_job)
    def asset_sensor_set_cursor(context, asset_event):
        return dg.SensorResult([dg.RunRequest("foo")], cursor="foo")

    with dg.instance_for_test() as instance:
        my_table_job.execute_in_process(instance=instance)
        with dg.build_sensor_context(
            instance=instance,
        ) as ctx:
            result = my_asset_sensor.evaluate_tick(ctx)
            assert len(result.run_requests) == 1  # pyright: ignore[reportArgumentType]
            assert result.run_requests[0].run_key == "foo"  # pyright: ignore[reportOptionalSubscript]
            assert result.cursor != observed["cursor"]  # ensure cursor progresses

        with dg.build_sensor_context(
            instance=instance,
        ) as ctx:
            with pytest.raises(
                dg.DagsterInvariantViolationError, match="The cursor is managed by the asset sensor"
            ):
                asset_sensor_set_cursor.evaluate_tick(ctx)


def test_yield_and_return():
    @dg.job
    def job1():
        pass

    @dg.sensor(job=job1)
    def sensor_with_yield_run_request_and_return_skip_reason(context):
        if context.cursor == "skip":
            return dg.SkipReason("This is a skip reason")
        else:
            yield dg.RunRequest()

    result_with_skip = sensor_with_yield_run_request_and_return_skip_reason.evaluate_tick(
        dg.build_sensor_context(cursor="skip")
    )
    assert result_with_skip.skip_message == "This is a skip reason"
    assert result_with_skip.run_requests == []

    result_without_skip = sensor_with_yield_run_request_and_return_skip_reason.evaluate_tick(
        dg.build_sensor_context(cursor="go")
    )
    assert result_without_skip.skip_message is None
    assert len(result_without_skip.run_requests) == 1  # pyright: ignore[reportArgumentType]

    @dg.sensor(job=job1)
    def sensor_with_yield_and_return_run_request(context):
        yield dg.RunRequest()
        return dg.RunRequest()

    result_yield_and_return_run_request = sensor_with_yield_and_return_run_request.evaluate_tick(
        dg.build_sensor_context()
    )
    assert len(result_yield_and_return_run_request.run_requests) == 2  # pyright: ignore[reportArgumentType]


def test_asset_materialization_in_sensor() -> None:
    @dg.sensor()
    def a_sensor() -> dg.SensorResult:
        return dg.SensorResult(asset_events=[dg.AssetMaterialization("asset_one")])

    instance = DagsterInstance.ephemeral()
    sensor_execution_data = a_sensor.evaluate_tick(dg.build_sensor_context(instance=instance))
    assert len(sensor_execution_data.asset_events) == 1
    output_mat = sensor_execution_data.asset_events[0]
    assert isinstance(output_mat, dg.AssetMaterialization)
    assert output_mat.asset_key == dg.AssetKey("asset_one")


def test_asset_observation_in_sensor() -> None:
    @dg.sensor()
    def a_sensor() -> dg.SensorResult:
        return dg.SensorResult(asset_events=[dg.AssetObservation("asset_one")])

    instance = DagsterInstance.ephemeral()
    sensor_execution_data = a_sensor.evaluate_tick(dg.build_sensor_context(instance=instance))
    assert len(sensor_execution_data.asset_events) == 1
    output_mat = sensor_execution_data.asset_events[0]
    assert isinstance(output_mat, dg.AssetObservation)
    assert output_mat.asset_key == dg.AssetKey("asset_one")


def test_asset_check_evaluation() -> None:
    @dg.sensor()
    def a_sensor() -> dg.SensorResult:
        return dg.SensorResult(
            asset_events=[
                dg.AssetCheckEvaluation(
                    asset_key=dg.AssetKey("asset_one"),
                    check_name="check_one",
                    passed=True,
                    metadata={},
                )
            ]
        )

    instance = DagsterInstance.ephemeral()
    sensor_execution_data = a_sensor.evaluate_tick(dg.build_sensor_context(instance=instance))
    assert len(sensor_execution_data.asset_events) == 1
    output_ace = sensor_execution_data.asset_events[0]
    assert isinstance(output_ace, dg.AssetCheckEvaluation)
    assert output_ace.asset_key == dg.AssetKey("asset_one")


def test_asset_materialization_in_sensor_direct_invocation() -> None:
    @dg.sensor()
    def a_sensor() -> dg.SensorResult:
        return dg.SensorResult(asset_events=[dg.AssetMaterialization("asset_one")])

    instance = DagsterInstance.ephemeral()
    a_sensor(dg.build_sensor_context(instance=instance))


def test_sensor_tags_not_on_run_request():
    @dg.sensor(target="foo", tags={"foo": "bar"})
    def my_sensor():
        return dg.RunRequest()

    with dg.instance_for_test() as instance:
        result = my_sensor.evaluate_tick(dg.build_sensor_context(instance))
        assert "foo" not in result.run_requests[0].tags  # pyright: ignore[reportOptionalSubscript]
