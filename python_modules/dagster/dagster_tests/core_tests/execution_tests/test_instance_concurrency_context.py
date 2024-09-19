import time
from contextlib import ExitStack

import mock
import pytest
from dagster import job, op
from dagster._core.execution.plan.instance_concurrency_context import (
    INITIAL_INTERVAL_VALUE,
    STEP_UP_BASE,
    InstanceConcurrencyContext,
)
from dagster._core.utils import make_new_run_id

from dagster_tests.core_tests.execution_tests.conftest import CUSTOM_SLEEP_INTERVAL


def define_foo_job():
    @op
    def foo_op():
        pass

    @job
    def foo_job():
        foo_op()

    return foo_job


def test_global_concurrency(concurrency_instance):
    run = concurrency_instance.create_run_for_job(define_foo_job(), run_id=make_new_run_id())
    concurrency_instance.event_log_storage.set_concurrency_slots("foo", 2)

    with InstanceConcurrencyContext(concurrency_instance, run) as context:
        assert context.claim("foo", "a")
        assert not context.has_pending_claims()
        assert context.claim("foo", "b")
        assert not context.has_pending_claims()
        assert not context.claim("foo", "c")
        assert context.has_pending_claims()
        assert context.pending_claim_steps() == ["c"]
        context.free_step("a")
        assert context.has_pending_claims()
        assert context.pending_claim_steps() == ["c"]

    foo_info = concurrency_instance.event_log_storage.get_concurrency_info("foo")
    assert foo_info.active_slot_count == 1
    assert foo_info.pending_step_count == 0


def test_limitless_context(concurrency_instance):
    run = concurrency_instance.create_run_for_job(define_foo_job(), run_id=make_new_run_id())
    assert concurrency_instance.event_log_storage.get_concurrency_info("foo").slot_count == 0

    with InstanceConcurrencyContext(concurrency_instance, run) as context:
        assert context.claim("foo", "a")
        assert context.claim("foo", "b")
        assert context.claim("foo", "d")
        assert context.claim("foo", "e")
        assert not context.has_pending_claims()

        foo_info = concurrency_instance.event_log_storage.get_concurrency_info("foo")
        assert foo_info.slot_count == 0
        assert foo_info.active_slot_count == 0


def test_context_error(concurrency_instance):
    run = concurrency_instance.create_run_for_job(define_foo_job(), run_id=make_new_run_id())
    concurrency_instance.event_log_storage.set_concurrency_slots("foo", 2)

    with pytest.raises(Exception, match="uh oh"):
        with InstanceConcurrencyContext(concurrency_instance, run) as context:
            assert context.claim("foo", "a")
            assert not context.has_pending_claims()
            assert context.claim("foo", "b")
            assert not context.has_pending_claims()
            assert not context.claim("foo", "c")
            assert context.has_pending_claims()
            assert context.pending_claim_steps() == ["c"]

            context.free_step("a")
            raise Exception("uh oh")

    foo_info = concurrency_instance.event_log_storage.get_concurrency_info("foo")
    assert foo_info.active_slot_count == 1
    assert foo_info.pending_step_count == 0


def test_default_interval(concurrency_instance):
    run = concurrency_instance.create_run_for_job(define_foo_job(), run_id=make_new_run_id())
    concurrency_instance.event_log_storage.set_concurrency_slots("foo", 1)

    with InstanceConcurrencyContext(concurrency_instance, run) as context:
        assert context.claim("foo", "a")
        assert not context.claim("foo", "b")
        call_count = concurrency_instance.event_log_storage.get_check_calls("b")

        context.claim("foo", "b")
        # we have not waited long enough to query the db again
        assert concurrency_instance.event_log_storage.get_check_calls("b") == call_count

        time.sleep(INITIAL_INTERVAL_VALUE)
        context.claim("foo", "b")
        assert concurrency_instance.event_log_storage.get_check_calls("b") == call_count + 1


