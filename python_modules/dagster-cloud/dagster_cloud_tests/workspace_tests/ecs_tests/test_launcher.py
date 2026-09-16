# ruff: noqa: SLF001
"""EcsUserCodeLauncher behaviour around cross-account service discovery: the reconcile thread's
lifecycle and the per-pass fan-out over the agent's services. Cloud Map / ECS calls themselves
are covered in test_service_discovery.py.
"""

import threading
from contextlib import contextmanager
from unittest import mock

import pytest
from dagster._core.test_utils import instance_for_test
from dagster._utils.merger import merge_dicts
from dagster_cloud.workspace.ecs import EcsUserCodeLauncher
from dagster_cloud.workspace.ecs.client import Client
from dagster_cloud.workspace.ecs.launcher import (
    DEFAULT_SERVICE_DISCOVERY_RECONCILE_INTERVAL_SECONDS,
)

CROSS_ACCOUNT_ROLE_ARN = "arn:aws:iam::123456789012:role/cross-account-sd"
ROLE_CONFIG = {"service_discovery_role_arn": CROSS_ACCOUNT_ROLE_ARN}
# moto answers every call as 123456789012. The instance-based tests use a namespace id that does
# not exist in moto, so its owning account is faked; the agent's account is faked to differ.
MOTO_ACCOUNT_ID = "123456789012"
OTHER_ACCOUNT_ID = "999999999999"
THREAD_NAME = "service-discovery-reconcile"


@pytest.fixture
def namespace_in_moto_account():
    with mock.patch.object(
        Client, "_service_discovery_namespace_account_id", return_value=MOTO_ACCOUNT_ID
    ):
        yield


@pytest.fixture
def agent_in_other_account(namespace_in_moto_account):
    """Namespace owned by moto's account, agent identity in another: cross-account mode."""
    with mock.patch.object(Client, "_agent_account_id", return_value=OTHER_ACCOUNT_ID):
        yield


@pytest.fixture(autouse=True)
def _no_control_plane(aws_mock):
    # start() and __exit__ both call _graceful_cleanup_servers, which asks the Dagster+ API for
    # active agents, and start() begins run-worker monitoring against it too. Neither exists here.
    with (
        mock.patch.object(EcsUserCodeLauncher, "_graceful_cleanup_servers"),
        mock.patch.object(EcsUserCodeLauncher, "_start_run_worker_monitoring"),
    ):
        yield


@contextmanager
def ecs_agent_instance(launcher_config_overrides=None):
    with instance_for_test(
        {
            "instance_class": {"module": "dagster_cloud", "class": "DagsterCloudAgentInstance"},
            "user_code_launcher": {
                "module": "dagster_cloud.workspace.ecs",
                "class": "EcsUserCodeLauncher",
                "config": merge_dicts(
                    {
                        "cluster": "fake-cluster",
                        "subnets": ["fake-subnet-1"],
                        "service_discovery_namespace_id": "fake-namespace",
                        "execution_role_arn": "fake-role",
                        "log_group": "fake-log-group",
                    },
                    launcher_config_overrides or {},
                ),
            },
            "dagster_cloud_api": {
                "url": "http://localhost:2874",
                "agent_token": "FAKE_TOKEN",
                "deployment": "sandbox",
            },
            "compute_logs": {
                "module": "dagster._core.storage.noop_compute_log_manager",
                "class": "NoOpComputeLogManager",
            },
        }
    ) as instance:
        yield instance


def _reconcile_threads():
    return [t for t in threading.enumerate() if t.name == THREAD_NAME]


def _start(instance) -> EcsUserCodeLauncher:
    """start() the launcher the way the agent CLI does; the base class's own threads are not
    what is under test here.
    """
    launcher = instance.user_code_launcher
    assert isinstance(launcher, EcsUserCodeLauncher)
    launcher.start(run_reconcile_thread=False, run_metrics_thread=False)
    return launcher


