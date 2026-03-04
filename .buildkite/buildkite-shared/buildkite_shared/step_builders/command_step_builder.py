import os
from collections.abc import Callable, Mapping
from enum import Enum
from typing import Any

from typing_extensions import NotRequired, TypedDict

DEFAULT_TIMEOUT_IN_MIN = 35

DOCKER_PLUGIN = "docker#v5.10.0"
ECR_PLUGIN = "ecr#v2.7.0"
SM_PLUGIN = "seek-oss/aws-sm#v2.3.1"

# Update this when updated in main repo
SUPPORTED_PYTHON_VERSION = "3.12"
BASE_IMAGE_NAME = "buildkite-test"
BASE_IMAGE_TAG = "2024-07-17T120716"

AWS_ACCOUNT_ID = os.getenv("AWS_ACCOUNT_ID")
AWS_ECR_REGION = "us-west-2"

ECR_LOGIN_FAILURE_EXIT_CODE = 200


class ResourceRequests:
    def __init__(self, cpu, memory, docker_cpu: str = "500m"):
        self._cpu = cpu
        self._memory = memory
        self._docker_cpu = docker_cpu

    @property
    def cpu(self):
        return self._cpu

    @property
    def memory(self):
        return self._memory

    @property
    def docker_cpu(self):
        return self._docker_cpu


