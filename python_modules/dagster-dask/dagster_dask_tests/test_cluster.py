import pytest

from dagster import ExecutionTargetHandle, check, execute_pipeline
from dagster.core.instance import DagsterInstance


def test_dask_cluster(dask_address, s3_bucket):
    # https://github.com/dagster-io/dagster/issues/1748
    with pytest.raises(check.CheckError, match='Must use remote DagsterInstance'):

        _result = execute_pipeline(
            ExecutionTargetHandle.for_pipeline_module(
                'dagster_examples.toys.hammer', 'hammer_pipeline'
            ).build_pipeline_definition(),
            environment_dict={
                'storage': {'s3': {'config': {'s3_bucket': s3_bucket}}},
                'execution': {'dask': {'config': {'address': '%s:8786' % dask_address}}},
            },
            # needs to become remote to work
            instance=DagsterInstance.local_temp(),
        )
        # assert result.success
        # assert result.result_for_solid('reducer').output_value() == 4
