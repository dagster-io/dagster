# ruff: noqa: SLF001
"""Cross-account service discovery in the ECS Client: when the Cloud Map namespace is owned by a
different AWS account than the agent (detected from the namespace ARN and the agent's identity,
and only possible with service_discovery_role_arn), ECS cannot register tasks into it, and the
agent registers and reconciles code server tasks in Cloud Map itself. Same-account behaviour,
with and without a role ARN, is covered here only to show it is untouched. The launcher's thread
and fan-out are in test_launcher.py.
"""

import asyncio
from collections import namedtuple
from contextlib import contextmanager
from itertools import chain, cycle
from unittest import mock

import pytest
from botocore.stub import ANY, Stubber
from dagster_cloud.workspace.ecs.client import (
    Client,
    Service,
    ServiceDiscoveryError,
    ServiceDiscoveryOperationError,
)

CROSS_ACCOUNT_ROLE_ARN = "arn:aws:iam::123456789012:role/cross-account-sd"
# moto answers every call as this account, so a "different" agent account has to be faked.
MOTO_ACCOUNT_ID = "123456789012"
OTHER_ACCOUNT_ID = "999999999999"
SD_SERVICE_ARN = "arn:aws:servicediscovery:us-east-1:123456789012:service/srv-fake"
ENI = "ElasticNetworkInterface"


def _make_client(**kwargs) -> Client:
    kwargs.setdefault("service_discovery_namespace_id", "fake-namespace")
    client = Client(
        cluster_name="test",
        log_group="fake-log-group",
        grace_period=0,
        **kwargs,
    )
    client._infer_assign_public_ip = lambda *args, **kwargs: "ENABLED"  # ty: ignore[invalid-assignment]
    return client


@pytest.fixture
def same_account_client():
    return _make_client()


def _create_moto_namespace() -> str:
    import boto3

    vpc_id = boto3.client("ec2").create_vpc(CidrBlock="10.0.0.0/16")["Vpc"]["VpcId"]
    service_discovery = boto3.client("servicediscovery")
    operation_id = service_discovery.create_private_dns_namespace(Name="demo.local", Vpc=vpc_id)[
        "OperationId"
    ]
    return service_discovery.get_operation(OperationId=operation_id)["Operation"]["Targets"][
        "NAMESPACE"
    ]


@pytest.fixture
def moto_namespace_id(aws_mock) -> str:
    return _create_moto_namespace()


@pytest.fixture
def cross_account_client(moto_namespace_id):
    """A real moto namespace (owned by moto's account) and an agent that reports a different
    account, so the client detects cross-account mode the way it would in AWS. Moto's STS hands
    out credentials for any role ARN, so the constructor's assume_role call succeeds too.
    """
    with mock.patch.object(Client, "_agent_account_id", return_value=OTHER_ACCOUNT_ID):
        yield _make_client(
            service_discovery_namespace_id=moto_namespace_id,
            service_discovery_role_arn=CROSS_ACCOUNT_ROLE_ARN,
            service_discovery_operation_timeout_seconds=10,
        )


@pytest.fixture
def role_only_client(moto_namespace_id):
    """A same-account setup that uses service_discovery_role_arn purely to put Cloud Map
    permissions on a separate role: the namespace and the agent are both moto's account. Must
    behave exactly like same_account_client.
    """
    return _make_client(
        service_discovery_namespace_id=moto_namespace_id,
        service_discovery_role_arn=CROSS_ACCOUNT_ROLE_ARN,
    )


def test_mode_is_cross_account_when_namespace_is_in_another_account(cross_account_client):
    assert cross_account_client.uses_cross_account_service_discovery


def test_mode_is_native_when_namespace_is_in_the_agent_account(role_only_client):
    assert not role_only_client.uses_cross_account_service_discovery


def test_mode_is_decided_at_construction(cross_account_client):
    """Reading the mode later never calls AWS, so every thread sees the same settled answer."""
    with (
        mock.patch.object(cross_account_client.service_discovery, "get_namespace") as get_namespace,
        mock.patch.object(cross_account_client, "_agent_account_id") as agent_account_id,
    ):
        assert cross_account_client.uses_cross_account_service_discovery
    get_namespace.assert_not_called()
    agent_account_id.assert_not_called()


