import responses

from dagster import execute_pipeline, pipeline, solid, ModeDefinition

from dagster_pagerduty import pagerduty_resource


@responses.activate
def test_pagerduty_resource():
    @solid
    def pagerduty_solid(context):
        assert context.resources.pagerduty
        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.POST,
                'https://events.pagerduty.com/v2/enqueue/',
                status=202,
                json={"status": "success", "message": "Event processed", "dedup_key": "foobar"},
            )
            context.resources.pagerduty.EventV2_create(
                summary='PING OK - Packet loss = 0%, RTA = 1.41 ms Host \'acme-andromeda-sv1-c40'
                ':: 179.21.24.50\' is DOWN',
                source="prod05.theseus.acme-widgets.com",
                severity='error',
                event_action='trigger',
                dedup_key='foobar',
                timestamp='2015-07-17T08:42:58.315+0000',
                component='mysql',
                group='prod-datapipe',
                event_class='High CPU',
                custom_details={'ping time': '1500ms', 'load avg': 0.75},
            )

    @pipeline(mode_defs=[ModeDefinition(resource_defs={'pagerduty': pagerduty_resource})])
    def pagerduty_resource_pipeline():
        pagerduty_solid()  # pylint: disable=no-value-for-parameter

    result = execute_pipeline(
        pagerduty_resource_pipeline,
        {
            'resources': {
                'pagerduty': {'config': {'routing_key': '0123456789abcdef0123456789abcdef'}}
            }
        },
    )
    assert result.success
