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

    def set_task(self, **kwargs):
        """Set an ECS Task Definition.

        Args:

        https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_RegisterTaskDefinition.html

        Returns:
            str: The Task Definition ARN
        """
        return self.client.register_task_definition(**kwargs)["taskDefinition"]["taskDefinitionArn"]

    def start_task(self, task_definition):
        """Start a single FARGATE task from task definition.

        Args:
            task_definition (str): The family and revision (family:revision) or full ARN
                of the task definition to run. If a revision is not specified, the
                latest ACTIVE revision is used.

        Returns:
            str: The Task ARN
        """
        return self._start_task(task_definition)

    def run_task(self, task_definition):
        """Synchronously run a single FARGATE task from a task definition until all tasks
        are STOPPED.

        Args:
            task_definition (str): The family and revision (family:revision) or full ARN
                of the task definition to run. If a revision is not specified, the
                latest ACTIVE revision is used.

        Returns:
            None
        """
        task_arn = self._start_task(task_definition)

        tasks = self._poll_until_stopped(task_arn)

        stop_codes = [task.get("stopCode") for task in tasks]
        errors = [stop_code for stop_code in stop_codes if stop_code != "EssentialContainerExited"]
        if any(errors):
            raise ECSError(";".join(errors))

    def stop_task(self, task_arn):
        """Synchronously stop a running task. This method will call ECS StopTask and then
            poll until the task reaches a STOPPED status.

        Args:
            task_arn (str): The Task ARN.

        Returns:
            bool: True if the task stops; False if the task was already stopped.
        """
        try:
            response = self.client.stop_task(cluster=self.cluster, task=task_arn)
        except Exception as e:
            raise ECSError(e)

        if response["task"]["lastStatus"] == "STOPPED":
            return False

        self._poll_until_stopped(task_arn)
        return True

    def _start_task(self, task_definition):
        response = self.client.run_task(
            count=1,
            launchType="FARGATE",
            taskDefinition=task_definition,
            cluster=self.cluster,
            networkConfiguration={
                "awsvpcConfiguration": {"subnets": self.subnets, "assignPublicIp": "ENABLED"}
            },
        )
        return response["tasks"][0]["taskArn"]

    def _poll_until_stopped(self, task_arn):
        retries = self.max_polls
        while retries > 0:
            response = self.client.describe_tasks(cluster=self.cluster, tasks=[task_arn])
            tasks = [task for task in response["tasks"]]

            if all(task["lastStatus"] == "STOPPED" for task in tasks):
                break

            retries -= 1
            time.sleep(self.polling_interval)

        if retries <= 0:
            raise ECSTimeout()

        return tasks


class FakeECSClient(ECSClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.polling_interval = 0
        self.stubber = Stubber(self.client)

    def start_task(self, task_definition):
        self.stubber.activate()

        self._stub_start_task(task_definition)
        result = super().start_task(task_definition)

        self.stubber.deactivate()
        self.stubber.assert_no_pending_responses()

        return result

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

        task_arn = self._stub_start_task(task_definition)
        self._stub_describe_tasks(expected_statuses, expected_stop_code, task_arn)
        super().run_task(task_definition, **kwargs)

        self.stubber.deactivate()
        self.stubber.assert_no_pending_responses()

    def stop_task(self, task_arn, expected_statuses=None):  # pylint: disable=arguments-differ
        """Fake for stop; stubs the expected ECS endpoints and polls against
        the provided expected container statuses until all containers are STOPPED.

        Args:
            task_arn (str): The Task ARN.
            expected_statuses (list[str]): The expected container satuses:
                https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-lifecycle.html
                Defaults to initially RUNNING and then STOPPED.

        Returns:
            bool: True if the task stops; False if the task was already stopped.
        """
        if not expected_statuses:
            expected_statuses = ["RUNNING", "STOPPED"]
        self.stubber.activate()

        self.stubber.add_response(
            method="stop_task",
            service_response={"task": {"lastStatus": expected_statuses.pop(0)}},
            expected_params={"task": task_arn, "cluster": self.cluster},
        )

        for status in expected_statuses:
            self.stubber.add_response(
                method="describe_tasks",
                service_response={"tasks": [{"lastStatus": status}]},
                expected_params={"cluster": self.cluster, "tasks": [task_arn]},
            )

        result = super().stop_task(task_arn)

        self.stubber.deactivate()
        self.stubber.assert_no_pending_responses()

        return result

    def _stub_start_task(self, task_definition):
        task = f"arn:aws:ecs:us-east-2:0123456789:task/{uuid.uuid4()}"

        self.stubber.add_response(
            method="run_task",
            service_response={"tasks": [{"taskArn": task}]},
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

        return task

    def _stub_describe_tasks(self, expected_statuses, expected_stop_code, task_arn):
        for status in expected_statuses:
            self.stubber.add_response(
                method="describe_tasks",
                service_response={
                    "tasks": [{"lastStatus": status, "stopCode": expected_stop_code}]
                },
                expected_params={"cluster": self.cluster, "tasks": [task_arn]},
            )
