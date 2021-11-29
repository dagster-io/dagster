import copy
import itertools
import uuid
from collections import defaultdict
from operator import itemgetter

import boto3
from botocore.exceptions import ClientError
from botocore.stub import Stubber


def stubbed(function):
    """
    A decorator that activates/deactivates the Stubber and makes sure all
    expected calls are made.

    The general pattern for stubbing a new method is:

    @stubbed
    def method(self, **kwargs):
        self.stubber.add_response(
            method="method", # Name of the method being stubbed
            service_response={}, # Stubber validates the resposne shape
            expected_params(**kwargs), # Stubber validates the params
        )
        self.client.method(**kwargs) # "super" (except we're not actually
                                     # subclassing anything)
    """

    def wrapper(*args, **kwargs):
        self = args[0]

        # If we're the first stub, activate:
        if not self.stub_count:
            self.stubber.activate()

        self.stub_count += 1
        try:
            response = function(*args, **kwargs)
            # If we're the outermost stub, clean up
            self.stub_count -= 1
            if not self.stub_count:
                self.stubber.deactivate()
                self.stubber.assert_no_pending_responses()
            return copy.deepcopy(response)
        except Exception as ex:
            # Exceptions should reset the stubber
            self.stub_count = 0
            self.stubber.deactivate()
            self.stubber = Stubber(self.client)
            raise ex

    return wrapper


class StubbedEcsError(Exception):
    pass


