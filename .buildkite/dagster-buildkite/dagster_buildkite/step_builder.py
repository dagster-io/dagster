import os
from enum import Enum
from typing import Dict, List, Optional

from .images.versions import BUILDKITE_TEST_IMAGE_VERSION
from .python_version import AvailablePythonVersion
from .utils import CommandStep

DEFAULT_TIMEOUT_IN_MIN = 20

DOCKER_PLUGIN = "docker#v3.7.0"
ECR_PLUGIN = "ecr#v2.2.0"


AWS_ACCOUNT_ID = os.environ.get("AWS_ACCOUNT_ID")
AWS_ECR_REGION = "us-west-2"


class BuildkiteQueue(Enum):
    DOCKER = "docker-p"
    MEDIUM = "buildkite-medium-v5-0-1"
    WINDOWS = "windows-medium"

    @classmethod
    def contains(cls, value: object) -> bool:
        return isinstance(value, cls)


class CommandStepBuilder:

    _step: CommandStep

    def __init__(
        self,
        label: str,
        key: Optional[str] = None,
        timeout_in_minutes: int = DEFAULT_TIMEOUT_IN_MIN,
    ):
        self._step = {
            "agents": {"queue": BuildkiteQueue.MEDIUM.value},
            "label": label,
            "timeout_in_minutes": timeout_in_minutes,
            "retry": {
                "automatic": [
                    {"exit_status": -1, "limit": 2},  # agent lost
                    {"exit_status": 255, "limit": 2},  # agent forced shut down
                ],
                "manual": {"permit_on_passed": True},
            },
        }
        if key is not None:
            self._step["key"] = key

    def run(self, *commands: str) -> "CommandStepBuilder":
        self._step["commands"] = ["time " + cmd for cmd in commands]
        return self

    def _base_docker_settings(self) -> Dict[str, object]:
        return {
            "shell": ["/bin/bash", "-xeuc"],
            "always-pull": True,
            "mount-ssh-agent": True,
        }

    def on_python_image(self, image: str, env: Optional[List[str]] = None) -> "CommandStepBuilder":
        settings = self._base_docker_settings()
        settings["image"] = f"{AWS_ACCOUNT_ID}.dkr.ecr.{AWS_ECR_REGION}.amazonaws.com/{image}"
        # Mount the Docker socket so we can run Docker inside of our container
        # Mount /tmp from the host machine to /tmp in our container. This is
        # useful if you need to mount a volume when running a Docker container;
        # because it's relying on the host machine's Docker socket, it looks
        # for a volume with a matching name on the host machine
        settings["volumes"] = ["/var/run/docker.sock:/var/run/docker.sock", "/tmp:/tmp"]
        settings["network"] = "kind"
        # Set PYTEST_DEBUG_TEMPROOT to our mounted /tmp volume. Any time the
        # pytest `tmp_path` or `tmpdir` fixtures are used used, the temporary
        # path they return will be nested under /tmp.
        # https://github.com/pytest-dev/pytest/blob/501637547ecefa584db3793f71f1863da5ffc25f/src/_pytest/tmpdir.py#L116-L117
        settings["environment"] = ["BUILDKITE", "PYTEST_DEBUG_TEMPROOT=/tmp"] + (env or [])
        ecr_settings = {
            "login": True,
            "no-include-email": True,
            "account-ids": AWS_ACCOUNT_ID,
            "region": AWS_ECR_REGION,
            "retries": 2,
        }
        self._step["plugins"] = [{ECR_PLUGIN: ecr_settings}, {DOCKER_PLUGIN: settings}]
        return self

    def on_test_image(
        self, ver: AvailablePythonVersion, env: Optional[List[str]] = None
    ) -> "CommandStepBuilder":
        if not isinstance(ver, AvailablePythonVersion):
            raise Exception(f"Unsupported python version for test image: {ver}.")

        return self.on_python_image(
            image=f"buildkite-test:py{ver}-{BUILDKITE_TEST_IMAGE_VERSION}",
            env=env,
        )

    # The below builder methods are no-ops if `None` is passed-- this allows chaining them together without the
    # need to check for `None` in advance.

    def with_timeout(self, num_minutes: Optional[int]) -> "CommandStepBuilder":
        if num_minutes is not None:
            self._step["timeout_in_minutes"] = num_minutes
        return self

    def with_retry(self, num_retries: Optional[int]) -> "CommandStepBuilder":
        if num_retries is not None:
            self._step["retry"] = {"automatic": {"limit": num_retries}}
        return self

    def with_queue(self, queue: Optional[BuildkiteQueue]) -> "CommandStepBuilder":
        if queue is not None:
            assert BuildkiteQueue.contains(queue)
            agents = self._step["agents"]  # type: ignore
            agents["queue"] = queue.value
        return self

    def with_dependencies(self, step_keys: Optional[List[str]]) -> "CommandStepBuilder":
        if step_keys is not None:
            self._step["depends_on"] = step_keys
        return self

    def build(self) -> CommandStep:
        return self._step
