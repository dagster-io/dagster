import responses
from dagster import graph, op
from dagster_pagerduty import pagerduty_resource
from dagster_pagerduty.hooks import pagerduty_on_failure


class SomeUserException(Exception):
    pass


@responses.activate
def test_failure_hook_on_op_instance():
    def my_summary_fn(_):
        return "A custom summary"

    @op
    def pass_op(_):
        pass

    @op
    def fail_op(_):
        raise SomeUserException()

    @graph
    def a_graph():
        pass_op.with_hooks(hook_defs={pagerduty_on_failure("info")})()
        pass_op.alias("op_with_hook").with_hooks(hook_defs={pagerduty_on_failure("info")})()
        fail_op.alias("fail_op_without_hook")()
        fail_op.with_hooks(
            hook_defs={pagerduty_on_failure(severity="info", summary_fn=my_summary_fn)}
        )()

    with responses.RequestsMock() as rsps:
        rsps.add(
            rsps.POST,
            "https://events.pagerduty.com/v2/enqueue/",
            status=202,
            json={"status": "success", "message": "Event processed"},
        )
        result = a_graph.to_job(resource_defs={"pagerduty": pagerduty_resource}).execute_in_process(
            run_config={
                "resources": {
                    "pagerduty": {"config": {"routing_key": "0123456789abcdef0123456789abcdef"}}
                }
            },
            raise_on_error=False,
        )
        assert not result.success
        assert len(rsps.calls) == 1


@responses.activate
def test_failure_hook_decorator():
    @op
    def pass_op(_):
        pass

    @op
    def fail_op(_):
        raise SomeUserException()

    @graph
    def a_graph():
        pass_op()
        fail_op()
        fail_op.alias("another_fail_op")()

    with responses.RequestsMock() as rsps:
        rsps.add(
            rsps.POST,
            "https://events.pagerduty.com/v2/enqueue/",
            status=202,
            json={"status": "success", "message": "Event processed"},
        )
        result = a_graph.to_job(
            hooks={pagerduty_on_failure(severity="info", dagit_base_url="localhost:3000")},
            resource_defs={"pagerduty": pagerduty_resource},
        ).execute_in_process(
            run_config={
                "resources": {
                    "pagerduty": {"config": {"routing_key": "0123456789abcdef0123456789abcdef"}}
                }
            },
            raise_on_error=False,
        )
        assert not result.success
        assert len(rsps.calls) == 2
