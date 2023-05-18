import pytest
from dagster._core.execution.plan.global_concurrency_context import GlobalConcurrencyContext
from dagster._core.utils import make_new_run_id


def test_global_concurrency(concurrency_instance):
    run_id = make_new_run_id()
    concurrency_instance.event_log_storage.set_concurrency_slots("foo", 2)

    with GlobalConcurrencyContext(concurrency_instance, run_id) as context:
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
    run_id = make_new_run_id()
    assert concurrency_instance.event_log_storage.get_concurrency_info("foo").slot_count == 0

    with GlobalConcurrencyContext(concurrency_instance, run_id) as context:
        assert context.claim("foo", "a")
        assert context.claim("foo", "b")
        assert context.claim("foo", "d")
        assert context.claim("foo", "e")
        assert not context.has_pending_claims()

        foo_info = concurrency_instance.event_log_storage.get_concurrency_info("foo")
        assert foo_info.slot_count == 0
        assert foo_info.active_slot_count == 0


def test_context_error(concurrency_instance):
    run_id = make_new_run_id()
    concurrency_instance.event_log_storage.set_concurrency_slots("foo", 2)

    with pytest.raises(Exception, match="uh oh"):
        with GlobalConcurrencyContext(concurrency_instance, run_id) as context:
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
