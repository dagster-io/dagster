import os

import docker
from dagster import check
from dagster.core.launcher.base import (
    CheckRunHealthResult,
    LaunchRunContext,
    RunLauncher,
    WorkerStatus,
)
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.core.storage.tags import DOCKER_IMAGE_TAG
from dagster.grpc.types import ExecuteRunArgs, ResumeRunArgs
from dagster.serdes import ConfigurableClass
from dagster_docker.utils import DOCKER_CONFIG_SCHEMA, validate_docker_config, validate_docker_image

DOCKER_CONTAINER_ID_TAG = "docker/container_id"


class DockerRunLauncher(RunLauncher, ConfigurableClass):
    """Launches runs in a Docker container.

    Args:
        image (Optional[str]): The docker image to be used if the repository does not specify one.
        registry (Optional[Dict[str, str]]): Information for using a non-local docker registry.
            If set, should include ``url``, ``username``, and ``password`` keys.
        env_vars (Optional[List[str]]): The list of environment variables names to forward to the
            docker container.
        network (Optional[str]): Name of the network this container to which to connect the
            launched container at creation time. DEPRECATED, prefer networks
        networks (Optional[List[str]]): List of networks to which to connect the
            launched container at creation time.
        container_kwargs(Optional[Dict[str, Any]]): Additional kwargs to pass into
            containers.create. See https://docker-py.readthedocs.io/en/stable/containers.html
            for the full list of available options.
    """

    def __init__(
        self,
        inst_data=None,
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

    @staticmethod
    def from_config_value(inst_data, config_value):
        return DockerRunLauncher(inst_data=inst_data, **config_value)

    def _get_client(self):
        client = docker.client.from_env()
        if self.registry:
            client.login(
                registry=self.registry["url"],
                username=self.registry["username"],
                password=self.registry["password"],
            )
        return client

    def launch_run(self, context: LaunchRunContext) -> None:

        run = context.pipeline_run

        pipeline_code_origin = context.pipeline_code_origin

        docker_image = pipeline_code_origin.repository_origin.container_image

        if not docker_image:
            docker_image = self.image

        if not docker_image:
            raise Exception("No docker image specified by the instance config or repository")

        validate_docker_image(docker_image)

        if not context.resume_from_failure:
            command = ExecuteRunArgs(
                pipeline_origin=pipeline_code_origin,
                pipeline_run_id=run.run_id,
                instance_ref=self._instance.get_ref(),
            ).get_command_args()
        else:
            command = ResumeRunArgs(
                pipeline_origin=pipeline_code_origin,
                pipeline_run_id=run.run_id,
                instance_ref=self._instance.get_ref(),
            ).get_command_args()

        docker_env = (
            {env_name: os.getenv(env_name) for env_name in self.env_vars} if self.env_vars else {}
        )

        client = self._get_client()

        try:
            container = client.containers.create(
                image=docker_image,
                command=command,
                detach=True,
                environment=docker_env,
                network=self.networks[0] if len(self.networks) else None,
                **self.container_kwargs,
            )

        except docker.errors.ImageNotFound:
            client.images.pull(docker_image)
            container = client.containers.create(
                image=docker_image,
                command=command,
                detach=True,
                environment=docker_env,
                network=self.networks[0] if len(self.networks) else None,
                **self.container_kwargs,
            )

        if len(self.networks) > 1:
            for network_name in self.networks[1:]:
                network = client.networks.get(network_name)
                network.connect(container)

        self._instance.report_engine_event(
            message="Launching run in a new container {container_id} with image {docker_image}".format(
                container_id=container.id,
                docker_image=docker_image,
            ),
            pipeline_run=run,
            cls=self.__class__,
        )

        self._instance.add_run_tags(
            run.run_id,
            {DOCKER_CONTAINER_ID_TAG: container.id, DOCKER_IMAGE_TAG: docker_image},
        )

        container.start()

    def _get_container(self, run):
        if not run or run.is_finished:
            return None

        container_id = run.tags.get(DOCKER_CONTAINER_ID_TAG)

        if not container_id:
            return None

        try:
            return self._get_client().containers.get(container_id)
        except Exception:
            return None

    def can_terminate(self, run_id):
        run = self._instance.get_run_by_id(run_id)
        return self._get_container(run) != None

    def terminate(self, run_id):
        run = self._instance.get_run_by_id(run_id)
        container = self._get_container(run)

        if not container:
            self._instance.report_engine_event(
                message="Unable to get docker container to send termination request to.",
                pipeline_run=run,
                cls=self.__class__,
            )
            return False

        self._instance.report_run_canceling(run)

        container.stop()

        return True

    @property
    def supports_check_run_worker_health(self):
        return True

    def check_run_worker_health(self, run: PipelineRun):
        container = self._get_container(run)
        if container == None:
            return CheckRunHealthResult(WorkerStatus.NOT_FOUND)
        if container.status == "running":
            return CheckRunHealthResult(WorkerStatus.RUNNING)
        return CheckRunHealthResult(
            WorkerStatus.FAILED, msg=f"Container status is {container.status}"
        )
