from dataclasses import dataclass

from typing_extensions import assert_never

from dagster_rest_resources.__generated__.input_types import RepositorySelector
from dagster_rest_resources.gql_client import IGraphQLClient
from dagster_rest_resources.schemas.exception import (
    DagsterPlusClientError,
    DagsterPlusServerError,
    DagsterPlusUnauthorizedError,
)
from dagster_rest_resources.schemas.partition import (
    DgApiDynamicPartition,
    DgApiDynamicPartitionsDeleteResult,
)

MAX_DYNAMIC_PARTITIONS_PER_DELETE = 100


@dataclass(frozen=True)
class DgApiPartitionApi:
    _client: IGraphQLClient

    def create_dynamic_partition(
        self,
        *,
        partitions_def_name: str,
        partition_key: str,
        repository_location_name: str,
        repository_name: str,
    ) -> DgApiDynamicPartition:
        result = self._client.add_dynamic_partition(
            partitions_def_name=partitions_def_name,
            partition_key=partition_key,
            repository_selector=RepositorySelector(
                repositoryLocationName=repository_location_name,
                repositoryName=repository_name,
            ),
        ).add_dynamic_partition

        match result.typename__:
            case "AddDynamicPartitionSuccess":
                return DgApiDynamicPartition(
                    partitions_def_name=result.partitions_def_name,  # ty: ignore[unresolved-attribute]
                    partition_key=result.partition_key,  # ty: ignore[unresolved-attribute]
                )
            case "DuplicateDynamicPartitionError":
                raise DagsterPlusClientError(f"Partition already exists: {result.message}")  # ty: ignore[unresolved-attribute]
            case "UnauthorizedError":
                raise DagsterPlusUnauthorizedError(f"Error adding partition: {result.message}")  # ty: ignore[unresolved-attribute]
            case "PythonError":
                raise DagsterPlusServerError(f"Error adding partition: {result.message}")  # ty: ignore[unresolved-attribute]
            case _ as unreachable:
                assert_never(unreachable)

    def delete_dynamic_partitions(
        self,
        *,
        partitions_def_name: str,
        partition_keys: list[str],
        repository_location_name: str,
        repository_name: str,
        wipe_materializations: bool = False,
    ) -> DgApiDynamicPartitionsDeleteResult:
        if len(partition_keys) > MAX_DYNAMIC_PARTITIONS_PER_DELETE:
            raise DagsterPlusClientError(
                f"Delete at most {MAX_DYNAMIC_PARTITIONS_PER_DELETE} partitions at a time;"
                f" got {len(partition_keys)}."
            )
        result = self._client.delete_dynamic_partitions(
            partitions_def_name=partitions_def_name,
            partition_keys=partition_keys,
            repository_selector=RepositorySelector(
                repositoryLocationName=repository_location_name,
                repositoryName=repository_name,
            ),
            wipe_materializations=wipe_materializations,
        ).delete_dynamic_partitions

        match result.typename__:
            case "DeleteDynamicPartitionsSuccess":
                return DgApiDynamicPartitionsDeleteResult(
                    partitions_def_name=result.partitions_def_name,  # ty: ignore[unresolved-attribute]
                    partition_keys=partition_keys,
                )
            case "UnsupportedOperationError":
                raise DagsterPlusClientError(f"Error deleting partitions: {result.message}")  # ty: ignore[unresolved-attribute]
            case "UnauthorizedError":
                raise DagsterPlusUnauthorizedError(f"Error deleting partitions: {result.message}")  # ty: ignore[unresolved-attribute]
            case "PythonError":
                raise DagsterPlusServerError(f"Error deleting partitions: {result.message}")  # ty: ignore[unresolved-attribute]
            case _ as unreachable:
                assert_never(unreachable)
