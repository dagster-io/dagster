from dagster import Definitions, asset, job, op, repository
from dagster._config.structured_config import Resource
from dagster._core.definitions.repository_definition import (
    PendingRepositoryDefinition,
    RepositoryDefinition,
)
from dagster._core.definitions.resource_definition import ResourceDefinition
from dagster._core.definitions.resource_output import ResourceOutput
from dagster._core.host_representation import (
    ExternalPipelineData,
    external_repository_data_from_def,
)
from dagster._core.snap import PipelineSnapshot


def test_repository_snap_all_props():
    @op
    def noop_op(_):
        pass

    @job
    def noop_job():
        noop_op()

    @repository
    def noop_repo():
        return [noop_job]

    external_repo_data = external_repository_data_from_def(noop_repo)

    assert external_repo_data.name == "noop_repo"
    assert len(external_repo_data.external_pipeline_datas) == 1
    assert isinstance(external_repo_data.external_pipeline_datas[0], ExternalPipelineData)

    pipeline_snapshot = external_repo_data.external_pipeline_datas[0].pipeline_snapshot
    assert isinstance(pipeline_snapshot, PipelineSnapshot)
    assert pipeline_snapshot.name == "noop_job"
    assert pipeline_snapshot.description is None
    assert pipeline_snapshot.tags == {}


def resolve_pending_repo_if_required(definitions: Definitions) -> RepositoryDefinition:
    repo_or_caching_repo = definitions.get_inner_repository_for_loading_process()
    return (
        repo_or_caching_repo.compute_repository_definition()
        if isinstance(repo_or_caching_repo, PendingRepositoryDefinition)
        else repo_or_caching_repo
    )


def test_repository_snap_definitions_resources_basic():
    @asset
    def my_asset(foo: ResourceOutput[str]):
        pass

    defs = Definitions(
        assets=[my_asset],
        resources={"foo": ResourceDefinition.hardcoded_resource("wrapped")},
    )

    repo = resolve_pending_repo_if_required(defs)
    external_repo_data = external_repository_data_from_def(repo)

    assert len(external_repo_data.external_resource_data) == 1
    assert external_repo_data.external_resource_data[0].name == "foo"
    assert external_repo_data.external_resource_data[0].resource_snapshot.name == "foo"
    assert external_repo_data.external_resource_data[0].resource_snapshot.description is None
    assert external_repo_data.external_resource_data[0].configured_values == {}


def test_repository_snap_definitions_resources_complex():
    class MyStringResource(Resource):
        """my description"""

        my_string: str = "bar"

    @asset
    def my_asset(foo: MyStringResource):
        pass

    defs = Definitions(
        assets=[my_asset],
        resources={
            "foo": MyStringResource(
                my_string="baz",
            )
        },
    )

    repo = resolve_pending_repo_if_required(defs)
    external_repo_data = external_repository_data_from_def(repo)

    assert len(external_repo_data.external_resource_data) == 1
    assert external_repo_data.external_resource_data[0].name == "foo"
    assert external_repo_data.external_resource_data[0].resource_snapshot.name == "foo"
    assert (
        external_repo_data.external_resource_data[0].resource_snapshot.description
        == "my description"
    )

    # Ensure we get config snaps for the resource's fields
    assert len(external_repo_data.external_resource_data[0].config_field_snaps) == 1
    snap = external_repo_data.external_resource_data[0].config_field_snaps[0]
    assert snap.name == "my_string"
    assert not snap.is_required
    assert snap.default_value_as_json_str == '"bar"'

    # Ensure we get the configured values for the resource
    assert external_repo_data.external_resource_data[0].configured_values == {
        "my_string": '"baz"',
    }


def test_repository_snap_empty():
    @repository
    def empty_repo():
        return []

    external_repo_data = external_repository_data_from_def(empty_repo)
    assert external_repo_data.name == "empty_repo"
    assert len(external_repo_data.external_pipeline_datas) == 0
    assert len(external_repo_data.external_resource_data) == 0
