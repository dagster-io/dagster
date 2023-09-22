from typing import Any, Mapping, Optional

import dagster._check as check
import docker
from dagster._core.launcher.base import (
    CheckRunHealthResult,
    LaunchRunContext,
    ResumeRunContext,
    RunLauncher,
    WorkerStatus,
)
from dagster._core.storage.dagster_run import DagsterRun
from dagster._core.storage.tags import DOCKER_IMAGE_TAG
from dagster._core.utils import parse_env_var
from dagster._grpc.types import ExecuteRunArgs, ResumeRunArgs
from dagster._serdes import ConfigurableClass
from dagster._serdes.config_class import ConfigurableClassData
from typing_extensions import Self

from dagster_docker.utils import DOCKER_CONFIG_SCHEMA, validate_docker_config, validate_docker_image

from .container_context import DockerContainerContext

DOCKER_CONTAINER_ID_TAG = "docker/container_id"


class DockerRunLauncher(RunLauncher, ConfigurableClass):
    """Launches runs in a Docker container."""

    def __init__(
        self,
        inst_data: Optional[ConfigurableClassData] = None,
        image=None,
        registry=None,
        env_vars=None,
        network=None,
        networks=None,
        container_kwargs=None,
    ):
        self._inst_data = inst_data
        self.image = image
        self.registry = registry
        self.env_vars = env_vars

        validate_docker_config(network, networks, container_kwargs)

        if network:
            self.networks = [network]
        elif networks:
            self.networks = networks
        else:
            self.networks = []

        self.container_kwargs = check.opt_dict_param(
            container_kwargs, "container_kwargs", key_type=str
        )

        super().__init__()

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return DOCKER_CONFIG_SCHEMA

    @classmethod
    def from_config_value(
        cls, inst_data: ConfigurableClassData, config_value: Mapping[str, Any]
    ) -> Self:
        return DockerRunLauncher(inst_data=inst_data, **config_value)

    def get_container_context(self, dagster_run: DagsterRun) -> DockerContainerContext:
        return DockerContainerContext.create_for_run(dagster_run, self)

    def _get_client(self, container_context: DockerContainerContext):
        client = docker.client.from_env()
        if container_context.registry:
            client.login(
                registry=container_context.registry["url"],
                username=container_context.registry["username"],
                password=container_context.registry["password"],
            )
        return client

    def _get_docker_image(self, job_code_origin):
        docker_image = job_code_origin.repository_origin.container_image

        if not docker_image:
            docker_image = self.image

        if not docker_image:
            raise Exception("No docker image specified by the instance config or repository")

        validate_docker_image(docker_image)
        return docker_image

    def _launch_container_with_command(self, run, docker_image, command):
        container_context = self.get_container_context(run)
        docker_env = dict([parse_env_var(env_var) for env_var in container_context.env_vars])
        docker_env["DAGSTER_RUN_JOB_NAME"] = run.job_name

        client = self._get_client(container_context)

        try:
            container = client.containers.create(
                image=docker_image,
                command=command,
                detach=True,
                environment=docker_env,
                network=container_context.networks[0] if len(container_context.networks) else None,
                **container_context.container_kwargs,
            )

        except docker.errors.ImageNotFound:
            client.images.pull(docker_image)
            container = client.containers.create(
                image=docker_image,
                command=command,
                detach=True,
                environment=docker_env,
                network=container_context.networks[0] if len(container_context.networks) else None,
                **container_context.container_kwargs,
            )

        if len(container_context.networks) > 1:
            for network_name in container_context.networks[1:]:
                network = client.networks.get(network_name)
                network.connect(container)

        self._instance.report_engine_event(
            message=f"Launching run in a new container {container.id} with image {docker_image}",
            dagster_run=run,
            cls=self.__class__,
        )

        self._instance.add_run_tags(
            run.run_id,
            {DOCKER_CONTAINER_ID_TAG: container.id, DOCKER_IMAGE_TAG: docker_image},
        )

        container.start()

    def launch_run(self, context: LaunchRunContext) -> None:
        run = context.dagster_run
        job_code_origin = check.not_none(context.job_code_origin)
        docker_image = self._get_docker_image(job_code_origin)

        command = ExecuteRunArgs(
            job_origin=job_code_origin,
            run_id=run.run_id,
            instance_ref=self._instance.get_ref(),
        ).get_command_args()

        self._launch_container_with_command(run, docker_image, command)

    @property
    def supports_resume_run(self):
        return True

    def resume_run(self, context: ResumeRunContext) -> None:
        run = context.dagster_run
        job_code_origin = check.not_none(context.job_code_origin)
        docker_image = self._get_docker_image(job_code_origin)

        command = ResumeRunArgs(
            job_origin=job_code_origin,
            run_id=run.run_id,
            instance_ref=self._instance.get_ref(),
        ).get_command_args()

        self._launch_container_with_command(run, docker_image, command)

    def _get_container(self, run):
        if not run or run.is_finished:
            return None

        container_id = run.tags.get(DOCKER_CONTAINER_ID_TAG)

        if not container_id:
            return None

        container_context = self.get_container_context(run)

        try:
            return self._get_client(container_context).containers.get(container_id)
        except Exception:
            return None

    def terminate(self, run_id):
        run = self._instance.get_run_by_id(run_id)

        if not run:
            return False

        self._instance.report_run_canceling(run)

        container = self._get_container(run)

        if not container:
            self._instance.report_engine_event(
                message="Unable to get docker container to send termination request to.",
                dagster_run=run,
                cls=self.__class__,
            )
            return False

        container.stop()

        return True

    @property
    def supports_check_run_worker_health(self):
        return True

    def check_run_worker_health(self, run: DagsterRun):
        container = self._get_container(run)
        if container is None:
            return CheckRunHealthResult(WorkerStatus.NOT_FOUND)
        if container.status == "running":
            return CheckRunHealthResult(WorkerStatus.RUNNING)
        return CheckRunHealthResult(
            WorkerStatus.FAILED, msg=f"Container status is {container.status}"
        )
