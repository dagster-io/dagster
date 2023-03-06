from typing import Dict, List

from dagster import Definitions, asset, job, op, repository
from dagster._config.field_utils import EnvVar
from dagster._config.structured_config import Config, ConfigurableResource
from dagster._core.definitions.repository_definition import (
    PendingRepositoryDefinition,
    RepositoryDefinition,
)
from dagster._core.definitions.resource_annotation import Resource
from dagster._core.definitions.resource_definition import ResourceDefinition
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
    def my_asset(foo: Resource[str]):
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


def test_repository_snap_definitions_resources_nested() -> None:
    class MyInnerResource(ConfigurableResource):
        a_str: str

    class MyOuterResource(ConfigurableResource):
        inner: MyInnerResource

    inner = MyInnerResource(a_str="wrapped")
    defs = Definitions(
        resources={"foo": MyOuterResource(inner=inner)},
    )

    repo = resolve_pending_repo_if_required(defs)
    external_repo_data = external_repository_data_from_def(repo)
    assert external_repo_data.external_resource_data

    assert len(external_repo_data.external_resource_data) == 2

    foo = [data for data in external_repo_data.external_resource_data if data.name == "foo"]
    inner = [
        data
        for data in external_repo_data.external_resource_data
        if data.name == f"_nested_{id(inner)}"
    ]

    assert foo
    assert inner


def test_repository_snap_definitions_resources_complex():
    class MyStringResource(ConfigurableResource):
        """My description."""

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
        == "My description."
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


def test_repository_snap_definitions_env_vars() -> None:
    class MyStringResource(ConfigurableResource):
        my_string: str

    class MyInnerResource(ConfigurableResource):
        my_string: str

    class MyOuterResource(ConfigurableResource):
        inner: MyInnerResource

    class MyInnerConfig(Config):
        my_string: str

    class MyDataStructureResource(ConfigurableResource):
        str_list: List[str]
        str_dict: Dict[str, str]

    class MyResourceWithConfig(ConfigurableResource):
        config: MyInnerConfig
        config_list: List[MyInnerConfig]

    @asset
    def my_asset(foo: MyStringResource):
        pass

    defs = Definitions(
        assets=[my_asset],
        resources={
            "foo": MyStringResource(
                my_string=EnvVar("MY_STRING"),
            ),
            "bar": MyStringResource(
                my_string=EnvVar("MY_STRING"),
            ),
            "baz": MyStringResource(
                my_string=EnvVar("MY_OTHER_STRING"),
            ),
            "qux": MyOuterResource(
                inner=MyInnerResource(
                    my_string=EnvVar("MY_INNER_STRING"),
                ),
            ),
            "quux": MyDataStructureResource(
                str_list=[EnvVar("MY_STRING")],
                str_dict={"foo": EnvVar("MY_STRING"), "bar": EnvVar("MY_OTHER_STRING")},
            ),
            "quuz": MyResourceWithConfig(
                config=MyInnerConfig(
                    my_string=EnvVar("MY_CONFIG_NESTED_STRING"),
                ),
                config_list=[
                    MyInnerConfig(
                        my_string=EnvVar("MY_CONFIG_LIST_NESTED_STRING"),
                    )
                ],
            ),
        },
    )

    repo = resolve_pending_repo_if_required(defs)
    external_repo_data = external_repository_data_from_def(repo)
    assert external_repo_data.utilized_env_vars

    env_vars = dict(external_repo_data.utilized_env_vars)

    assert len(env_vars) == 5
    assert "MY_STRING" in env_vars
    assert {consumer.name for consumer in env_vars["MY_STRING"]} == {"foo", "bar", "quux"}
    assert "MY_OTHER_STRING" in env_vars
    assert {consumer.name for consumer in env_vars["MY_OTHER_STRING"]} == {"baz", "quux"}
    assert "MY_INNER_STRING" in env_vars
    assert {consumer.name for consumer in env_vars["MY_INNER_STRING"]} == {"qux"}
    assert "MY_CONFIG_NESTED_STRING" in env_vars
    assert {consumer.name for consumer in env_vars["MY_CONFIG_NESTED_STRING"]} == {"quuz"}
    assert "MY_CONFIG_LIST_NESTED_STRING" in env_vars
    assert {consumer.name for consumer in env_vars["MY_CONFIG_LIST_NESTED_STRING"]} == {"quuz"}
