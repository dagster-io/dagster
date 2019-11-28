import os

import boto3
import pytest
from dagster_aws.emr.resources import emr_pyspark_resource
from dagster_pyspark import pyspark_resource, pyspark_solid
from moto import mock_emr

from dagster import (
    DagsterInvalidDefinitionError,
    Field,
    ModeDefinition,
    RunConfig,
    execute_pipeline,
    pipeline,
)
from dagster.seven import mock


@pyspark_solid
def example_solid(context):
    list_p = [('John', 19), ('Jennifer', 29), ('Adam', 35), ('Henry', 50)]
    rdd = context.resources.pyspark.spark_context.parallelize(list_p)
    res = rdd.take(2)
    for name, age in res:
        context.log.info('%s: %d' % (name, age))


@pyspark_solid(
    name='blah', description='this is a test', config={'foo': Field(str), 'bar': Field(int)}
)
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
@mock.patch('dagster_aws.emr.resources.EMRPySparkResource.wait_for_steps')
def test_pyspark_emr(mock_wait):
    client = boto3.client('emr', region_name='us-west-1')

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

    job_flow_id = client.run_job_flow(**run_job_flow_args)['JobFlowId']
    result = execute_pipeline(
        example_pipe,
        environment_dict={
            'solids': {'blah': {'config': {'foo': 'a string', 'bar': 123}}},
            'resources': {
                'pyspark': {
                    'config': {
                        'pipeline_file': __file__,
                        'pipeline_fn_name': 'example_pipe',
                        'job_flow_id': job_flow_id,
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
                            'job_flow_id': 'some_job_flow_id',
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


@pytest.mark.skip
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
                        'job_flow_id': os.environ.get('AWS_EMR_JOB_FLOW_ID'),
                        'staging_bucket': 'dagster-scratch-80542c2',
                        'region_name': 'us-west-1',
                    }
                }
            },
        },
        run_config=RunConfig(mode='prod'),
    )
    assert result.success
