import os
import subprocess
import warnings
from contextlib import contextmanager

import pytest
from dagstermill.test_utils import cleanup_result_notebook

from dagster import execute_job
from dagster._core.definitions.reconstruct import ReconstructableJob
from dagster._core.test_utils import instance_for_test


# Dagstermill tests invoke notebooks that look for an ipython kernel called dagster -- if this is
# not already present, then the tests fail. This fixture creates the kernel if it is not already
# present before tests run.
@pytest.fixture(autouse=True)
def kernel():
    warnings.warn(
        "Installing Jupyter kernel dagster. Don't worry, this is noninvasive "
        "and you can reverse it by running `jupyter kernelspec uninstall dagster`."
    )
    try:
        subprocess.check_output(
            ["ipython", "kernel", "install", "--name", "dagster", "--user"],
            stderr=subprocess.STDOUT,
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        pytest.skip(
            f"Could not install Jupyter kernel 'dagster' — ipython may not be installed: {e}"
        )


@contextmanager
def exec_for_test(module_name, fn_name, env=None, raise_on_error=True, **kwargs):
    result = None
    recon_job = ReconstructableJob.for_module(module_name, fn_name)

    with instance_for_test() as instance:
        try:
            with execute_job(
                recon_job,
                run_config=env,
                instance=instance,
                raise_on_error=raise_on_error,
                **kwargs,
            ) as result:
                yield result
        finally:
            if result:
                cleanup_result_notebook(result)


@pytest.mark.flaky(reruns=1)
def test_config_asset():
    with exec_for_test(
        module_name="docs_snippets.integrations.dagstermill.iris_notebook_config",
        fn_name="config_asset_job",
    ) as result:
        assert result.success, [str(e) for e in result.all_node_events if e.is_failure]


@pytest.mark.flaky(reruns=1)
def test_iris_classify_job():
    with exec_for_test(
        module_name="docs_snippets.integrations.dagstermill.iris_notebook_op",
        fn_name="iris_classify",
    ) as result:
        assert result.success, [str(e) for e in result.all_node_events if e.is_failure]


@pytest.mark.flaky(reruns=1)
def test_outputs_job():
    with exec_for_test(
        module_name="docs_snippets.integrations.dagstermill.notebook_outputs",
        fn_name="my_job",
    ) as result:
        assert result.success, [str(e) for e in result.all_node_events if e.is_failure]
