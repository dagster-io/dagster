import os
from enum import Enum

from .defines import SupportedPythons
from .images.versions import INTEGRATION_IMAGE_VERSION, UNIT_IMAGE_VERSION

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
    def contains(cls, value):
        return isinstance(value, cls)


class StepBuilder:
    def __init__(self, label, key=None):
        self._step = {
            "agents": {"queue": BuildkiteQueue.MEDIUM.value},
            "label": label,
            "timeout_in_minutes": TIMEOUT_IN_MIN,
            "retry": {
                "automatic": [
                    {"exit_status": -1, "limit": 2},  # agent lost
                    {"exit_status": 255, "limit": 2},  # agent forced shut down
                ]
            },
        }
        if key is not None:
            self._step["key"] = key

    def run(self, *argc):
        commands = []
        for entry in argc:
            if isinstance(entry, list):
                commands.extend(entry)
            else:
                commands.append(entry)

        self._step["commands"] = ["time " + cmd for cmd in commands]
        return self

    def _base_docker_settings(self):
        return {
            "shell": ["/bin/bash", "-xeuc"],
            "always-pull": True,
            "mount-ssh-agent": True,
        }

    def on_python_image(self, image, env=None):
        settings = self._base_docker_settings()
        settings["image"] = "{account_id}.dkr.ecr.us-west-2.amazonaws.com/{image}".format(
            account_id=AWS_ACCOUNT_ID, image=image
        )
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

    def on_unit_image(self, ver, env=None):
        if ver not in SupportedPythons:
            raise Exception("Unsupported python version for unit image {ver}".format(ver=ver))

        return self.on_python_image(
            image="buildkite-unit:py{python_version}-{image_version}".format(
                python_version=ver, image_version=UNIT_IMAGE_VERSION
            ),
            env=env,
        )

    def on_integration_image(self, ver, env=None):
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

    def with_timeout(self, num_minutes):
        self._step["timeout_in_minutes"] = num_minutes
        return self

    def with_retry(self, num_retries):
        self._step["retry"] = {"automatic": {"limit": num_retries}}
        return self

    def on_queue(self, queue):
        assert BuildkiteQueue.contains(queue)

        self._step["agents"]["queue"] = queue.value
        return self

    def depends_on(self, step_keys):
        self._step["depends_on"] = step_keys
        return self

    def build(self):
        return self._step