def test_no_role_means_no_lookup_and_native_registration(same_account_client):
    """Without a role the agent could not reach another account's namespace anyway, so the
    decision is made without calling AWS at all.
    """
    with mock.patch.object(same_account_client.service_discovery, "get_namespace") as get_namespace:
        assert not same_account_client.uses_cross_account_service_discovery
    get_namespace.assert_not_called()


def test_role_arn_alone_keeps_ecs_native_registration(role_only_client):
    """The role ARN predates cross-account support and is used in same-account setups. Setting
    it must not change the ECS service that gets created.
    """
    arn = "arn:aws:ecs:us-east-1:1234567890:service/cluster-name/service-name"
    with Stubber(role_only_client.ecs) as stubber:
        stubber.add_response(
            method="create_service",
            service_response={"service": {"serviceArn": arn}},
            expected_params={
                "serviceRegistries": [{"registryArn": SD_SERVICE_ARN}],
                **dict.fromkeys(
                    [
                        "clientToken",
                        "cluster",
                        "desiredCount",
                        "launchType",
                        "networkConfiguration",
                        "serviceName",
                        "taskDefinition",
                        "enableExecuteCommand",
                        "propagateTags",
                    ],
                    ANY,
                ),
            },
        )
        role_only_client._create_service(
            service_name="fake", service_registry_arn=SD_SERVICE_ARN, task_definition_arn="fake"
        )


def test_role_arn_alone_never_registers_or_reconciles(role_only_client):
    with (
        mock.patch.object(role_only_client.service_discovery, "register_instance") as register,
        mock.patch.object(role_only_client.ecs, "list_tasks") as list_tasks,
    ):
        role_only_client.reconcile_service_discovery_instances(_stub_service())
    register.assert_not_called()
    list_tasks.assert_not_called()


def _task_arn(task_id):
    return f"arn:aws:ecs:us-east-1:123456789012:task/test/{task_id}"


def _fake_task(task_id, ip="10.0.0.5", last_status="RUNNING", attachments=None):
    if attachments is None:
        attachments = [{"type": ENI, "details": [{"name": "privateIPv4Address", "value": ip}]}]
    return {"taskArn": _task_arn(task_id), "lastStatus": last_status, "attachments": attachments}


def _stub_service(name="my_service", service_discovery_arn=SD_SERVICE_ARN):
    StubService = namedtuple("StubService", "name service_discovery_arn")
    return StubService(name=name, service_discovery_arn=service_discovery_arn)


@contextmanager
def _patch_cloud_map(client, *, registered_ids=(), operation_status="SUCCESS"):
    """Stubs the four Cloud Map calls the cross-account code makes. Yields a namespace whose
    `calls` records register / deregister / get_operation in the order they happened.
    """
    parent = mock.Mock()
    with (
        mock.patch.object(
            client.service_discovery,
            "list_instances",
            return_value={"Instances": [{"Id": instance_id} for instance_id in registered_ids]},
        ),
        mock.patch.object(
            client.service_discovery,
            "register_instance",
            side_effect=lambda **kwargs: {"OperationId": f"reg-{kwargs['InstanceId']}"},
        ) as register,
        mock.patch.object(
            client.service_discovery,
            "deregister_instance",
            side_effect=lambda **kwargs: {"OperationId": f"dereg-{kwargs['InstanceId']}"},
        ) as deregister,
        mock.patch.object(
            client.service_discovery,
            "get_operation",
            return_value={"Operation": {"Status": operation_status}},
        ) as get_operation,
    ):
        parent.attach_mock(register, "register")
        parent.attach_mock(deregister, "deregister")
        parent.attach_mock(get_operation, "get_operation")
        yield mock.Mock(
            register=register,
            deregister=deregister,
            get_operation=get_operation,
            calls=parent.mock_calls,
        )


