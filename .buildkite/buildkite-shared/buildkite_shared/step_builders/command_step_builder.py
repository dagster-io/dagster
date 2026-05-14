import os
from collections.abc import Callable, Mapping, Sequence
from enum import StrEnum
from typing import Any, Self

from buildkite_shared.python_version import AvailablePythonVersion
from buildkite_shared.step_builders.slug import make_label
from buildkite_shared.utils import BUILDKITE_TEST_IMAGE_VERSION, RETRYABLE_INFRA_FAILURE_EXIT_CODE
from typing_extensions import NotRequired, TypedDict

DEFAULT_TIMEOUT_IN_MIN = 35

DOCKER_PLUGIN = "docker#v5.10.0"
ECR_PLUGIN = "ecr#v2.7.0"
SM_PLUGIN = "seek-oss/aws-sm#v2.3.1"
BASE_IMAGE_NAME = "buildkite-test"
BASE_IMAGE_TAG = "2026-05-04T142331"
BUILDKITE_TEST_IMAGE_PY_SLIM = "buildkite-test-image-py-slim:prod-1777949196"

AWS_ACCOUNT_ID = os.getenv("AWS_ACCOUNT_ID")
AWS_ECR_REGION = "us-west-2"


class ResourceRequests:
    def __init__(
        self,
        cpu: str,
        *,
        memory: str | None = None,
        docker_cpu: str = "2000m",
        docker_memory: str = "1Gi",
        docker_memory_limit: str = "2Gi",
        ephemeral_storage: str | None = None,
    ) -> None:
        self._cpu = cpu
        self._memory = memory
        self._docker_cpu = docker_cpu
        self._docker_memory = docker_memory
        self._docker_memory_limit = docker_memory_limit
        self._ephemeral_storage = ephemeral_storage

    @property
    def cpu(self) -> str:
        return self._cpu

    @property
    def memory(self) -> str | None:
        return self._memory

    @property
    def docker_cpu(self) -> str:
        return self._docker_cpu

    @property
    def docker_memory(self) -> str:
        return self._docker_memory

    @property
    def docker_memory_limit(self) -> str:
        return self._docker_memory_limit

    @property
    def ephemeral_storage(self) -> str | None:
        return self._ephemeral_storage


class BuildkiteQueue(StrEnum):
    KUBERNETES_GKE = os.getenv("BUILDKITE_KUBERNETES_QUEUE_GKE", "kubernetes-gke")
    KUBERNETES_EKS = os.getenv("BUILDKITE_KUBERNETES_QUEUE_EKS", "kubernetes-eks")
    DOCKER = os.getenv("BUILDKITE_DOCKER_QUEUE", "buildkite-docker-october22")
    MEDIUM = os.getenv("BUILDKITE_MEDIUM_QUEUE", "buildkite-medium-october22")
    WINDOWS = os.getenv("BUILDKITE_WINDOWS_QUEUE", "buildkite-windows-october22")

    @classmethod
    def contains(cls, value: str) -> bool:
        return isinstance(value, cls)


class CommandStepConfiguration(TypedDict, closed=True):
    agents: dict[str, str]
    label: str
    timeout_in_minutes: int
    plugins: list[dict[str, object]]
    retry: dict[str, object]
    commands: NotRequired[list[str]]
    depends_on: NotRequired[list[str]]
    key: NotRequired[str]
    skip: NotRequired[str | None]
    artifact_paths: NotRequired[list[str]]
    concurrency: NotRequired[int]
    concurrency_group: NotRequired[str]
    allow_dependency_failure: NotRequired[bool]
    soft_fail: NotRequired[bool]
    # Covers the "if" key, which is a Python reserved word and cannot be used as
    # a class attribute. Buildkite uses "if" for conditional step execution.
    __extra_items__: str


