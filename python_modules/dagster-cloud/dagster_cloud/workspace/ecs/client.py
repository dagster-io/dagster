import asyncio
import datetime
import json
import logging
import os
import time
import uuid

import boto3
import botocore.exceptions
import dagster._check as check
from botocore.config import Config
from botocore.exceptions import ClientError
from dagster._utils.backoff import backoff
from dagster._utils.cached_method import cached_method
from dagster_aws.ecs.tasks import DagsterEcsTaskDefinitionConfig
from dagster_aws.ecs.utils import is_transient_task_stopped_reason, task_definitions_match

from dagster_cloud.workspace.ecs.service import Service

DEFAULT_ECS_TIMEOUT = 600
DEFAULT_ECS_GRACE_PERIOD = 30

STOPPED_TASK_GRACE_PERIOD = 30


ECS_EXEC_LINUX_PARAMETERS = {
    "capabilities": {"add": ["SYS_PTRACE"]},
    "initProcessEnabled": True,
}

config = Config(retries={"max_attempts": 50, "mode": "standard"})


def get_debug_ecs_prompt(cluster: str, task_arn: str) -> str:
    return (
        "For more information about the failure, check the ECS console for logs for task"
        f" {task_arn} in cluster {cluster}."
    )


class EcsServiceError(Exception):
    def __init__(self, cluster, task_arn, stopped_reason, logs, show_debug_prompt: bool):
        log_str = "Task logs:\n" + "\n".join(logs) if logs else "No task logs."

        message = (
            f"ECS service failed because task {task_arn} failed: {stopped_reason}\n\n{log_str}"
        )

        if show_debug_prompt:
            message = message + f"\n\n{get_debug_ecs_prompt(cluster, task_arn)}"
        super().__init__(message)


