from dagster import execute_pipeline, solid, PipelineContextDefinition, PipelineDefinition
from dagster_datadog import datadog_resource

try:
    import unittest.mock as mock
except ImportError:
    import mock


# To support this test, we need to do the following:
# 1. Have CircleCI publish Scala/Spark jars when that code changes
# 2. Ensure we have Spark available to CircleCI
# 3. Include example / test data in this repository
@mock.patch('datadog.statsd.timing')
@mock.patch('datadog.statsd.timed')
@mock.patch('datadog.statsd.service_check')
@mock.patch('datadog.statsd.set')
@mock.patch('datadog.statsd.distribution')
@mock.patch('datadog.statsd.histogram')
@mock.patch('datadog.statsd.decrement')
@mock.patch('datadog.statsd.increment')
@mock.patch('datadog.statsd.gauge')
def test_datadog_resource(
    gauge, increment, decrement, histogram, distribution, statsd_set, service_check, timed, timing
):
    called = {}

    @solid
    def datadog_solid(context):
        called['solid'] = True
        assert context.resources.datadog

        # gauge
        context.resources.datadog.gauge('users.online', 1001, tags=["protocol:http"])
        gauge.assert_called_with('users.online', 1001, ["protocol:http"], 1)

        # increment
        context.resources.datadog.increment('page.views')
        increment.assert_called_with('page.views', 1, None, 1)

        # decrement
        context.resources.datadog.decrement('page.views')
        decrement.assert_called_with('page.views', 1, None, 1)

        context.resources.datadog.histogram('album.photo.count', 26, tags=["gender:female"])
        histogram.assert_called_with('album.photo.count', 26, ["gender:female"], 1)

        context.resources.datadog.distribution('album.photo.count', 26, tags=["gender:female"])
        distribution.assert_called_with('album.photo.count', 26, ["gender:female"], 1)

        context.resources.datadog.set('visitors.uniques', 999, tags=["browser:ie"])
        statsd_set.assert_called_with('visitors.uniques', 999, ["browser:ie"], 1)

        context.resources.datadog.service_check(
            'my_service.check_name', context.resources.datadog.WARNING
        )
        service_check.assert_called_with(
            'my_service.check_name', context.resources.datadog.WARNING, None, None, None, None
        )

        context.resources.datadog.timing("query.response.time", 1234)
        timing.assert_called_with("query.response.time", 1234, None, 1)

        @context.resources.datadog.timed
        def run_fn():
            pass

        run_fn()
        timed.assert_called()

    pipeline = PipelineDefinition(
        name='test_datadog_resource',
        solids=[datadog_solid],
        context_definitions={
            'default': PipelineContextDefinition(resources={'datadog': datadog_resource})
        },
    )

    execute_pipeline(
        pipeline,
        {
            'context': {
                'default': {
                    'resources': {
                        'datadog': {'config': {'api_key': 'NOT_USED', 'app_key': 'NOT_USED'}}
                    }
                }
            }
        },
    )
