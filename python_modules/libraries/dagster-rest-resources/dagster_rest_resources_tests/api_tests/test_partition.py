from unittest.mock import Mock

import pytest
from dagster_rest_resources.__generated__.add_dynamic_partition import (
    AddDynamicPartition,
    AddDynamicPartitionAddDynamicPartitionAddDynamicPartitionSuccess,
    AddDynamicPartitionAddDynamicPartitionDuplicateDynamicPartitionError,
    AddDynamicPartitionAddDynamicPartitionPythonError,
    AddDynamicPartitionAddDynamicPartitionUnauthorizedError,
)
from dagster_rest_resources.__generated__.delete_dynamic_partitions import (
    DeleteDynamicPartitions,
    DeleteDynamicPartitionsDeleteDynamicPartitionsDeleteDynamicPartitionsSuccess,
    DeleteDynamicPartitionsDeleteDynamicPartitionsPythonError,
    DeleteDynamicPartitionsDeleteDynamicPartitionsUnauthorizedError,
    DeleteDynamicPartitionsDeleteDynamicPartitionsUnsupportedOperationError,
)
from dagster_rest_resources.__generated__.input_types import RepositorySelector
from dagster_rest_resources.api.partition import (
    MAX_DYNAMIC_PARTITIONS_PER_DELETE,
    DgApiPartitionApi,
)
from dagster_rest_resources.gql_client import IGraphQLClient
from dagster_rest_resources.schemas.exception import (
    DagsterPlusClientError,
    DagsterPlusServerError,
    DagsterPlusUnauthorizedError,
)

SELECTOR = RepositorySelector(repositoryLocationName="loc", repositoryName="repo")


class TestCreateDynamicPartition:
    def test_adds_the_key(self):
        client = Mock(spec=IGraphQLClient)
        client.add_dynamic_partition.return_value = AddDynamicPartition(
            addDynamicPartition=AddDynamicPartitionAddDynamicPartitionAddDynamicPartitionSuccess(
                __typename="AddDynamicPartitionSuccess",
                partitionsDefName="customers",
                partitionKey="acme",
            )
        )

        result = DgApiPartitionApi(client).create_dynamic_partition(
            partitions_def_name="customers",
            partition_key="acme",
            repository_location_name="loc",
            repository_name="repo",
        )

        client.add_dynamic_partition.assert_called_once_with(
            partitions_def_name="customers", partition_key="acme", repository_selector=SELECTOR
        )
        assert (result.partitions_def_name, result.partition_key) == ("customers", "acme")

    def test_duplicate_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.add_dynamic_partition.return_value = AddDynamicPartition(
            addDynamicPartition=AddDynamicPartitionAddDynamicPartitionDuplicateDynamicPartitionError(
                __typename="DuplicateDynamicPartitionError", message=""
            )
        )
        with pytest.raises(DagsterPlusClientError, match="already exists"):
            DgApiPartitionApi(client).create_dynamic_partition(
                partitions_def_name="customers",
                partition_key="acme",
                repository_location_name="loc",
                repository_name="repo",
            )

    def test_unauthorized_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.add_dynamic_partition.return_value = AddDynamicPartition(
            addDynamicPartition=AddDynamicPartitionAddDynamicPartitionUnauthorizedError(
                __typename="UnauthorizedError", message=""
            )
        )
        with pytest.raises(DagsterPlusUnauthorizedError, match="Error adding partition"):
            DgApiPartitionApi(client).create_dynamic_partition(
                partitions_def_name="customers",
                partition_key="acme",
                repository_location_name="loc",
                repository_name="repo",
            )

    def test_python_error_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.add_dynamic_partition.return_value = AddDynamicPartition(
            addDynamicPartition=AddDynamicPartitionAddDynamicPartitionPythonError(
                __typename="PythonError", message=""
            )
        )
        with pytest.raises(DagsterPlusServerError, match="Error adding partition"):
            DgApiPartitionApi(client).create_dynamic_partition(
                partitions_def_name="customers",
                partition_key="acme",
                repository_location_name="loc",
                repository_name="repo",
            )


