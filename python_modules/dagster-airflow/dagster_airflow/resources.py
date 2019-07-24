import datetime

from dagster import Dict, Field, resource, String


AirflowMacroData = Dict(
    {
        'utcnow': Field(
            String,
            is_optional=True,
            description=(
                'Optionally specify \'now\' as a string timestamp in the format prescribed by '
                'RFC 3339, e.g. "2019-03-29T01:18:17+00:00"'
            ),
        )
    }
)


# pylint: disable=unused-argument
@resource
def airflow_time_macro_resource(config_field=Field(AirflowMacroData)):
    pass


def time_resource(init_context):
    class TimeResource(object):
        def __init__(self, utcnow):
            self._utcnow = utcnow

        @property
        def utcnow(self):
            return self._utcnow

    utcnow = init_context.resource_config.get('utcnow')
    if utcnow is not None:
        try:
            utcnow = datetime.datetime.strptime(utcnow, '%Y-%m-%dT%H:%M:%S+00:00')
        except ValueError:
            utcnow = None
    if utcnow is None:
        utcnow = datetime.datetime.utcnow()

    return TimeResource(utcnow)