def _reconcile(
    client,
    *,
    live_tasks,
    registered_ids=(),
    describe_failures=(),
    list_tasks_pages=None,
    before_run=None,
):
    """Runs one reconcile pass for a service whose ECS tasks are `live_tasks` and whose Cloud Map
    service has `registered_ids` registered, and returns the stubbed Cloud Map calls.

    ListTasks returns the tasks' ARNs in one page unless `list_tasks_pages` is given; DescribeTasks
    answers only for the ARNs asked about, and reports `describe_failures` ARNs under "failures"
    instead of "tasks". `before_run(cloud_map)` can adjust the stubs before the pass runs.
    """
    tasks_by_arn = {task["taskArn"]: task for task in live_tasks}

    def _describe_tasks(cluster, tasks):
        return {
            "tasks": [tasks_by_arn[arn] for arn in tasks if arn not in describe_failures],
            "failures": [
                {"arn": arn, "reason": "MISSING"} for arn in tasks if arn in describe_failures
            ],
        }

    list_tasks_patch = (
        mock.patch.object(client.ecs, "list_tasks", side_effect=list_tasks_pages)
        if list_tasks_pages is not None
        else mock.patch.object(
            client.ecs, "list_tasks", return_value={"taskArns": list(tasks_by_arn)}
        )
    )
    with (
        list_tasks_patch,
        mock.patch.object(client.ecs, "describe_tasks", side_effect=_describe_tasks) as describe,
        _patch_cloud_map(client, registered_ids=registered_ids) as cloud_map,
    ):
        cloud_map.describe_tasks = describe
        if before_run:
            before_run(cloud_map)
        client.reconcile_service_discovery_instances(_stub_service())
    return cloud_map


# ---- service creation and startup ------------------------------------------------------------


def test_create_service_cross_account_skips_service_registries(cross_account_client):
    """ServiceRegistries is omitted for cross-account clients (ecs:CreateService rejects it), but
    still passed for same-account clients - see test_client.test_create_service_tags.
    """
    arn = "arn:aws:ecs:us-east-1:1234567890:service/cluster-name/service-name"
    params_without_service_registries = [
        "clientToken",
        "cluster",
        "desiredCount",
        "launchType",
        "networkConfiguration",
        "serviceName",
        "taskDefinition",
        "enableExecuteCommand",
        "propagateTags",
    ]
    with Stubber(cross_account_client.ecs) as stubber:
        stubber.add_response(
            method="create_service",
            service_response={"service": {"serviceArn": arn}},
            expected_params=dict.fromkeys(params_without_service_registries, ANY),
        )
        service = cross_account_client._create_service(
            service_name="fake", service_registry_arn=SD_SERVICE_ARN, task_definition_arn="fake"
        )
    # The registry ARN is remembered on the handle so startup registration needs no lookup...
    assert service.service_discovery_arn == SD_SERVICE_ARN
    # ...and seeded into the name -> ARN cache, so a reconcile pass that lists the service
    # before the next cache reload resolves it without calling Cloud Map.
    with mock.patch.object(cross_account_client.service_discovery, "list_services") as list_svcs:
        assert cross_account_client.get_service_discovery_arn("fake") == SD_SERVICE_ARN
    list_svcs.assert_not_called()


def test_create_service_same_account_handle_still_reads_registry_from_ecs(same_account_client):
    """Same-account handles do not carry a Cloud Map ARN: reading it goes through DescribeServices
    exactly as before this feature, so nothing changes for agents that do not need it.
    """
    arn = "arn:aws:ecs:us-east-1:1234567890:service/test/service-name"
    with Stubber(same_account_client.ecs) as stubber:
        stubber.add_response(
            method="create_service", service_response={"service": {"serviceArn": arn}}
        )
        service = same_account_client._create_service(
            service_name="service-name",
            service_registry_arn=SD_SERVICE_ARN,
            task_definition_arn="fake",
        )
        assert service._service_registry_arn is None

        stubber.add_response(
            method="describe_services",
            service_response={
                "services": [{"serviceRegistries": [{"registryArn": SD_SERVICE_ARN}]}]
            },
            expected_params={"cluster": "test", "services": [service.arn]},
        )
        assert service.service_discovery_arn == SD_SERVICE_ARN
        stubber.assert_no_pending_responses()


