from typing import Dict, Optional, cast

import pypd
from dagster import ConfigurableResource, resource
from dagster._config.pythonic_config import infer_schema_from_config_class
from dagster._core.definitions.resource_definition import dagster_maintained_resource
from dagster._utils.warnings import suppress_dagster_warnings
from pydantic import Field as PyField


class PagerDutyService(ConfigurableResource):
    """This resource is for posting events to PagerDuty."""

    """Integrates with PagerDuty via the pypd library.

    See:
        https://v2.developer.pagerduty.com/docs/events-api-v2
        https://v2.developer.pagerduty.com/docs/send-an-event-events-api-v2
        https://support.pagerduty.com/docs/services-and-integrations#section-events-api-v2
        https://github.com/PagerDuty/pagerduty-api-python-client

    for documentation and more information.
    """

    routing_key: str = PyField(
        ...,
        description=(
            "The routing key provisions access to your PagerDuty service. You"
            "will need to include the integration key for your new integration, as a"
            "routing_key in the event payload."
        ),
    )

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    def EventV2_create(
        self,
        summary: str,
        source: str,
        severity: str,
        event_action: str = "trigger",
        dedup_key: Optional[str] = None,
        timestamp: Optional[str] = None,
        component: Optional[str] = None,
        group: Optional[str] = None,
        event_class: Optional[str] = None,
        custom_details: Optional[object] = None,
    ) -> object:
        """Events API v2 enables you to add PagerDuty's advanced event and incident management
        functionality to any system that can make an outbound HTTP connection.

        Args:
            summary (str):
                A high-level, text summary message of the event. Will be used to construct an
                alert's description. Example:

                "PING OK - Packet loss = 0%, RTA = 1.41 ms" "Host
                'acme-andromeda-sv1-c40 :: 179.21.24.50' is DOWN"

            source (str):
                Specific human-readable unique identifier, such as a hostname, for the system having
                the problem. Examples:

               "prod05.theseus.acme-widgets.com"
               "171.26.23.22"
               "aws:elasticache:us-east-1:852511987:cluster/api-stats-prod-003"
               "9c09acd49a25"

            severity (str):
                How impacted the affected system is. Displayed to users in lists and influences the
                priority of any created incidents. Must be one of {info, warning, error, critical}

        Keyword Args:
            event_action (str):
                There are three types of events that PagerDuty recognizes, and are used to represent
                different types of activity in your monitored systems. (default: 'trigger')

                * trigger: When PagerDuty receives a trigger event, it will either open a new alert,
                           or add a new trigger log entry to an existing alert, depending on the
                           provided dedup_key. Your monitoring tools should send PagerDuty a trigger
                           when a new problem has been detected. You may send additional triggers
                           when a previously detected problem has occurred again.

                * acknowledge: acknowledge events cause the referenced incident to enter the
                               acknowledged state. While an incident is acknowledged, it won't
                               generate any additional notifications, even if it receives new
                               trigger events. Your monitoring tools should send PagerDuty an
                               acknowledge event when they know someone is presently working on the
                               problem.

                * resolve: resolve events cause the referenced incident to enter the resolved state.
                           Once an incident is resolved, it won't generate any additional
                           notifications. New trigger events with the same dedup_key as a resolved
                           incident won't re-open the incident. Instead, a new incident will be
                           created. Your monitoring tools should send PagerDuty a resolve event when
                           the problem that caused the initial trigger event has been fixed.

            dedup_key (str):
                Deduplication key for correlating triggers and resolves. The maximum permitted
                length of this property is 255 characters.

            timestamp (str):
                Timestamp (ISO 8601). When the upstream system detected / created the event. This is
                useful if a system batches or holds events before sending them to PagerDuty. This
                will be auto-generated by PagerDuty if not provided. Example:

                2015-07-17T08:42:58.315+0000

            component (str):
                The part or component of the affected system that is broken. Examples:

                "keepalive"
                "webping"
                "mysql"
                "wqueue"

            group (str):
                A cluster or grouping of sources. For example, sources "prod-datapipe-02" and
                "prod-datapipe-03" might both be part of "prod-datapipe". Examples:

                "prod-datapipe"
                "www"
                "web_stack"

            event_class (str):
                The class/type of the event. Examples:

                "High CPU"
                "Latency"
                "500 Error"

            custom_details (Dict[str, str]):
                Additional details about the event and affected system. Example:

                {"ping time": "1500ms", "load avg": 0.75 }
        """
        data = {
            "routing_key": self.routing_key,
            "event_action": event_action,
            "payload": {"summary": summary, "source": source, "severity": severity},
        }

        if dedup_key is not None:
            data["dedup_key"] = dedup_key

        payload: Dict[str, object] = cast(Dict[str, object], data["payload"])

        if timestamp is not None:
            payload["timestamp"] = timestamp

        if component is not None:
            payload["component"] = component

        if group is not None:
            payload["group"] = group

        if event_class is not None:
            payload["class"] = event_class

        if custom_details is not None:
            payload["custom_details"] = custom_details

        return pypd.EventV2.create(data=data)


@dagster_maintained_resource
@resource(
    config_schema=infer_schema_from_config_class(PagerDutyService),
    description="""This resource is for posting events to PagerDuty.""",
)
@suppress_dagster_warnings
def pagerduty_resource(context) -> PagerDutyService:
    """A resource for posting events (alerts) to PagerDuty.

    Example:
        .. code-block:: python

            @op
            def pagerduty_op(pagerduty: PagerDutyService):
                pagerduty.EventV2_create(
                    summary='alert from dagster'
                    source='localhost',
                    severity='error',
                    event_action='trigger',
                )

            @job(resource_defs={ 'pagerduty': pagerduty_resource })
            def pagerduty_test():
                pagerduty_op()

            pagerduty_test.execute_in_process(
                run_config={
                    "resources": {
                        'pagerduty': {'config': {'routing_key': '0123456789abcdef0123456789abcdef'}}
                    }
                }
            )
    """
    return PagerDutyService(**context.resource_config)
