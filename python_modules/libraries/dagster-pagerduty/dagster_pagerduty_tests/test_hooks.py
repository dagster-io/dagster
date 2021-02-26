import responses
from dagster import ModeDefinition, execute_pipeline, pipeline, solid
from dagster_pagerduty import pagerduty_resource
from dagster_pagerduty.hooks import pagerduty_on_failure


class SomeUserException(Exception):
    pass


@responses.activate
def test_failure_hook_on_solid_instance():
    def my_summary_fn(_):
        return "A custom summary"

    @solid
    def pass_solid(_):
        pass

    @solid
    def fail_solid(_):
        raise SomeUserException()

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"pagerduty": pagerduty_resource})])
    def a_pipeline():
        pass_solid.with_hooks(hook_defs={pagerduty_on_failure("info")})()
        pass_solid.alias("solid_with_hook").with_hooks(hook_defs={pagerduty_on_failure("info")})()
        fail_solid.alias("fail_solid_without_hook")()
        fail_solid.with_hooks(
            hook_defs={pagerduty_on_failure(severity="info", summary_fn=my_summary_fn)}
        )()

    with responses.RequestsMock() as rsps:
        rsps.add(
            rsps.POST,
            "https://events.pagerduty.com/v2/enqueue/",
            status=202,
            json={"status": "success", "message": "Event processed"},
        )
        result = execute_pipeline(
            a_pipeline,
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
    @solid
    def pass_solid(_):
        pass

    @solid
    def fail_solid(_):
        raise SomeUserException()

    @pagerduty_on_failure(severity="info", dagit_base_url="localhost:3000")
    @pipeline(mode_defs=[ModeDefinition(resource_defs={"pagerduty": pagerduty_resource})])
    def a_pipeline():
        pass_solid()
        fail_solid()
        fail_solid.alias("another_fail_solid")()

    with responses.RequestsMock() as rsps:
        rsps.add(
            rsps.POST,
            "https://events.pagerduty.com/v2/enqueue/",
            status=202,
            json={"status": "success", "message": "Event processed"},
        )
        result = execute_pipeline(
            a_pipeline,
            run_config={
                "resources": {
                    "pagerduty": {"config": {"routing_key": "0123456789abcdef0123456789abcdef"}}
                }
            },
            raise_on_error=False,
        )
        assert not result.success
        assert len(rsps.calls) == 2
