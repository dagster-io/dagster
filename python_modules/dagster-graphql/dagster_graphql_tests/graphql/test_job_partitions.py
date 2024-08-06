from dagster import (
    AssetKey,
    ConfigurableResource,
    Definitions,
    StaticPartitionsDefinition,
    asset,
    job,
    op,
    static_partitioned_config,
)
from dagster._core.definitions.repository_definition import SINGLETON_REPOSITORY_NAME
from dagster._core.test_utils import ensure_dagster_tests_import, instance_for_test
from dagster_graphql.test.utils import define_out_of_process_context, execute_dagster_graphql

ensure_dagster_tests_import()


GET_PARTITIONS_QUERY = """
    query SingleJobQuery($selector: PipelineSelector!, $selectedAssetKeys: [AssetKeyInput!]) {
        pipelineOrError(params: $selector) {
            ... on Pipeline {
                name
                partitionKeysOrError(selectedAssetKeys: $selectedAssetKeys) {
                    partitionKeys
                }
            }
        }
    }
"""

GET_PARTITION_TAGS_QUERY = """
    query SingleJobQuery($selector: PipelineSelector!, $partitionName: String!, $selectedAssetKeys: [AssetKeyInput!]) {
        pipelineOrError(params: $selector) {
            ... on Pipeline {
                name
                partition(partitionName: $partitionName, selectedAssetKeys: $selectedAssetKeys) {
                    name
                    tagsOrError {
                        ... on PartitionTags {
                            results {
                                key
                                value
                            }
                        }
                    }
                }
            }
        }
    }
"""

GET_PARTITION_RUN_CONFIG_QUERY = """
    query SingleJobQuery($selector: PipelineSelector!, $partitionName: String!, $selectedAssetKeys: [AssetKeyInput!]) {
        pipelineOrError(params: $selector) {
            ... on Pipeline {
                name
                partition(partitionName: $partitionName, selectedAssetKeys: $selectedAssetKeys) {
                    name
                    runConfigOrError {
                        ... on PartitionRunConfig {
                            yaml
                        }
                    }
                }
            }
        }
    }
"""


def get_repo_with_partitioned_op_job():
    @op
    def op1(): ...

    @static_partitioned_config(["1", "2"])
    def my_partitioned_config(partition):
        return {"ops": {"op1": {"config": {"p": partition}}}}

    @job(config=my_partitioned_config)
    def job1():
        op1()

    return Definitions(jobs=[job1]).get_repository_def()


def get_repo_with_differently_partitioned_assets():
    @asset(partitions_def=StaticPartitionsDefinition(["1", "2"]))
    def asset1(): ...

    ab_partitions_def = StaticPartitionsDefinition(["a", "b"])

    @asset(partitions_def=ab_partitions_def)
    def asset2(): ...

    class MyResource(ConfigurableResource):
        foo: str

    @asset(partitions_def=ab_partitions_def)
    def asset3(resource1: MyResource): ...

    return Definitions(
        assets=[asset1, asset2, asset3], resources={"resource1": MyResource(foo="bar")}
    ).get_repository_def()


def test_get_partition_names():
    with instance_for_test() as instance:
        with define_out_of_process_context(
            __file__, "get_repo_with_partitioned_op_job", instance
        ) as context:
            result = execute_dagster_graphql(
                context,
                GET_PARTITIONS_QUERY,
                variables={
                    "selector": {
                        "repositoryLocationName": context.code_location_names[0],
                        "repositoryName": SINGLETON_REPOSITORY_NAME,
                        "pipelineName": "job1",
                    }
                },
            )
            assert result.data["pipelineOrError"]["name"] == "job1"
            assert result.data["pipelineOrError"]["partitionKeysOrError"]["partitionKeys"] == [
                "1",
                "2",
            ]


def test_get_partition_names_asset_selection():
    with instance_for_test() as instance:
        with define_out_of_process_context(
            __file__, "get_repo_with_differently_partitioned_assets", instance
        ) as context:
            result = execute_dagster_graphql(
                context,
                GET_PARTITIONS_QUERY,
                variables={
                    "selector": {
                        "repositoryLocationName": context.code_location_names[0],
                        "repositoryName": SINGLETON_REPOSITORY_NAME,
                        "pipelineName": "__ASSET_JOB",
                    },
                    "selectedAssetKeys": [
                        AssetKey("asset2").to_graphql_input(),
                        AssetKey("asset3").to_graphql_input(),
                    ],
                },
            )
            assert result.data["pipelineOrError"]["name"] == "__ASSET_JOB"
            assert result.data["pipelineOrError"]["partitionKeysOrError"]["partitionKeys"] == [
                "a",
                "b",
            ]