@pytest.mark.parametrize(
    ("client_fixture", "expected_registrations"),
    [
        pytest.param("cross_account_client", 1, id="cross-account registers the task itself"),
        pytest.param("same_account_client", 0, id="same-account leaves it to ECS"),
    ],
)
def test_check_service_has_running_tasks_registration(
    request, client_fixture, expected_registrations
):
    """Initial registration: once every task is running, a cross-account client registers each
    task's private IP with Cloud Map, which is what ECS would have done natively.
    """
    client = request.getfixturevalue(client_fixture)
    client.timeout = 60
    with (
        mock.patch("dagster_cloud.workspace.ecs.client.time") as mock_time,
        Stubber(client.ecs) as stubber,
        _patch_cloud_map(client) as cloud_map,
    ):
        mock_time.time.side_effect = chain([1, 20], cycle([30]))
        stubber.add_response(
            method="describe_services",
            service_response={"services": [{"desiredCount": 1, "runningCount": 1}]},
        )
        stubber.add_response(method="list_tasks", service_response={"taskArns": [_task_arn("t1")]})
        stubber.add_response(
            method="describe_tasks", service_response={"tasks": [_fake_task("t1")]}
        )
        client._check_for_stopped_tasks = mock.MagicMock(return_value=[])  # ty: ignore[invalid-assignment]
        client._check_all_essential_containers_are_running = mock.MagicMock(return_value=True)  # ty: ignore[invalid-assignment]

        result = asyncio.run(
            client.check_service_has_running_tasks(
                "my_service", "my_container", service_registry_arn=SD_SERVICE_ARN
            )
        )

    assert result == [_task_arn("t1")]
    assert cloud_map.register.call_count == expected_registrations
    if expected_registrations:
        cloud_map.register.assert_called_once_with(
            ServiceId="srv-fake", InstanceId="t1", Attributes={"AWS_INSTANCE_IPV4": "10.0.0.5"}
        )


@pytest.mark.parametrize(
    ("client_fixture", "expected_registry_arn"),
    [
        pytest.param("cross_account_client", SD_SERVICE_ARN, id="cross-account passes the ARN"),
        pytest.param("same_account_client", None, id="same-account never looks it up"),
    ],
)
def test_wait_for_new_service_passes_registry_arn_only_cross_account(
    request, client_fixture, expected_registry_arn
):
    """The guard that keeps same-account startups off Cloud Map entirely."""
    client = request.getfixturevalue(client_fixture)
    service = Service(
        arn="arn:aws:ecs:us-east-1:123456789012:service/test/svc",
        client=client,
        service_registry_arn=SD_SERVICE_ARN,
    )

    async def _fake_check(service_name, container_name, service_registry_arn=None, logger=None):
        return [_task_arn("t1")]

    with (
        Stubber(client.ecs) as stubber,
        mock.patch.object(
            client, "check_service_has_running_tasks", side_effect=_fake_check
        ) as check,
    ):
        stubber.add_response(
            method="describe_services", service_response={"services": [{"serviceName": "svc"}]}
        )
        assert asyncio.run(client.wait_for_new_service(service, "dagster")) == _task_arn("t1")

    assert check.call_args.kwargs["service_registry_arn"] == expected_registry_arn


def test_check_service_has_running_tasks_fails_when_registration_fails(cross_account_client):
    """A failed Cloud Map registration fails the code server start instead of being swallowed,
    and the error survives the hop through asyncio.to_thread.
    """
    client = cross_account_client
    client.timeout = 60
    with (
        mock.patch("dagster_cloud.workspace.ecs.client.time") as mock_time,
        Stubber(client.ecs) as stubber,
        _patch_cloud_map(client, operation_status="FAIL"),
    ):
        mock_time.time.side_effect = chain([1, 20], cycle([30]))
        stubber.add_response(
            method="describe_services",
            service_response={"services": [{"desiredCount": 1, "runningCount": 1}]},
        )
        stubber.add_response(method="list_tasks", service_response={"taskArns": [_task_arn("t1")]})
        stubber.add_response(
            method="describe_tasks", service_response={"tasks": [_fake_task("t1")]}
        )
        client._check_for_stopped_tasks = mock.MagicMock(return_value=[])  # ty: ignore[invalid-assignment]
        client._check_all_essential_containers_are_running = mock.MagicMock(return_value=True)  # ty: ignore[invalid-assignment]

        with pytest.raises(ServiceDiscoveryOperationError, match="register instances"):
            asyncio.run(
                client.check_service_has_running_tasks(
                    "my_service", "my_container", service_registry_arn=SD_SERVICE_ARN
                )
            )


