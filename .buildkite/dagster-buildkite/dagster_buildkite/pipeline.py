import abc
import os
from enum import Enum
from typing import Callable, Dict, List, Optional, Set


class BuildkiteQueue(Enum):
    DOCKER = "docker-p"
    MEDIUM = "buildkite-medium-v5-0-1"
    WINDOWS = "windows-medium"


DOCKER_PLUGIN = "docker#v3.7.0"
ECR_PLUGIN = "ecr#v2.2.0"

AWS_ACCOUNT_ID = os.environ.get("AWS_ACCOUNT_ID")
AWS_ECR_REGION = "us-west-2"

DEFAULT_TIMEOUT_IN_MINUTES = 20
DEFAULT_QUEUE = BuildkiteQueue.MEDIUM


class BuildkitePipeline:
    def __init__(self, steps: Optional[List[BuildkiteStep]] = None):
        self._steps: List[BuildkiteStep] = steps or []

    def with_step(self, step: BuildkiteStep) -> "BuildkitePipeline":
        self._steps.append(step)
        return self

    def build(self) -> Dict:
        return [step.build() for step in self._steps]


class BuildkiteStep(abc.ABC):
    def __init__(self):
        self._dependencies: Set["BuildkiteStep"]

    def with_dependencies(self, dependencies: Set["BuildkiteStep"]) -> "BuildkiteStep":
        self._dependencies = dependencies
        return self

    @abc.abstractmethod
    def build(self) -> Dict:
        ...


class BuildkiteCommandStep(BuildkiteStep):
    def __init__(self):
        super().__init__(self)
        self._commands: List[str] = []
        self._queue: BuildkiteQueue = DEFAULT_QUEUE
        self._retries: int = 0
        self._skip_reason: Optional[str] = None
        self._timeout_in_minutes: int = DEFAULT_TIMEOUT_IN_MINUTES

    def build(self) -> Dict:
        return {
            "agents": {"queue": self._queue},
            "label": self._label,
            "timeout_in_minutes": self._timeout_in_minutes,
            "retry": {
                "automatic": [
                    {"exit_status": -1, "limit": 2},  # agent lost
                    {"exit_status": 255, "limit": 2},  # agent forced shut down
                ],
                "manual": {"permit_on_passed": True},
            },
        }

    def run(self, *commands: str) -> "BuildkitecommandSteps":
        self._commands = ["time " + command for command in commands]
        return self

    def with_queue(self, queue: Optional[BuildkiteQueue]) -> "BuildkiteCommandStep":
        self._queue = queue
        return self

    def with_retry(self, retries: int) -> "BuildkiteCommandStep":
        self._retries = retries
        return self

    def with_skip_if(self, skip_reason: Callable[..., Optional[str]]) -> "BuildCommandStep":
        self._skip_reason = skip_reason()
        return self

    def with_timeout(self, minutes: int) -> "BuildkiteCommandStep":
        self._timeout_in_minutes = minutes
        return self

    # TODO: We may be able to simplify this setup substantially by switching to
    # https://github.com/buildkite-plugins/docker-compose-buildkite-plugin
    def on_python_image(
        self, image: str, env: Optional[List[str]] = None
    ) -> "BuildkiteCommandStep":
        settings = {
            "shell": ["/bin/bash", "-xeuc"],
            "always-pull": True,
            "mount-ssh-agent": True,
        }

        settings["image"] = f"{AWS_ACCOUNT_ID}.dkr.ecr.{AWS_ECR_REGION}.amazonaws.com/{image}"
        # Mount the Docker socket so we can run Docker inside of our container
        # Mount /tmp from the host machine to /tmp in our container. This is
        # useful if you need to mount a volume when running a Docker container;
        # because it's relying on the host machine's Docker socket, it looks
        # for a volume with a matching name on the host machine
        settings["volumes"] = ["/var/run/docker.sock:/var/run/docker.sock", "/tmp:/tmp"]
        settings["network"] = "kind"

        # Pass through all BUILDKITE* envvars so our test analytics are properly tagged
        buildkite_envvars = [env for env in list(os.environ.keys()) if env.startswith("BUILDKITE")]

        # Set PYTEST_DEBUG_TEMPROOT to our mounted /tmp volume. Any time the
        # pytest `tmp_path` or `tmpdir` fixtures are used used, the temporary
        # path they return will be nested under /tmp.
        # https://github.com/pytest-dev/pytest/blob/501637547ecefa584db3793f71f1863da5ffc25f/src/_pytest/tmpdir.py#L116-L117
        settings["environment"] = (
            [
                "PYTEST_DEBUG_TEMPROOT=/tmp",
            ]
            + buildkite_envvars
            + (env or [])
        )
        ecr_settings = {
            "login": True,
            "no-include-email": True,
            "account-ids": AWS_ACCOUNT_ID,
            "region": AWS_ECR_REGION,
            "retries": 2,
        }
        self._step["plugins"] = [{ECR_PLUGIN: ecr_settings}, {DOCKER_PLUGIN: settings}]
        return self