def test_get_partition_tags():
    with instance_for_test() as instance:
        with define_out_of_process_context(
            __file__, "get_repo_with_partitioned_op_job", instance
        ) as context:
            result = execute_dagster_graphql(
                context,
                GET_PARTITION_TAGS_QUERY,
                variables={
                    "selector": {
                        "repositoryLocationName": context.code_location_names[0],
                        "repositoryName": SINGLETON_REPOSITORY_NAME,
                        "pipelineName": "job1",
                    },
                    "partitionName": "1",
                },
            )
            assert result.data["pipelineOrError"]["name"] == "job1"
            result_partition = result.data["pipelineOrError"]["partition"]
            assert result_partition["name"] == "1"
            assert {
                item["key"]: item["value"] for item in result_partition["tagsOrError"]["results"]
            } == {
                "dagster/partition": "1",
                "dagster/partition_set": "job1_partition_set",
            }


def test_get_partition_tags_asset_selection():
    with instance_for_test() as instance:
        with define_out_of_process_context(
            __file__, "get_repo_with_differently_partitioned_assets", instance
        ) as context:
            result = execute_dagster_graphql(
                context,
                GET_PARTITION_TAGS_QUERY,
                variables={
                    "selector": {
                        "repositoryLocationName": context.code_location_names[0],
                        "repositoryName": SINGLETON_REPOSITORY_NAME,
                        "pipelineName": "__ASSET_JOB",
                    },
                    "selectedAssetKeys": [
                        AssetKey("asset2").to_graphql_input(),
                        AssetKey("asset3").to_graphql_input(),
                    ],
                    "partitionName": "b",
                },
            )
            assert result.data["pipelineOrError"]["name"] == "__ASSET_JOB"
            result_partition = result.data["pipelineOrError"]["partition"]
            assert result_partition["name"] == "b"
            assert {
                item["key"]: item["value"] for item in result_partition["tagsOrError"]["results"]
            } == {"dagster/partition": "b"}


def test_get_partition_config():
    with instance_for_test() as instance:
        with define_out_of_process_context(
            __file__, "get_repo_with_partitioned_op_job", instance
        ) as context:
            result = execute_dagster_graphql(
                context,
                GET_PARTITION_RUN_CONFIG_QUERY,
                variables={
                    "selector": {
                        "repositoryLocationName": context.code_location_names[0],
                        "repositoryName": SINGLETON_REPOSITORY_NAME,
                        "pipelineName": "job1",
                    },
                    "partitionName": "1",
                },
            )
            assert result.data["pipelineOrError"]["name"] == "job1"
            result_partition = result.data["pipelineOrError"]["partition"]
            assert result_partition["name"] == "1"
            assert (
                result_partition["runConfigOrError"]["yaml"]
                == """ops:\n  op1:\n    config:\n      p: '1'\n"""
            )


def test_get_partition_config_asset_selection():
    with instance_for_test() as instance:
        with define_out_of_process_context(
            __file__, "get_repo_with_differently_partitioned_assets", instance
        ) as context:
            result = execute_dagster_graphql(
                context,
                GET_PARTITION_RUN_CONFIG_QUERY,
                variables={
                    "selector": {
                        "repositoryLocationName": context.code_location_names[0],
                        "repositoryName": SINGLETON_REPOSITORY_NAME,
                        "pipelineName": "__ASSET_JOB",
                    },
                    "selectedAssetKeys": [
                        AssetKey("asset2").to_graphql_input(),
                        AssetKey("asset3").to_graphql_input(),
                    ],
                    "partitionName": "b",
                },
            )
            assert result.data["pipelineOrError"]["name"] == "__ASSET_JOB"
            result_partition = result.data["pipelineOrError"]["partition"]
            assert result_partition["name"] == "b"
            assert result_partition["runConfigOrError"]["yaml"] == "{}\n"
