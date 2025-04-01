from pprint import pformat
from typing import TYPE_CHECKING, Any, Optional, Union, cast

import boto3
import botocore
import dagster._check as check
from dagster import DagsterInvariantViolationError, MetadataValue, PipesClient
from dagster._annotations import public
from dagster._core.definitions.metadata import RawMetadataMapping
from dagster._core.definitions.resource_annotation import TreatAsResourceParam
from dagster._core.errors import DagsterExecutionInterruptedError
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._core.execution.context.compute import OpExecutionContext
from dagster._core.pipes.client import (
    PipesClientCompletedInvocation,
    PipesContextInjector,
    PipesMessageReader,
)
from dagster._core.pipes.utils import PipesEnvContextInjector, open_pipes_session

from dagster_aws.pipes.clients.utils import WaiterConfig
from dagster_aws.pipes.message_readers import PipesCloudWatchLogReader, PipesCloudWatchMessageReader

if TYPE_CHECKING:
    from mypy_boto3_ecs.client import ECSClient
    from mypy_boto3_ecs.type_defs import (
        DescribeTasksResponseTypeDef,
        RunTaskRequestTypeDef,
        RunTaskResponseTypeDef,
    )


class PipesECSClient(PipesClient, TreatAsResourceParam):
    """A pipes client for running AWS ECS tasks.

    Args:
        client (Any): The boto ECS client used to launch the ECS task
        context_injector (Optional[PipesContextInjector]): A context injector to use to inject
            context into the ECS task. Defaults to :py:class:`PipesEnvContextInjector`.
        message_reader (Optional[PipesMessageReader]): A message reader to use to read messages
            from the ECS task. Defaults to :py:class:`PipesCloudWatchMessageReader`.
        forward_termination (bool): Whether to cancel the ECS task when the Dagster process receives a termination signal.
    """

    def __init__(
        self,
        client: Optional["ECSClient"] = None,
        context_injector: Optional[PipesContextInjector] = None,
        message_reader: Optional[PipesMessageReader] = None,
        forward_termination: bool = True,
    ):
        self._client: ECSClient = client or boto3.client("ecs")
        self._context_injector = context_injector or PipesEnvContextInjector()
        self._message_reader = message_reader or PipesCloudWatchMessageReader()
        self.forward_termination = check.bool_param(forward_termination, "forward_termination")

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    @public
    def run(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        *,
        context: Union[OpExecutionContext, AssetExecutionContext],
        run_task_params: "RunTaskRequestTypeDef",
        extras: Optional[dict[str, Any]] = None,
        pipes_container_name: Optional[str] = None,
        waiter_config: Optional[WaiterConfig] = None,
    ) -> PipesClientCompletedInvocation:
        """Run ECS tasks, enriched with the pipes protocol.

        Args:
            context (Union[OpExecutionContext, AssetExecutionContext]): The context of the currently executing Dagster op or asset.
            run_task_params (dict): Parameters for the ``run_task`` boto3 ECS client call.
                Must contain ``taskDefinition`` key.
                See `Boto3 API Documentation <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ecs/client/run_task.html#run-task>`_
            extras (Optional[Dict[str, Any]]): Additional information to pass to the Pipes session in the external process.
            pipes_container_name (Optional[str]): If running more than one container in the task,
                and using :py:class:`PipesCloudWatchMessageReader`, specify the container name which will be running Pipes.
            waiter_config (Optional[WaiterConfig]): Optional waiter configuration to use. Defaults to 70 days (Delay: 6, MaxAttempts: 1000000).

        Returns:
            PipesClientCompletedInvocation: Wrapper containing results reported by the external
            process.
        """
        waiter_config = waiter_config or WaiterConfig(Delay=6, MaxAttempts=1000000)

        with open_pipes_session(
            context=context,
            message_reader=self._message_reader,
            context_injector=self._context_injector,
            extras=extras,
        ) as session:
            # we can't be running more than 1 replica of the task
            # because this guarantees multiple Pipes sessions running at the same time
            # which we don't support yet

            if run_task_params.get("count", 1) > 1:
                raise DagsterInvariantViolationError(
                    "Running more than one ECS task is not supported."
                )

            task_definition = run_task_params["taskDefinition"]
            cluster = run_task_params.get("cluster")

            overrides = cast(dict, run_task_params.get("overrides") or {})
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

            run_task_params["overrides"] = (  # pyright: ignore (reportGeneralTypeIssues)
                overrides  # assign in case overrides was created here as an empty dict
            )

            # inject Dagster tags
            tags = list(run_task_params.get("tags", []))
            for key, value in session.default_remote_invocation_info.items():
                tags.append({"key": key, "value": value})
            run_task_params["tags"] = tags

            response = self._client.run_task(**run_task_params)

            if len(response["tasks"]) > 1:
                # this error should never happen, as we're running a single task
                raise DagsterInvariantViolationError(
                    f"Expected to get a single task from response, got multiple: {response['tasks']}"
                )

            task = response["tasks"][0]
            task_arn = task["taskArn"]  # pyright: ignore (reportTypedDictNotRequiredAccess)
            task_id = task_arn.split("/")[-1]
            containers = task["containers"]  # pyright: ignore (reportTypedDictNotRequiredAccess)

            def get_cloudwatch_params(container_name: str) -> Optional[dict[str, str]]:
                """This will either return the log group and stream for the container, or None in case of a bad log configuration."""
                if log_config := log_configurations.get(container_name):
                    if log_config["logDriver"] == "awslogs":
                        log_group = log_config["options"]["awslogs-group"]  # pyright: ignore (reportTypedDictNotRequiredAccess)

                        # stream name is combined from: prefix, container name, task id
                        log_stream = f"{log_config['options']['awslogs-stream-prefix']}/{container_name}/{task_id}"  # pyright: ignore (reportTypedDictNotRequiredAccess)

                        return {"log_group": log_group, "log_stream": log_stream}
                    else:
                        context.log.warning(
                            f"[pipes] Unsupported log driver {log_config['logDriver']} for Pipes container {container_name} in task {task_arn}. Dagster Pipes won't be able to read CloudWatch logs from this container."
                        )
                else:
                    context.log.warning(
                        f"[pipes] log configuration for container {container_name} not found in task definition {task_definition}."
                    )
                return None

            try:
                if (
                    isinstance(self._message_reader, PipesCloudWatchMessageReader)
                    and len(containers) > 1
                    and not pipes_container_name
                ):
                    raise DagsterInvariantViolationError(
                        "When using PipesCloudWatchMessageReader with more than one container, pipes_container_name must be set."
                    )
                elif (
                    isinstance(self._message_reader, PipesCloudWatchMessageReader)
                    and len(containers) == 1
                ):
                    pipes_container_name = containers[0]["name"]  # pyright: ignore (reportTypedDictNotRequiredAccess)

                if isinstance(self._message_reader, PipesCloudWatchMessageReader):
                    pipes_container_name = cast(str, pipes_container_name)

                    params = get_cloudwatch_params(pipes_container_name)

                    if params:
                        # update log group and stream for the message reader
                        # it should start receiving messages shortly after this call
                        session.report_launched({"extras": params})

                # collect logs from all containers

                # TODO: insert container names into the log message
                # right now all logs will be mixed together, which is not very good

                for container in containers:
                    container_name = container["name"]  # pyright: ignore (reportTypedDictNotRequiredAccess)

                    if isinstance(self._message_reader, PipesCloudWatchMessageReader):
                        params = get_cloudwatch_params(container_name)

                        if params:
                            self._message_reader.add_log_reader(
                                PipesCloudWatchLogReader(
                                    client=self._message_reader.client,
                                    log_group=params["log_group"],
                                    log_stream=params["log_stream"],
                                    start_time=int(session.created_at.timestamp() * 1000),
                                    debug_info=f"reader for container {container_name}",
                                ),
                            )

                response = self._wait_for_completion(
                    response, cluster=cluster, waiter_config=waiter_config
                )

                # check for failed containers
                failed_containers = {}

                for task in response["tasks"]:
                    for container in task["containers"]:  # pyright: ignore (reportTypedDictNotRequiredAccess)
                        if container.get("exitCode") not in (0, None):
                            failed_containers[container["runtimeId"]] = container.get("exitCode")  # pyright: ignore (reportTypedDictNotRequiredAccess)

                if failed_containers:
                    raise RuntimeError(
                        f"Some ECS containers finished with non-zero exit code:\n{pformat(list(failed_containers.keys()))}"
                    )

            except DagsterExecutionInterruptedError:
                if self.forward_termination:
                    context.log.warning(
                        "[pipes] Dagster process interrupted, terminating ECS tasks"
                    )
                    self._terminate(context=context, wait_response=response, cluster=cluster)
                raise

        context.log.info(f"[pipes] ECS task {task_arn} completed")
        return PipesClientCompletedInvocation(
            session, metadata=self._extract_dagster_metadata(response)
        )

    def _wait_for_completion(
        self,
        start_response: "RunTaskResponseTypeDef",
        cluster: Optional[str] = None,
        waiter_config: Optional[WaiterConfig] = None,
    ) -> "DescribeTasksResponseTypeDef":
        waiter = self._client.get_waiter("tasks_stopped")

        params: dict[str, Any] = {"tasks": [start_response["tasks"][0]["taskArn"]]}  # pyright: ignore (reportGeneralTypeIssues)

        if cluster:
            params["cluster"] = cluster

        waiter_params = {"WaiterConfig": waiter_config, **params} if waiter_config else params

        waiter.wait(**waiter_params)

        return self._client.describe_tasks(**params)

    def _extract_dagster_metadata(
        self, response: "DescribeTasksResponseTypeDef"
    ) -> RawMetadataMapping:
        metadata: RawMetadataMapping = {}

        region = self._client.meta.region_name

        task = response["tasks"][0]

        task_id = task["taskArn"].split("/")[-1]  # pyright: ignore (reportTypedDictNotRequiredAccess)
        cluster = task["clusterArn"].split("/")[-1]  # pyright: ignore (reportTypedDictNotRequiredAccess)

        metadata["AWS ECS Task URL"] = MetadataValue.url(
            f"https://{region}.console.aws.amazon.com/ecs/v2/clusters/{cluster}/tasks/{task_id}"
        )

        return metadata

    def _terminate(
        self,
        context: Union[OpExecutionContext, AssetExecutionContext],
        wait_response: "DescribeTasksResponseTypeDef",
        cluster: Optional[str] = None,
    ):
        task = wait_response["tasks"][0]

        try:
            self._client.stop_task(
                cluster=cluster,  # pyright: ignore ()
                task=wait_response["tasks"][0]["taskArn"],  # pyright: ignore (reportGeneralTypeIssues)
                reason="Dagster process was interrupted",
            )
        except botocore.exceptions.ClientError as e:  # pyright: ignore (reportAttributeAccessIssue)
            context.log.warning(f"[pipes] Couldn't stop ECS task {task} in cluster {cluster}:\n{e}")
