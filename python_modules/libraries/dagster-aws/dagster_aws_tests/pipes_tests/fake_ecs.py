import sys
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from subprocess import PIPE, Popen
from typing import Optional, cast

import boto3
import botocore


@dataclass
class SimulatedTaskRun:
    popen: Popen
    cluster: str
    task_arn: str
    log_group: str
    log_stream: str
    created_at: datetime
    runtime_id: str
    stopped_reason: Optional[str] = None
    stopped: bool = False
    logs_uploaded: bool = False


class LocalECSMockClient:
    CONTAINER_NAME = "test-container"

    def __init__(self, ecs_client: boto3.client, cloudwatch_client: boto3.client):  # pyright: ignore (reportGeneralTypeIssues)
        self.ecs_client = ecs_client
        self.cloudwatch_client = cloudwatch_client

        self._task_runs: dict[
            str, SimulatedTaskRun
        ] = {}  # mapping of TaskDefinitionArn to TaskDefinition

    @property
    def meta(self):
        return self.ecs_client.meta

    def get_waiter(self, waiter_name: str):
        return WaiterMock(self, waiter_name)

    def register_task_definition(self, **kwargs):
        return self.ecs_client.register_task_definition(**kwargs)

    def describe_task_definition(self, **kwargs):
        response = self.ecs_client.describe_task_definition(**kwargs)
        assert (
            len(response["taskDefinition"]["containerDefinitions"]) == 1
        ), "Only 1 container is supported in tests"
        # unlike real ECS, moto doesn't use cloudwatch logging by default
        # so let's add it here
        response["taskDefinition"]["containerDefinitions"][0]["logConfiguration"] = (
            response["taskDefinition"]["containerDefinitions"][0].get("logConfiguration")
            or {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": f"{response['taskDefinition']['taskDefinitionArn']}",  # this value doesn't really matter
                    "awslogs-stream-prefix": "ecs",
                },
            }
        )
        return response

    def run_task(self, **kwargs):
        response = self.ecs_client.run_task(**kwargs)

        # inject container name in case it's missing
        response["tasks"][0]["containers"] = response["tasks"][0].get("containers") or []

        if len(response["tasks"][0]["containers"]) == 0:
            response["tasks"][0]["containers"].append({})

        response["tasks"][0]["containers"][0]["name"] = (
            response["tasks"][0]["containers"][0].get("name") or self.CONTAINER_NAME
        )

        task_arn = response["tasks"][0]["taskArn"]
        task_definition_arn = response["tasks"][0]["taskDefinitionArn"]

        task_definition = self.describe_task_definition(taskDefinition=task_definition_arn)[
            "taskDefinition"
        ]

        assert (
            len(task_definition["containerDefinitions"]) == 1
        ), "Only 1 container is supported in tests"

        # execute in a separate process
        command = task_definition["containerDefinitions"][0]["command"]

        assert (
            command[0] == sys.executable
        ), "Only the current Python interpreter is supported in tests"

        created_at = datetime.now()

        popen = Popen(
            command,
            stdout=PIPE,
            stderr=PIPE,
            # get env from container overrides
            env={
                env["name"]: env["value"]
                for env in kwargs["overrides"]["containerOverrides"][0].get("environment", [])
            },
        )

        log_group = task_definition["containerDefinitions"][0]["logConfiguration"]["options"][
            "awslogs-group"
        ]
        stream_prefix = task_definition["containerDefinitions"][0]["logConfiguration"]["options"][
            "awslogs-stream-prefix"
        ]
        container_name = task_definition["containerDefinitions"][0]["name"]
        log_stream = f"{stream_prefix}/{container_name}/{task_arn.split('/')[-1]}"

        self._task_runs[task_arn] = SimulatedTaskRun(
            popen=popen,
            cluster=kwargs.get("cluster", "default"),
            task_arn=task_arn,
            log_group=log_group,
            log_stream=log_stream,
            created_at=created_at,
            runtime_id=str(uuid.uuid4()),
        )

        self._create_cloudwatch_streams(task_arn)

        return response

    def describe_tasks(self, cluster: str, tasks: list[str]):
        assert len(tasks) == 1, "Only 1 task is supported in tests"

        simulated_task = cast(SimulatedTaskRun, self._task_runs[tasks[0]])

        response = self.ecs_client.describe_tasks(cluster=cluster, tasks=tasks)

        assert len(response["tasks"]) == 1, "Only 1 task is supported in tests"

        task_definition = self.describe_task_definition(
            taskDefinition=response["tasks"][0]["taskDefinitionArn"]
        )["taskDefinition"]

        assert (
            len(task_definition["containerDefinitions"]) == 1
        ), "Only 1 container is supported in tests"

        # need to inject container name since moto doesn't return it

        response["tasks"][0]["containers"].append(
            {
                "name": task_definition["containerDefinitions"][0]["name"],
                "runtimeId": simulated_task.runtime_id,
            }
        )

        response["tasks"][0]["createdAt"] = simulated_task.created_at

        # check if any failed
        for task in response["tasks"]:
            if task["taskArn"] in self._task_runs:
                simulated_task = self._task_runs[task["taskArn"]]

                if simulated_task.stopped:
                    task["lastStatus"] = "STOPPED"
                    task["stoppedReason"] = simulated_task.stopped_reason
                    task["containers"][0]["exitCode"] = 1
                    self._upload_logs_to_cloudwatch(task["taskArn"])
                    return response

                if simulated_task.popen.poll() is not None:
                    simulated_task.popen.wait()
                    # check status code
                    if simulated_task.popen.returncode == 0:
                        task["lastStatus"] = "STOPPED"
                        task["containers"][0]["exitCode"] = 0
                    else:
                        task["lastStatus"] = "STOPPED"
                        # _, stderr = simulated_task.popen.communicate()
                        task["containers"][0]["exitCode"] = 1

                    self._upload_logs_to_cloudwatch(task["taskArn"])

                else:
                    task["lastStatus"] = "RUNNING"

        return response

    def stop_task(self, cluster: str, task: str, reason: Optional[str] = None):
        if simulated_task := self._task_runs.get(task):
            simulated_task.popen.terminate()
            simulated_task.stopped = True
            simulated_task.stopped_reason = reason
            self._upload_logs_to_cloudwatch(task)
        else:
            raise RuntimeError(f"Task {task} was not found")

    def _create_cloudwatch_streams(self, task: str):
        simulated_task = self._task_runs[task]

        log_group = simulated_task.log_group
        log_stream = simulated_task.log_stream

        try:
            self.cloudwatch_client.create_log_group(
                logGroupName=f"{log_group}",
            )
        except self.cloudwatch_client.exceptions.ResourceAlreadyExistsException:
            pass

        try:
            self.cloudwatch_client.create_log_stream(
                logGroupName=f"{log_group}",
                logStreamName=log_stream,
            )
        except self.cloudwatch_client.exceptions.ResourceAlreadyExistsException:
            pass

    def _upload_logs_to_cloudwatch(self, task: str):
        simulated_task = self._task_runs[task]

        if simulated_task.logs_uploaded:
            return

        log_group = simulated_task.log_group
        log_stream = simulated_task.log_stream

        stdout, stderr = self._task_runs[task].popen.communicate()

        for out in [stderr, stdout]:
            for line in out.decode().split("\n"):
                if line:
                    self.cloudwatch_client.put_log_events(
                        logGroupName=f"{log_group}",
                        logStreamName=log_stream,
                        logEvents=[{"timestamp": int(time.time() * 1000), "message": str(line)}],
                    )

        time.sleep(0.1)

        simulated_task.logs_uploaded = True


class WaiterMock:
    def __init__(self, client: LocalECSMockClient, waiter_name: str):
        self.client = client
        self.waiter_name = waiter_name

    def wait(self, **kwargs):
        waiter_config = kwargs.pop("WaiterConfig", {"MaxAttempts": 100, "Delay": 6})
        max_attempts = int(waiter_config.get("MaxAttempts", 100))
        delay = int(waiter_config.get("Delay", 6))
        num_attempts = 0

        if self.waiter_name == "tasks_stopped":
            while True:
                response = self.client.describe_tasks(**kwargs)
                num_attempts += 1

                if all(task["lastStatus"] == "STOPPED" for task in response["tasks"]):
                    return

                if num_attempts >= max_attempts:
                    raise botocore.exceptions.WaiterError(  # pyright: ignore[reportAttributeAccessIssue]
                        name=self.waiter_name,
                        reason="Max attempts exceeded",
                        last_response=response,
                    )

                time.sleep(delay)

        else:
            raise NotImplementedError(f"Waiter {self.waiter_name} is not implemented")
