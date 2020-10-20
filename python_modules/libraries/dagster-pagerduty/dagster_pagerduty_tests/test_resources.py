import responses
from dagster import ModeDefinition, execute_solid, solid
from dagster_pagerduty import pagerduty_resource


@responses.activate
def test_pagerduty_resource():
    @solid(required_resource_keys={"pagerduty"})
    def pagerduty_solid(context):
        assert context.resources.pagerduty
        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.POST,
                "https://events.pagerduty.com/v2/enqueue/",
                status=202,
                json={"status": "success", "message": "Event processed", "dedup_key": "foobar"},
            )
            context.resources.pagerduty.EventV2_create(
                summary="PING OK - Packet loss = 0%, RTA = 1.41 ms Host 'acme-andromeda-sv1-c40"
                ":: 179.21.24.50' is DOWN",
                source="prod05.theseus.acme-widgets.com",
                severity="error",
                event_action="trigger",
                dedup_key="foobar",
                timestamp="2015-07-17T08:42:58.315+0000",
                component="mysql",
                group="prod-datapipe",
                event_class="High CPU",
                custom_details={"ping time": "1500ms", "load avg": 0.75},
            )

    result = execute_solid(
        pagerduty_solid,
        run_config={
            "resources": {
                "pagerduty": {"config": {"routing_key": "0123456789abcdef0123456789abcdef"}}
            }
        },
        mode_def=ModeDefinition(resource_defs={"pagerduty": pagerduty_resource}),
    )
    assert result.success
