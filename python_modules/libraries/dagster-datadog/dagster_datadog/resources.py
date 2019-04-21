from datadog import api, initialize, statsd

from dagster import Dict, Field, ResourceDefinition, String


class DataDogResource:
    def __init__(self, api_key, app_key):
        self.api_key = api_key
        self.app_key = app_key
        initialize(api_key=api_key, app_key=app_key)

    def event(
        self,
        title,
        text,
        alert_type=None,
        aggregation_key=None,
        source_type_name=None,
        date_happened=None,
        priority=None,
        tags=None,
        hostname=None,
    ):
        statsd.event(
            title=title,
            text=text,
            alert_type=alert_type,
            aggregation_key=aggregation_key,
            source_type_name=source_type_name,
            date_happened=date_happened,
            priority=priority,
            tags=tags,
            hostname=hostname,
        )

    def increment(self, key, value=1, tags=None, sample_rate=1):
        statsd.increment(key, value, tags, sample_rate)

    def decrement(self, key, value=1, tags=None, sample_rate=1):
        statsd.decrement(key, value, tags, sample_rate)

    def gauge(self, key, value, tags=None, sample_rate=1):
        statsd.gauge(key, value, tags, sample_rate)

    def histogram(self, key, value, tags=None, sample_rate=1):
        statsd.histogram(key, value, tags, sample_rate)

    def set(self, metric, value, tags=None, sample_rate=1):
        statsd.set(metric, value, tags, sample_rate)


def define_datadog_resource():
    return ResourceDefinition(
        resource_fn=lambda init_context: DataDogResource(
            init_context.resource_config['api_key'], init_context.resource_config['app_key']
        ),
        config_field=Field(Dict({'api_key': Field(String), 'app_key': Field(String)})),
        description='''This resource is for publishing to DataDog''',
    )