class CommandStepBuilder:
    _step: CommandStepConfiguration

    def __init__(
        self,
        key: str,
        label_emojis: list[str] | None = None,
        *,
        timeout_in_minutes: int = DEFAULT_TIMEOUT_IN_MIN,
        retry_automatically: bool = True,
        plugins: list[dict[str, object]] | None = None,
    ) -> None:
        self._secrets = {}
        self._k8s_secrets = []
        self._k8s_volume_mounts = []
        self._k8s_volumes = []
        self._docker_settings = None

        retry: dict[str, Any] = {
            "manual": {"permit_on_passed": True},
        }

        if retry_automatically:
            # This list contains exit codes that should map only to ephemeral infrastructure issues.
            # Normal test failures (exit code 1), make command failures (exit code 2) and the like
            # should not be included here. Our shell wrappers may exit with
            # RETRYABLE_INFRA_FAILURE_EXIT_CODE (200) to escalate a known-transient failure
            # (e.g. ECR login, pip/uv install) to a fresh-job retry.
            retry["automatic"] = [
                # https://buildkite.com/docs/agent/v3#exit-codes
                {"exit_status": -1, "limit": 2},  # agent lost
                {
                    "exit_status": -10,
                    "limit": 2,
                },  # example: https://buildkite.com/dagster/internal/builds/108316#0196fd13-d816-42e7-bf26-b264385b245d
                {
                    "exit_status": 94,
                    "limit": 2,
                },  # checkout failed (e.g. git-mirror clone lock timeout)
                {"exit_status": 125, "limit": 2},  # docker daemon error
                {"exit_status": 128, "limit": 2},  # k8s git clone error
                {"exit_status": 130, "limit": 2},  # SIGINT (e.g. spot reclamation)
                {"exit_status": 143, "limit": 2},  # agent lost
                {"exit_status": 255, "limit": 2},  # agent forced shut down
                {
                    "exit_status": RETRYABLE_INFRA_FAILURE_EXIT_CODE,
                    "limit": 2,
                },  # our shell wrappers signaling a transient infra failure
                {
                    "exit_status": 28,
                    "limit": 2,
                },  # node ran out of space, try to reschedule
                {
                    "signal_reason": "agent_stop",
                    "limit": 2,
                },  # agent stopped (e.g. spot eviction, pod termination)
            ]

        self._step = {
            "agents": {"queue": BuildkiteQueue.MEDIUM.value},
            "key": key,
            "label": make_label(key, label_emojis),
            "timeout_in_minutes": timeout_in_minutes,
            "retry": retry,
            "plugins": plugins or [],
        }
        # Default off: most steps don't need a docker daemon (lints, type-checkers,
        # k8s manifests, helm, kaniko image builds, dashboard publishing). Steps that
        # actually invoke `docker compose`/`docker build`/`docker pull` opt in via
        # `.with_docker()`. Off-by-default avoids attaching a privileged dind sidecar
        # — which costs scheduling resources and is the kubelet's first eviction
        # target under fan-out memory pressure — to steps that don't need one.
        self._requires_docker = False  # used for k8s queue; opt in via .with_docker()
        self._resources = None

    def run(self, *argc: str) -> Self:
        self._step["commands"] = list(argc)
        return self

    def resources(self, resources: ResourceRequests | None) -> Self:
        self._resources = resources
        return self

    def with_docker(self) -> Self:
        self._requires_docker = True
        return self

    def on_python_image(
        self,
        image: str,
        *,
        env: list[str] | None = None,
        account_id: str | None = AWS_ACCOUNT_ID,
        region: str = AWS_ECR_REGION,
    ) -> Self:
        settings = self._base_docker_settings(env)
        settings["image"] = f"{account_id}.dkr.ecr.{region}.amazonaws.com/{image}"
        settings["network"] = "kind"
        self._docker_settings = settings
        return self

    def on_specific_image(
        self, image: str, extra_docker_plugin_args: dict[str, object] = {}
    ) -> Self:
        settings = {"image": image, **extra_docker_plugin_args}
        if self._docker_settings:
            self._docker_settings.update(settings)
        else:
            self._docker_settings = settings
        return self

    def on_test_image(
        self,
        ver: str = AvailablePythonVersion.get_cloud().value,
        image_version: str = BUILDKITE_TEST_IMAGE_VERSION,
        env: list[str] | None = None,
    ) -> Self:
        return self.on_python_image(
            image=f"buildkite-test:py{ver}-{image_version}",
            env=env,
        ).with_ecr_login()

    def on_integration_slim_image(self, env: list[str] | None = None) -> Self:
        return self.on_python_image(
            image=BUILDKITE_TEST_IMAGE_PY_SLIM,
            env=env,
        )

    def on_integration_image(
        self,
        ver: str = AvailablePythonVersion.get_cloud().value,
        env: list[str] | None = None,
        image_name: str = BASE_IMAGE_NAME,
        image_version: str = BASE_IMAGE_TAG,
        ecr_account_ids: list[str | None] = [AWS_ACCOUNT_ID],
    ) -> Self:
        return self.on_python_image(
            image=f"{image_name}:py{ver}-{image_version}",
            env=env,
        ).with_ecr_login(ecr_account_ids)

    def with_ecr_login(self, ecr_account_ids: list[str | None] = [AWS_ACCOUNT_ID]) -> Self:
        assert "plugins" in self._step
        self._step["plugins"].append(
            {
                ECR_PLUGIN: {
                    "login": True,
                    "no-include-email": True,
                    "account_ids": ecr_account_ids,
                    "region": "us-west-2",
                }
            }
        )
        return self

    def with_ecr_passthru(self) -> Self:
        assert self._docker_settings
        assert self._docker_settings["environment"]
        assert self._docker_settings["volumes"]
        self._docker_settings["environment"] = [
            *self._docker_settings["environment"],
            "BUILDKITE_DOCKER_CONFIG_TEMP_DIRECTORY",
            "DOCKER_CONFIG=/tmp/.docker",
        ]
        self._docker_settings["volumes"] = list(
            set(
                [
                    *[v for v in self._docker_settings["volumes"]],
                    # share auth with the docker buildkite-test
                    "$$BUILDKITE_DOCKER_CONFIG_TEMP_DIRECTORY/config.json:/tmp/.docker/config.json",
                ]
            )
        )
        return self

    def with_artifact_paths(self, *paths: str) -> Self:
        if "artifact_paths" not in self._step:
            self._step["artifact_paths"] = []
        self._step["artifact_paths"].extend(paths)
        return self

    def with_condition(self, condition: str) -> Self:
        self._step["if"] = condition  # pyright: ignore[reportGeneralTypeIssues]
        return self

    def with_secret(self, name: str, reference: str) -> Self:
        self._secrets[name] = reference
        return self

    def with_timeout(self, num_minutes: int | None) -> Self:
        if num_minutes is not None:
            self._step["timeout_in_minutes"] = num_minutes
        return self

    def on_queue(self, queue: BuildkiteQueue) -> Self:
        self._step["agents"]["queue"] = queue.value
        return self

    def with_kubernetes_secret(self, secret: str) -> Self:
        self._k8s_secrets.append(secret)
        return self

    def with_kubernetes_volume(self, volume: dict[str, Any]) -> Self:
        self._k8s_volumes.append(volume)
        return self

    def with_kubernetes_volume_mount(self, volume_mount: dict[str, Any]) -> Self:
        self._k8s_volume_mounts.append(volume_mount)
        return self

    def concurrency(self, limit: int) -> Self:
        self._step["concurrency"] = limit
        return self

    def concurrency_group(self, concurrency_group_name: str) -> Self:
        self._step["concurrency_group"] = concurrency_group_name
        return self

    def depends_on(self, dependencies: str | Sequence[str] | None) -> Self:
        if dependencies is not None:
            self._step["depends_on"] = (
                [dependencies] if isinstance(dependencies, str) else list(dependencies)
            )
        return self

    def allow_dependency_failure(self) -> Self:
        self._step["allow_dependency_failure"] = True
        return self

    def soft_fail(self, fail: bool = True) -> Self:
        self._step["soft_fail"] = fail
        return self

    def skip(self, skip_reason: str | None = None) -> Self:
        self._step["skip"] = skip_reason
        return self

    def _get_resources(self) -> dict[str, object]:
        cpu = (
            self._resources.cpu
            if self._resources
            else ("1000m" if self._requires_docker else "500m")
        )
        memory = self._resources.memory if self._resources else None
        default_ephemeral_storage = "10Gi" if self._requires_docker else "5Gi"
        ephemeral_storage = (
            self._resources.ephemeral_storage if self._resources else None
        ) or default_ephemeral_storage
        return {
            "requests": {
                "cpu": cpu,
                "memory": memory,
                "ephemeral-storage": ephemeral_storage,
            },
        }

    def _base_docker_settings(self, env: list[str] | None = None) -> dict[str, object]:
        return {
            "shell": ["/bin/bash", "-xeuc"],
            "mount-ssh-agent": True,
            "propagate-environment": False,
            "expand-volume-vars": True,
            "volumes": ["/var/run/docker.sock:/var/run/docker.sock", "/tmp:/tmp"],
            "environment": [
                "PYTEST_ADDOPTS",
                "PYTEST_PLUGINS",
                "BUILDKITE",
                "BUILDKITE_BUILD_CHECKOUT_PATH",
                "BUILDKITE_BUILD_URL",
                "BUILDKITE_ORGANIZATION_SLUG",
                "BUILDKITE_PIPELINE_SLUG",
                "BUILDKITE_ANALYTICS_TOKEN",
                "BUILDKITE_TEST_QUARANTINE_TOKEN",
                "BUILDKITE_TEST_SUITE_SLUG",
                # Buildkite uses this to tag tests in Test Engine
                "BUILDKITE_BRANCH",
                "BUILDKITE_COMMIT",
                "BUILDKITE_MESSAGE",
            ]
            + [
                # these are exposed via the ECR plugin and then threaded through
                # to kubernetes. see https://github.com/buildkite-plugins/ecr-buildkite-plugin
                "AWS_SECRET_ACCESS_KEY",
                "AWS_ACCESS_KEY_ID",
                "AWS_SESSION_TOKEN",
                "AWS_REGION",
                "AWS_ACCOUNT_ID",
                "UV_DEFAULT_INDEX",
            ]
            + [
                # needed by our own stuff
                "DAGSTER_INTERNAL_GIT_REPO_DIR",
                "DAGSTER_GIT_REPO_DIR",
                "COMBINED_COMMIT_HASH",
                "DAGSTER_COMMIT_HASH",
                "INTERNAL_COMMIT_HASH",
            ]
            + [
                # tox related env variables. ideally these are in
                # the test specification themselves, but for now this is easier
                "AWS_DEFAULT_REGION",
                "SNOWFLAKE_ACCOUNT",
                "SNOWFLAKE_USER",
                "SNOWFLAKE_PASSWORD",
            ]
            + ["PYTEST_DEBUG_TEMPROOT=/tmp"]
            + (env or []),
            "mount-buildkite-agent": True,
        }

    def _base_k8s_settings(self) -> Mapping[Any, Any]:
        buildkite_shell = "/bin/bash -e -c"
        assert self._docker_settings
        image = str(self._docker_settings["image"])
        if image == "hashicorp/terraform:light" or "/datadog-ci:" in image or "/alpine:" in image:
            buildkite_shell = "/bin/sh -e -c"
        elif "kaniko-project/executor" in image:
            buildkite_shell = "/busybox/sh -e -c"

        sidecars = []
        if self._requires_docker:
            # Determine docker image based on queue (GKE vs EKS)
            queue = self._step.get("agents", {}).get("queue", "")
            is_gke = "gke" in queue
            if is_gke:
                docker_image = "us-central1-docker.pkg.dev/dagster-production/buildkite-images/docker:28.5.2-dind"
            else:
                docker_image = "public.ecr.aws/docker/library/docker:28.5.2-dind"

            # Bump max-concurrent-downloads/uploads from default 3 to 10 to
            # parallelize layer pulls. The dockerd-entrypoint.sh of the
            # docker:dind image execs `dockerd` with whatever args are
            # passed, so these forward through cleanly.
            dind_args = [
                "--max-concurrent-downloads=10",
                "--max-concurrent-uploads=10",
            ]
            if not is_gke:
                # Route docker.io pulls through the in-cluster Docker Hub
                # mirror to avoid Docker Hub 5xx flakes and rate limits. The
                # mirror is a `registry:2` Deployment in the buildkite-agent
                # namespace; see infra/k8s/buildkite/overlays/buildkite-eks/
                # dockerhub-mirror.yaml. dockerd transparently falls back to
                # registry-1.docker.io if the mirror is unreachable.
                dind_args.append(
                    "--registry-mirror=http://dockerhub-mirror.buildkite-agent.svc.cluster.local:5000"
                )

            sidecars.append(
                {
                    "image": docker_image,
                    "command": ["dockerd-entrypoint.sh"],
                    "args": dind_args,
                    # Memory request/limit promote the dind sidecar from
                    # BestEffort to Burstable QoS, so it isn't the first
                    # container the kubelet evicts when a node is under
                    # memory pressure during fan-out waves. Without this,
                    # docker API calls (`containers.create` etc.) can hang
                    # for minutes mid-test before the SDK's read timeout
                    # fires — see test_docker_launcher.py flakes.
                    "resources": {
                        "requests": {
                            "cpu": self._resources.docker_cpu if self._resources else "2000m",
                            "memory": self._resources.docker_memory if self._resources else "1Gi",
                        },
                        "limits": {
                            "memory": self._resources.docker_memory_limit
                            if self._resources
                            else "2Gi",
                        },
                    },
                    "env": [
                        {
                            "name": "DOCKER_TLS_CERTDIR",
                            "value": "",
                        },
                    ],
                    "volumeMounts": [
                        {
                            "mountPath": "/var/run",
                            "name": "docker-sock",
                        }
                    ],
                    "securityContext": {
                        "privileged": True,
                        "allowPrivilegeEscalation": True,
                    },
                    # Block main containers from starting until dockerd is
                    # actually responding to API calls. agent-stack-k8s only
                    # gates main-container startup on the sidecar's "Started"
                    # signal, which fires once dockerd's binary is running but
                    # not necessarily once the daemon is accepting connections.
                    # `docker info` round-trips to dockerd over the socket, so
                    # it catches the window between bind() (where the socket
                    # file appears) and listen()/accept() — a window that
                    # `test -S /var/run/docker.sock` was passing through,
                    # letting test code race ahead and hit "Cannot connect to
                    # the Docker daemon" when invoking `docker compose up`.
                    "startupProbe": {
                        "exec": {"command": ["docker", "info"]},
                        "periodSeconds": 1,
                        "failureThreshold": 30,
                        "timeoutSeconds": 5,
                    },
                }
            )
            self._k8s_volumes.append(
                {
                    "name": "docker-sock",
                    "emptyDir": {},
                }
            )
            self._k8s_volume_mounts.append(
                {
                    "mountPath": "/var/run/",
                    "name": "docker-sock",
                },
            )

        return {
            "gitEnvFrom": [{"secretRef": {"name": "git-ssh-credentials"}}],
            "mirrorVolumeMounts": True,
            "sidecars": sidecars,
            "podSpec": {
                "serviceAccountName": "buildkite-job",
                "containers": [
                    {
                        "image": self._docker_settings["image"],
                        "env": [
                            {
                                "name": "BUILDKITE_SHELL",
                                "value": buildkite_shell,
                            },
                            # {
                            #     "name": "UV_DEFAULT_INDEX",
                            #     "value": "http://devpi.buildkite-agent.svc.cluster.local/root/pypi",
                            # },
                            {
                                "name": "POD_NAME",
                                "valueFrom": {"fieldRef": {"fieldPath": "metadata.name"}},
                            },
                            {
                                "name": "NODE_NAME",
                                "valueFrom": {"fieldRef": {"fieldPath": "spec.nodeName"}},
                            },
                            {
                                "name": "INTERNAL_BUILDKITE_TEST_ANALYTICS_TOKEN",
                                "valueFrom": {
                                    "secretKeyRef": {
                                        "name": "buildkite-dagster-secrets",
                                        "key": "INTERNAL_BUILDKITE_TEST_ANALYTICS_TOKEN",
                                    }
                                },
                            },
                            {
                                "name": "INTERNAL_BUILDKITE_STEP_ANALYTICS_TOKEN",
                                "valueFrom": {
                                    "secretKeyRef": {
                                        "name": "buildkite-dagster-secrets",
                                        "key": "INTERNAL_BUILDKITE_STEP_ANALYTICS_TOKEN",
                                    }
                                },
                            },
                            {
                                "name": "DOGFOOD_BUILDKITE_STEP_ANALYTICS_TOKEN",
                                "valueFrom": {
                                    "secretKeyRef": {
                                        "name": "buildkite-dagster-secrets",
                                        "key": "DOGFOOD_BUILDKITE_STEP_ANALYTICS_TOKEN",
                                    }
                                },
                            },
                        ],
                        "envFrom": [
                            {"secretRef": {"name": "buildkite-dagster-secrets"}},
                            {"secretRef": {"name": "honeycomb-api-key"}},
                            *[
                                {"secretRef": {"name": secret_name}}
                                for secret_name in self._k8s_secrets
                            ],
                        ],
                        "resources": self._get_resources(),
                        "volumeMounts": self._k8s_volume_mounts,
                        "securityContext": {"capabilities": {"add": ["SYS_PTRACE"]}},
                    },
                ],
                "volumes": self._k8s_volumes,
            },
        }

    def build(self) -> CommandStepConfiguration:
        assert "agents" in self._step
        on_k8s = self._step["agents"]["queue"] in (
            BuildkiteQueue.KUBERNETES_GKE,
            BuildkiteQueue.KUBERNETES_EKS,
        )
        # Note: `self._requires_docker` is k8s-only. On non-k8s queues docker is
        # provided by the host agent regardless of the flag, so we don't gate.

        if not on_k8s and self._k8s_secrets:
            raise Exception(
                "Specified a kubernetes secret on a non-kubernetes queue. Please call .on_queue(BuildkiteQueue.KUBERNETES_GKE) or .on_queue(BuildkiteQueue.KUBERNETES_EKS) if you want to run on k8s"
            )

        if on_k8s:
            # for k8s we take the image that we were going to run in docker
            # and instead launch it as a pod directly on k8s. to do this
            # we need to patch the image that buildkite will actually run
            # during the test step to match. `buildkite-agent bootstrap` (which
            # is the entrypoint that ends up getting run (via some volume mounting
            # magic) depends on a BUILDKITE_SHELL variable to actually execute
            # the specified command (like "terraform fmt -check -recursive"). some
            # images require /bin/bash, others don't have it, so there's some setting
            # munging done below as well.
            if self._docker_settings:
                self._step["plugins"] = [{"kubernetes": self._base_k8s_settings()}]

            return self._step

        # adding SM and DOCKER plugin in build allows secrets to be passed to docker envs
        assert "plugins" in self._step
        self._step["plugins"].append({SM_PLUGIN: {"region": "us-west-1", "env": self._secrets}})
        if self._docker_settings:
            for secret in self._secrets.keys():
                self._docker_settings["environment"].append(secret)

            # we need to dedup the env vars to make sure that the ones we set
            # aren't overridden by the ones that are already set in the parent env
            # the last one wins
            envvar_map = {}
            for ev in self._docker_settings.get("environment", []):
                k, v = ev.split("=") if "=" in ev else (ev, None)
                envvar_map[k] = v
            self._docker_settings["environment"] = [
                f"{k}={v}" if v is not None else k for k, v in envvar_map.items()
            ]
            assert "plugins" in self._step
            self._step["plugins"].append({DOCKER_PLUGIN: self._docker_settings})
        return self._step


StepBuilderMutator = Callable[[CommandStepBuilder], CommandStepBuilder]
