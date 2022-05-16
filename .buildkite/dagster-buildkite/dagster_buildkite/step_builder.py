import os
from enum import Enum
from typing import Dict, List, Optional

from .defines import SupportedPythons
from .images.versions import INTEGRATION_IMAGE_VERSION, UNIT_IMAGE_VERSION
from .utils import CommandStep

TIMEOUT_IN_MIN = 20

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


class StepBuilder:

    _step: CommandStep

    def __init__(
        self, label: str, key: Optional[str] = None, timeout_in_minutes: Optional[int] = None
    ):
        self._step = {
            "agents": {"queue": BuildkiteQueue.MEDIUM.value},
            "label": label,
            "timeout_in_minutes": timeout_in_minutes or TIMEOUT_IN_MIN,
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

    def run(self, *commands: str) -> "StepBuilder":
        self._step["commands"] = ["time " + cmd for cmd in commands]
        return self

    def _base_docker_settings(self) -> Dict[str, object]:
        return {
            "shell": ["/bin/bash", "-xeuc"],
            "always-pull": True,
            "mount-ssh-agent": True,
        }

    def on_python_image(self, image: str, env: Optional[List[str]] = None) -> "StepBuilder":
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

    def on_unit_image(self, ver: str, env: Optional[List[str]] = None) -> "StepBuilder":
        if ver not in SupportedPythons:
            raise Exception("Unsupported python version for unit image {ver}".format(ver=ver))

        return self.on_python_image(
            image="buildkite-unit:py{python_version}-{image_version}".format(
                python_version=ver, image_version=UNIT_IMAGE_VERSION
            ),
            env=env,
        )

    def on_integration_image(self, ver: str, env: Optional[List[str]] = None) -> "StepBuilder":
        if ver not in SupportedPythons:
            raise Exception(
                "Unsupported python version for integration image {ver}".format(ver=ver)
            )

        return self.on_python_image(
            image="buildkite-integration:py{python_version}-{image_version}".format(
                python_version=ver, image_version=INTEGRATION_IMAGE_VERSION
            ),
            env=env,
        )

    def with_timeout(self, num_minutes: int) -> "StepBuilder":
        self._step["timeout_in_minutes"] = num_minutes
        return self

    def with_retry(self, num_retries: int) -> "StepBuilder":
        self._step["retry"] = {"automatic": {"limit": num_retries}}
        return self

    def on_queue(self, queue: BuildkiteQueue) -> "StepBuilder":
        assert BuildkiteQueue.contains(queue)
        agents = self._step["agents"]  # type: ignore
        agents["queue"] = queue.value
        return self

    def depends_on(self, step_keys: List[str]) -> "StepBuilder":
        self._step["depends_on"] = step_keys
        return self

    def build(self) -> CommandStep:
        return self._step