class TestDeleteDynamicPartitions:
    def test_deletes_the_keys(self):
        client = Mock(spec=IGraphQLClient)
        client.delete_dynamic_partitions.return_value = DeleteDynamicPartitions(
            deleteDynamicPartitions=DeleteDynamicPartitionsDeleteDynamicPartitionsDeleteDynamicPartitionsSuccess(
                __typename="DeleteDynamicPartitionsSuccess", partitionsDefName="customers"
            )
        )

        result = DgApiPartitionApi(client).delete_dynamic_partitions(
            partitions_def_name="customers",
            partition_keys=["acme", "globex"],
            repository_location_name="loc",
            repository_name="repo",
            wipe_materializations=True,
        )

        client.delete_dynamic_partitions.assert_called_once_with(
            partitions_def_name="customers",
            partition_keys=["acme", "globex"],
            repository_selector=SELECTOR,
            wipe_materializations=True,
        )
        assert result.partition_keys == ["acme", "globex"]

    def test_unauthorized_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.delete_dynamic_partitions.return_value = DeleteDynamicPartitions(
            deleteDynamicPartitions=DeleteDynamicPartitionsDeleteDynamicPartitionsUnauthorizedError(
                __typename="UnauthorizedError", message=""
            )
        )
        with pytest.raises(DagsterPlusUnauthorizedError, match="Error deleting partitions"):
            DgApiPartitionApi(client).delete_dynamic_partitions(
                partitions_def_name="customers",
                partition_keys=["acme"],
                repository_location_name="loc",
                repository_name="repo",
            )

    def test_unsupported_operation_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.delete_dynamic_partitions.return_value = DeleteDynamicPartitions(
            deleteDynamicPartitions=DeleteDynamicPartitionsDeleteDynamicPartitionsUnsupportedOperationError(
                __typename="UnsupportedOperationError", message=""
            )
        )
        with pytest.raises(DagsterPlusClientError, match="Error deleting partitions"):
            DgApiPartitionApi(client).delete_dynamic_partitions(
                partitions_def_name="customers",
                partition_keys=["acme"],
                repository_location_name="loc",
                repository_name="repo",
            )

    def test_python_error_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.delete_dynamic_partitions.return_value = DeleteDynamicPartitions(
            deleteDynamicPartitions=DeleteDynamicPartitionsDeleteDynamicPartitionsPythonError(
                __typename="PythonError", message=""
            )
        )
        with pytest.raises(DagsterPlusServerError, match="Error deleting partitions"):
            DgApiPartitionApi(client).delete_dynamic_partitions(
                partitions_def_name="customers",
                partition_keys=["acme"],
                repository_location_name="loc",
                repository_name="repo",
            )

    def test_deletes_up_to_the_limit(self):
        client = Mock(spec=IGraphQLClient)
        client.delete_dynamic_partitions.return_value = DeleteDynamicPartitions(
            deleteDynamicPartitions=DeleteDynamicPartitionsDeleteDynamicPartitionsDeleteDynamicPartitionsSuccess(
                __typename="DeleteDynamicPartitionsSuccess", partitionsDefName="customers"
            )
        )
        keys = [f"key-{i}" for i in range(MAX_DYNAMIC_PARTITIONS_PER_DELETE)]

        result = DgApiPartitionApi(client).delete_dynamic_partitions(
            partitions_def_name="customers",
            partition_keys=keys,
            repository_location_name="loc",
            repository_name="repo",
        )

        assert result.partition_keys == keys

    def test_over_the_limit_raises(self):
        client = Mock(spec=IGraphQLClient)
        with pytest.raises(
            DagsterPlusClientError, match="at most 100 partitions at a time; got 101"
        ):
            DgApiPartitionApi(client).delete_dynamic_partitions(
                partitions_def_name="customers",
                partition_keys=[f"key-{i}" for i in range(MAX_DYNAMIC_PARTITIONS_PER_DELETE + 1)],
                repository_location_name="loc",
                repository_name="repo",
            )
        client.delete_dynamic_partitions.assert_not_called()
