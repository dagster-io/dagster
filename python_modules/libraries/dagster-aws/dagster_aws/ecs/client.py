import time
import uuid

from botocore.stub import Stubber
from dagster import check


class ECSError(Exception):
    pass


class ECSTimeout(ECSError):
    pass


class ECSClient:
    def __init__(self, client, cluster, subnets, polling_interval=5, max_polls=120):
        check.invariant(
            polling_interval >= 0, "polling_interval must be greater than or equal to 0"
        )
        check.invariant(max_polls > 0, "max_polls must be greater than 0")
        self.client = client
        self.cluster = cluster
        self.subnets = subnets
        self.max_polls = max_polls
        self.polling_interval = polling_interval

    def run_task(self, task_definition):
        """Synchronously run a task definition on ECS.

        Args:
            task_definition (str): The family and revision (family:revision) or full ARN
                of the task definition to run. If a revision is not specified, the
                latest ACTIVE revision is used.

        Returns:
            None
        """
        response = self.client.run_task(
            count=1,
            launchType="FARGATE",
            taskDefinition=task_definition,
            cluster=self.cluster,
            networkConfiguration={
                "awsvpcConfiguration": {"subnets": self.subnets, "assignPublicIp": "ENABLED"}
            },
        )
        task_arns = [task["taskArn"] for task in response["tasks"]]

        retries = self.max_polls
        while retries > 0:
            response = self.client.describe_tasks(cluster=self.cluster, tasks=task_arns)
            tasks = [task for task in response["tasks"]]

            if all(task["lastStatus"] == "STOPPED" for task in tasks):
                break

            retries -= 1
            time.sleep(self.polling_interval)

        if retries <= 0:
            raise ECSTimeout()

        stop_codes = [task.get("stopCode") for task in tasks]
        errors = [stop_code for stop_code in stop_codes if stop_code != "EssentialContainerExited"]
        if any(errors):
            raise ECSError(";".join(errors))


class FakeECSClient(ECSClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.polling_interval = 0
        self.stubber = Stubber(self.client)
        self.tasks = [f"arn:aws:ecs:us-east-2:0123456789:task/{uuid.uuid4()}"]

    def run_task(
        self,
        task_definition,
        expected_statuses=None,
        expected_stop_code="EssentialContainerExited",
        **kwargs,
    ):  # pylint: disable=arguments-differ
        """Fake for run_task; stubs the expected ECS endpoints and polls against
        the provided expected container statuses until all containers are STOPPED.

        Args:
            task_definition (str): The family and revision (family:revision) or full ARN
                of the task definition to run. If a revision is not specified, the
                latest ACTIVE revision is used.
            expected_statuses (list[str]): The expected container satuses:
                https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-lifecycle.html
                Defaults to successfully passing through PROVISIONING, RUNNING, and
                STOPPED.
            expected_stop_code (str): The expected Stopped Task Error Code:
                https://docs.aws.amazon.com/AmazonECS/latest/userguide/stopped-task-error-codes.html
                Defaults to EssentialContainerExited; the fake container successfully runs
                to completion before reaching the STOPPED status.

        Returns:
            None
        """
        if not expected_statuses:
            expected_statuses = ["PROVISIONING", "RUNNING", "STOPPED"]

        self.stubber.activate()

        self._stub_run_task(task_definition)
        self._stub_describe_tasks(expected_statuses, expected_stop_code)
        super().run_task(task_definition, **kwargs)

        self.stubber.deactivate()
        self.stubber.assert_no_pending_responses()

    def _stub_run_task(self, task_definition):
        self.stubber.add_response(
            method="run_task",
            service_response={"tasks": [{"taskArn": task} for task in self.tasks]},
            expected_params={
                "count": 1,
                "launchType": "FARGATE",
                "taskDefinition": task_definition,
                "cluster": self.cluster,
                "networkConfiguration": {
                    "awsvpcConfiguration": {"subnets": self.subnets, "assignPublicIp": "ENABLED"}
                },
            },
        )

    def _stub_describe_tasks(self, expected_statuses, expected_stop_code):
        for status in expected_statuses:
            self.stubber.add_response(
                method="describe_tasks",
                service_response={
                    "tasks": [{"lastStatus": status, "stopCode": expected_stop_code}]
                },
                expected_params={"cluster": self.cluster, "tasks": self.tasks},
            )
