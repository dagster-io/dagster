import os
import sys

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))

sys.path.append(SCRIPT_PATH)

from defines import IMAGE_VERSION_MAP, SupportedPython

TIMEOUT_IN_MIN = 15

DOCKER_PLUGIN = "docker#v3.2.0"

PY_IMAGE_MAP = {
    SupportedPython.V3_7: "python:3.7.3-stretch",
    SupportedPython.V3_6: "python:3.6.8-stretch",
    SupportedPython.V3_5: "python:3.5.7-stretch",
    SupportedPython.V2_7: "python:2.7.16-stretch",
}


class StepBuilder:
    def __init__(self, label):
        self._step = {"label": label, "timeout_in_minutes": TIMEOUT_IN_MIN}

    def run(self, *argc):
        self._step["commands"] = map(lambda cmd: "time " + cmd, argc)
        return self

    def base_docker_settings(self):
        return {"shell": ["/bin/bash", "-xeuc"], "always-pull": True}

    def on_python_image(self, ver, env=None):
        settings = self.base_docker_settings()
        settings["image"] = PY_IMAGE_MAP[ver]
        if env:
            settings['environment'] = env

        self._step["plugins"] = [{DOCKER_PLUGIN: settings}]

        return self

    def on_integration_image(self, ver, env=None):
        settings = self.base_docker_settings()

        # version like dagster/buildkite-integration:py3.7.3-v2
        settings["image"] = "dagster/buildkite-integration:py" + IMAGE_VERSION_MAP[ver] + '-v2'

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

    def build(self):
        return self._step
