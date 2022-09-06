import pendulum
import pytest

from dagster import AssetKey, materialize
from dagster._core.scheduler.instigation import TickStatus
from dagster._seven.compat.pendulum import create_pendulum_time, to_timezone

from .test_sensor_run import (
    e,
    evaluate_sensors,
    get_sensor_executors,
    instance_with_sensors,
    validate_tick,
    wait_for_all_runs_to_finish,
    x,
    z,
)


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_simple_parent_sensor(executor):
    """Asset graph:
        x
        |
        y
    Sensor for y
    Tests that materializing x results in a materialization of y
    """
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with instance_with_sensors(attribute="asset_sensor_repo") as (
        instance,
        workspace,
        external_repo,
    ):
        with pendulum.test(freeze_datetime):
            y_sensor = external_repo.get_external_sensor("just_y")
            instance.start_sensor(y_sensor)

            evaluate_sensors(instance, workspace, executor)

            ticks = instance.get_ticks(y_sensor.get_external_origin_id(), y_sensor.selector_id)
            assert len(ticks) == 1
            validate_tick(
                ticks[0],
                y_sensor,
                freeze_datetime,
                TickStatus.SKIPPED,
            )

            freeze_datetime = freeze_datetime.add(seconds=60)
        with pendulum.test(freeze_datetime):

            materialize([x], instance=instance)
            wait_for_all_runs_to_finish(instance)

            evaluate_sensors(instance, workspace, executor)

            # sensor should materialize
            ticks = instance.get_ticks(y_sensor.get_external_origin_id(), y_sensor.selector_id)
            assert len(ticks) == 2
            validate_tick(
                ticks[0],
                y_sensor,
                freeze_datetime,
                TickStatus.SUCCESS,
            )

            wait_for_all_runs_to_finish(instance)
            run_request_runs = [r for r in instance.get_runs() if r.pipeline_name == "__ASSET_JOB"]
            assert len(run_request_runs) == 1
            assert run_request_runs[0].asset_selection == {AssetKey("y")}

            freeze_datetime = freeze_datetime.add(seconds=60)

        with pendulum.test(freeze_datetime):

            materialize([x], instance=instance)
            wait_for_all_runs_to_finish(instance)

            evaluate_sensors(instance, workspace, executor)

            # sensor should materialize
            ticks = instance.get_ticks(y_sensor.get_external_origin_id(), y_sensor.selector_id)
            assert len(ticks) == 3
            validate_tick(
                ticks[0],
                y_sensor,
                freeze_datetime,
                TickStatus.SUCCESS,
            )

            wait_for_all_runs_to_finish(instance)
            run_request_runs = [r for r in instance.get_runs() if r.pipeline_name == "__ASSET_JOB"]
            assert len(run_request_runs) == 2
            assert all([r.asset_selection == {AssetKey("y")} for r in run_request_runs])

            freeze_datetime = freeze_datetime.add(seconds=60)


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_two_parents_parent_sensor(executor):
    """Asset graph:
        x   z
        \   /
          d
    Sensor for d
    Tests that materializing x does nothing, then materialize z and see that d gets materialized
    """
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with instance_with_sensors(attribute="asset_sensor_repo") as (
        instance,
        workspace,
        external_repo,
    ):
        with pendulum.test(freeze_datetime):
            d_sensor = external_repo.get_external_sensor("just_d")
            instance.start_sensor(d_sensor)

            evaluate_sensors(instance, workspace, executor)

            ticks = instance.get_ticks(d_sensor.get_external_origin_id(), d_sensor.selector_id)
            assert len(ticks) == 1
            validate_tick(
                ticks[0],
                d_sensor,
                freeze_datetime,
                TickStatus.SKIPPED,
            )

            freeze_datetime = freeze_datetime.add(seconds=60)
        with pendulum.test(freeze_datetime):

            materialize([x], instance=instance)
            wait_for_all_runs_to_finish(instance)

            evaluate_sensors(instance, workspace, executor)

            # sensor should not start a materialization
            ticks = instance.get_ticks(d_sensor.get_external_origin_id(), d_sensor.selector_id)
            assert len(ticks) == 2
            validate_tick(
                ticks[0],
                d_sensor,
                freeze_datetime,
                TickStatus.SKIPPED,
            )

            freeze_datetime = freeze_datetime.add(seconds=60)

        with pendulum.test(freeze_datetime):

            materialize([z], instance=instance)
            wait_for_all_runs_to_finish(instance)

            evaluate_sensors(instance, workspace, executor)

            # sensor should fire
            ticks = instance.get_ticks(d_sensor.get_external_origin_id(), d_sensor.selector_id)
            assert len(ticks) == 3
            validate_tick(
                ticks[0],
                d_sensor,
                freeze_datetime,
                TickStatus.SUCCESS,
            )

            wait_for_all_runs_to_finish(instance)
            run_request_runs = [r for r in instance.get_runs() if r.pipeline_name == "__ASSET_JOB"]
            assert len(run_request_runs) == 1
            assert all([r.asset_selection == {AssetKey("d")} for r in run_request_runs])

            freeze_datetime = freeze_datetime.add(seconds=60)


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_two_downstream_sensor(executor):
    """Asset graph:
        x   z   e
        \   /\  /
          d    f
    Sensor for d and f
    Tests that materializing z and e does nothing, then materializing z causes d and f to materialize
    """
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with instance_with_sensors(attribute="asset_sensor_repo") as (
        instance,
        workspace,
        external_repo,
    ):
        with pendulum.test(freeze_datetime):
            d_and_f_sensor = external_repo.get_external_sensor("d_and_f")
            instance.start_sensor(d_and_f_sensor)

            evaluate_sensors(instance, workspace, executor)

            ticks = instance.get_ticks(
                d_and_f_sensor.get_external_origin_id(), d_and_f_sensor.selector_id
            )
            assert len(ticks) == 1
            validate_tick(
                ticks[0],
                d_and_f_sensor,
                freeze_datetime,
                TickStatus.SKIPPED,
            )

            freeze_datetime = freeze_datetime.add(seconds=60)
        with pendulum.test(freeze_datetime):

            materialize([x, e], instance=instance)
            wait_for_all_runs_to_finish(instance)

            evaluate_sensors(instance, workspace, executor)

            # sensor should not start a materialize
            ticks = instance.get_ticks(
                d_and_f_sensor.get_external_origin_id(), d_and_f_sensor.selector_id
            )
            assert len(ticks) == 2
            validate_tick(
                ticks[0],
                d_and_f_sensor,
                freeze_datetime,
                TickStatus.SKIPPED,
            )

            freeze_datetime = freeze_datetime.add(seconds=60)

        with pendulum.test(freeze_datetime):

            materialize([z], instance=instance)
            wait_for_all_runs_to_finish(instance)

            evaluate_sensors(instance, workspace, executor)

            # sensor should materialize
            ticks = instance.get_ticks(
                d_and_f_sensor.get_external_origin_id(), d_and_f_sensor.selector_id
            )
            assert len(ticks) == 3
            validate_tick(
                ticks[0],
                d_and_f_sensor,
                freeze_datetime,
                TickStatus.SUCCESS,
            )

            wait_for_all_runs_to_finish(instance)
            run_request_runs = [r for r in instance.get_runs() if r.pipeline_name == "__ASSET_JOB"]
            assert len(run_request_runs) == 1
            assert all(
                [r.asset_selection == {AssetKey("f"), AssetKey("d")} for r in run_request_runs]
            )

            freeze_datetime = freeze_datetime.add(seconds=60)


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_layered_sensor(executor):
    """Asset graph:
        x       z       e
        \       /\      /
            d       f
            \       /
                g
    Sensor for d, f, and g
    Tests that materializing x, z, and e causes a materialization of d and f, which causes a materialization of g
    """
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with instance_with_sensors(attribute="asset_sensor_repo") as (
        instance,
        workspace,
        external_repo,
    ):
        with pendulum.test(freeze_datetime):
            the_sensor = external_repo.get_external_sensor("d_and_f_and_g")
            instance.start_sensor(the_sensor)

            evaluate_sensors(instance, workspace, executor)

            ticks = instance.get_ticks(the_sensor.get_external_origin_id(), the_sensor.selector_id)
            assert len(ticks) == 1
            validate_tick(
                ticks[0],
                the_sensor,
                freeze_datetime,
                TickStatus.SKIPPED,
            )

            freeze_datetime = freeze_datetime.add(seconds=60)
        with pendulum.test(freeze_datetime):

            materialize([x, z, e], instance=instance)
            wait_for_all_runs_to_finish(instance)

            evaluate_sensors(instance, workspace, executor)

            # sensor should materialize
            ticks = instance.get_ticks(the_sensor.get_external_origin_id(), the_sensor.selector_id)
            assert len(ticks) == 2
            validate_tick(
                ticks[0],
                the_sensor,
                freeze_datetime,
                TickStatus.SUCCESS,
            )

            wait_for_all_runs_to_finish(instance)
            run_request_runs = [r for r in instance.get_runs() if r.pipeline_name == "__ASSET_JOB"]
            assert len(run_request_runs) == 1
            assert run_request_runs[0].asset_selection == {AssetKey("d"), AssetKey("f"), AssetKey("g")}

            freeze_datetime = freeze_datetime.add(seconds=60)



