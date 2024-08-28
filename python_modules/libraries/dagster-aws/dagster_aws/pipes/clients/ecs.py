from pprint import pformat
from typing import TYPE_CHECKING, Any, Dict, List, Optional, cast

import boto3
import botocore
import dagster._check as check
from dagster import PipesClient
from dagster._annotations import experimental, public
from dagster._core.definitions.resource_annotation import TreatAsResourceParam
from dagster._core.errors import DagsterExecutionInterruptedError
from dagster._core.execution.context.compute import OpExecutionContext
from dagster._core.pipes.client import (
    PipesClientCompletedInvocation,
    PipesContextInjector,
    PipesMessageReader,
)
from dagster._core.pipes.utils import PipesEnvContextInjector, open_pipes_session

from dagster_aws.pipes.message_readers import PipesCloudWatchMessageReader

if TYPE_CHECKING:
    from mypy_boto3_ecs.client import ECSClient
    from mypy_boto3_ecs.type_defs import RunTaskRequestRequestTypeDef


@experimental
class PipesECSClient(PipesClient, TreatAsResourceParam):
    """A pipes client for running AWS ECS tasks.

    Args:
        client (Optional[boto3.client]): The boto ECS client used to launch the ECS task
        context_injector (Optional[PipesContextInjector]): A context injector to use to inject
            context into the ECS task. Defaults to :py:class:`PipesEnvContextInjector`.
        message_reader (Optional[PipesMessageReader]): A message reader to use to read messages
            from the ECS task. Defaults to :py:class:`PipesCloudWatchMessageReader`.
        forward_termination (bool): Whether to cancel the ECS task when the Dagster process receives a termination signal.
    """

    def __init__(
        self,
        client: Optional[boto3.client] = None,  # pyright: ignore (reportGeneralTypeIssues)
        context_injector: Optional[PipesContextInjector] = None,
        message_reader: Optional[PipesMessageReader] = None,
        forward_termination: bool = True,
    ):
        self._client: "ECSClient" = client or boto3.client("ecs")
        self._context_injector = context_injector or PipesEnvContextInjector()
        self._message_reader = message_reader or PipesCloudWatchMessageReader()
        self.forward_termination = check.bool_param(forward_termination, "forward_termination")

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    @public
    def run(
        self,
        *,
        context: OpExecutionContext,
        run_task_params: "RunTaskRequestRequestTypeDef",
        extras: Optional[Dict[str, Any]] = None,
    ) -> PipesClientCompletedInvocation:
        """Run ECS tasks, enriched with the pipes protocol.

        Args:
            context (OpExecutionContext): The context of the currently executing Dagster op or asset.
            run_task_params (dict): Parameters for the ``run_task`` boto3 ECS client call.
                Must contain ``taskDefinition`` key.
                See `Boto3 API Documentation <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ecs/client/run_task.html#run-task>`_
            extras (Optional[Dict[str, Any]]): Additional information to pass to the Pipes session in the external process.

        Returns:
            PipesClientCompletedInvocation: Wrapper containing results reported by the external
            process.
        """
        with open_pipes_session(
            context=context,
            message_reader=self._message_reader,
            context_injector=self._context_injector,
            extras=extras,
        ) as session:
            params = run_task_params

            task_definition = params["taskDefinition"]
            cluster = params.get("cluster")

            overrides = cast(dict, params.get("overrides") or {})
            overrides["containerOverrides"] = overrides.get("containerOverrides", [])

            # get all containers from task definition
            task_definition_response = self._client.describe_task_definition(
                taskDefinition=task_definition
            )

            log_configurations = {
                container["name"]: container.get("logConfiguration")  # pyright: ignore (reportTypedDictNotRequiredAccess)
                for container in task_definition_response["taskDefinition"]["containerDefinitions"]  # pyright: ignore (reportTypedDictNotRequiredAccess)
            }

            all_container_names = {
                container["name"]  # pyright: ignore (reportTypedDictNotRequiredAccess)
                for container in task_definition_response["taskDefinition"]["containerDefinitions"]  # pyright: ignore (reportTypedDictNotRequiredAccess)
            }

            container_names_with_overrides = {
                container_override["name"] for container_override in overrides["containerOverrides"]
            }

            pipes_args = session.get_bootstrap_env_vars()

            # set env variables for every container in the taskDefinition
            # respecting current overrides provided by the user

            environment_overrides = [
                {
                    "name": k,
                    "value": v,
                }
                for k, v in pipes_args.items()
            ]

            # set environment variables for existing overrides

            for container_override in overrides["containerOverrides"]:
                container_override["environment"] = container_override.get("environment", [])
                container_override["environment"].extend(environment_overrides)

            # set environment variables for containers that are not in the overrides
            for container_name in all_container_names - container_names_with_overrides:
                overrides["containerOverrides"].append(
                    {
                        "name": container_name,
                        "environment": environment_overrides,
                    }
                )

            params["overrides"] = (  # pyright: ignore (reportGeneralTypeIssues)
                overrides  # assign in case overrides was created here as an empty dict
            )

            response = self._client.run_task(**params)

            tasks: List[str] = [task["taskArn"] for task in response["tasks"]]  # pyright: ignore (reportTypedDictNotRequiredAccess)

            try:
                response = self._wait_for_tasks_completion(tasks=tasks, cluster=cluster)

                # collect logs from all containers
                for task in response["tasks"]:
                    task_id = task["taskArn"].split("/")[-1]

                    for container in task["containers"]:
                        if log_config := log_configurations.get(container["name"]):
                            if log_config["logDriver"] == "awslogs":
                                log_group = log_config["options"]["awslogs-group"]  # pyright: ignore (reportTypedDictNotRequiredAccess)

                                # stream name is combined from: prefix, container name, task id
                                log_stream = f"{log_config['options']['awslogs-stream-prefix']}/{container['name']}/{task_id}"  # pyright: ignore (reportTypedDictNotRequiredAccess)

                                if isinstance(self._message_reader, PipesCloudWatchMessageReader):
                                    self._message_reader.consume_cloudwatch_logs(
                                        log_group,
                                        log_stream,
                                        start_time=int(task["createdAt"].timestamp() * 1000),
                                    )
                            else:
                                context.log.warning(
                                    f"[pipes] Unsupported log driver {log_config['logDriver']} for container {container['name']} in task {task['taskArn']}. Dagster Pipes won't be able to receive messages from this container."
                                )

                # check for failed containers
                failed_containers = {}

                for task in response["tasks"]:
                    for container in task["containers"]:
                        if container.get("exitCode") not in (0, None):
                            failed_containers[container["runtimeId"]] = container.get("exitCode")

                if failed_containers:
                    raise RuntimeError(
                        f"Some ECS containers finished with non-zero exit code:\n{pformat(list(failed_containers.keys()))}"
                    )

            except DagsterExecutionInterruptedError:
                if self.forward_termination:
                    context.log.warning(
                        "[pipes] Dagster process interrupted, terminating ECS tasks"
                    )
                    self._terminate_tasks(context=context, tasks=tasks, cluster=cluster)
                raise

            context.log.info(f"[pipes] ECS tasks {tasks} completed")

        return PipesClientCompletedInvocation(session)

    def _wait_for_tasks_completion(
        self, tasks: List[str], cluster: Optional[str] = None
    ) -> Dict[str, Any]:
        waiter = self._client.get_waiter("tasks_stopped")

        params: Dict[str, Any] = {"tasks": tasks}

        if cluster:
            params["cluster"] = cluster

        waiter.wait(**params)
        return self._client.describe_tasks(**params)  # pyright: ignore (reportReturnType)

    def _terminate_tasks(
        self, context: OpExecutionContext, tasks: List[str], cluster: Optional[str] = None
    ):
        for task in tasks:
            try:
                self._client.stop_task(
                    cluster=cluster,  # pyright: ignore ()
                    task=task,
                    reason="Dagster process was interrupted",
                )
            except botocore.exceptions.ClientError as e:  # pyright: ignore (reportAttributeAccessIssue)
                context.log.warning(
                    f"[pipes] Couldn't stop ECS task {task} in cluster {cluster}:\n{e}"
                )