def test_backoff_interval(concurrency_instance):
    run = concurrency_instance.create_run_for_job(define_foo_job(), run_id=make_new_run_id())
    concurrency_instance.event_log_storage.set_concurrency_slots("foo", 1)

    with InstanceConcurrencyContext(concurrency_instance, run) as context:
        assert context.claim("foo", "a")
        assert not context.claim("foo", "b")
        call_count = concurrency_instance.event_log_storage.get_check_calls("b")

        context.claim("foo", "b")
        # we have not waited long enough to query the db again
        assert concurrency_instance.event_log_storage.get_check_calls("b") == call_count

        time.sleep(INITIAL_INTERVAL_VALUE)
        context.claim("foo", "b")
        assert concurrency_instance.event_log_storage.get_check_calls("b") == call_count + 1

        # sleeping another second will not incur another check call, there's an exponential backoff
        time.sleep(INITIAL_INTERVAL_VALUE)
        context.claim("foo", "b")
        assert concurrency_instance.event_log_storage.get_check_calls("b") == call_count + 1
        time.sleep(STEP_UP_BASE - INITIAL_INTERVAL_VALUE)
        context.claim("foo", "b")
        assert concurrency_instance.event_log_storage.get_check_calls("b") == call_count + 2


def test_custom_interval(concurrency_custom_sleep_instance):
    run = concurrency_custom_sleep_instance.create_run_for_job(
        define_foo_job(), run_id=make_new_run_id()
    )
    storage = concurrency_custom_sleep_instance.event_log_storage
    storage.set_concurrency_slots("foo", 1)

    with InstanceConcurrencyContext(concurrency_custom_sleep_instance, run) as context:
        assert context.claim("foo", "a")
        assert not context.claim("foo", "b")
        call_count = storage.get_check_calls("b")

        context.claim("foo", "b")
        # we have not waited long enough to query the db again
        assert storage.get_check_calls("b") == call_count

        assert INITIAL_INTERVAL_VALUE < CUSTOM_SLEEP_INTERVAL
        time.sleep(INITIAL_INTERVAL_VALUE)
        context.claim("foo", "b")
        # we have waited the default interval, but not the custom interval
        assert storage.get_check_calls("b") == call_count

        interval_to_custom = CUSTOM_SLEEP_INTERVAL - INITIAL_INTERVAL_VALUE
        time.sleep(interval_to_custom)
        context.claim("foo", "b")
        assert storage.get_check_calls("b") == call_count + 1


def test_unset_concurrency_default(concurrency_instance):
    run = concurrency_instance.create_run_for_job(define_foo_job(), run_id=make_new_run_id())

    assert concurrency_instance.event_log_storage.get_concurrency_keys() == set()

    with InstanceConcurrencyContext(concurrency_instance, run) as context:
        assert context.claim("foo", "a")
        assert context.claim("foo", "b")


def test_default_concurrency_key(concurrency_instance_with_default_one):
    run = concurrency_instance_with_default_one.create_run_for_job(
        define_foo_job(), run_id=make_new_run_id()
    )

    assert concurrency_instance_with_default_one.event_log_storage.get_concurrency_keys() == set()
    assert concurrency_instance_with_default_one.global_op_concurrency_default_limit == 1

    with InstanceConcurrencyContext(concurrency_instance_with_default_one, run) as context:
        assert context.claim("foo", "a")
        assert not context.claim("foo", "b")


def test_zero_concurrency_key(concurrency_instance):
    run = concurrency_instance.create_run_for_job(define_foo_job(), run_id=make_new_run_id())

    concurrency_instance.event_log_storage.set_concurrency_slots("foo", 0)
    assert concurrency_instance.event_log_storage.get_concurrency_keys() == set(["foo"])

    with InstanceConcurrencyContext(concurrency_instance, run) as context:
        assert not context.claim("foo", "a")
        assert not context.claim("foo", "b")


@mock.patch("dagster._core.execution.plan.instance_concurrency_context.INITIAL_INTERVAL_VALUE", 0.1)
@mock.patch("dagster._core.execution.plan.instance_concurrency_context.STEP_UP_BASE", 1)
def test_step_priority(concurrency_instance):
    run = concurrency_instance.create_run_for_job(define_foo_job(), run_id=make_new_run_id())
    concurrency_instance.event_log_storage.set_concurrency_slots("foo", 1)
    with InstanceConcurrencyContext(concurrency_instance, run) as context:
        assert context.claim("foo", "a")
        assert not context.claim("foo", "b")
        assert not context.claim("foo", "c", step_priority=1000)
        assert not context.claim("foo", "d", step_priority=-1)

        context.free_step("a")
        time.sleep(0.1)

        # highest priority step should be able to claim the slot
        assert not context.claim("foo", "b")
        assert context.claim("foo", "c")
        assert not context.claim("foo", "d")


