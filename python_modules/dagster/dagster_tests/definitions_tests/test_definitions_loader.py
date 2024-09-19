from unittest.mock import patch

import pytest
from dagster._core.code_pointer import CodePointer
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.definitions.decorators.definitions_decorator import definitions
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.definitions_loader import DefinitionsLoadContext, DefinitionsLoadType
from dagster._core.definitions.external_asset import external_assets_from_specs
from dagster._core.definitions.metadata.metadata_value import MetadataValue
from dagster._core.definitions.reconstruct import (
    ReconstructableJob,
    ReconstructableRepository,
    repository_def_from_pointer,
    repository_def_from_target_def,
)
from dagster._core.definitions.repository_definition.repository_definition import (
    PendingRepositoryDefinition,
    RepositoryDefinition,
    RepositoryLoadData,
)
from dagster._core.definitions.unresolved_asset_job_definition import define_asset_job
from dagster._core.errors import DagsterInvalidInvocationError
from dagster._core.execution.api import execute_job
from dagster._core.instance_for_test import instance_for_test
from dagster._utils import file_relative_path

FOO_INTEGRATION_SOURCE_KEY = "foo_integration"

WORKSPACE_ID = "my_workspace"


def fetch_foo_integration_asset_info(workspace_id: str):
    if workspace_id == WORKSPACE_ID:
        return [{"id": "alpha"}, {"id": "beta"}]
    else:
        raise Exception("Unknown workspace")


# This function would be provided by integration lib dagster-foo
def _get_foo_integration_defs(context: DefinitionsLoadContext, workspace_id: str) -> Definitions:
    cache_key = f"{FOO_INTEGRATION_SOURCE_KEY}/{workspace_id}"
    if (
        context.load_type == DefinitionsLoadType.RECONSTRUCTION
        and cache_key in context.reconstruction_metadata
    ):
        payload = context.reconstruction_metadata[cache_key]
    else:
        payload = fetch_foo_integration_asset_info(workspace_id)
    asset_specs = [AssetSpec(item["id"]) for item in payload]
    assets = external_assets_from_specs(asset_specs)
    return Definitions(
        assets=assets,
    ).with_reconstruction_metadata({cache_key: payload})


@definitions
def metadata_defs(context: DefinitionsLoadContext):
    @asset
    def regular_asset(): ...

    all_asset_job = define_asset_job("all_assets", selection=AssetSelection.all())

    return Definitions.merge(
        _get_foo_integration_defs(context, WORKSPACE_ID),
        Definitions(assets=[regular_asset], jobs=[all_asset_job]),
    )


# ########################
# ##### TESTS
# ########################


def test_reconstruction_metadata():
    repo = repository_def_from_target_def(metadata_defs, DefinitionsLoadType.INITIALIZATION)
    assert repo
    assert repo.assets_defs_by_key.keys() == {
        AssetKey("regular_asset"),
        AssetKey("alpha"),
        AssetKey("beta"),
    }

    defs = metadata_defs(context=DefinitionsLoadContext(DefinitionsLoadType.INITIALIZATION))
    inner_repo = defs.get_inner_repository()
    assert isinstance(inner_repo, PendingRepositoryDefinition)

    recon_repo = ReconstructableRepository.for_file(__file__, "metadata_defs")
    assert isinstance(recon_repo.get_definition(), RepositoryDefinition)

    repo_load_data = RepositoryLoadData(
        cacheable_asset_data={},
        reconstruction_metadata={
            f"{FOO_INTEGRATION_SOURCE_KEY}/{WORKSPACE_ID}": MetadataValue.code_location_reconstruction(
                fetch_foo_integration_asset_info(WORKSPACE_ID)
            )
        },
    )

    # Ensure we don't call the expensive fetch function when we have the data cached
    with patch(
        "dagster_tests.definitions_tests.test_definitions_loader.fetch_foo_integration_asset_info"
    ) as mock_fetch:
        inner_repo.reconstruct_repository_definition(repository_load_data=repo_load_data)
        mock_fetch.assert_not_called()


def test_reconstruction_metadata_with_global_context():
    defs_path = file_relative_path(__file__, "metadata_defs_global_context.py")

    recon_repo = ReconstructableRepository.for_file(defs_path, "defs")
    assert isinstance(recon_repo.get_definition(), RepositoryDefinition)

    recon_repo_with_cache = recon_repo.with_repository_load_data(
        RepositoryLoadData(
            cacheable_asset_data={},
            reconstruction_metadata={
                f"{FOO_INTEGRATION_SOURCE_KEY}/{WORKSPACE_ID}": MetadataValue.code_location_reconstruction(
                    fetch_foo_integration_asset_info(WORKSPACE_ID)
                )
            },
        )
    )

    # Ensure we don't call the expensive fetch function when we have the data cached
    with patch(
        "dagster_tests.definitions_tests.test_definitions_loader.fetch_foo_integration_asset_info"
    ) as mock_fetch:
        recon_repo_with_cache.get_definition()
        mock_fetch.assert_not_called()


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

    # Executing a job should cause the definitions to be loaded with a non-INITIALIZATION load type
    with instance_for_test() as instance:
        with pytest.raises(Exception, match="Unexpected load type"):
            execute_job(recon_job, instance=instance)
