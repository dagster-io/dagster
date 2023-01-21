import os
from contextlib import contextmanager

from dagstermill_tests.test_ops import cleanup_result_notebook

from dagster._core.definitions.reconstruct import ReconstructablePipeline
from dagster._core.test_utils import instance_for_test
from dagster._legacy import execute_pipeline

IS_BUILDKITE = os.getenv("BUILDKITE") is not None

import subprocess
import warnings

import pytest


# Dagstermill tests invoke notebooks that look for an ipython kernel called dagster -- if this is
# not already present, then the tests fail. This fixture creates the kernel if it is not already
# present before tests run.
@pytest.fixture(autouse=True)
def kernel():
    warnings.warn(
        "Installing Jupyter kernel dagster. Don't worry, this is noninvasive "
        "and you can reverse it by running `jupyter kernelspec uninstall dagster`."
    )
    subprocess.check_output(
        ["ipython", "kernel", "install", "--name", "dagster", "--user"]
    )


@contextmanager
def exec_for_test(module_name, fn_name, env=None, raise_on_error=True, **kwargs):
    result = None
    recon_pipeline = ReconstructablePipeline.for_module(module_name, fn_name)

    with instance_for_test() as instance:
        try:
            result = execute_pipeline(
                recon_pipeline,
                env,
                instance=instance,
                raise_on_error=raise_on_error,
                **kwargs,
            )
            yield result
        finally:
            if result:
                cleanup_result_notebook(result)


@pytest.mark.flaky(reruns=1)
def test_config_asset():
    module_path = "docs_snippets.integrations.dagstermill.iris_notebook_config"
    if not IS_BUILDKITE:
        module_path = "examples.docs_snippets." + module_path

    with exec_for_test(
        module_name=module_path,
        fn_name="config_asset_job",
    ) as result:
        assert result.success


@pytest.mark.flaky(reruns=1)
def test_iris_classify_job():
    module_path = "docs_snippets.integrations.dagstermill.iris_notebook_op"
    if not IS_BUILDKITE:
        module_path = "examples.docs_snippets." + module_path

    with exec_for_test(
        module_name=module_path,
        fn_name="iris_classify",
    ) as result:
        assert result.success


@pytest.mark.flaky(reruns=1)
def test_outputs_job():
    module_path = "docs_snippets.integrations.dagstermill.notebook_outputs"
    if not IS_BUILDKITE:
        module_path = "examples.docs_snippets." + module_path

    with exec_for_test(
        module_name=module_path,
        fn_name="my_job",
    ) as result:
        assert result.success