class Client:
    def __init__(
        self,
        cluster_name: str,
        service_discovery_namespace_id: str,
        log_group: str,
        subnet_ids: list[str] | None = None,
        security_group_ids: list[str] | None = None,
        ecs_client=None,
        timeout: int = DEFAULT_ECS_TIMEOUT,
        grace_period: int = DEFAULT_ECS_GRACE_PERIOD,
        launch_type: str = "FARGATE",
        show_debug_cluster_info: bool = True,
        assign_public_ip: bool | None = None,
        service_discovery_role_arn: str | None = None,
    ):
        self.ecs = ecs_client if ecs_client else boto3.client("ecs", config=config)
        self.logs = boto3.client("logs", config=config)
        self.tags_client = boto3.client("resourcegroupstaggingapi", config=config)

        self._service_discovery_role_arn = service_discovery_role_arn
        if service_discovery_role_arn:
            self._sts = boto3.client("sts", config=config)
            self._sd_session_expires: datetime.datetime | None = None
            self._create_service_discovery_session()
        else:
            self._service_discovery = boto3.client("servicediscovery", config=config)
        self._use_legacy_tag_filtering = False

        self.cluster_name = cluster_name.split("/")[-1]
        self.subnet_ids = check.opt_list_param(subnet_ids, "subnet_ids")
        self.security_group_ids = check.opt_list_param(security_group_ids, "security_group_ids")
        self.service_discovery_namespace_id = check.str_param(
            service_discovery_namespace_id, "service_discovery_namespace_id"
        )
        self.log_group = check.str_param(log_group, "log_group")

        self.show_debug_cluster_info = show_debug_cluster_info

        self.timeout = check.int_param(timeout, "timeout")
        self.grace_period = check.int_param(grace_period, "grace_period")
        self.launch_type = check.str_param(launch_type, "launch_type")
        self._namespace: str | None = None
        self._assign_public_ip_override = assign_public_ip

    def _create_service_discovery_session(self) -> None:
        """Assume cross-account role and create a servicediscovery client with temporary credentials."""
        response = self._sts.assume_role(
            RoleArn=check.not_none(self._service_discovery_role_arn),
            RoleSessionName=f"dagster-ecs-sd-{uuid.uuid4()}",
            DurationSeconds=3600,
        )
        self._sd_session_expires = response["Credentials"]["Expiration"]
        session = boto3.Session(
            aws_access_key_id=response["Credentials"]["AccessKeyId"],
            aws_secret_access_key=response["Credentials"]["SecretAccessKey"],
            aws_session_token=response["Credentials"]["SessionToken"],
        )
        self._service_discovery = session.client("servicediscovery", config=config)

    def _refresh_service_discovery_session(self) -> None:
        """Refresh the cross-account session if it's within 5 minutes of expiration."""
        if self._sd_session_expires is None:
            return
        now = datetime.datetime.now(self._sd_session_expires.tzinfo)
        if self._sd_session_expires <= now + datetime.timedelta(minutes=5):
            self._create_service_discovery_session()

    @property
    def service_discovery(self):
        if self._service_discovery_role_arn:
            self._refresh_service_discovery_session()
        return self._service_discovery

    @property
    def ec2(self):
        # Reconstruct the resource on each call because it's not threadsafe
        # https://boto3.amazonaws.com/v1/documentation/api/latest/guide/resources.html#multithreading-or-multiprocessing-with-resources
        return boto3.resource("ec2", config=config)

    @property
    def namespace(self):
        if not self._namespace:
            self._namespace = (
                self.service_discovery.get_namespace(
                    Id=self.service_discovery_namespace_id,
                )
                .get("Namespace")
                .get("Name")
            )
        return self._namespace

    @property
    def taggable(self):
        settings = self.ecs.list_account_settings(
            name="serviceLongArnFormat",
            effectiveSettings=True,
        )
        return settings["settings"][0]["value"] == "enabled"

    @property
    @cached_method
    def network_configuration(self):
        if self.launch_type != "FARGATE":
            assign_public_ip = None
        elif self._assign_public_ip_override is not None:
            assign_public_ip = "ENABLED" if self._assign_public_ip_override else "DISABLED"
        else:
            assign_public_ip = self._infer_assign_public_ip()

        network_configuration = {
            "awsvpcConfiguration": {
                "subnets": self.subnet_ids,
                **({"assignPublicIp": assign_public_ip} if assign_public_ip else {}),
            },
        }

        if self.security_group_ids:
            network_configuration["awsvpcConfiguration"]["securityGroups"] = self.security_group_ids

        return network_configuration

    def _reuse_or_register_task_definition(
        self,
        desired_task_definition_config: DagsterEcsTaskDefinitionConfig,
        container_name: str,
        logger: logging.Logger,
    ):
        family = desired_task_definition_config.family

        try:
            existing_task_definition = self.ecs.describe_task_definition(taskDefinition=family)[
                "taskDefinition"
            ]
        except ClientError:
            logger.info("No existing task definition")
            # task definition does not exist, do not reuse
            existing_task_definition = None

        if not existing_task_definition or not task_definitions_match(
            desired_task_definition_config,
            existing_task_definition,
            container_name=container_name,
        ):
            task_definition_arn = (
                self.ecs.register_task_definition(
                    **desired_task_definition_config.task_definition_dict()
                )
                .get("taskDefinition")
                .get("taskDefinitionArn")
            )
            logger.info(f"Created new task definition {task_definition_arn}")
        else:
            task_definition_arn = check.not_none(existing_task_definition.get("taskDefinitionArn"))
            logger.info(f"Re-using existing task definition {task_definition_arn}")

        return task_definition_arn

    def register_task_definition(
        self,
        family,
        image,
        command,
        execution_role_arn,
        container_name=None,
        task_role_arn=None,
        env=None,
        secrets=None,
        sidecars=None,
        logger=None,
        cpu=None,
        memory=None,
        ephemeral_storage=None,
        repository_credentials=None,
        runtime_platform=None,
        mount_points=None,
        volumes=None,
        linux_parameters=None,
        health_check=None,
    ):
        container_name = container_name or family

        logger = logger or logging.getLogger("dagster_cloud.EcsClient")

        env = env or {}
        environment = [{"name": key, "value": value} for key, value in env.items()]

        secrets = (
            [{"name": key, "valueFrom": value} for key, value in secrets.items()] if secrets else []
        )

        task_definition_config = DagsterEcsTaskDefinitionConfig(
            family=family,
            image=image,
            container_name=container_name,
            command=command,
            log_configuration={
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": self.log_group,
                    "awslogs-region": self.ecs.meta.region_name,
                    "awslogs-stream-prefix": family,
                },
            },
            secrets=secrets,
            environment=environment,
            execution_role_arn=execution_role_arn,
            task_role_arn=task_role_arn,
            sidecars=sidecars,
            requires_compatibilities=[self.launch_type],
            cpu=cpu,
            memory=memory,
            ephemeral_storage=ephemeral_storage,
            repository_credentials=repository_credentials,
            runtime_platform=runtime_platform,
            mount_points=mount_points,
            volumes=volumes,
            linux_parameters=linux_parameters,
            health_check=health_check,
        )

        task_definition_arn = backoff(
            self._reuse_or_register_task_definition,
            retry_on=(Exception,),
            kwargs={
                "desired_task_definition_config": task_definition_config,
                "container_name": container_name,
                "logger": logger,
            },
            max_retries=int(os.getenv("DAGSTER_CLOUD_REGISTER_TASK_DEFINITION_RETRIES", "5")),
        )

        return task_definition_arn

    def create_service(
        self,
        name,
        image,
        command,
        execution_role_arn,
        family=None,
        container_name=None,
        task_role_arn=None,
        env=None,
        tags=None,
        register_service_discovery=True,
        secrets=None,
        sidecars=None,
        logger=None,
        cpu=None,
        memory=None,
        ephemeral_storage=None,
        replica_count=None,
        repository_credentials=None,
        allow_ecs_exec=False,
        runtime_platform=None,
        mount_points=None,
        volumes=None,
        health_check=None,
    ):
        logger = logger or logging.getLogger("dagster_cloud.EcsClient")

        service_name = name
        family = family or name

        logger.info(f"Checking if task definition {family} for {name} can be re-used...")

        task_definition_arn = self.register_task_definition(
            family=family,
            image=image,
            container_name=container_name,
            execution_role_arn=execution_role_arn,
            task_role_arn=task_role_arn,
            command=command,
            env=env or {},
            secrets=secrets,
            sidecars=sidecars,
            logger=logger,
            cpu=cpu,
            memory=memory,
            ephemeral_storage=ephemeral_storage,
            repository_credentials=repository_credentials,
            runtime_platform=runtime_platform,
            mount_points=mount_points,
            volumes=volumes,
            linux_parameters=ECS_EXEC_LINUX_PARAMETERS if allow_ecs_exec else None,
            health_check=health_check,
        )

        service_registry_arn = None
        # Configure service discovery
        if register_service_discovery:
            logger.info(f"Creating service registry for {service_name}...")
            service_registry_arn = self._create_service_registry(
                service_name=service_name,
                tags=tags,
            )

        logger.info(f"Creating ECS service {service_name}...")

        # Create the service
        return self._create_service(
            service_name=service_name,
            service_registry_arn=service_registry_arn,
            task_definition_arn=task_definition_arn,
            replica_count=replica_count,
            tags=tags,
            allow_ecs_exec=allow_ecs_exec,
        )

    def delete_service(
        self,
        service,
        logger=None,
    ):
        logger = logger or logging.getLogger("dagster_cloud.EcsClient")

        # Reduce running tasks to 0
        try:
            self.ecs.update_service(
                cluster=self.cluster_name,
                service=service.name,
                desiredCount=0,
            )
        except botocore.exceptions.ClientError as error:
            if error.response["Error"]["Code"] in [
                "ServiceNotFoundException",
                "ServiceNotActiveException",
            ]:
                logger.warning(
                    f"Service {self.cluster_name}/{service.name} is not found or inactive: {error}"
                )
                return
            raise

        # Delete the ECS service
        self.ecs.delete_service(
            cluster=self.cluster_name,
            service=service.name,
            force=True,
        )
        # get service discovery id
        service_discovery_id = self._get_service_discovery_id(
            service.hostname,
        )
        if service_discovery_id:
            # Unregister dangling ecs tasks from service discovery
            instances_paginator = self.service_discovery.get_paginator("list_instances")
            instances = instances_paginator.paginate(
                ServiceId=service_discovery_id,
            ).build_full_result()["Instances"]
            deregister_operation_ids = []
            for instance in instances:
                resp = self.service_discovery.deregister_instance(
                    ServiceId=service_discovery_id, InstanceId=instance["Id"]
                )
                deregister_operation_ids.append(resp["OperationId"])

            # wait for instances to complete deregistering
            for operation_id in deregister_operation_ids:
                status = ""
                while status != "SUCCESS":
                    status = self.service_discovery.get_operation(OperationId=operation_id)[
                        "Operation"
                    ]["Status"]
                    if status == "FAIL":
                        raise Exception("deregister operation failed")
                    time.sleep(2)

            # delete service discovery
            self.service_discovery.delete_service(
                Id=service_discovery_id,
            )

    def list_services(self, tags=None, logger=None):
        logger = logger or logging.getLogger("dagster_cloud.EcsClient")

        services = []

        if tags:
            if not self._use_legacy_tag_filtering:
                try:
                    # obtain services present in the cluster
                    ecs_services_paginator = self.ecs.get_paginator("list_services")
                    actual_services = []
                    for page in ecs_services_paginator.paginate(cluster=self.cluster_name):
                        actual_services.extend(page["serviceArns"])

                    # obtain services with the specified tags
                    tag_paginator = self.tags_client.get_paginator("get_resources")
                    for page in tag_paginator.paginate(
                        TagFilters=[
                            {
                                "Key": key,
                                "Values": [value],
                            }
                            for key, value in tags.items()
                        ],
                        ResourceTypeFilters=["ecs:service"],
                    ):
                        for resource in page["ResourceTagMappingList"]:
                            resource_arn = resource["ResourceARN"]
                            # note: the Resource Group Tagging API may return resources corresponding to services
                            # that are no longer present in the cluster, so we filter out those that are not present
                            if resource_arn in actual_services:
                                services.append(Service(client=self, arn=resource_arn))

                except botocore.exceptions.ClientError as error:
                    if error.response["Error"]["Code"] == "AccessDeniedException":
                        self._use_legacy_tag_filtering = True
                        logger.warning(
                            "dagster-cloud 1.4.0 includes performance enhancements that rely on the"
                            " Resource"
                            " Group Tagging API. To take advantage, add 'tags:GetResources'"
                            " permissions to"
                            " your"
                            " task role."
                            " https://docs.aws.amazon.com/resourcegroupstagging/latest/APIReference/overview.html"
                        )
                        services = self.list_services(tags)
                    else:
                        raise
            else:
                filtered_services = [
                    service
                    for service in self.list_services()
                    if tags.items() <= service.tags.items()
                ]
                return filtered_services

        else:
            service_paginator = self.ecs.get_paginator("list_services")
            for page in service_paginator.paginate(cluster=self.cluster_name):
                for service_arn in page.get("serviceArns"):
                    service = Service(client=self, arn=service_arn)
                    services.append(service)

        return services

    def _run_task(self, name, image, command, execution_role_arn):
        """This is no longer used except as an integration test util
        for testing various network configurations.
        """
        task_definition_arn = self.register_task_definition(
            family=name,
            image=image,
            command=command,
            execution_role_arn=execution_role_arn,
        )

        task_arn = (
            self.ecs.run_task(
                taskDefinition=task_definition_arn,
                cluster=self.cluster_name,
                launchType=self.launch_type,
                networkConfiguration=self.network_configuration,
                clientToken=str(uuid.uuid4()),
            )
            .get("tasks", [{}])[0]
            .get("taskArn")
        )

        self.ecs.get_waiter("tasks_stopped").wait(
            cluster=self.cluster_name,
            tasks=[task_arn],
            WaiterConfig={"Delay": 1, "MaxAttempts": self.timeout},
        )

        exit_code = (
            self.ecs.describe_tasks(
                cluster=self.cluster_name,
                tasks=[task_arn],
            )
            .get("tasks", [{}])[0]
            .get("containers", [{}])[0]
            .get("exitCode")
        )

        if exit_code:
            raise Exception(self.get_task_logs(task_arn))  # ty: ignore[missing-argument]

        return True

    def _create_service_registry(self, service_name, tags=None):
        if not tags:
            tags = {}

        # https://docs.aws.amazon.com/AmazonECS/latest/developerguide/create-service-discovery.html
        service_registry_arn = (
            self.service_discovery.create_service(
                Name=service_name,
                NamespaceId=self.service_discovery_namespace_id,
                DnsConfig={
                    "DnsRecords": [
                        {"Type": "A", "TTL": 60},
                    ]
                },
                Tags=[{"Key": key, "Value": value} for key, value in tags.items()],
            )
            .get("Service", {})
            .get("Arn")
        )
        return service_registry_arn

    def _create_service(
        self,
        service_name,
        task_definition_arn,
        service_registry_arn,
        replica_count=None,
        tags=None,
        allow_ecs_exec=False,
    ):
        params = dict(
            cluster=self.cluster_name,
            serviceName=service_name,
            taskDefinition=task_definition_arn,
            launchType=self.launch_type,
            desiredCount=replica_count or 1,
            enableExecuteCommand=allow_ecs_exec,
            propagateTags="SERVICE",
            clientToken=str(uuid.uuid4()),
        )
        params["networkConfiguration"] = self.network_configuration

        if service_registry_arn:
            params["serviceRegistries"] = [{"registryArn": service_registry_arn}]

        if tags and self.taggable:
            params["tags"] = [
                {"key": key, **({"value": value} if value is not None else {})}
                for key, value in tags.items()
            ]

        arn = self.ecs.create_service(**params).get("service").get("serviceArn")

        return Service(client=self, arn=arn)

    async def wait_for_new_service(self, service, container_name, logger=None) -> str:
        logger = logger or logging.getLogger("dagster_cloud.EcsClient")
        service_name = service.name
        start_time = time.time()
        while True:
            response = self.ecs.describe_services(
                cluster=self.cluster_name,
                services=[service_name],
            )
            if response.get("services"):
                running_tasks = await self.check_service_has_running_tasks(
                    service_name, container_name, logger=logger
                )
                return running_tasks[0]

            failures = response.get("failures")

            if not failures:
                # This might not be a possible state; it's unclear if the ECS API can return empty lists for both
                # "failures" and "services":
                # https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_DescribeServices.html
                raise Exception(
                    "ECS DescribeServices API returned an empty response for service"
                    f" {service.arn}."
                )

            # Even if we fail, check a few more times in case it's just the ECS API
            # being eventually consistent
            if time.time() - start_time >= self.grace_period:
                raise Exception(
                    f"ECS DescribeServices API returned failures: {json.dumps(failures)}"
                )

            await asyncio.sleep(10)

    def _raise_failed_task(self, task, container_name, logger):
        task_arn = task["taskArn"]
        stopped_reason = task["stoppedReason"]

        logs = None

        try:
            logs = self.get_task_logs(task_arn, container_name=container_name)
        except:
            logger.exception(f"Error trying to get logs for failed task {task_arn}")

        raise EcsServiceError(
            cluster=self.cluster_name,
            task_arn=task_arn,
            stopped_reason=stopped_reason,
            logs=logs,
            show_debug_prompt=self.show_debug_cluster_info,
        )

    def assert_task_not_stopped(self, task_arn, container_name, logger=None):
        logger = logger or logging.getLogger("dagster_cloud.EcsClient")

        task = self.ecs.describe_tasks(cluster=self.cluster_name, tasks=[task_arn]).get("tasks")[0]
        if task.get("lastStatus") == "STOPPED":
            self._raise_failed_task(task, container_name, logger)

    async def check_service_has_running_tasks(
        self, service_name, container_name, logger=None
    ) -> list[str]:
        # return the ARN of the task if it starts
        logger = logger or logging.getLogger("dagster_cloud.EcsClient")
        start_time = time.time()

        tasks_to_track = None

        while start_time + self.timeout > time.time():
            # Check for running tasks to track
            if not tasks_to_track:
                services = self.ecs.describe_services(
                    cluster=self.cluster_name,
                    services=[service_name],
                )
                if not services or not services.get("services"):
                    raise Exception(
                        f"Service description not found for {self.cluster_name}/{service_name}"
                    )

                service = services["services"][0]
                desired_count = service.get("desiredCount")
                running_count = service.get("runningCount")

                # If the service has reached the desired count, we can start tracking the tasks
                if desired_count and (desired_count > 0) and (desired_count == running_count):
                    running_tasks = self.ecs.list_tasks(
                        cluster=self.cluster_name,
                        serviceName=service_name,
                        desiredStatus="RUNNING",
                    ).get("taskArns")

                    if running_tasks:
                        tasks_to_track = running_tasks

            if not tasks_to_track and time.time() > start_time + STOPPED_TASK_GRACE_PERIOD:
                # If there are still no running_tasks tasks after a certain grace period, check for stopped tasks
                stopped_tasks = self._check_for_stopped_tasks(service_name)
                if stopped_tasks:
                    latest_stopped_task = stopped_tasks[0]
                    stopped_reason = latest_stopped_task.get("stoppedReason", "")

                    if is_transient_task_stopped_reason(stopped_reason):
                        logger.warning(
                            f"Task stopped with a transient stoppedReason: {stopped_reason} - waiting for the service to launch a new task"
                        )
                    else:
                        self._raise_failed_task(stopped_tasks[0], container_name, logger)

            if tasks_to_track:
                tasks = self.ecs.describe_tasks(
                    cluster=self.cluster_name, tasks=tasks_to_track
                ).get("tasks")

                # Wait for all tasks essential containers to be running
                all_tasks_running = len(tasks) > 0
                for task in tasks:
                    if task.get("lastStatus") == "RUNNING":
                        if not self._check_all_essential_containers_are_running(task):
                            all_tasks_running = False
                    elif task.get("lastStatus") == "STOPPED":
                        stopped_reason = task.get("stoppedReason", "")
                        if is_transient_task_stopped_reason(stopped_reason):
                            logger.warning(
                                f"Running task stopped with a transient stoppedReason: {stopped_reason} - waiting for the service to launch a new task"
                            )
                            tasks_to_track = []
                            all_tasks_running = False
                        else:
                            self._raise_failed_task(task, container_name, logger)

                if all_tasks_running:
                    return tasks_to_track

            await asyncio.sleep(20)

        # Fetch the service event logs to try to get some clue about why the service never spun
        # up any tasks
        service_events_str = ""
        try:
            response = self.ecs.describe_services(
                cluster=self.cluster_name,
                services=[service_name],
            )
            if response.get("services"):
                service = response["services"][0]
                service_events = [str(event.get("message")) for event in service.get("events", [])]
                service_events_str = "Service events:\n" + "\n".join(service_events)
        except:
            logger.exception(f"Error trying to get service event logs from service {service_name}")

        raise Exception(
            f"Timed out waiting for a running task for service: {service_name}."
            f" {service_events_str}"
        )

    def _check_for_stopped_tasks(self, service_name):
        stopped = self.ecs.list_tasks(
            cluster=self.cluster_name,
            serviceName=service_name,
            desiredStatus="STOPPED",
        ).get("taskArns")
        if stopped:
            stopped_tasks = self.ecs.describe_tasks(cluster=self.cluster_name, tasks=stopped).get(
                "tasks"
            )

            stopped_tasks = sorted(
                stopped_tasks,
                key=lambda task: task["createdAt"].timestamp(),
                reverse=True,
            )
            return stopped_tasks
        return []

    def _check_all_essential_containers_are_running(self, task) -> bool:
        task_definition = self.ecs.describe_task_definition(
            taskDefinition=task.get("taskDefinitionArn"),
        ).get("taskDefinition")

        essential_containers = {
            check.not_none(container.get("name"))
            for container in task_definition.get("containerDefinitions", [])
            if container.get("essential") and container.get("name")
        }

        # Just because the task is RUNNING doesn't mean everything has started up correctly -
        # sometimes it briefly thinks it is RUNNING even though individual containers have STOPPED.
        # Wait for all essential containers to be running_tasks too before declaring victory.
        return all(
            container["name"] not in essential_containers or container["lastStatus"] == "RUNNING"
            for container in task["containers"]
        )

    def _get_service_discovery_id(self, hostname):
        service_name = hostname.split("." + self.namespace)[0]

        paginator = self.service_discovery.get_paginator("list_services")
        for page in paginator.paginate(
            Filters=[
                {
                    "Name": "NAMESPACE_ID",
                    "Values": [
                        self.service_discovery_namespace_id,
                    ],
                    "Condition": "EQ",
                },
            ],
        ):
            for service in page["Services"]:
                if service["Name"] == service_name:
                    return service["Id"]

    def _infer_assign_public_ip(self):
        # https://docs.aws.amazon.com/AmazonECS/latest/userguide/fargate-task-networking.html
        # Assign a public IP if any of the subnets are public
        route_tables = self.ec2.route_tables.filter(
            Filters=[
                {"Name": "association.subnet-id", "Values": self.subnet_ids},
            ]
        )

        # Consider a subnet to be public if it has a route that targets
        # an internet gateway; private subnets have routes that target NAT gateways
        for route_table in route_tables:
            if any(route.nat_gateway_id for route in route_table.routes):
                return "DISABLED"
        return "ENABLED"

    def get_task_logs(self, task_arn, container_name, limit=10):
        task = self.ecs.describe_tasks(cluster=self.cluster_name, tasks=[task_arn]).get("tasks")[0]

        task_definition_arn = task.get("taskDefinitionArn")
        task_definition = self.ecs.describe_task_definition(taskDefinition=task_definition_arn).get(
            "taskDefinition"
        )

        matching_container_definitions = [
            container_definition
            for container_definition in task_definition.get("containerDefinitions", [])
            if container_definition["name"] == container_name
        ]
        if not matching_container_definitions:
            raise Exception(f"Could not find container with name {container_name}")

        container_definition = matching_container_definitions[0]

        log_stream_prefix = (
            container_definition.get("logConfiguration").get("options").get("awslogs-stream-prefix")
        )
        container_name = container_definition.get("name")
        task_id = task_arn.split("/")[-1]

        log_stream = f"{log_stream_prefix}/{container_name}/{task_id}"

        events = self.logs.get_log_events(
            logGroupName=self.log_group, logStreamName=log_stream, limit=limit
        ).get("events")

        return [event.get("message") for event in events]