@mock.patch("dagster._core.execution.plan.instance_concurrency_context.INITIAL_INTERVAL_VALUE", 0.1)
@mock.patch("dagster._core.execution.plan.instance_concurrency_context.STEP_UP_BASE", 1)
def test_run_priority(concurrency_instance):
    regular_priority_run = concurrency_instance.create_run_for_job(
        define_foo_job(), run_id=make_new_run_id()
    )
    high_priority_run = concurrency_instance.create_run_for_job(
        define_foo_job(), run_id=make_new_run_id(), tags={"dagster/priority": "1000"}
    )
    concurrency_instance.event_log_storage.set_concurrency_slots("foo", 1)

    with ExitStack() as stack:
        regular_context = stack.enter_context(
            InstanceConcurrencyContext(concurrency_instance, regular_priority_run)
        )
        high_context = stack.enter_context(
            InstanceConcurrencyContext(concurrency_instance, high_priority_run)
        )
        assert regular_context.claim("foo", "a")
        assert not regular_context.claim("foo", "b")
        assert not high_context.claim("foo", "c")

        # free the occupied slot
        regular_context.free_step("a")
        time.sleep(0.1)

        # high priority run should now be able to claim the slot
        assert not regular_context.claim("foo", "b")
        assert high_context.claim("foo", "c")


@mock.patch("dagster._core.execution.plan.instance_concurrency_context.INITIAL_INTERVAL_VALUE", 0.1)
@mock.patch("dagster._core.execution.plan.instance_concurrency_context.STEP_UP_BASE", 1)
def test_run_step_priority(concurrency_instance):
    low_priority_run = concurrency_instance.create_run_for_job(
        define_foo_job(), run_id=make_new_run_id(), tags={"dagster/priority": "-1000"}
    )
    regular_priority_run = concurrency_instance.create_run_for_job(
        define_foo_job(), run_id=make_new_run_id()
    )
    concurrency_instance.event_log_storage.set_concurrency_slots("foo", 0)

    with ExitStack() as stack:
        low_context = stack.enter_context(
            InstanceConcurrencyContext(concurrency_instance, low_priority_run)
        )
        regular_context = stack.enter_context(
            InstanceConcurrencyContext(concurrency_instance, regular_priority_run)
        )

        # at first all steps are blocked
        assert not low_context.claim("foo", "low_run_low_step", step_priority=-1)  # -1001
        assert not low_context.claim("foo", "low_run_high_step", step_priority=1000)  # 0
        assert not regular_context.claim("foo", "regular_run_low_step", step_priority=-1)  # -1
        assert not regular_context.claim("foo", "regular_run_high_step", step_priority=1000)  # 1000

        concurrency_instance.event_log_storage.set_concurrency_slots("foo", 1)
        time.sleep(0.1)

        assert not low_context.claim("foo", "low_run_low_step", step_priority=-1)  # -1001
        assert not low_context.claim("foo", "low_run_high_step", step_priority=1000)  # 0
        assert not regular_context.claim("foo", "regular_run_low_step", step_priority=-1)  # -1
        assert regular_context.claim("foo", "regular_run_high_step", step_priority=1000)  # 1000

        regular_context.free_step("regular_run_high_step")
        time.sleep(0.1)

        assert not low_context.claim("foo", "low_run_low_step", step_priority=-1)  # -1001
        assert low_context.claim("foo", "low_run_high_step", step_priority=1000)  # 0
        assert not regular_context.claim("foo", "regular_run_low_step", step_priority=-1)  # -1

        low_context.free_step("low_run_high_step")
        time.sleep(0.1)

        assert not low_context.claim("foo", "low_run_low_step", step_priority=-1)  # -1001
        assert regular_context.claim("foo", "regular_run_low_step", step_priority=-1)  # -1

        regular_context.free_step("regular_run_low_step")
        time.sleep(0.1)

        assert low_context.claim("foo", "low_run_low_step", step_priority=-1)  # -1001
