import os

import pytest
from dagster_aws.emr import EmrJobRunner, emr_pyspark_resource
from dagster_pyspark import pyspark_resource, pyspark_solid
from moto import mock_emr

from dagster import (
    DagsterInvalidDefinitionError,
    ModeDefinition,
    RunConfig,
    execute_pipeline,
    pipeline,
)
from dagster.seven import mock
from dagster.utils.test import create_test_pipeline_execution_context


@pyspark_solid
def example_solid(context):
    list_p = [('John', 19), ('Jennifer', 29), ('Adam', 35), ('Henry', 50)]
    rdd = context.resources.pyspark.spark_context.parallelize(list_p)
    res = rdd.take(2)
    for name, age in res:
        context.log.info('%s: %d' % (name, age))


@pyspark_solid(name='blah', description='this is a test', config={'foo': str, 'bar': int})
def other_example_solid(context):
    list_p = [('John', 19), ('Jennifer', 29), ('Adam', 35), ('Henry', 50)]
    rdd = context.resources.pyspark.spark_context.parallelize(list_p)
    res = rdd.take(2)
    for name, age in res:
        context.log.info('%s: %d' % (name, age))


@pipeline(
    mode_defs=[
        ModeDefinition('prod', resource_defs={'pyspark': emr_pyspark_resource}),
        ModeDefinition('local', resource_defs={'pyspark': pyspark_resource}),
    ]
)
def example_pipe():
    example_solid()
    other_example_solid()


def test_local():
    result = execute_pipeline(
        example_pipe,
        environment_dict={'solids': {'blah': {'config': {'foo': 'a string', 'bar': 123}}},},
        run_config=RunConfig(mode='local'),
    )
    assert result.success


@mock_emr
@mock.patch('dagster_aws.emr.emr.EmrJobRunner.wait_for_steps_to_complete')
def test_pyspark_emr(mock_wait):
    run_job_flow_args = dict(
        Instances={
            'InstanceCount': 1,
            'KeepJobFlowAliveWhenNoSteps': True,
            'MasterInstanceType': 'c3.medium',
            'Placement': {'AvailabilityZone': 'us-west-1a'},
            'SlaveInstanceType': 'c3.xlarge',
        },
        JobFlowRole='EMR_EC2_DefaultRole',
        LogUri='s3://mybucket/log',
        Name='cluster',
        ServiceRole='EMR_DefaultRole',
        VisibleToAllUsers=True,
    )

    # Doing cluster setup outside of a solid here, because run_job_flow is not yet plumbed through
    # to the pyspark EMR resource.
    job_runner = EmrJobRunner(region='us-west-1')
    context = create_test_pipeline_execution_context()
    cluster_id = job_runner.run_job_flow(context, run_job_flow_args)

    result = execute_pipeline(
        example_pipe,
        environment_dict={
            'solids': {'blah': {'config': {'foo': 'a string', 'bar': 123}}},
            'resources': {
                'pyspark': {
                    'config': {
                        'pipeline_file': __file__,
                        'pipeline_fn_name': 'example_pipe',
                        'cluster_id': cluster_id,
                        'staging_bucket': 'dagster-scratch-80542c2',
                        'region_name': 'us-west-1',
                    }
                }
            },
        },
        run_config=RunConfig(mode='prod'),
    )
    assert result.success
    assert mock_wait.called_once


def test_bad_requirements_txt():
    with pytest.raises(DagsterInvalidDefinitionError) as exc_info:
        execute_pipeline(
            example_pipe,
            environment_dict={
                'solids': {'blah': {'config': {'foo': 'a string', 'bar': 123}}},
                'resources': {
                    'pyspark': {
                        'config': {
                            'requirements_file_path': 'DOES_NOT_EXIST',
                            'pipeline_file': __file__,
                            'pipeline_fn_name': 'example_pipe',
                            'cluster_id': 'some_cluster_id',
                            'staging_bucket': 'dagster-scratch-80542c2',
                            'region_name': 'us-west-1',
                        }
                    }
                },
            },
            run_config=RunConfig(mode='prod'),
        )
    assert 'The requirements.txt file that was specified does not exist' in str(exc_info.value)

    # We have to manually stop the pyspark context here because we interrupted before resources
    # were cleaned up, and so stop() was never called on the spark session.
    from pyspark.sql import SparkSession

    SparkSession.builder.getOrCreate().stop()


@pytest.mark.skipif(
    'AWS_EMR_TEST_DO_IT_LIVE' not in os.environ,
    reason='This test is slow and requires a live EMR cluster; run only upon explicit request',
)
def test_do_it_live_emr():
    result = execute_pipeline(
        example_pipe,
        environment_dict={
            'solids': {'blah': {'config': {'foo': 'a string', 'bar': 123}}},
            'resources': {
                'pyspark': {
                    'config': {
                        'pipeline_file': __file__,
                        'pipeline_fn_name': 'example_pipe',
                        'cluster_id': os.environ.get('AWS_EMR_JOB_FLOW_ID'),
                        'staging_bucket': 'dagster-scratch-80542c2',
                        'region_name': 'us-west-1',
                        'wait_for_logs': True,
                    }
                }
            },
        },
        run_config=RunConfig(mode='prod'),
    )
    assert result.success
