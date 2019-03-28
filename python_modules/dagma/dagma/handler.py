import logging
import pickle

import boto3

from io import BytesIO

from dagster import check, PipelineDefinition
from dagster.core.execution import (
    construct_system_pipeline_execution_context,
    RunConfig,
    ExecutionContext,
)
from dagster.core.execution_context import SystemPipelineExecutionContext
from dagster.core.execution_plan.objects import ExecutionStepEvent
from dagster.core.execution_plan.simple_engine import execute_step_in_memory

from .serialize import deserialize, serialize
from .utils import get_input_key, get_resources_key, get_step_key, LambdaInvocationPayload

logger = logging.getLogger(__name__)


def _all_inputs_covered(step, results):
    for step_input in step.step_inputs:
        handle = step_input.prev_output_handle
        if (handle.step.key, handle.output_name) not in results:
            return False
    return True


def aws_lambda_handler(event, _context):
    """The lambda handler function."""
    logger.setLevel(logging.INFO)

    (
        run_id,
        step_idx,
        key,
        s3_bucket,
        s3_key_inputs,
        s3_key_body,
        s3_key_resources,
        s3_key_outputs,
    ) = LambdaInvocationPayload(*event['config'])

    s3 = boto3.client('s3')

    logger.info(
        'Beginning execution of lambda function for run_id %s step %s (%s)', run_id, step_idx, key
    )
    logger.info('Looking for inputs at %s/%s', s3_bucket, s3_key_inputs)

    intermediate_results_object = s3.get_object(Bucket=s3_bucket, Key=s3_key_inputs)
    intermediate_results = deserialize(intermediate_results_object['Body'].read())

    logger.info('Looking for resources at %s/%s', s3_bucket, s3_key_resources)
    resources_object = s3.get_object(Bucket=s3_bucket, Key=s3_key_resources)
    resources = deserialize(resources_object['Body'].read())
    execution_context = construct_system_pipeline_execution_context(
        pipeline=PipelineDefinition(name='dummy', solids=[]),
        run_config=RunConfig(run_id=run_id),
        execution_context=ExecutionContext(loggers=[logger]),
        resources=resources,
        environment_config={},
    )

    logger.info('Looking for step body at %s/%s', s3_bucket, s3_key_body)
    step_body_object = s3.get_object(Bucket=s3_bucket, Key=s3_key_body)
    step = deserialize(step_body_object['Body'].read())

    logger.info('Checking inputs')
    if not _all_inputs_covered(step, intermediate_results):
        result_keys = set(intermediate_results.keys())
        expected_outputs = [ni.prev_output_handle for ni in step.step_inputs]
        logger.error(
            'Not all inputs covered for %s. Not executing.\nKeys in result: %s'
            '\nOutputs needed for inputs %s',
            key,
            result_keys,
            expected_outputs,
        )
        raise Exception()

    logger.info('Constructing input values')
    input_values = {}
    for step_input in step.step_inputs:
        prev_output_handle = step_input.prev_output_handle
        handle = (prev_output_handle.step.key, prev_output_handle.output_name)
        # FIXME - we need a less hacky strategy for serializing and deserializing input handles and
        # result values -- the subscript below is like accessing .step_output_data on the namedtuple
        # in the simple engine
        input_value = intermediate_results[handle][1].value
        input_values[step_input.name] = input_value

    logger.info('Executing step {key}'.format(key=key))
    step_events = list(execute_step_in_memory(step, execution_context, input_values))

    for step_event in step_events:
        check.invariant(isinstance(step_event, ExecutionStepEvent))
        output_name = step_event.step_output_data.output_name
        output_handle = (step.key, output_name)
        intermediate_results[output_handle] = (
            step_event.success,
            step_event.step_output_data,
            step_event.step_failure_data,
        )
        logger.info('Processing result: %s', output_name)

    logger.info('Uploading intermediate_results to %s', s3_key_outputs)
    s3.put_object(
        ACL='public-read',
        Body=serialize(intermediate_results),
        Bucket=s3_bucket,
        Key=s3_key_outputs,
    )