@pytest.mark.parametrize(
    ("config", "expected_seconds"),
    [
        pytest.param({}, DEFAULT_SERVICE_DISCOVERY_RECONCILE_INTERVAL_SECONDS, id="default"),
        pytest.param({"service_discovery_reconcile_interval": 45}, 45, id="configured"),
    ],
)
def test_reconcile_interval_config(config, expected_seconds):
    with ecs_agent_instance(config) as instance:
        launcher = instance.user_code_launcher
        assert launcher.service_discovery_reconcile_interval_seconds == expected_seconds


def test_cross_account_starts_and_stops_reconcile_thread(agent_in_other_account):
    assert not _reconcile_threads()
    with ecs_agent_instance(ROLE_CONFIG) as instance:
        launcher = _start(instance)
        threads = _reconcile_threads()
        assert len(threads) == 1
        assert threads[0].daemon
        assert launcher._service_discovery_reconcile_thread is threads[0]
    # Leaving the instance context disposes it, which closes its ExitStack, which calls
    # EcsUserCodeLauncher.__exit__: shutdown event set, thread joined.
    assert not _reconcile_threads()
    assert launcher._service_discovery_reconcile_shutdown_event.is_set()


@pytest.mark.parametrize(
    "config",
    [
        pytest.param({}, id="no role"),
        pytest.param({"service_discovery_role_arn": CROSS_ACCOUNT_ROLE_ARN}, id="role only"),
    ],
)
def test_same_account_has_no_reconcile_thread(config, namespace_in_moto_account):
    """A same-account setup, including one that uses the role ARN only to split Cloud Map
    permissions, must not get the polling thread.
    """
    with ecs_agent_instance(config) as instance:
        launcher = _start(instance)
        assert not _reconcile_threads()
        assert launcher._service_discovery_reconcile_thread is None


def test_reconcile_thread_keeps_ticking_after_errors(agent_in_other_account):
    ticked_three_times = threading.Event()
    calls = []

    def _failing_pass():
        calls.append(1)
        if len(calls) >= 3:
            ticked_three_times.set()
        raise RuntimeError("simulated AWS failure")

    with ecs_agent_instance(ROLE_CONFIG) as instance:
        launcher = instance.user_code_launcher
        launcher.service_discovery_reconcile_interval_seconds = 0.05  # ty: ignore[invalid-assignment]
        with mock.patch.object(launcher, "_reconcile_service_discovery", side_effect=_failing_pass):
            _start(instance)
            assert ticked_three_times.wait(5), "thread stopped ticking after an exception"
            assert _reconcile_threads()[0].is_alive()
    assert not _reconcile_threads()


def test_reconcile_pass_covers_every_service_owned_by_this_agent(agent_in_other_account):
    """One pass lists all of this agent's services (gRPC and multipex alike) by tag and
    reconciles each independently, so one failure does not skip the rest.
    """
    handle_a, handle_b = mock.Mock(name="a"), mock.Mock(name="b")
    handle_a.name, handle_b.name = "service-a", "service-b"

    with ecs_agent_instance(ROLE_CONFIG) as instance:
        launcher = instance.user_code_launcher
        with (
            mock.patch.object(
                launcher.client, "list_services", return_value=[handle_a, handle_b]
            ) as list_services,
            mock.patch.object(
                launcher.client,
                "reconcile_service_discovery_instances",
                side_effect=[RuntimeError("boom"), None],
            ) as reconcile,
        ):
            launcher._reconcile_service_discovery()

        assert list_services.call_args.kwargs["tags"] == {
            "dagster/agent_id": instance.instance_uuid
        }
        assert [call.args[0] for call in reconcile.call_args_list] == [handle_a, handle_b]


