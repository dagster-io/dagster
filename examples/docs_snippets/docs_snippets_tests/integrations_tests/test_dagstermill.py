from contextlib import contextmanager

from dagstermill_tests.test_ops import cleanup_result_notebook

from dagster._core.definitions.reconstruct import ReconstructablePipeline
from dagster._core.test_utils import instance_for_test
from dagster._legacy import execute_pipeline


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


def test_config_asset():
    with exec_for_test(
        module_name="examples.docs_snippets.docs_snippets.integrations.dagstermill.iris_notebook_config",
        fn_name="config_asset_job",
    ) as result:
        assert result.success


def test_iris_classify_job():
    with exec_for_test(
        module_name="examples.docs_snippets.docs_snippets.integrations.dagstermill.iris_notebook_op",
        fn_name="iris_classify",
    ) as result:
        assert result.success


def test_outputs_job():
    with exec_for_test(
        module_name="examples.docs_snippets.docs_snippets.integrations.dagstermill.notebook_outputs",
        fn_name="my_job",
    ) as result:
        assert result.success
