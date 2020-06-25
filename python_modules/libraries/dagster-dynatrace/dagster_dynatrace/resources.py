from dagster import Field, StringSource, resource
from .client import DTClient

class DynatraceResource:
    def __init__(self, api_token=None, host_name=None):
        self.client = DTClient(api_token, host_name)

    @staticmethod
    def serialize_metrics(metric_key, value, dimensions, timestamp=None, ignore_empty_dimensions=True):
        '''Prepare metrics to send it to the Dynatrace API v2

        Args:
            metric_key (str): The metric category for Dynatrace
            value: The value which gets stored
            dimensions (dict): A dict of dimensions
            timestamp (int): The timestamp for this metric
        '''
        sorted_dimensions = {k: v for k, v in dimensions.items() if v is not None and len(v) != 0}

        if len(sorted_dimensions.items()) == 0 and not ignore_empty_dimensions:
            print(f'Warning: metric key "{metric_key}" does not have any dimensions and got ignored')

            return ""

        serialized_attrs = ','.join(f'{k}={v}' for k, v in sorted_dimensions.items() if v)
        timestamp_string = f" {int(timestamp)}" if timestamp is not None else ""

        return f'{metric_key},{serialized_attrs} {value}{timestamp_string}'


    def set_metrics_v1(self, metric_key, values, dimensions):
        pushed_data = self.client.push_metric_v1(metric_key, dimensions, values)

        return pushed_data


    def set_multiple_metrics(self, metrics):
        data = []

        for metric in metrics:
            serialized_call = DynatraceResource.serialize_metrics(
                metric['metric_key'],
                metric['value'],
                metric['dimensions'],
                metric.get('timestamp', None),
                ignore_empty_dimensions=False
            )

            if serialized_call:
                data.append(serialized_call)

        pushed_data = self.client.push('\n'.join(data), endpoint='metrics/ingest')

        return pushed_data


    def set_metrics(self, metric_key, value, dimensions, timestamp=None):
        '''Send metrics to the Dynatrace API v2

        Args:
            metric_key (str): The metric category for Dynatrace
            value: The value which gets stored
            dimensions (dict): A dict of dimensions
            timestamp (int): The timestamp for this metric
        '''
        pushed_data = self.client.push(
            DynatraceResource.serialize_metrics(metric_key, value, dimensions, timestamp),
            endpoint='metrics/ingest'
        )

        return pushed_data


    def get_metrics(self, entities):
        '''Get metrics from the Dynatrace API v2

        Args:
            entities (list of str): The metric category for Dynatrace
        '''
        pulled_data = self.client.pull(entities, endpoint='metrics/query')

        return pulled_data


@resource(
    {
        'api_token': Field(StringSource, description='Dynatrace API token/key'),
        'host_name': Field(StringSource, description='Dynatrace host name')
    },
    description='This resource is a wrapper over the Dynatrace API v1 and v2',
)
def dynatrace_resource(context):
    '''This resource is a wrapper over the Dynatrace API v1 and v2

    Make sure your API token has following permissions:
        - "Access problem and event feed, metrics, and topology"
        - "Data ingest, e.g.: metrics and events"
        - "Read entities using API V2"
        - "Write entities using API V2

    Config Options:
        `api_token`: The [generated API token](https://www.dynatrace.com/support/help/dynatrace-api/basics/dynatrace-api-authentication/)
        `host_name`: Your Dynatrace instance, e.g. 'https://mySampleEnv.live.dynatrace.com'

    Examples:

        .. code-block:: python

            @solid(required_resource_keys={'dynatrace'})
            def dynatrace_solid(context):
                dt = context.resources.dynatrace

                dt.set_metrics('unique.users', 3, dimensions={'browser': 'ie11'}, timestamp=1577836800000)
                dt.set_multiple_metrics(
                    [
                        {
                            'metric_key': 'unique.users',
                            'value': 999,
                            'dimensions': {'browser': 'chrome'},
                            'timestamp': 1577836800000
                        },
                        {
                            'metric_key': 'users',
                            'value': 10,
                            'dimensions': {'browser': 'ie11'},
                        },
                    ],
                )

                dt.get_metrics('unique.users')


            @pipeline(mode_defs=[ModeDefinition(resource_defs={'dynatrace': dynatrace_resource})])
            def dt_pipeline():
                dynatrace_solid()


            result = execute_pipeline(
                dt_pipeline,
                {'resources': {'dynatrace': {'config': {'api_token': 'API_TOKEN', 'host_name': 'HOST_NAME'}}}},
            )

    '''
    return DynatraceResource(context.resource_config.get('api_token'), context.resource_config.get('host_name'))
