# pylint: disable=anomalous-backslash-in-string
import threading

import pendulum
import pytest

from dagster import AssetKey, materialize
from dagster._core.scheduler.instigation import TickStatus
from dagster._seven.compat.pendulum import create_pendulum_time, to_timezone

from .test_run_status_sensors import instance_with_sensors
from .test_sensor_run import (
    d,
    e,
    evaluate_sensors,
    f,
    get_sensor_executors,
    h,
    sleeper,
    validate_tick,
    wait_for_all_runs_to_finish,
    wait_for_all_runs_to_start,
    x,
    y,
    z,
)


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_simple_parent_sensor(executor):
    """Asset graph:
        x
        |
        y
    Sensor for y that materializes y when all of its parents have materialized
    Tests that materializing x results in a materialization of y
    """
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with instance_with_sensors(attribute="asset_sensor_repo") as (
        instance,
        workspace_ctx,
        external_repo,
    ):
        with pendulum.test(freeze_datetime):
            y_sensor = external_repo.get_external_sensor("just_y_AND")
            instance.start_sensor(y_sensor)

            evaluate_sensors(workspace_ctx, executor)

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

            evaluate_sensors(workspace_ctx, executor)

            ticks = instance.get_ticks(y_sensor.get_external_origin_id(), y_sensor.selector_id)
            assert len(ticks) == 2
            validate_tick(
                ticks[0],
                y_sensor,
                freeze_datetime,
                TickStatus.SUCCESS,
            )

            wait_for_all_runs_to_finish(instance)
            run_request = instance.get_runs(limit=1)[0]
            assert run_request.pipeline_name == "__ASSET_JOB"
            assert run_request.asset_selection == {AssetKey("y")}

            freeze_datetime = freeze_datetime.add(seconds=60)

        with pendulum.test(freeze_datetime):

            materialize([x], instance=instance)
            wait_for_all_runs_to_finish(instance)

            evaluate_sensors(workspace_ctx, executor)

            ticks = instance.get_ticks(y_sensor.get_external_origin_id(), y_sensor.selector_id)
            assert len(ticks) == 3
            validate_tick(
                ticks[0],
                y_sensor,
                freeze_datetime,
                TickStatus.SUCCESS,
            )

            wait_for_all_runs_to_finish(instance)
            run_request = instance.get_runs(limit=1)[0]
            assert run_request.pipeline_name == "__ASSET_JOB"
            assert run_request.asset_selection == {AssetKey("y")}


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_two_parents_AND_sensor(executor):
    """Asset graph:
        x   z
        \   /
          d
    Sensor for d that materializes d when all of its parents have materialized
    Tests that materializing x materializes d since this is an OR sensor
    """
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with instance_with_sensors(attribute="asset_sensor_repo") as (
        instance,
        workspace_ctx,
        external_repo,
    ):
        with pendulum.test(freeze_datetime):
            d_sensor = external_repo.get_external_sensor("just_d_AND")
            instance.start_sensor(d_sensor)

            evaluate_sensors(workspace_ctx, executor)

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

            evaluate_sensors(workspace_ctx, executor)

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

            evaluate_sensors(workspace_ctx, executor)

            ticks = instance.get_ticks(d_sensor.get_external_origin_id(), d_sensor.selector_id)
            assert len(ticks) == 3
            validate_tick(
                ticks[0],
                d_sensor,
                freeze_datetime,
                TickStatus.SUCCESS,
            )

            wait_for_all_runs_to_finish(instance)
            run_request = instance.get_runs(limit=1)[0]
            assert run_request.pipeline_name == "__ASSET_JOB"
            assert run_request.asset_selection == {AssetKey("d")}


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_two_parents_OR_sensor(executor):
    """Asset graph:
        x   z
        \   /
          d
    Sensor that materializes d if x OR z materializes
    Tests that materializing x materializes d
    """
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with instance_with_sensors(attribute="asset_sensor_repo") as (
        instance,
        workspace_ctx,
        external_repo,
    ):
        with pendulum.test(freeze_datetime):
            # materialize the whole graph so that we can materialize d successfully when only one parent updates
            materialize([x, z, d], instance=instance)
            d_sensor = external_repo.get_external_sensor("just_d_OR")
            instance.start_sensor(d_sensor)

            evaluate_sensors(workspace_ctx, executor)

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

            evaluate_sensors(workspace_ctx, executor)

            ticks = instance.get_ticks(d_sensor.get_external_origin_id(), d_sensor.selector_id)
            assert len(ticks) == 2
            validate_tick(
                ticks[0],
                d_sensor,
                freeze_datetime,
                TickStatus.SUCCESS,
            )
            wait_for_all_runs_to_finish(instance)
            run_request = instance.get_runs(limit=1)[0]
            assert run_request.pipeline_name == "__ASSET_JOB"
            assert run_request.asset_selection == {AssetKey("d")}

            freeze_datetime = freeze_datetime.add(seconds=60)

        with pendulum.test(freeze_datetime):

            materialize([z], instance=instance)
            wait_for_all_runs_to_finish(instance)

            evaluate_sensors(workspace_ctx, executor)

            ticks = instance.get_ticks(d_sensor.get_external_origin_id(), d_sensor.selector_id)
            assert len(ticks) == 3
            validate_tick(
                ticks[0],
                d_sensor,
                freeze_datetime,
                TickStatus.SUCCESS,
            )

            wait_for_all_runs_to_finish(instance)
            run_request = instance.get_runs(limit=1)[0]
            assert run_request.pipeline_name == "__ASSET_JOB"
            assert run_request.asset_selection == {AssetKey("d")}


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_two_downstream_AND_sensor(executor):
    """Asset graph:
        x   z   e
        \   /\  /
          d    f
    Sensor for d and f that will materialize d (or f) when all of its parents have materialized
    Tests that materializing x and e does nothing, then materializing z causes d and f to materialize
    """
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with instance_with_sensors(attribute="asset_sensor_repo") as (
        instance,
        workspace_ctx,
        external_repo,
    ):
        with pendulum.test(freeze_datetime):
            d_and_f_sensor = external_repo.get_external_sensor("d_and_f_AND")
            instance.start_sensor(d_and_f_sensor)

            evaluate_sensors(workspace_ctx, executor)

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

            evaluate_sensors(workspace_ctx, executor)

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

            evaluate_sensors(workspace_ctx, executor)

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
            run_request = instance.get_runs(limit=1)[0]
            assert run_request.pipeline_name == "__ASSET_JOB"
            assert run_request.asset_selection == {AssetKey("f"), AssetKey("d")}


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_two_downstream_OR_sensor(executor):
    """Asset graph:
        x   z   e
        \   /\  /
          d    f
    Sensor for d and f that will materialize d (or f) if any of their parents materializes
    Tests that materializing x only materializes d, materializing e only materializes f, and materializing
    z materializes d and f
    """
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with instance_with_sensors(attribute="asset_sensor_repo") as (
        instance,
        workspace_ctx,
        external_repo,
    ):
        with pendulum.test(freeze_datetime):
            # materialize the whole graph so that we can materialize d or f successfully when only
            # one parent updates
            materialize([x, z, e, d, f], instance=instance)

            d_and_f_sensor = external_repo.get_external_sensor("d_and_f_OR")
            instance.start_sensor(d_and_f_sensor)

            evaluate_sensors(workspace_ctx, executor)

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

            materialize([x], instance=instance)
            wait_for_all_runs_to_finish(instance)

            evaluate_sensors(workspace_ctx, executor)

            ticks = instance.get_ticks(
                d_and_f_sensor.get_external_origin_id(), d_and_f_sensor.selector_id
            )
            assert len(ticks) == 2
            validate_tick(
                ticks[0],
                d_and_f_sensor,
                freeze_datetime,
                TickStatus.SUCCESS,
            )

            wait_for_all_runs_to_finish(instance)
            run_request = instance.get_runs(limit=1)[0]
            assert run_request.pipeline_name == "__ASSET_JOB"
            assert run_request.asset_selection == {AssetKey("d")}

            freeze_datetime = freeze_datetime.add(seconds=60)

        with pendulum.test(freeze_datetime):

            materialize([e], instance=instance)
            wait_for_all_runs_to_finish(instance)

            evaluate_sensors(workspace_ctx, executor)

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
            run_request = instance.get_runs(limit=1)[0]
            assert run_request.pipeline_name == "__ASSET_JOB"
            assert run_request.asset_selection == {AssetKey("f")}

            freeze_datetime = freeze_datetime.add(seconds=60)

        with pendulum.test(freeze_datetime):

            materialize([z], instance=instance)
            wait_for_all_runs_to_finish(instance)

            evaluate_sensors(workspace_ctx, executor)

            ticks = instance.get_ticks(
                d_and_f_sensor.get_external_origin_id(), d_and_f_sensor.selector_id
            )
            assert len(ticks) == 4
            validate_tick(
                ticks[0],
                d_and_f_sensor,
                freeze_datetime,
                TickStatus.SUCCESS,
            )

            wait_for_all_runs_to_finish(instance)
            run_request = instance.get_runs(limit=1)[0]
            assert run_request.pipeline_name == "__ASSET_JOB"
            assert run_request.asset_selection == {AssetKey("f"), AssetKey("d")}


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_layered_sensor(executor):
    """Asset graph:
        x       z       e
        \       /\      /
            d       f
            \       /
                g
    Sensor for d, f, and g that materializes a child asset when all of its parents have materialized
    Tests that materializing x, z, and e causes a materialization of d and f, which causes a materialization of g
    """
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with instance_with_sensors(attribute="asset_sensor_repo") as (
        instance,
        workspace_ctx,
        external_repo,
    ):
        with pendulum.test(freeze_datetime):
            the_sensor = external_repo.get_external_sensor("d_and_f_and_g_AND")
            instance.start_sensor(the_sensor)

            evaluate_sensors(workspace_ctx, executor)

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

            evaluate_sensors(workspace_ctx, executor)

            ticks = instance.get_ticks(the_sensor.get_external_origin_id(), the_sensor.selector_id)
            assert len(ticks) == 2
            validate_tick(
                ticks[0],
                the_sensor,
                freeze_datetime,
                TickStatus.SUCCESS,
            )

            wait_for_all_runs_to_finish(instance)
            run_request = instance.get_runs(limit=1)[0]
            assert run_request.pipeline_name == "__ASSET_JOB"
            assert run_request.asset_selection == {AssetKey("d"), AssetKey("f"), AssetKey("g")}


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_layered_AND_sensor_no_materialize(executor):
    """Asset graph:
        x       z       e
        \       /\      /
            d       f
            \       /
                g
    Sensor for g that materializes g when all of its parents have materialized
    Tests that materializing x, z, and e does not cause a materialization of g
    """
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with instance_with_sensors(attribute="asset_sensor_repo") as (
        instance,
        workspace_ctx,
        external_repo,
    ):
        with pendulum.test(freeze_datetime):
            the_sensor = external_repo.get_external_sensor("just_g_AND")
            instance.start_sensor(the_sensor)

            evaluate_sensors(workspace_ctx, executor)

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

            evaluate_sensors(workspace_ctx, executor)

            ticks = instance.get_ticks(the_sensor.get_external_origin_id(), the_sensor.selector_id)
            assert len(ticks) == 2
            validate_tick(
                ticks[0],
                the_sensor,
                freeze_datetime,
                TickStatus.SKIPPED,
            )


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_layered_OR_sensor_no_materialize(executor):
    """Asset graph:
        x       z       e
        \       /\      /
            d       f
            \       /
                g
    Sensor for g that will materialize g if any of its parents materialize
    Tests that materializing x, z, and e does not cause a materialization of g
    """
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with instance_with_sensors(attribute="asset_sensor_repo") as (
        instance,
        workspace_ctx,
        external_repo,
    ):
        with pendulum.test(freeze_datetime):
            the_sensor = external_repo.get_external_sensor("just_g_OR")
            instance.start_sensor(the_sensor)

            evaluate_sensors(workspace_ctx, executor)

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

            evaluate_sensors(workspace_ctx, executor)

            ticks = instance.get_ticks(the_sensor.get_external_origin_id(), the_sensor.selector_id)
            assert len(ticks) == 2
            validate_tick(
                ticks[0],
                the_sensor,
                freeze_datetime,
                TickStatus.SKIPPED,
            )


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_lots_of_materializations_sensor(executor):
    """Asset graph:
        x
        |
        y
    Sensor for y
    Tests that materializing x a few times then starting the sensor results in only one materialization
        of y
    """
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with instance_with_sensors(attribute="asset_sensor_repo") as (
        instance,
        workspace_ctx,
        external_repo,
    ):
        with pendulum.test(freeze_datetime):
            for _ in range(5):
                materialize([x], instance=instance)
                wait_for_all_runs_to_finish(instance)

            y_sensor = external_repo.get_external_sensor("just_y_AND")
            instance.start_sensor(y_sensor)

            evaluate_sensors(workspace_ctx, executor)

            ticks = instance.get_ticks(y_sensor.get_external_origin_id(), y_sensor.selector_id)
            assert len(ticks) == 1
            validate_tick(
                ticks[0],
                y_sensor,
                freeze_datetime,
                TickStatus.SUCCESS,
            )

            wait_for_all_runs_to_finish(instance)
            run_request = instance.get_runs(limit=1)[0]
            assert run_request.pipeline_name == "__ASSET_JOB"
            assert run_request.asset_selection == {AssetKey("y")}

            freeze_datetime = freeze_datetime.add(seconds=60)
        with pendulum.test(freeze_datetime):

            evaluate_sensors(workspace_ctx, executor)

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
        x    z
        |\   /
        y  d
    Sensor for y and d that materializes y (or d) when all of its parents have materialized
    Tests that materializing x many times only materializes y, then materializing z materializes
        d once
    """
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with instance_with_sensors(attribute="asset_sensor_repo") as (
        instance,
        workspace_ctx,
        external_repo,
    ):
        with pendulum.test(freeze_datetime):
            the_sensor = external_repo.get_external_sensor("y_and_d_AND")
            instance.start_sensor(the_sensor)

            evaluate_sensors(workspace_ctx, executor)

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

            evaluate_sensors(workspace_ctx, executor)

            ticks = instance.get_ticks(the_sensor.get_external_origin_id(), the_sensor.selector_id)
            assert len(ticks) == 2
            validate_tick(
                ticks[0],
                the_sensor,
                freeze_datetime,
                TickStatus.SUCCESS,
            )

            wait_for_all_runs_to_finish(instance)
            run_request = instance.get_runs(limit=1)[0]
            assert run_request.pipeline_name == "__ASSET_JOB"
            assert run_request.asset_selection == {AssetKey("y")}

            freeze_datetime = freeze_datetime.add(seconds=60)

        with pendulum.test(freeze_datetime):

            materialize([x], instance=instance)
            wait_for_all_runs_to_finish(instance)

            evaluate_sensors(workspace_ctx, executor)

            ticks = instance.get_ticks(the_sensor.get_external_origin_id(), the_sensor.selector_id)
            assert len(ticks) == 3
            validate_tick(
                ticks[0],
                the_sensor,
                freeze_datetime,
                TickStatus.SUCCESS,
            )

            wait_for_all_runs_to_finish(instance)
            run_request = instance.get_runs(limit=1)[0]
            assert run_request.pipeline_name == "__ASSET_JOB"
            assert run_request.asset_selection == {AssetKey("y")}

            freeze_datetime = freeze_datetime.add(seconds=60)

        with pendulum.test(freeze_datetime):

            materialize([z], instance=instance)
            wait_for_all_runs_to_finish(instance)

            evaluate_sensors(workspace_ctx, executor)

            ticks = instance.get_ticks(the_sensor.get_external_origin_id(), the_sensor.selector_id)
            assert len(ticks) == 4
            validate_tick(
                ticks[0],
                the_sensor,
                freeze_datetime,
                TickStatus.SUCCESS,
            )

            wait_for_all_runs_to_finish(instance)
            run_request = instance.get_runs(limit=1)[0]
            assert run_request.pipeline_name == "__ASSET_JOB"
            assert run_request.asset_selection == {AssetKey("d")}


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_two_graph_sensor(executor):
    """Asset graph:
        x   h
        |   |
        y   i
    Sensor for y and i that materializes y (or i) when all of its parents have materialized
    Tests that materializing x results in a materialization of y, materializing h results in a
        materialization of i
    """
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with instance_with_sensors(attribute="asset_sensor_repo") as (
        instance,
        workspace_ctx,
        external_repo,
    ):
        with pendulum.test(freeze_datetime):
            the_sensor = external_repo.get_external_sensor("y_and_i_AND")
            instance.start_sensor(the_sensor)

            evaluate_sensors(workspace_ctx, executor)

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

            evaluate_sensors(workspace_ctx, executor)

            ticks = instance.get_ticks(the_sensor.get_external_origin_id(), the_sensor.selector_id)
            assert len(ticks) == 2
            validate_tick(
                ticks[0],
                the_sensor,
                freeze_datetime,
                TickStatus.SUCCESS,
            )

            wait_for_all_runs_to_finish(instance)
            run_request = instance.get_runs(limit=1)[0]
            assert run_request.pipeline_name == "__ASSET_JOB"
            assert run_request.asset_selection == {AssetKey("y")}

            freeze_datetime = freeze_datetime.add(seconds=60)

        with pendulum.test(freeze_datetime):

            materialize([h], instance=instance)
            wait_for_all_runs_to_finish(instance)

            evaluate_sensors(workspace_ctx, executor)

            ticks = instance.get_ticks(the_sensor.get_external_origin_id(), the_sensor.selector_id)
            assert len(ticks) == 3
            validate_tick(
                ticks[0],
                the_sensor,
                freeze_datetime,
                TickStatus.SUCCESS,
            )

            wait_for_all_runs_to_finish(instance)
            run_request = instance.get_runs(limit=1)[0]
            assert run_request.pipeline_name == "__ASSET_JOB"
            assert run_request.asset_selection == {AssetKey("i")}


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_parent_in_progress_stops_materialization(executor):
    """Asset graph:
        sleeper    x
            \      /
        waits_on_sleep
    Sensor for waits_on_sleep
    Tests that setting parent_in_progress_stops_materialization=True will cause the sensor to not
    materialize waits_on_sleep if one of it's parents is materializing
    """
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with instance_with_sensors(attribute="asset_sensor_repo") as (
        instance,
        workspace_ctx,
        external_repo,
    ):
        with pendulum.test(freeze_datetime):
            the_sensor = external_repo.get_external_sensor("in_progress_condition_sensor")
            instance.start_sensor(the_sensor)

            evaluate_sensors(workspace_ctx, executor)

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
            # materialize x first so that waits_for_sleep would be materialized unless sleeper is in progress
            materialize([x], instance=instance)
            wait_for_all_runs_to_finish(instance)
            # materialize sleeper in a thread so that it will be actively materializing while the sensor tick is evaluated
            sleeper_materialize_thread = threading.Thread(
                target=materialize, args=([sleeper],), kwargs={"instance": instance}
            )
            sleeper_materialize_thread.start()
            wait_for_all_runs_to_start(instance)

            evaluate_sensors(workspace_ctx, executor)
            ticks = instance.get_ticks(the_sensor.get_external_origin_id(), the_sensor.selector_id)
            assert len(ticks) == 2
            validate_tick(
                ticks[0],
                the_sensor,
                freeze_datetime,
                TickStatus.SKIPPED,
            )

            wait_for_all_runs_to_finish(instance, timeout=50)

            freeze_datetime = freeze_datetime.add(seconds=60)
        with pendulum.test(freeze_datetime):
            evaluate_sensors(workspace_ctx, executor)
            ticks = instance.get_ticks(the_sensor.get_external_origin_id(), the_sensor.selector_id)
            assert len(ticks) == 3
            validate_tick(
                ticks[0],
                the_sensor,
                freeze_datetime,
                TickStatus.SUCCESS,
            )

            run_request = instance.get_runs(limit=1)[0]
            assert run_request.pipeline_name == "__ASSET_JOB"
            assert run_request.asset_selection == {AssetKey("waits_on_sleep")}


@pytest.mark.parametrize("executor", get_sensor_executors())
def test_materialization_of_parent_and_child(executor):
    """Asset graph:
        x
        |
        y
    Sensor for y
    Tests that if x and y are both materialized, the sensor will not materialize y (since it was already
    materialized with x)
    """
    freeze_datetime = to_timezone(
        create_pendulum_time(year=2019, month=2, day=27, tz="UTC"),
        "US/Central",
    )
    with instance_with_sensors(attribute="asset_sensor_repo") as (
        instance,
        workspace_ctx,
        external_repo,
    ):
        with pendulum.test(freeze_datetime):
            y_sensor = external_repo.get_external_sensor("just_y_AND")
            instance.start_sensor(y_sensor)

            evaluate_sensors(workspace_ctx, executor)

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
            materialize([x, y], instance=instance)

            evaluate_sensors(workspace_ctx, executor)

            ticks = instance.get_ticks(y_sensor.get_external_origin_id(), y_sensor.selector_id)
            assert len(ticks) == 2
            validate_tick(
                ticks[0],
                y_sensor,
                freeze_datetime,
                TickStatus.SKIPPED,
            )
