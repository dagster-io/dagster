import os
import sys
from enum import Enum

from defines import SupportedPython, SupportedPythons

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))

sys.path.append(SCRIPT_PATH)


TIMEOUT_IN_MIN = 20

DOCKER_PLUGIN = "docker#v3.2.0"
ECR_PLUGIN = "ecr#v2.0.0"

# Update this when releasing a new version of our integration image
INTEGRATION_IMAGE_VERSION = "v6"

AWS_ACCOUNT_ID = os.environ.get('AWS_ACCOUNT_ID')
AWS_ECR_REGION = 'us-west-1'


class BuildkiteQueue(Enum):
    '''These are the Buildkite CloudFormation queues that we use. All queues with "-p" suffix are
    provisioned by Pulumi.
    '''

    DOCKER = "docker-p"
    MICRO = "micro-p"
    MEDIUM = "medium-p"
    C4_2XLARGE = "c4-2xlarge-p"

    @classmethod
    def contains(cls, value):
        return isinstance(value, cls)


class StepBuilder(object):
    def __init__(self, label, key=None):
        self._step = {
            # use Pulumi-managed medium queue by default
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
        self._step["commands"] = map(lambda cmd: "time " + cmd, argc)
        return self

    def _base_docker_settings(self):
        return {"shell": ["/bin/bash", "-xeuc"], "always-pull": True, "mount-ssh-agent": True}

    def on_integration_image(self, ver, env=None):
        # See: https://github.com/dagster-io/dagster/issues/1960
        if ver not in SupportedPythons + [SupportedPython.V3_8]:
            raise Exception(
                'Unsupported python version for integration image {ver}'.format(ver=ver)
            )

        settings = self._base_docker_settings()

        # version like dagster/buildkite-integration:py3.7.3-v3
        settings["image"] = "%s.dkr.ecr.us-west-1.amazonaws.com/buildkite-integration:py%s-%s" % (
            AWS_ACCOUNT_ID,
            ver,
            INTEGRATION_IMAGE_VERSION,
        )

        # map the docker socket to enable docker to be run from inside docker
        settings["volumes"] = ["/var/run/docker.sock:/var/run/docker.sock"]

        settings["environment"] = ["BUILDKITE"] + (env or [])

        ecr_settings = {
            'login': True,
            'no-include-email': True,
            'account-ids': AWS_ACCOUNT_ID,
            'region': AWS_ECR_REGION,
        }
        self._step["plugins"] = [{ECR_PLUGIN: ecr_settings}, {DOCKER_PLUGIN: settings}]
        return self

    def with_timeout(self, num_minutes):
        self._step["timeout_in_minutes"] = num_minutes
        return self

    def with_retry(self, num_retries):
        self._step["retry"] = {'automatic': {'limit': num_retries}}
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