# ---- registering and waiting -----------------------------------------------------------------


def test_register_instances_issues_all_calls_before_waiting(cross_account_client):
    with _patch_cloud_map(cross_account_client) as cloud_map:
        cross_account_client._register_service_discovery_instances(
            tasks=[_fake_task("t1", "10.0.0.1"), _fake_task("t2", "10.0.0.2")],
            service_registry_arn=SD_SERVICE_ARN,
        )
    assert [call[0] for call in cloud_map.calls] == [
        "register",
        "register",
        "get_operation",
        "get_operation",
    ]
    assert cloud_map.register.call_args_list[1].kwargs == {
        "ServiceId": "srv-fake",
        "InstanceId": "t2",
        "Attributes": {"AWS_INSTANCE_IPV4": "10.0.0.2"},
    }


def test_register_instances_resolves_every_address_before_issuing_calls(cross_account_client):
    """A task without an address fails the batch before any RegisterInstance goes out, so
    nothing is left issued but never awaited.
    """
    with _patch_cloud_map(cross_account_client) as cloud_map:
        with pytest.raises(ServiceDiscoveryError, match="no private IPv4 address"):
            cross_account_client._register_service_discovery_instances(
                tasks=[
                    _fake_task("t1", "10.0.0.1"),
                    _fake_task("t2", attachments=[{"type": ENI, "details": []}]),
                ],
                service_registry_arn=SD_SERVICE_ARN,
            )
    cloud_map.register.assert_not_called()


def test_register_instances_reports_every_failed_operation(cross_account_client):
    def _get_operation(OperationId):
        if OperationId == "reg-t2":
            return {"Operation": {"Status": "FAIL", "ErrorMessage": "quota exceeded"}}
        return {"Operation": {"Status": "SUCCESS"}}

    with _patch_cloud_map(cross_account_client) as cloud_map:
        cloud_map.get_operation.side_effect = _get_operation
        with pytest.raises(ServiceDiscoveryOperationError, match="quota exceeded") as excinfo:
            cross_account_client._register_service_discovery_instances(
                tasks=[_fake_task("t1", "10.0.0.1"), _fake_task("t2", "10.0.0.2")],
                service_registry_arn=SD_SERVICE_ARN,
            )
    assert excinfo.value.failures == {"t2": "quota exceeded"}
    assert "srv-fake" in str(excinfo.value)


def test_wait_for_operations_times_out(cross_account_client):
    with (
        mock.patch("dagster_cloud.workspace.ecs.client.time") as mock_time,
        _patch_cloud_map(cross_account_client, operation_status="PENDING"),
    ):
        # deadline = 0 + 10; the check at t=5 keeps waiting, the one at t=11 gives up.
        mock_time.time.side_effect = chain([0, 5], cycle([11]))
        with pytest.raises(
            ServiceDiscoveryOperationError, match="did not finish within 10 seconds"
        ) as excinfo:
            cross_account_client._wait_for_service_discovery_operations(
                {"t1": "op-1"}, "register instances with Cloud Map service srv-fake"
            )
    assert set(excinfo.value.failures) == {"t1"}
    mock_time.sleep.assert_called()


@pytest.mark.parametrize(
    ("attachments", "expected_ip", "expected_error"),
    [
        pytest.param(None, "10.0.0.5", None, id="one network interface"),
        pytest.param(
            [
                {"type": ENI, "details": [{"name": "privateIPv4Address", "value": "10.0.0.5"}]},
                {"type": "ServiceConnect", "details": []},
            ],
            "10.0.0.5",
            None,
            id="non-network attachments are ignored",
        ),
        pytest.param([], None, "exactly one network interface", id="no attachments"),
        pytest.param(
            [
                {"type": ENI, "details": [{"name": "privateIPv4Address", "value": "10.0.0.1"}]},
                {"type": ENI, "details": [{"name": "privateIPv4Address", "value": "10.0.0.2"}]},
            ],
            None,
            "found 2",
            id="two network interfaces",
        ),
        pytest.param(
            [{"type": ENI, "details": [{"name": "subnetId", "value": "subnet-1"}]}],
            None,
            "no private IPv4 address",
            id="interface without an address yet",
        ),
    ],
)
def test_get_task_private_ip(attachments, expected_ip, expected_error):
    task = _fake_task("t1", attachments=attachments)
    if expected_error:
        with pytest.raises(ServiceDiscoveryError, match=expected_error):
            Client._get_task_private_ip(task)
    else:
        assert Client._get_task_private_ip(task) == expected_ip