def test_reconcile_pass_registers_multipex_and_grpc_servers_in_cloud_map(monkeypatch):
    """End to end against moto: the launcher creates a multipex server and a standalone gRPC
    server the way _start_new_server_spinup does (same tags, cross-account mode, so no
    serviceRegistries), then one reconcile pass registers each service's running task in the
    real (moto) Cloud Map namespace. Only ECS's task listing is faked, because moto never starts
    tasks for a service.
    """
    # The namespace below is real (moto's account); only the agent's identity is faked.
    monkeypatch.setattr(
        "dagster_cloud.workspace.ecs.client.Client._agent_account_id",
        lambda self: OTHER_ACCOUNT_ID,
    )
    import boto3

    monkeypatch.setattr("dagster_cloud.workspace.ecs.client.Client.taggable", True)
    monkeypatch.setattr(
        "dagster_cloud.workspace.ecs.client.Client._infer_assign_public_ip",
        lambda *args, **kwargs: "ENABLED",
    )

    ec2 = boto3.client("ec2")
    vpc_id = ec2.create_vpc(CidrBlock="10.0.0.0/16")["Vpc"]["VpcId"]
    subnet_id = ec2.create_subnet(VpcId=vpc_id, CidrBlock="10.0.1.0/24")["Subnet"]["SubnetId"]
    sg_id = ec2.create_security_group(GroupName="sg", Description="sg", VpcId=vpc_id)["GroupId"]
    boto3.client("ecs").create_cluster(clusterName="test")
    service_discovery = boto3.client("servicediscovery")
    operation_id = service_discovery.create_private_dns_namespace(Name="demo.local", Vpc=vpc_id)[
        "OperationId"
    ]
    namespace_id = service_discovery.get_operation(OperationId=operation_id)["Operation"][
        "Targets"
    ]["NAMESPACE"]

    with ecs_agent_instance(
        {
            **ROLE_CONFIG,
            "service_discovery_namespace_id": namespace_id,
            "cluster": "test",
            "subnets": [subnet_id],
            "security_group_ids": [sg_id],
        }
    ) as instance:
        launcher = instance.user_code_launcher
        client = launcher.client

        # The two kinds of code server the ECS launcher creates, tagged as
        # _start_new_server_spinup tags them.
        for name, kind_tag in [
            ("multipex-server", "dagster/multipex_server"),
            ("grpc-server", "dagster/grpc_server"),
        ]:
            client.create_service(
                name=name,
                image="test",
                command=["test"],
                execution_role_arn="test",
                tags={
                    kind_tag: "1",
                    "dagster/agent_id": instance.instance_uuid,
                    "dagster/location_name": name,
                },
            )
        # A service owned by another agent on the same cluster must be left alone.
        client.create_service(
            name="other-agents-server",
            image="test",
            command=["test"],
            execution_role_arn="test",
            tags={"dagster/grpc_server": "1", "dagster/agent_id": "someone-else"},
        )

        ecs_service_arns = [
            service["serviceArn"]
            for service in boto3.client("ecs").describe_services(
                cluster="test", services=["multipex-server", "grpc-server", "other-agents-server"]
            )["services"]
        ]
        assert all(
            not service.get("serviceRegistries")
            for service in boto3.client("ecs").describe_services(
                cluster="test", services=ecs_service_arns
            )["services"]
        ), "cross-account mode must not attach an ECS-managed service registry"

        def _list_tasks(cluster, serviceName, **kwargs):
            return {
                "taskArns": [f"arn:aws:ecs:us-east-1:123456789012:task/test/{serviceName}-task"]
            }

        def _describe_tasks(cluster, tasks):
            return {
                "tasks": [
                    {
                        "taskArn": task_arn,
                        "lastStatus": "RUNNING",
                        "attachments": [
                            {
                                "type": "ElasticNetworkInterface",
                                "details": [{"name": "privateIPv4Address", "value": "10.0.1.10"}],
                            }
                        ],
                    }
                    for task_arn in tasks
                ]
            }

        with (
            mock.patch.object(client.ecs, "list_tasks", side_effect=_list_tasks),
            mock.patch.object(client.ecs, "describe_tasks", side_effect=_describe_tasks),
        ):
            launcher._reconcile_service_discovery()

        def registered_instance_ids(service_name):
            service_id = client.get_service_discovery_arn(service_name).split("/")[-1]
            return {
                instance["Id"]
                for instance in service_discovery.list_instances(ServiceId=service_id)["Instances"]
            }

        assert registered_instance_ids("multipex-server") == {"multipex-server-task"}
        assert registered_instance_ids("grpc-server") == {"grpc-server-task"}
        assert registered_instance_ids("other-agents-server") == set()
