import uuid
from collections import defaultdict
from operator import itemgetter

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
            return response
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

        self.tasks = defaultdict(list)
        self.task_definitions = defaultdict(list)
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
    def register_task_definition(self, **kwargs):
        family = kwargs.get("family")
        # Revisions are 1 indexed
        revision = len(self.task_definitions[family]) + 1
        arn = self._task_definition_arn(family, revision)

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
            containers = task_definition.get("containerDefinitions", [])

            network_configuration = kwargs.get("networkConfiguration", {})
            vpc_configuration = network_configuration.get("awsvpcConfiguration")
            container_overrides = kwargs.get("overrides", {}).get("containerOverrides", [])

            if is_awsvpc:
                if not network_configuration:
                    raise StubbedEcsError
                if not vpc_configuration:
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
                    "overrides": {"containerOverrides": container_overrides},
                    "taskArn": arn,
                    "taskDefinitionArn": task_definition["taskDefinitionArn"],
                }

                if vpc_configuration:
                    for subnet in vpc_configuration["subnets"]:
                        task["attachments"].append(
                            {
                                "type": "ElasticNetworkInterface",
                                "details": [{"name": "subnetId", "value": subnet}],
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

    def _arn(self, resource_type, resource_id):
        return f"arn:aws:ecs:us-east-1:1234567890:{resource_type}/{resource_id}"

    def _cluster(self, cluster):
        return (cluster or "default").split("/")[-1]

    def _cluster_arn(self, cluster):
        return self._arn("cluster", self._cluster(cluster))

    def _task_arn(self, cluster):
        return self._arn("task", f"{self._cluster(cluster)}/{uuid.uuid4()})")

    def _task_definition_arn(self, family, revision):
        return self._arn("task-definition", f"{family}:{revision}")