# ---- periodic reconciliation -----------------------------------------------------------------


def test_reconcile_registers_new_tasks_and_deregisters_stale_instances(cross_account_client):
    """A task ECS started after initial registration (e.g. a replacement after a health check
    failure) gets registered; an instance whose task is gone gets deregistered.
    """
    cloud_map = _reconcile(
        cross_account_client, live_tasks=[_fake_task("live")], registered_ids=["stale"]
    )
    cloud_map.register.assert_called_once_with(
        ServiceId="srv-fake", InstanceId="live", Attributes={"AWS_INSTANCE_IPV4": "10.0.0.5"}
    )
    cloud_map.deregister.assert_called_once_with(ServiceId="srv-fake", InstanceId="stale")


def test_reconcile_is_a_noop_when_in_sync(cross_account_client):
    cloud_map = _reconcile(
        cross_account_client, live_tasks=[_fake_task("t1")], registered_ids=["t1"]
    )
    cloud_map.register.assert_not_called()
    cloud_map.deregister.assert_not_called()


def test_reconcile_skips_tasks_that_are_not_running_yet(cross_account_client):
    """ListTasks with desiredStatus=RUNNING also returns tasks still provisioning. Those are not
    registered (no address, not listening) but are not treated as gone either.
    """
    pending = _fake_task(
        "pending", last_status="PENDING", attachments=[{"type": ENI, "details": []}]
    )
    cloud_map = _reconcile(
        cross_account_client,
        live_tasks=[_fake_task("running"), pending],
        registered_ids=["pending", "stale"],
    )
    cloud_map.register.assert_called_once()
    assert cloud_map.register.call_args.kwargs["InstanceId"] == "running"
    cloud_map.deregister.assert_called_once_with(ServiceId="srv-fake", InstanceId="stale")


def test_reconcile_same_account_is_a_noop(same_account_client):
    """Same-account clients must never make any AWS calls here: ECS's native serviceRegistries
    path already handles task replacement.
    """
    with mock.patch.object(same_account_client.ecs, "list_tasks") as list_tasks:
        same_account_client.reconcile_service_discovery_instances(_stub_service())
    list_tasks.assert_not_called()


def test_reconcile_warns_without_cloud_map_service(cross_account_client, caplog):
    with mock.patch.object(cross_account_client.ecs, "list_tasks") as list_tasks:
        cross_account_client.reconcile_service_discovery_instances(
            _stub_service(service_discovery_arn=None)
        )
    list_tasks.assert_not_called()
    assert "No Cloud Map service named my_service" in caplog.text


def test_reconcile_describes_each_list_tasks_page(cross_account_client):
    """ListTasks is fully paginated and each page is described as-is, so tasks on later pages
    are neither missed (and wrongly deregistered) nor batched past DescribeTasks' 100 limit.
    """
    cloud_map = _reconcile(
        cross_account_client,
        live_tasks=[_fake_task("page-1-task", "10.0.0.1"), _fake_task("page-2-task", "10.0.0.2")],
        registered_ids=["page-1-task", "page-2-task"],
        # boto3's paginator key for ECS ListTasks is "nextToken" (lowercase).
        list_tasks_pages=[
            {"taskArns": [_task_arn("page-1-task")], "nextToken": "next-page"},
            {"taskArns": [_task_arn("page-2-task")]},
        ],
    )
    assert cloud_map.describe_tasks.call_count == 2
    cloud_map.register.assert_not_called()
    cloud_map.deregister.assert_not_called()


