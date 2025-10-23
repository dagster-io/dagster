import time

import pytest
from dagster._core.scheduler import DagsterDaemonScheduler
from dagster._daemon.daemon import SensorDaemon
from dagster._daemon.types import DaemonHeartbeat
from dagster._utils.error import SerializableErrorInfo
from dagster_graphql.test.utils import execute_dagster_graphql

from dagster_graphql_tests.graphql.graphql_context_test_suite import (
    ExecutingGraphQLContextTestMatrix,
)

INDIVIDUAL_DAEMON_QUERY = """
query InstanceDetailSummaryQuery {
    instance {
        daemonHealth {
            id
            sensor: daemonStatus(daemonType: "SENSOR") {
                daemonType
                required
                healthy
                lastHeartbeatTime
            }
            run_coordinator: daemonStatus(daemonType: "QUEUED_RUN_COORDINATOR") {
                daemonType
                required
                healthy
                lastHeartbeatTime
            }
            scheduler: daemonStatus(daemonType: "SCHEDULER") {
                daemonType
                required
                healthy
                lastHeartbeatTime
            }
        }
    }
}
"""

ALL_DAEMON_QUERY = """
query InstanceDetailSummaryQuery {
    instance {
        daemonHealth {
            id
            allDaemonStatuses {
                daemonType
                required
                healthy
                lastHeartbeatTime
            }
        }
    }
}
"""

DAEMON_HEALTH_QUERY = """
query InstanceDetailSummaryQuery {
    instance {
        daemonHealth {
            id
            sensor: daemonStatus(daemonType: "SENSOR"){
                lastHeartbeatErrors {
                    message
                }
                healthy
            }
        }
    }
}
"""


class TestDaemonHealth(ExecutingGraphQLContextTestMatrix):
    def test_get_individual_daemons(self, graphql_context):
        if graphql_context.instance.is_ephemeral:
            pytest.skip("The daemon isn't compatible with an in-memory instance")
        graphql_context.instance.add_daemon_heartbeat(
            DaemonHeartbeat(
                timestamp=100.0, daemon_type=SensorDaemon.daemon_type(), daemon_id=None, errors=None
            )
        )
        results = execute_dagster_graphql(graphql_context, INDIVIDUAL_DAEMON_QUERY)

        scheduler_required = isinstance(graphql_context.instance.scheduler, DagsterDaemonScheduler)
        assert results.data == {
            "instance": {
                "daemonHealth": {
                    "id": "daemonHealth",
                    "sensor": {
                        "daemonType": "SENSOR",
                        "required": True,
                        "healthy": False,
                        "lastHeartbeatTime": 100.0,
                    },
                    "run_coordinator": {
                        "daemonType": "QUEUED_RUN_COORDINATOR",
                        "required": False,
                        "healthy": None,
                        "lastHeartbeatTime": None,
                    },
                    "scheduler": {
                        "daemonType": "SCHEDULER",
                        "required": scheduler_required,
                        "healthy": False if scheduler_required else None,
                        "lastHeartbeatTime": None,
                    },
                }
            }
        }

    def test_get_all_daemons(self, graphql_context):
        if graphql_context.instance.is_ephemeral:
            pytest.skip("The daemon isn't compatible with an in-memory instance")
        results = execute_dagster_graphql(graphql_context, ALL_DAEMON_QUERY)
        scheduler_required = isinstance(graphql_context.instance.scheduler, DagsterDaemonScheduler)

        assert results.data == {
            "instance": {
                "daemonHealth": {
                    "id": "daemonHealth",
                    "allDaemonStatuses": [
                        {
                            "daemonType": "SENSOR",
                            "required": True,
                            "healthy": False,
                            "lastHeartbeatTime": None,
                        },
                        {
                            "daemonType": "BACKFILL",
                            "required": True,
                            "healthy": False,
                            "lastHeartbeatTime": None,
                        },
                        {
                            "daemonType": "ASSET",
                            "required": True,
                            "healthy": False,
                            "lastHeartbeatTime": None,
                        },
                        {
                            "daemonType": "FRESHNESS_DAEMON",
                            "required": True,
                            "healthy": False,
                            "lastHeartbeatTime": None,
                        },
                    ]
                    + (
                        [
                            {
                                "daemonType": "SCHEDULER",
                                "required": True,
                                "healthy": False if scheduler_required else None,
                                "lastHeartbeatTime": None,
                            }
                        ]
                        if scheduler_required
                        else []
                    ),
                }
            }
        }

    def test_get_daemon_error(self, graphql_context):
        if graphql_context.instance.is_ephemeral:
            pytest.skip("The daemon isn't compatible with an in-memory instance")
        graphql_context.instance.add_daemon_heartbeat(
            DaemonHeartbeat(
                timestamp=time.time(),
                daemon_type=SensorDaemon.daemon_type(),
                daemon_id=None,
                errors=[
                    SerializableErrorInfo(message="foobar", stack=[], cls_name=None, cause=None)
                ],
            )
        )
        results = execute_dagster_graphql(graphql_context, DAEMON_HEALTH_QUERY)
        assert results.data["instance"]["daemonHealth"]["sensor"] == {
            "lastHeartbeatErrors": [{"message": "foobar"}],
            "healthy": True,
        }
