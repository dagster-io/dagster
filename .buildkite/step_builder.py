import os
import sys
from enum import Enum

from defines import SupportedPythons

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))

sys.path.append(SCRIPT_PATH)


TIMEOUT_IN_MIN = 20

DOCKER_PLUGIN = "docker#v3.2.0"

PY_IMAGE_MAP = {ver: "python:{}-stretch".format(ver) for ver in SupportedPythons}

# Update this when releasing a new version of our integration image
INTEGRATION_IMAGE_VERSION = "v5"


class BuildkiteQueue(Enum):
    DEFAULT = "default"
    MEDIUM = "medium"
    DOCKER = "docker-p"

    @classmethod
    def contains(cls, value):
        return isinstance(value, cls)


class StepBuilder:
    def __init__(self, label):
        self._step = {
            "label": label,
            "timeout_in_minutes": TIMEOUT_IN_MIN,
            "retry": {
                "automatic": [
                    {"exit_status": -1, "limit": 2},  # agent lost
                    {"exit_status": 255, "limit": 2},  # agent forced shut down
                ]
            },
        }

    def run(self, *argc):
        self._step["commands"] = map(lambda cmd: "time " + cmd, argc)
        return self

    def _base_docker_settings(self):
        return {"shell": ["/bin/bash", "-xeuc"], "always-pull": True, "mount-ssh-agent": True}

    def on_python_image(self, ver, env=None):
        settings = self._base_docker_settings()
        settings["image"] = PY_IMAGE_MAP[ver]
        if env:
            settings['environment'] = env

        self._step["plugins"] = [{DOCKER_PLUGIN: settings}]

        return self

    def on_integration_image(self, ver, env=None):
        if ver not in SupportedPythons:
            raise Exception(
                'Unsupported python version for integration image {ver}'.format(ver=ver)
            )

        settings = self._base_docker_settings()

        # version like dagster/buildkite-integration:py3.7.3-v3
        settings["image"] = "dagster/buildkite-integration:py%s-%s" % (
            ver,
            INTEGRATION_IMAGE_VERSION,
        )

        # map the docker socket to enable docker to be run from inside docker
        settings["volumes"] = ["/var/run/docker.sock:/var/run/docker.sock"]

        if env:
            settings['environment'] = env

        self._step["plugins"] = [{DOCKER_PLUGIN: settings}]
        return self

    def with_timeout(self, num_minutes):
        self._step["timeout_in_minutes"] = num_minutes
        return self

    def with_retry(self, num_retries):
        self._step["retry"] = {'automatic': {'limit': num_retries}}
        return self

    def on_queue(self, queue_name):
        assert BuildkiteQueue.contains(queue_name)

        self._step["agents"] = {'queue': queue_name.value}
        return self

    def build(self):
        return self._step
