import pytest
from dagster._core.execution.plan.global_concurrency_context import GlobalConcurrencyContext
from dagster._core.test_utils import instance_for_test
from dagster._core.utils import make_new_run_id


def test_global_concurrency():
    run_id = make_new_run_id()
    with instance_for_test() as instance:
        instance.event_log_storage.set_concurrency_slots("foo", 2)

        with GlobalConcurrencyContext(instance, run_id) as context:
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

        foo_info = instance.event_log_storage.get_concurrency_info("foo")
        assert foo_info.active_slot_count == 1
        assert foo_info.pending_step_count == 0


def test_limitless_context():
    run_id = make_new_run_id()
    with instance_for_test() as instance:
        with GlobalConcurrencyContext(instance, run_id) as context:
            assert context.claim("foo", "a")
            assert context.claim("foo", "b")
            assert context.claim("foo", "d")
            assert context.claim("foo", "e")
            assert not context.has_pending_claims()

            foo_info = instance.event_log_storage.get_concurrency_info("foo")
            assert foo_info.slot_count == 0
            assert foo_info.active_slot_count == 0


def test_context_error():
    run_id = make_new_run_id()
    with instance_for_test() as instance:
        instance.event_log_storage.set_concurrency_slots("foo", 2)

        with pytest.raises(Exception, match="uh oh"):
            with GlobalConcurrencyContext(instance, run_id) as context:
                assert context.claim("foo", "a")
                assert not context.has_pending_claims()
                assert context.claim("foo", "b")
                assert not context.has_pending_claims()
                assert not context.claim("foo", "c")
                assert context.has_pending_claims()
                assert context.pending_claim_steps() == ["c"]

                context.free_step("a")
                raise Exception("uh oh")

        foo_info = instance.event_log_storage.get_concurrency_info("foo")
        assert foo_info.active_slot_count == 1
        assert foo_info.pending_step_count == 0
