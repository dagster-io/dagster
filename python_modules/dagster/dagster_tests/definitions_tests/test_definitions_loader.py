import pytest
from dagster._core.code_pointer import CodePointer
from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.definitions.decorators.definitions_decorator import definitions
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.definitions_loader import DefinitionsLoadContext, DefinitionsLoadType
from dagster._core.definitions.reconstruct import (
    ReconstructableJob,
    ReconstructableRepository,
    repository_def_from_pointer,
)
from dagster._core.definitions.unresolved_asset_job_definition import define_asset_job
from dagster._core.errors import DagsterInvalidInvocationError
from dagster._core.execution.api import execute_job
from dagster._core.instance_for_test import instance_for_test


def test_invoke_definitions_loader_with_context():
    @definitions
    def defs(context: DefinitionsLoadContext) -> Definitions:
        return Definitions()

    assert defs(DefinitionsLoadContext(load_type=DefinitionsLoadType.INITIALIZATION))

    with pytest.raises(DagsterInvalidInvocationError, match="requires a DefinitionsLoadContext"):
        defs()


def test_invoke_definitions_loader_no_context():
    @definitions
    def defs() -> Definitions:
        return Definitions()

    assert defs()

    with pytest.raises(DagsterInvalidInvocationError, match="Passed a DefinitionsLoadContext"):
        defs(DefinitionsLoadContext(load_type=DefinitionsLoadType.INITIALIZATION))


@definitions
def load_type_test_defs(context: DefinitionsLoadContext) -> Definitions:
    if not context.load_type == DefinitionsLoadType.INITIALIZATION:
        raise Exception("Unexpected load type")

    @asset
    def foo(): ...

    foo_job = define_asset_job("foo_job", [foo])

    return Definitions(assets=[foo], jobs=[foo_job])


def test_definitions_load_type():
    pointer = CodePointer.from_python_file(__file__, "load_type_test_defs", None)

    # Load type is INITIALIZATION so should not raise
    assert repository_def_from_pointer(pointer, DefinitionsLoadType.INITIALIZATION, None)

    recon_job = ReconstructableJob(
        repository=ReconstructableRepository(pointer),
        job_name="foo_job",
    )

    # Executing a job should cause the definitions to be loaded with a non-ROOT load type
    with instance_for_test() as instance:
        with pytest.raises(Exception, match="Unexpected load type"):
            execute_job(recon_job, instance=instance)
