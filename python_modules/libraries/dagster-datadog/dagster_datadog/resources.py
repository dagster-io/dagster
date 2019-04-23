from datadog import initialize, statsd, DogStatsd

from dagster import resource, Dict, Field, String


class DataDogResource:
    # Mirroring levels from the dogstatsd library
    OK, WARNING, CRITICAL, UNKNOWN = (
        DogStatsd.OK,
        DogStatsd.WARNING,
        DogStatsd.CRITICAL,
        DogStatsd.UNKNOWN,
    )

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
        '''
        Send an event. Attributes are the same as the Event API.
            http://docs.datadoghq.com/api/

        datadog_resource.event('Man down!', 'This server needs assistance.')
        datadog_resource.event(
            'The web server restarted',
            'The web server is up again',
            alert_type='success'
        )
        '''
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

    def gauge(self, key, value, tags=None, sample_rate=1):
        '''
        Record the value of a gauge, optionally setting a list of tags and a sample rate.

        datadog_resource.gauge('users.online', 123)
        datadog_resource.gauge('active.connections', 1001, tags=["protocol:http"])
        '''
        return statsd.gauge(key, value, tags, sample_rate)

    def increment(self, key, value=1, tags=None, sample_rate=1):
        '''
        Increment a counter, optionally setting a value, tags and a sample rate.

        datadog_resource.increment('page.views')
        datadog_resource.increment('files.transferred', 124)
        '''
        return statsd.increment(key, value, tags, sample_rate)

    def decrement(self, key, value=1, tags=None, sample_rate=1):
        '''
        Decrement a counter, optionally setting a value, tags and a sample rate.

        datadog_resource.decrement('files.remaining')
        datadog_resource.decrement('active.connections', 2)
        '''
        return statsd.decrement(key, value, tags, sample_rate)

    def histogram(self, key, value, tags=None, sample_rate=1):
        '''
        Sample a histogram value, optionally setting tags and a sample rate.

        datadog_resource.histogram('uploaded.file.size', 1445)
        datadog_resource.histogram('album.photo.count', 26, tags=["gender:female"])
        '''
        return statsd.histogram(key, value, tags, sample_rate)

    def distribution(self, metric, value, tags=None, sample_rate=1):
        """
        Send a global distribution value, optionally setting tags and a sample rate.

        datadog_resource.distribution('uploaded.file.size', 1445)
        datadog_resource.distribution('album.photo.count', 26, tags=["gender:female"])
        This is a beta feature that must be enabled specifically for your organization.
        """
        return statsd.distribution(metric, value, tags, sample_rate)

    def set(self, metric, value, tags=None, sample_rate=1):
        '''
        Sample a set value.

        datadog_resource.set('visitors.uniques', 999)
        '''
        return statsd.set(metric, value, tags, sample_rate)

    def service_check(
        self, check_name, status, tags=None, timestamp=None, hostname=None, message=None
    ):
        '''
        Send a service check run.

        datadog_resource.service_check('my_service.check_name', DataDogResource.WARNING)
        '''
        return statsd.service_check(check_name, status, tags, timestamp, hostname, message)

    def timed(self, metric=None, tags=None, sample_rate=1, use_ms=None):
        '''
        A decorator or context manager that will measure the distribution of a
        function's/context's run time. Optionally specify a list of tags or a
        sample rate. If the metric is not defined as a decorator, the module
        name and function name will be used. The metric is required as a context
        manager.
        ::

            @datadog_resource.timed('user.query.time', sample_rate=0.5)
            def get_user(user_id):
                # Do what you need to ...
                pass
            # Is equivalent to ...
            with datadog_resource.timed('user.query.time', sample_rate=0.5):
                # Do what you need to ...
                pass
            # Is equivalent to ...
            start = time.time()
            try:
                get_user(user_id)
            finally:
                datadog_resource.timing('user.query.time', time.time() - start)
        '''
        return statsd.timed(metric, tags, sample_rate, use_ms)

    def timing(self, metric, value, tags=None, sample_rate=1):
        '''
        Record a timing, optionally setting tags and a sample rate.

        datadog_resource.timing("query.response.time", 1234)
        '''
        return statsd.timing(metric, value, tags, sample_rate)


@resource(
    config_field=Field(Dict({'api_key': Field(String), 'app_key': Field(String)})),
    description='This resource is for publishing to DataDog',
)
def datadog_resource(context):
    return DataDogResource(
        context.resource_config.get('api_key'), context.resource_config.get('app_key')
    )
