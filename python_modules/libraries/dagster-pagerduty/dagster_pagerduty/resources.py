import pypd

from dagster import Dict, Field, ResourceDefinition, String


class PagerDutyService:
    def __init__(self, token):
        self.token = token

    def create_incident(self, summary):
        pypd.EventV2.create(
            data={
                'routing_key': self.token,
                'event_action': 'trigger',
                'payload': {'summary': summary, 'severity': 'error', 'source': 'Dagster'},
            }
        )


def define_pagerduty_resource():
    return ResourceDefinition(
        resource_fn=lambda init_context: PagerDutyService(init_context.resource_config['token']),
        config_field=Field(Dict({'token': Field(String)})),
        description='''This resource is for posting PagerDuty alerts''',
    )
