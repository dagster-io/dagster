import os

import docker

IS_BUILDKITE = os.getenv("BUILDKITE") is not None

# docker-py defaults to a 60s socket read timeout and reads no env var for it, so
# the only way to raise it is at construction. A dockerd busy committing layers
# can blow past 60s on a plain inspect, which fails the test on the daemon rather
# than on what it was testing.
DOCKER_CLIENT_TIMEOUT = 180


def docker_client() -> docker.DockerClient:
    """A docker-py client that tolerates a slow daemon. See DOCKER_CLIENT_TIMEOUT."""
    return docker.client.from_env(timeout=DOCKER_CLIENT_TIMEOUT)
