import os
import random
import subprocess

import six

from dagster.core.code_pointer import FileCodePointer
from dagster.core.host_representation import ExternalPipeline
from dagster.core.origin import PipelinePythonOrigin, RepositoryPythonOrigin

IS_BUILDKITE = os.getenv("BUILDKITE") is not None


def image_pull_policy():
    # This is because when running local tests, we need to load the image into the kind cluster (and
    # then not attempt to pull it) because we don't want to require credentials for a private
    # registry / pollute the private registry / set up and network a local registry as a condition
    # of running tests
    if IS_BUILDKITE:
        return "Always"
    else:
        return "IfNotPresent"


def check_output(*args, **kwargs):
    try:
        return subprocess.check_output(*args, **kwargs)
    except subprocess.CalledProcessError as exc:
        output = exc.output.decode()
        six.raise_from(Exception(output), exc)


def which_(exe):
    """Uses distutils to look for an executable, mimicking unix which"""
    from distutils import spawn  # pylint: disable=no-name-in-module

    # https://github.com/PyCQA/pylint/issues/73
    return spawn.find_executable(exe)


def get_test_namespace():
    namespace_suffix = hex(random.randint(0, 16 ** 6))[2:]
    return "dagster-test-%s" % namespace_suffix


def within_docker():
    """detect if we're running inside of a docker container

    from: https://stackoverflow.com/a/48710609/11295366
    """
    cgroup_path = "/proc/self/cgroup"
    return (
        os.path.exists("/.dockerenv")
        or os.path.isfile(cgroup_path)
        and any("docker" in line for line in open(cgroup_path))
    )


def remove_none_recursively(obj):
    """Remove none values from a dict. This is used here to support comparing provided config vs.
    config we retrive from kubernetes, which returns all fields, even those which have no value
    configured.
    """
    if isinstance(obj, (list, tuple, set)):
        return type(obj)(remove_none_recursively(x) for x in obj if x is not None)
    elif isinstance(obj, dict):
        return type(obj)(
            (remove_none_recursively(k), remove_none_recursively(v))
            for k, v in obj.items()
            if k is not None and v is not None
        )
    else:
        return obj


class ReOriginatedExternalPipelineForTest(ExternalPipeline):
    def __init__(
        self, external_pipeline,
    ):
        super(ReOriginatedExternalPipelineForTest, self).__init__(
            external_pipeline.external_pipeline_data, external_pipeline.repository_handle,
        )

    def get_origin(self):
        """
        Hack! Inject origin that the k8s images will use. The BK image uses a different directory
        structure (/workdir/python_modules/dagster-test/dagster_test/test_project) than the images
        inside the kind cluster (/dagster_test/test_project). As a result the normal origin won't
        work, we need to inject this one.
        """

        return PipelinePythonOrigin(
            self._pipeline_index.name,
            RepositoryPythonOrigin(
                executable_path="python",
                code_pointer=FileCodePointer(
                    "/dagster_test/test_project/test_pipelines/repo.py",
                    "define_demo_execution_repo",
                ),
            ),
        )
