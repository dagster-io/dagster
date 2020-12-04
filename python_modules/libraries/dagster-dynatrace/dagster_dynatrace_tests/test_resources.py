from dagster_dynatrace import dynatrace_resource
import responses

from dagster import ModeDefinition, execute_solid, solid

@responses.activate
def test_dynatrace_set_v2():
    @solid(required_resource_keys={'dynatrace'})
    def dynatrace_solid(context):
        responses.add(
            responses.POST,
            'http://not_used/api/v2/metrics/ingest',
            json={'linesOk': 1},
            status=200,
        )

        responses.add(
            responses.GET,
            'http://not_used/api/v2/metrics/ingest',
            json={'linesOk': 1},
            status=200,
        )

        assert context.resources.dynatrace

        # first call
        resp = context.resources.dynatrace.set_metrics(
            'visitors.unique',
            999,
            dimensions={'browser': 'chrome'},
        )

        # second call with timestamp
        context.resources.dynatrace.set_metrics(
            'visitors.unique',
            999,
            dimensions={'browser': 'chrome'},
            timestamp='1577836800000'
        )

        # third call with timestamp + dimensions
        context.resources.dynatrace.set_metrics(
            'visitors.unique',
            999,
            dimensions={'browser': 'chrome'},
            timestamp=1577836800000.32
        )

        # fourth call with multiple metrics
        multiple_resp = context.resources.dynatrace.set_multiple_metrics(
            [
                {
                    'metric_key': 'visitors.unique',
                    'value': 999,
                    'dimensions': {'browser': 'chrome'},
                },
                {
                    'metric_key': 'users',
                    'dimensions': {'shouldbeempty': ''},
                    'value': 99,
                },
                {
                    'metric_key': 'visitors.unique',
                    'value': '2',
                    'dimensions': {'browser': 'ie11', 'shouldbeempty': ''},
                },
                {
                    'metric_key': 'visitors.unique',
                    'value': '2',
                    'dimensions': {'shouldbeempty': ''},
                    'timestamp': 1577836800000,
                },
                {
                    'metric_key': 'visitors.unique',
                    'value': '20',
                    'dimensions': {'browser': 'ie10'},
                    'timestamp': 1577836800000,
                },
            ],
        )

        assert responses.calls[0].request.body == 'visitors.unique,browser=chrome 999'
        assert responses.calls[1].request.body == 'visitors.unique,browser=chrome 999 1577836800000'
        assert responses.calls[2].request.body == 'visitors.unique,browser=chrome 999 1577836800000'
        assert responses.calls[3].request.body == 'visitors.unique,browser=chrome 999\nvisitors.unique,browser=ie11 2\nvisitors.unique,browser=ie10 20 1577836800000'
        assert resp['linesOk'] == 1
        assert multiple_resp['linesOk'] == 1

    result = execute_solid(
        dynatrace_solid,
        run_config={
            'resources': {'dynatrace': {'config': {'api_token': 'NOT_USED', 'host_name': 'http://not_used'}}}
        },
        mode_def=ModeDefinition(resource_defs={'dynatrace': dynatrace_resource}),
    )
    assert result.success