class StubbedEcs:
    """
    A class that stubs ECS responses using botocore's Stubber:
    https://botocore.amazonaws.com/v1/documentation/api/latest/reference/stubber.html

    Stubs are minimally sufficient for testing existing Dagster ECS behavior;
    consequently, not all endpoints are stubbed and not all stubbed endpoints
    are stubbed exhaustively.

    Stubber validates that we aren't passing invalid parameters or returning
    an invalid response shape. Additionally, some resources (tasks, tags,
    task_definitions) are stored in the instance which allows methods to have
    some minimal interaction - for example, you can't run a task if you haven't
    first created a task definition.

    We can't extend botocore.client.ECS directly. Eventually, we might want to
    register these methods as events instead of maintaing our own StubbedEcs
    class:
    https://boto3.amazonaws.com/v1/documentation/api/latest/guide/events.html
    """

    def __init__(self, boto3_client):
        self.client = boto3_client
        self.stubber = Stubber(self.client)
        self.meta = self.client.meta

        self.tasks = defaultdict(list)
        self.task_definitions = defaultdict(list)
        self.tags = defaultdict(list)
        self.account_settings = {}
        self.default_account_settings = {"taskLongArnFormat": "enabled"}
        self.stub_count = 0

    @stubbed
    def describe_task_definition(self, **kwargs):
        family = kwargs.get("taskDefinition") or ""
        revision = None

        if ":" in family:
            # We received either an ARN or family:revision
            family, revision = family.split(":")[-2:]
        if "/" in family:
            # We received an ARN
            family = family.split("/")[-1]

        task_definitions = self.task_definitions.get(family, [])

        if revision:
            # Match the exact revision
            task_definition = next(
                (
                    task_definition
                    for task_definition in task_definitions
                    if task_definition["revision"] == int(revision)
                ),
                None,
            )
        else:
            # Get the latest revision
            task_definition = next(
                iter(sorted(task_definitions, key=itemgetter("revision"), reverse=True)), None
            )

        if task_definition:
            self.stubber.add_response(
                method="describe_task_definition",
                service_response={"taskDefinition": task_definition},
                expected_params={**kwargs},
            )
        else:
            self.stubber.add_client_error(
                method="describe_task_definition", expected_params={**kwargs}
            )

        return self.client.describe_task_definition(**kwargs)

    @stubbed
    def describe_tasks(self, **kwargs):
        cluster = self._cluster(kwargs.get("cluster"))
        arns = kwargs.get("tasks")

        for i, arn in enumerate(arns):
            if ":" not in arn:
                # We received just a task ID, not a full ARN
                arns[i] = self._arn("task", f"{cluster}/{arn}")

        tasks = [task for task in self.tasks[cluster] if task["taskArn"] in arns]

        self.stubber.add_response(
            method="describe_tasks",
            service_response={"tasks": tasks},
            expected_params={**kwargs},
        )
        return self.client.describe_tasks(**kwargs)

    @stubbed
    def list_account_settings(self, **kwargs):
        """
        Only taskLongArnFormat has a default value
        """
        if kwargs.get("effectiveSettings"):
            account_settings = {
                **self.default_account_settings,
                **self.account_settings,
            }
        else:
            account_settings = self.account_settings

        account_settings = [
            {
                "name": key,
                "value": value,
            }
            for key, value in account_settings.items()
        ]

        self.stubber.add_response(
            method="list_account_settings",
            service_response={"settings": account_settings},
            expected_params={**kwargs},
        )
        return self.client.list_account_settings(**kwargs)

    @stubbed
    def list_tags_for_resource(self, **kwargs):
        """
        Only task tagging is stubbed; other resources won't work.
        """
        arn = kwargs.get("resourceArn")

        if self._task_exists(arn) and self._long_arn_enabled():
            self.stubber.add_response(
                method="list_tags_for_resource",
                service_response={"tags": self.tags.get(arn, [])},
                expected_params={**kwargs},
            )
        else:
            self.stubber.add_client_error(
                method="list_tags_for_resource", expected_params={**kwargs}
            )
        return self.client.list_tags_for_resource(**kwargs)

    @stubbed
    def list_task_definitions(self, **kwargs):
        arns = [
            task_definition["taskDefinitionArn"]
            for task_definition in itertools.chain.from_iterable(self.task_definitions.values())
        ]

        self.stubber.add_response(
            method="list_task_definitions",
            service_response={"taskDefinitionArns": arns},
            expected_params={**kwargs},
        )
        return self.client.list_task_definitions(**kwargs)

    @stubbed
    def list_tasks(self, **kwargs):
        """
        Only filtering by family and cluster is stubbed.
        TODO: Pagination
        """
        cluster = self._cluster(kwargs.get("cluster"))
        family = kwargs.get("family")

        tasks = self.tasks[cluster]
        if family:
            tasks = [
                task
                for task in tasks
                # family isn't part of task response can be infered from the arn
                if task["taskDefinitionArn"].split("/")[-1].split(":")[0] == family
            ]

        arns = [task["taskArn"] for task in tasks]

        self.stubber.add_response(
            method="list_tasks",
            service_response={"taskArns": arns},
            expected_params={**kwargs},
        )

        return self.client.list_tasks(**kwargs)

    @stubbed
    def put_account_setting(self, **kwargs):
        name = kwargs.get("name")
        value = kwargs.get("value")
        self.account_settings[name] = value

        self.stubber.add_response(
            method="put_account_setting",
            service_response={"setting": {"name": name, "value": value}},
            expected_params={**kwargs},
        )

        return self.client.put_account_setting(**kwargs)

    @stubbed
    def register_task_definition(self, **kwargs):
        family = kwargs.get("family")
        # Revisions are 1 indexed
        revision = len(self.task_definitions[family]) + 1
        arn = self._task_definition_arn(family, revision)

        memory = kwargs.get("memory")
        cpu = kwargs.get("cpu")

        if self._valid_cpu_and_memory(cpu=cpu, memory=memory):
            task_definition = {
                "family": family,
                "revision": revision,
                "taskDefinitionArn": arn,
                **kwargs,
            }

            self.task_definitions[family].append(task_definition)
            self.stubber.add_response(
                method="register_task_definition",
                service_response={"taskDefinition": task_definition},
                expected_params={**kwargs},
            )
        else:
            self.stubber.add_client_error(
                method="register_task_definition", expected_params={**kwargs}
            )

        return self.client.register_task_definition(**kwargs)

    @stubbed
    def run_task(self, **kwargs):
        """
        run_task is an endpoint with complex behaviors and consequently is not
        exhaustively stubbed.
        """
        try:
            task_definition = self.describe_task_definition(
                taskDefinition=kwargs.get("taskDefinition")
            )["taskDefinition"]

            is_awsvpc = task_definition.get("networkMode") == "awsvpc"
            containers = []
            for container in task_definition.get("containerDefinitions", []):
                containers.append(
                    {key: value for key, value in container.items() if key in ["name", "image"]}
                )

            network_configuration = kwargs.get("networkConfiguration", {})
            vpc_configuration = network_configuration.get("awsvpcConfiguration")

            if is_awsvpc:
                if not network_configuration:
                    raise StubbedEcsError
                if not vpc_configuration:
                    raise StubbedEcsError

            overrides = kwargs.get("overrides", {})
            cpu = overrides.get("cpu") or task_definition.get("cpu")
            memory = overrides.get("memory") or task_definition.get("memory")
            if not self._valid_cpu_and_memory(cpu=cpu, memory=memory):
                raise StubbedEcsError

            cluster = self._cluster(kwargs.get("cluster"))
            count = kwargs.get("count", 1)
            tasks = []
            for _ in range(count):
                arn = self._task_arn(cluster)
                task = {
                    "attachments": [],
                    "clusterArn": self._cluster_arn(cluster),
                    "containers": containers,
                    "lastStatus": "RUNNING",
                    "overrides": kwargs.get("overrides", {}),
                    "taskArn": arn,
                    "taskDefinitionArn": task_definition["taskDefinitionArn"],
                    "cpu": task_definition["cpu"],
                    "memory": task_definition["memory"],
                }

                if vpc_configuration:
                    for subnet in vpc_configuration["subnets"]:
                        ec2 = boto3.resource("ec2", region_name=self.client.meta.region_name)
                        subnet = ec2.Subnet(subnet)
                        # The provided subnet doesn't exist
                        subnet.load()

                        eni = subnet.create_network_interface()
                        if vpc_configuration.get("assignPublicIp") == "ENABLED":
                            allocation_id = subnet.meta.client.allocate_address(Domain="vpc").get(
                                "AllocationId",
                            )
                            subnet.meta.client.associate_address(
                                NetworkInterfaceId=eni.id,
                                AllocationId=allocation_id,
                            )
                            eni.load()

                        task["attachments"].append(
                            {
                                "type": "ElasticNetworkInterface",
                                "details": [
                                    {"name": "subnetId", "value": subnet.id},
                                    {
                                        "name": "networkInterfaceId",
                                        "value": eni.id,
                                    },
                                ],
                            }
                        )

                tasks.append(task)

            self.stubber.add_response(
                method="run_task",
                service_response={"tasks": tasks},
                expected_params={**kwargs},
            )

            self.tasks[cluster] += tasks
        except (StubbedEcsError, ClientError):
            self.stubber.add_client_error(method="run_task", expected_params={**kwargs})

        return self.client.run_task(**kwargs)

    @stubbed
    def stop_task(self, **kwargs):
        cluster = self._cluster(kwargs.get("cluster"))
        task = kwargs.get("task")
        tasks = self.describe_tasks(tasks=[task], cluster=cluster)["tasks"]

        if tasks:
            stopped_task = tasks[0]
            self.tasks[cluster].remove(tasks[0])
            stopped_task["lastStatus"] = "STOPPED"
            self.tasks[cluster].append(stopped_task)
            self.stubber.add_response(
                method="stop_task",
                service_response={"task": stopped_task},
                expected_params={**kwargs},
            )
        else:
            self.stubber.add_client_error(method="stop_task", expected_params={**kwargs})

        return self.client.stop_task(**kwargs)

    @stubbed
    def tag_resource(self, **kwargs):
        """
        Only task tagging is stubbed; other resources won't work
        """
        tags = kwargs.get("tags")
        arn = kwargs.get("resourceArn")

        if self._task_exists(arn) and self._long_arn_enabled():
            self.stubber.add_response(
                method="tag_resource",
                service_response={},
                expected_params={**kwargs},
            )
            self.tags[arn] = tags
        else:
            self.stubber.add_client_error(method="tag_resource", expected_params={**kwargs})

        return self.client.tag_resource(**kwargs)

    def _task_exists(self, arn):
        for task in itertools.chain.from_iterable(self.tasks.values()):
            if task["taskArn"] == arn:
                return True

        return False

    def _arn(self, resource_type, resource_id):
        return f"arn:aws:ecs:us-east-1:1234567890:{resource_type}/{resource_id}"

    def _cluster(self, cluster):
        return (cluster or "default").split("/")[-1]

    def _cluster_arn(self, cluster):
        return self._arn("cluster", self._cluster(cluster))

    def _task_arn(self, cluster):
        return self._arn("task", f"{self._cluster(cluster)}/{uuid.uuid4()}")

    def _task_definition_arn(self, family, revision):
        return self._arn("task-definition", f"{family}:{revision}")

    def _long_arn_enabled(self):
        settings = self.list_account_settings(effectiveSettings=True)["settings"]
        task_arn_format_setting = [
            setting for setting in settings if setting["name"] == "taskLongArnFormat"
        ][0]
        return task_arn_format_setting["value"] != "disabled"

    def _valid_cpu_and_memory(self, cpu, memory):
        # https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-cpu-memory-error.html
        # {cpu: [memory]}
        constraints = {
            "256": ["512", "1024", "2048"],
            "512": [str(i) for i in range(1024, 4096 + 1, 1024)],
            "1024": [str(i) for i in range(2048, 8192 + 1, 1024)],
            "2048": [str(i) for i in range(4096, 16384 + 1, 1024)],
            "4096": [str(i) for i in range(8192, 30720 + 1, 1024)],
        }
        return bool(memory in constraints.get(cpu, []))