class BuildkiteQueue(Enum):
    KUBERNETES_GKE = os.getenv("BUILDKITE_KUBERNETES_QUEUE_GKE", "kubernetes-gke")
    KUBERNETES_EKS = os.getenv("BUILDKITE_KUBERNETES_QUEUE_EKS", "kubernetes-eks")
    DOCKER = os.getenv("BUILDKITE_DOCKER_QUEUE", "buildkite-docker-october22")
    MEDIUM = os.getenv("BUILDKITE_MEDIUM_QUEUE") or "buildkite-medium-october22"
    WINDOWS = os.getenv("BUILDKITE_WINDOWS_QUEUE") or "buildkite-windows-october22"

    @classmethod
    def contains(cls, value):
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
        label,
        key: str | None = None,
        timeout_in_minutes: int = DEFAULT_TIMEOUT_IN_MIN,
        retry_automatically: bool = True,
        plugins: list[dict[str, object]] | None = None,
    ):
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
            # should not be included here.
            retry["automatic"] = [
                # https://buildkite.com/docs/agent/v3#exit-codes
                {"exit_status": -1, "limit": 2},  # agent lost
                {
                    "exit_status": -10,
                    "limit": 2,
                },  # example: https://buildkite.com/dagster/internal/builds/108316#0196fd13-d816-42e7-bf26-b264385b245d
                {"exit_status": 125, "limit": 2},  # docker daemon error
                {"exit_status": 128, "limit": 2},  # k8s git clone error
                {"exit_status": 143, "limit": 2},  # agent lost
                {"exit_status": 255, "limit": 2},  # agent forced shut down
                {
                    "exit_status": ECR_LOGIN_FAILURE_EXIT_CODE,
                    "limit": 2,
                },  # ecr login failed
                {
                    "exit_status": 28,
                    "limit": 2,
                },  # node ran out of space, try to reschedule
            ]

        self._step = {
            "agents": {"queue": BuildkiteQueue.MEDIUM.value},
            "label": label,
            "timeout_in_minutes": timeout_in_minutes,
            "retry": retry,
            "plugins": plugins or [],
        }
        self._requires_docker = True  # used for k8s queue
        if key is not None:
            self._step["key"] = key
        self._resources = None

    def run(self, *argc):
        self._step["commands"] = list(argc)
        return self

    def resources(self, resources: ResourceRequests | None) -> "CommandStepBuilder":
        self._resources = resources
        return self

    def no_docker(self) -> "CommandStepBuilder":
        self._requires_docker = False
        return self

    def on_python_image(
        self,
        image,
        env=None,
        account_id=AWS_ACCOUNT_ID,
        region=AWS_ECR_REGION,
    ):
        settings = self._base_docker_settings(env)
        settings["image"] = f"{account_id}.dkr.ecr.{region}.amazonaws.com/{image}"
        settings["network"] = "kind"
        self._docker_settings = settings
        return self

    def on_specific_image(self, image, extra_docker_plugin_args={}):
        settings = {"image": image, **extra_docker_plugin_args}
        if self._docker_settings:
            self._docker_settings.update(settings)
        else:
            self._docker_settings = settings
        return self

    def on_integration_slim_image(self, env=None):
        return self.on_python_image(
            image="buildkite-test-image-py-slim:prod-1749737887",
            env=env,
        )

    def on_integration_image(
        self,
        ver=SUPPORTED_PYTHON_VERSION,
        env=None,
        image_name=BASE_IMAGE_NAME,
        image_version=BASE_IMAGE_TAG,
        ecr_account_ids=[AWS_ACCOUNT_ID],
    ):
        return self.on_python_image(
            image=f"{image_name}:py{ver}-{image_version}",
            env=env,
        ).with_ecr_login(ecr_account_ids)

    def with_ecr_login(self, ecr_account_ids=[AWS_ACCOUNT_ID]):
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

    def with_ecr_passthru(self) -> "CommandStepBuilder":
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

    def with_artifact_paths(self, *paths):
        if "artifact_paths" not in self._step:
            self._step["artifact_paths"] = []
        self._step["artifact_paths"].extend(paths)
        return self

    def with_condition(self, condition):
        self._step["if"] = condition  # pyright: ignore[reportGeneralTypeIssues]
        return self

    def with_secret(self, name, reference):
        self._secrets[name] = reference
        return self

    def with_timeout(self, num_minutes):
        self._step["timeout_in_minutes"] = num_minutes
        return self

    def with_retry(self, num_retries):
        # Update default retry config to blanket limit with num_retries
        if num_retries is not None and num_retries > 0:
            self._step["retry"]["automatic"] = {"limit": num_retries}

        return self

    def on_queue(self, queue: BuildkiteQueue):
        self._step["agents"]["queue"] = queue.value
        return self

    def with_kubernetes_secret(self, secret: str) -> "CommandStepBuilder":
        self._k8s_secrets.append(secret)
        return self

    def with_kubernetes_volume(self, volume: dict[str, Any]) -> "CommandStepBuilder":
        self._k8s_volumes.append(volume)
        return self

    def with_kubernetes_volume_mount(self, volume_mount: dict[str, Any]) -> "CommandStepBuilder":
        self._k8s_volume_mounts.append(volume_mount)
        return self

    def concurrency(self, limit):
        self._step["concurrency"] = limit
        return self

    def concurrency_group(self, concurrency_group_name):
        self._step["concurrency_group"] = concurrency_group_name
        return self

    def depends_on(self, dependencies):
        self._step["depends_on"] = dependencies
        return self

    def allow_dependency_failure(self):
        self._step["allow_dependency_failure"] = True
        return self

    def soft_fail(self, fail: bool = True):
        self._step["soft_fail"] = fail
        return self

    def skip(self, skip_reason: str | None = None):
        self._step["skip"] = skip_reason
        return self

    def _get_resources(self):
        cpu = (
            self._resources.cpu
            if self._resources
            else ("1500m" if self._requires_docker else "500m")
        )
        memory = self._resources.memory if self._resources else None
        return {
            "requests": {
                "cpu": cpu,
                "memory": memory,
                "ephemeral-storage": ("10Gi" if self._requires_docker else "5Gi"),
            },
        }

    def _base_docker_settings(self, env=None):
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
                "DAGSTER_BRANCH",
            ]
            + [
                # tox related env variables. ideally these are in
                # the test specification themselves, but for now this is easier
                "DD_DOGSTATSD_DISABLE",
                "AWS_DEFAULT_REGION",
                "TOYS_SNOWFLAKE_ACCOUNT",
                "TOYS_SNOWFLAKE_PASSWORD",
                "TOYS_BIGQUERY_PROJECT",
                "TOYS_BIGQUERY_CREDENTIALS",
                "TOYS_GCP_PRIVATE_KEY_ID",
                "TOYS_GCP_PRIVATE_KEY",
                "TOYS_GCP_CLIENT_EMAIL",
                "TOYS_GCP_CLIENT_ID",
                "TOYS_GCP_CLIENT_CERT_URL",
                "SNOWFLAKE_ACCOUNT",
                "SNOWFLAKE_USER",
                "SNOWFLAKE_PASSWORD",
                "DAGSTER_SERVERLESS_AWS_ACCOUNT_ID",
                "DAGSTER_SERVERLESS_SERVICE_NAME",
                "DAGSTER_SERVERLESS_AWS_ACCOUNT_NAME",
                "DAGSTER_SERVERLESS_SUBNETS_PER_VPC",
            ]
            + [
                "DATADOG_API_KEY",
                "FOSSA_API_KEY",
            ]
            + ["PYTEST_DEBUG_TEMPROOT=/tmp"]
            + (env or []),
            "mount-buildkite-agent": True,
        }

    def _base_k8s_settings(self) -> Mapping[Any, Any]:
        buildkite_shell = "/bin/bash -e -c"
        assert self._docker_settings
        if self._docker_settings["image"] == "hashicorp/terraform:light":
            buildkite_shell = "/bin/sh -e -c"

        sidecars = []
        if self._requires_docker:
            # Determine docker image based on queue (GKE vs EKS)
            queue = self._step.get("agents", {}).get("queue", "")
            if "gke" in queue:
                docker_image = "us-central1-docker.pkg.dev/dagster-production/buildkite-images/docker:20.10.16-dind"
            else:
                docker_image = "public.ecr.aws/docker/library/docker:20.10.16-dind"

            sidecars.append(
                {
                    "image": docker_image,
                    "command": ["dockerd-entrypoint.sh"],
                    "resources": {
                        "requests": {
                            "cpu": self._resources.docker_cpu if self._resources else "500m"
                        }
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
                            *(
                                [{"secretRef": {"name": "aws-creds"}}]
                                if self._step.get("agents", {}).get("queue")
                                == BuildkiteQueue.KUBERNETES_GKE.value
                                else []
                            ),
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

    def build(self):
        assert "agents" in self._step
        on_k8s = self._step["agents"]["queue"] in (
            BuildkiteQueue.KUBERNETES_GKE.value,
            BuildkiteQueue.KUBERNETES_EKS.value,
        )
        if self._requires_docker is False and not on_k8s:
            raise Exception("you specified .no_docker() but you're not running on kubernetes")

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
