from dagster import ExecutionTargetHandle, execute_pipeline


def test_dask_cluster(dask_address, s3_bucket):
    result = execute_pipeline(
        ExecutionTargetHandle.for_pipeline_module(
            'dagster_examples.toys.hammer', 'hammer_pipeline'
        ).build_pipeline_definition(),
        environment_dict={
            'storage': {'s3': {'config': {'s3_bucket': s3_bucket}}},
            'execution': {'dask': {'config': {'address': '%s:8786' % dask_address}}},
        },
    )
    assert result.success
    assert result.result_for_solid('reducer').output_value() == 4