def test_reconcile_tolerates_describe_tasks_failures(cross_account_client):
    """DescribeTasks is eventually consistent: a task ListTasks just reported RUNNING can come
    back under `failures` (e.g. MISSING). That must not deregister a live code server.
    """
    cloud_map = _reconcile(
        cross_account_client,
        live_tasks=[_fake_task("live")],
        registered_ids=["live"],
        describe_failures=[_task_arn("live")],
    )
    # Can't register it either (no address), but that is the smaller problem.
    cloud_map.register.assert_not_called()
    cloud_map.deregister.assert_not_called()


def test_reconcile_continues_past_registration_failure(cross_account_client, caplog):
    """A failed registration is logged and does not stop stale instances being deregistered;
    the next pass retries.
    """

    def _break_registration(cloud_map):
        cloud_map.register.side_effect = Exception("RegisterInstance denied")

    cloud_map = _reconcile(
        cross_account_client,
        live_tasks=[_fake_task("new", "10.0.0.7")],
        registered_ids=["stale"],
        before_run=_break_registration,
    )
    cloud_map.deregister.assert_called_once_with(ServiceId="srv-fake", InstanceId="stale")
    assert "Failed to register 1 task(s) of my_service" in caplog.text
    assert "RegisterInstance denied" in caplog.text


def test_reconcile_continues_past_deregistration_failure(cross_account_client, caplog):
    """The mirror case: a failed deregistration is logged after registration has already
    happened, and the next pass retries it.
    """

    def _break_deregistration(cloud_map):
        cloud_map.deregister.side_effect = Exception("DeregisterInstance denied")

    cloud_map = _reconcile(
        cross_account_client,
        live_tasks=[_fake_task("new", "10.0.0.7")],
        registered_ids=["stale"],
        before_run=_break_deregistration,
    )
    cloud_map.register.assert_called_once()
    assert "Failed to deregister 1 stale instance(s) of my_service" in caplog.text
    assert "DeregisterInstance denied" in caplog.text


# ---- looking up a service's Cloud Map ARN ----------------------------------------------------


def test_service_discovery_arn_same_account_reads_the_registry_ecs_attached(same_account_client):
    """Unchanged pre-PR behaviour: one DescribeServices call, no Cloud Map call."""
    service = Service(
        arn="arn:aws:ecs:us-east-1:123456789012:service/test/svc", client=same_account_client
    )
    with (
        Stubber(same_account_client.ecs) as stubber,
        mock.patch.object(same_account_client.service_discovery, "list_services") as list_services,
    ):
        stubber.add_response(
            method="describe_services",
            service_response={
                "services": [{"serviceRegistries": [{"registryArn": SD_SERVICE_ARN}]}]
            },
            expected_params={"cluster": "test", "services": [service.arn]},
        )
        assert service.service_discovery_arn == SD_SERVICE_ARN
    list_services.assert_not_called()


def test_service_discovery_arn_cross_account_is_looked_up_by_name_and_cached(cross_account_client):
    client = cross_account_client
    with (
        mock.patch("dagster_cloud.workspace.ecs.client.time") as mock_time,
        mock.patch.object(
            client.service_discovery,
            "list_services",
            return_value={
                "Services": [
                    {"Name": "a", "Arn": "arn:a", "Id": "srv-a"},
                    {"Name": "b", "Arn": "arn:b", "Id": "srv-b"},
                ]
            },
        ) as list_services,
    ):
        # t=0: first lookup loads the namespace. t=1: a miss inside the refresh window does not
        # reload. t=31: a miss outside the window does.
        mock_time.time.side_effect = [0, 1, 31, 31]

        service_a = Service(arn="arn:aws:ecs:us-east-1:123456789012:service/test/a", client=client)
        assert service_a.service_discovery_arn == "arn:a"
        assert client.get_service_discovery_arn("b") == "arn:b"
        assert list_services.call_count == 1, "second name is served from the cache"

        assert client.get_service_discovery_arn("not-a-dagster-service") is None
        assert list_services.call_count == 1, "a miss within the window does not reload"

        assert client.get_service_discovery_arn("not-a-dagster-service") is None
        assert list_services.call_count == 2, "a miss after the window reloads once"