@pytest.mark.parametrize("executor", get_sensor_executors())
def test_lots_of_materializations_sensor(executor):
    """Asset graph:
        x
        |
        y
    Sensor for y
    Tests that materializing x a few times, then starting the sensor results in only one materialization
        of y
    """
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with instance_with_sensors(attribute="asset_sensor_repo") as (
        instance,
        workspace,
        external_repo,
    ):
        with pendulum.test(freeze_datetime):
            for _ in range(5):
                materialize([x], instance=instance)
            wait_for_all_runs_to_finish(instance)

            y_sensor = external_repo.get_external_sensor("just_y")
            instance.start_sensor(y_sensor)

            evaluate_sensors(instance, workspace, executor)

            ticks = instance.get_ticks(y_sensor.get_external_origin_id(), y_sensor.selector_id)
            assert len(ticks) == 1
            validate_tick(
                ticks[0],
                y_sensor,
                freeze_datetime,
                TickStatus.SUCCESS,
            )

            wait_for_all_runs_to_finish(instance)
            run_request_runs = [r for r in instance.get_runs() if r.pipeline_name == "__ASSET_JOB"]
            assert len(run_request_runs) == 1
            assert run_request_runs[0].asset_selection == {AssetKey("y")}

            freeze_datetime = freeze_datetime.add(seconds=60)
        with pendulum.test(freeze_datetime):

            evaluate_sensors(instance, workspace, executor)

            # sensor should materialize
            ticks = instance.get_ticks(y_sensor.get_external_origin_id(), y_sensor.selector_id)
            assert len(ticks) == 2
            validate_tick(
                ticks[0],
                y_sensor,
                freeze_datetime,
                TickStatus.SKIPPED,
            )


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_many_materializations_for_one_parent_sensor(executor):
    """Asset graph:
        x   z
        |\   /
        y  d
    Sensor for y and d
    Tests that materializing x x many times only materializes y, then materializing z materializes
        d once
    """
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with instance_with_sensors(attribute="asset_sensor_repo") as (
        instance,
        workspace,
        external_repo,
    ):
        with pendulum.test(freeze_datetime):
            the_sensor = external_repo.get_external_sensor("y_and_d")
            instance.start_sensor(the_sensor)

            evaluate_sensors(instance, workspace, executor)

            ticks = instance.get_ticks(the_sensor.get_external_origin_id(), the_sensor.selector_id)
            assert len(ticks) == 1
            validate_tick(
                ticks[0],
                the_sensor,
                freeze_datetime,
                TickStatus.SKIPPED,
            )

            freeze_datetime = freeze_datetime.add(seconds=60)
        with pendulum.test(freeze_datetime):

            materialize([x], instance=instance)
            wait_for_all_runs_to_finish(instance)

            evaluate_sensors(instance, workspace, executor)

            # sensor should  materialize y
            ticks = instance.get_ticks(the_sensor.get_external_origin_id(), the_sensor.selector_id)
            assert len(ticks) == 2
            validate_tick(
                ticks[0],
                the_sensor,
                freeze_datetime,
                TickStatus.SUCCESS,
            )

            wait_for_all_runs_to_finish(instance)
            run_request_runs = [r for r in instance.get_runs() if r.pipeline_name == "__ASSET_JOB"]
            assert len(run_request_runs) == 1
            assert all([r.asset_selection == {AssetKey("y")} for r in run_request_runs])

            freeze_datetime = freeze_datetime.add(seconds=60)

        with pendulum.test(freeze_datetime):

            materialize([x], instance=instance)
            wait_for_all_runs_to_finish(instance)

            evaluate_sensors(instance, workspace, executor)

            # sensor should materialize y
            ticks = instance.get_ticks(the_sensor.get_external_origin_id(), the_sensor.selector_id)
            assert len(ticks) == 3
            validate_tick(
                ticks[0],
                the_sensor,
                freeze_datetime,
                TickStatus.SUCCESS,
            )

            wait_for_all_runs_to_finish(instance)
            run_request_runs = [r for r in instance.get_runs() if r.pipeline_name == "__ASSET_JOB"]
            assert len(run_request_runs) == 2
            assert all([r.asset_selection == {AssetKey("y")} for r in run_request_runs])

            freeze_datetime = freeze_datetime.add(seconds=60)

        with pendulum.test(freeze_datetime):

            materialize([z], instance=instance)
            wait_for_all_runs_to_finish(instance)

            evaluate_sensors(instance, workspace, executor)

            # sensor should fire
            ticks = instance.get_ticks(the_sensor.get_external_origin_id(), the_sensor.selector_id)
            assert len(ticks) == 4
            validate_tick(
                ticks[0],
                the_sensor,
                freeze_datetime,
                TickStatus.SUCCESS,
            )

            wait_for_all_runs_to_finish(instance)
            run_request_runs = [r for r in instance.get_runs() if r.pipeline_name == "__ASSET_JOB"]
            assert len(run_request_runs) == 3
            assert run_request_runs[0].asset_selection == {AssetKey("d")}
