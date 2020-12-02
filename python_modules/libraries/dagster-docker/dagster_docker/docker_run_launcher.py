import json
import os
import sys
import weakref

import docker
from dagster import Field, StringSource, check
from dagster.core.host_representation import ExternalPipeline
from dagster.core.instance import DagsterInstance
from dagster.core.launcher.base import RunLauncher
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.grpc.types import ExecuteRunArgs
from dagster.serdes import ConfigurableClass, serialize_dagster_namedtuple
from dagster.utils.error import serializable_error_info_from_exc_info

DOCKER_CONTAINER_ID_TAG = "docker_container_id"


class DockerRunLauncher(RunLauncher, ConfigurableClass):
    """Launches runs in a Docker container.

        image (Optional[str]): The docker image to be used if the repository does not specify one.
        registry (Optional[Dict[str, str]]): Information for using a non-local docker registry.
            If set, should include ``url``, ``username``, and ``password`` keys.
        env_vars (Optional[List[str]]): The list of environment variables names to forward to the
            docker container.
        network (Optional[str]): Name of the network this container to which to connect the
            launched container at creation time.
"""

    def __init__(self, inst_data=None, image=None, registry=None, env_vars=None, network=None):
        self._instance_weakref = None
        self._inst_data = inst_data
        self._image = image
        self._registry = registry
        self._env_vars = env_vars
        self._network = network

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {
            "image": Field(
                StringSource,
                is_required=False,
                description="The docker image to be used if the repository does not specify one.",
            ),
            "registry": Field(
                {
                    "url": Field(StringSource),
                    "username": Field(StringSource),
                    "password": Field(StringSource),
                },
                is_required=False,
                description="Information for using a non local/public docker registry",
            ),
            "env_vars": Field(
                [str],
                is_required=False,
                description="The list of environment variables names to forward to the docker container",
            ),
            "network": Field(
                str,
                is_required=False,
                description="Name of the network this container to which to connect the launched container at creation time",
            ),
        }

    @staticmethod
    def from_config_value(inst_data, config_value):
        return DockerRunLauncher(inst_data=inst_data, **config_value)

    @property
    def _instance(self):
        return self._instance_weakref() if self._instance_weakref else None

    def initialize(self, instance):
        check.inst_param(instance, "instance", DagsterInstance)
        check.invariant(self._instance is None, "Must only call initialize once")
        # Store a weakref to avoid a circular reference / enable GC
        self._instance_weakref = weakref.ref(instance)

    def _get_client(self):
        client = docker.client.from_env()
        if self._registry:
            client.login(
                registry=self._registry["url"],
                username=self._registry["username"],
                password=self._registry["password"],
            )
        return client

    def launch_run(self, instance, run, external_pipeline):
        check.inst_param(run, "run", PipelineRun)
        check.inst_param(external_pipeline, "external_pipeline", ExternalPipeline)

        docker_image = external_pipeline.get_python_origin().repository_origin.container_image

        if not docker_image:
            docker_image = self._image

        if not docker_image:
            raise Exception("No docker image specified by the instance config or repository")

        input_json = serialize_dagster_namedtuple(
            ExecuteRunArgs(
                pipeline_origin=external_pipeline.get_python_origin(),
                pipeline_run_id=run.run_id,
                instance_ref=instance.get_ref(),
            )
        )

        command = "dagster api execute_run_with_structured_logs {}".format(json.dumps(input_json))

        docker_env = (
            {env_name: os.getenv(env_name) for env_name in self._env_vars} if self._env_vars else {}
        )

        client = self._get_client()

        print("LOADED DOCKER CLIENT")

        try:
            container = client.containers.create(
                image=docker_image,
                command=command,
                detach=True,
                environment=docker_env,
                network=self._network,
            )

            print("FOUND IMAGE AND CREATED CONTAINER")
        except docker.errors.ImageNotFound:
            print("IMAGE NOT FOUND, PULLING IMAGE")

            client.images.pull(docker_image)

            print("IMAGE PULLED CREATING CONTAINER")

            container = client.containers.create(
                image=docker_image,
                command=command,
                detach=True,
                environment=docker_env,
                network=self._network,
            )

            print("CREATED CONTAINER")

        self._instance.add_run_tags(
            run.run_id, {DOCKER_CONTAINER_ID_TAG: container.id},
        )

        print("STARTING CONTAINER WITH ID: " + str(container.id))

        container.start()

        #        print("STARTED CONTAINER, LOGS????")

        #        out = container.logs(stream=True, follow=True)

        #        for line in out:
        #            print("LOG: " + str(line))

        #        print("NOW WIATING, WAITING!")

        #        exit_status = container.wait()["StatusCode"]

        #        print("EXIT STATUS: " + str(exit_status))

        return run

    def _get_container(self, run):
        if not run or run.is_finished:
            return None

        container_id = run.tags.get(DOCKER_CONTAINER_ID_TAG)

        if not container_id:
            return None

        try:
            return self._get_client().containers.get(container_id)
        except:
            print(
                "Error loading container: "
                + str(serializable_error_info_from_exc_info(sys.exc_info()))
            )
            return None

    def can_terminate(self, run_id):
        run = self._instance.get_run_by_id(run_id)
        return self._get_container(run) != None

    def terminate(self, run_id):
        run = self._instance.get_run_by_id(run_id)
        container = self._get_container(run)

        self._instance.report_engine_event(
            message="Received pipeline termination request.", pipeline_run=run, cls=self.__class__
        )

        if not container:
            return False

        container.stop()

        return True