def test_service_tags_cross_account_resolve_through_cloud_map_by_name(cross_account_client):
    """Ownership and cleanup checks in the launcher read a handle's tags off its Cloud Map
    service. Cross-account handles have no ECS-attached registry, so the lookup goes by name.
    """
    client = cross_account_client
    service = Service(arn="arn:aws:ecs:us-east-1:123456789012:service/test/svc", client=client)
    with (
        mock.patch.object(
            client.service_discovery,
            "list_services",
            return_value={"Services": [{"Name": "svc", "Arn": SD_SERVICE_ARN, "Id": "srv-fake"}]},
        ),
        mock.patch.object(
            client.service_discovery,
            "list_tags_for_resource",
            return_value={"Tags": [{"Key": "dagster/agent_id", "Value": "agent-1"}]},
        ) as list_tags,
    ):
        assert service.tags == {"dagster/agent_id": "agent-1"}
    list_tags.assert_called_once_with(ResourceARN=SD_SERVICE_ARN)


def _instance_not_found(client):
    return client.service_discovery.exceptions.InstanceNotFound(
        {"Error": {"Code": "InstanceNotFound", "Message": "gone"}}, "DeregisterInstance"
    )


def _create_cloud_map_service_with_instance(client, namespace_id, name="svc", instance_id="t1"):
    sd_service_id = client.service_discovery.create_service(
        Name=name, NamespaceId=namespace_id, DnsConfig={"DnsRecords": [{"Type": "A", "TTL": 60}]}
    )["Service"]["Id"]
    client.service_discovery.register_instance(
        ServiceId=sd_service_id,
        InstanceId=instance_id,
        Attributes={"AWS_INSTANCE_IPV4": "10.0.0.5"},
    )
    return sd_service_id


def test_delete_service_cross_account_deregisters_agent_registered_instances(
    cross_account_client, moto_namespace_id
):
    """delete_service is unchanged, but in cross-account mode the instances it finds were
    registered by the agent, and it resolves the Cloud Map service through the namespace and
    the assumed-role client. Real moto Cloud Map; only ECS is stubbed.
    """
    client = cross_account_client
    assert client.uses_cross_account_service_discovery

    # What the agent leaves behind in cross-account mode: a Cloud Map service with an instance
    # the agent registered itself (ECS would have removed it on task stop in same-account mode).
    sd_service_id = _create_cloud_map_service_with_instance(client, moto_namespace_id)

    service = Service(arn="arn:aws:ecs:us-east-1:123456789012:service/test/svc", client=client)
    with (
        mock.patch.object(client.ecs, "update_service"),
        mock.patch.object(client.ecs, "delete_service"),
        mock.patch.object(
            client.service_discovery,
            "deregister_instance",
            wraps=client.service_discovery.deregister_instance,
        ) as deregister,
    ):
        client.delete_service(service)

    deregister.assert_called_once_with(ServiceId=sd_service_id, InstanceId="t1")
    assert client.get_service_discovery_arn("svc") is None, "Cloud Map service should be deleted"


def test_delete_service_tolerates_instance_already_deregistered(
    cross_account_client, moto_namespace_id
):
    """The reconcile thread can deregister a stale instance between delete_service's
    list_instances and deregister_instance calls. That must not abort the teardown and leave
    the Cloud Map service behind.
    """
    client = cross_account_client
    _create_cloud_map_service_with_instance(client, moto_namespace_id)
    service = Service(arn="arn:aws:ecs:us-east-1:123456789012:service/test/svc", client=client)

    with (
        mock.patch.object(client.ecs, "update_service"),
        mock.patch.object(client.ecs, "delete_service"),
        mock.patch.object(
            client.service_discovery, "deregister_instance", side_effect=_instance_not_found(client)
        ),
    ):
        client.delete_service(service)

    assert client.get_service_discovery_arn("svc") is None, "Cloud Map service should be deleted"


def test_reconcile_deregister_tolerates_instance_already_gone(cross_account_client):
    """The other direction of the same race: delete_service removed the instance first."""
    client = cross_account_client
    with (
        mock.patch.object(
            client.service_discovery, "deregister_instance", side_effect=_instance_not_found(client)
        ),
        mock.patch.object(client.service_discovery, "get_operation") as get_operation,
    ):
        client._deregister_service_discovery_instances(service_id="srv-fake", instance_ids=["t1"])
    get_operation.assert_not_called()
