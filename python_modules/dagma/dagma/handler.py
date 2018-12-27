import logging
import pickle

import boto3

from dagster import check
from dagster.core.execution_context import RuntimeExecutionContext
from dagster.core.execution_plan.objects import (
    StepOutputHandle,
    StepResult,
)
from dagster.core.execution_plan.simple_engine import (
    _all_inputs_covered,
    execute_step,
)

from .utils import (
    get_input_key,
    get_resources_key,
    get_step_key,
    LambdaInvocationPayload,
)

logger = logging.getLogger(__name__)


def aws_lambda_handler(event, context):
    """The lambda handler function."""
    logger.setLevel(logging.INFO)

    (
        run_id, step_idx, key, s3_bucket, s3_key_inputs, s3_key_body, s3_key_resources,
        s3_key_outputs
    ) = LambdaInvocationPayload(event['config'])

    s3 = boto3.client('s3')

    logger.info(
        'Beginning execution of lambda function for run_id %s step %s (%s)',
        run_id,
        step_idx,
        key,
    )
    logger.info('Looking for inputs at %s/%s', s3_bucket, s3_key_inputs)

    intermediate_results_object = s3.get_object(
        Bucket=s3_bucket,
        Key=s3_key_inputs,
    )
    intermediate_results = pickle.loads(intermediate_results_object['Body'].read())

    logger.info('Looking for resources at %s/%s', s3_bucket, s3_key_resources)
    resources_object = s3.get_object(
        Bucket=s3_bucket,
        Key=s3_key_resources,
    )
    resources = pickle.loads(resources_object['Body'].read())
    execution_context = RuntimeExecutionContext(run_id, loggers=[logger], resources=resources)

    logger.info('Looking for step body at %s/%s', s3_bucket, s3_key_body)
    step_body_object = s3.get_object(
        Bucket=s3_bucket,
        Key=s3_key_body,
    )
    step = pickle.loads(step_body_object['Body'].read())

    if not _all_inputs_covered(step, intermediate_results):
        result_keys = set(intermediate_results.keys())
        expected_outputs = [ni.prev_output_handle for ni in step.step_inputs]
        logger.error(
            'Not all inputs covered for %s. Not executing.\nKeys in result: %s'
            '\nOutputs need for inputs %s', key, result_keys, expected_outputs
        )
        raise Exception()

    input_values = {}
    for step_input in step.step_inputs:
        prev_output_handle = step_input.prev_output_handle
        input_value = intermediate_results[prev_output_handle].success_data.value
        input_values[step_input.name] = input_value

    logger.info('Executing step {key}'.format(key=key))
    results = [result for result in execute_step(step, execution_context, input_values)]

    for result in results:
        check.invariant(isinstance(result, StepResult))
        output_name = result.success_data.output_name
        output_handle = StepOutputHandle(step, output_name)
        intermediate_results[output_handle] = result
        logger.info('Processing result: %s', output_name)

    logger.info('Uploading intermediate_results to %s', s3_key_outputs)
    intermediate_results_object = pickle.dumps(intermediate_results, -1)
    s3.put_object(
        ACL='public-read',
        Body=intermediate_results_object,
        Bucket=s3_bucket,
        Key=s3_key_outputs,
    )
