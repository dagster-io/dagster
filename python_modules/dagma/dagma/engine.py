"""The core dagma execution engine."""

import base64
import io
import json
import os
import pickle
import shutil
import subprocess
import tempfile

from collections import namedtuple

import cloudpickle as pickle

from dagster import check
from dagster.core.execution_context import RuntimeExecutionContext
from dagster.core.execution_plan.objects import ExecutionPlan
from dagster.utils.zip import zip_folder

from .config import (ASSUME_ROLE_POLICY_DOCUMENT, BUCKET_POLICY_DOCUMENT_TEMPLATE)
from .serialize import (
    deserialize,
    serialize,
)
from .utils import (
    get_deployment_package_key,
    get_input_key,
    get_resources_key,
    get_step_key,
    LambdaInvocationPayload,
)

# TODO make this configurable on the dagma resource
LAMBDA_MEMORY_SIZE = 3008

# TODO: rip out this horror
TEMPDIR_REGISTRY = []

SOURCE_DIR = os.path.dirname(os.path.abspath(__file__))


def _get_or_create_iam_role(iam_client, iam_resource):
    try:
        role = iam_client.create_role(
            RoleName=
            'dagster_lambda_iam_role',  # TODO make the role name configurable on the resource
            AssumeRolePolicyDocument=ASSUME_ROLE_POLICY_DOCUMENT,
        )
    except iam_client.exceptions.EntityAlreadyExistsException:
        role = iam_resource.Role('dagster_lambda_iam_role')
        role.load()
    return role


def _get_or_create_s3_bucket(s3_client, aws_region, role, context):
    try:
        s3_client.create_bucket(
            ACL='private',
            Bucket=context.resources.dagma.
            s3_bucket,  # TODO make the bucket name configurable on the resource
            CreateBucketConfiguration={
                'LocationConstraint': aws_region,
            },
        )
    except s3_client.exceptions.BucketAlreadyOwnedByYou:
        pass

    policy = BUCKET_POLICY_DOCUMENT_TEMPLATE.format(
        role_arn=role.arn, bucket_arn='arn:aws:s3:::' + context.resources.dagma.s3_bucket
    )
    context.debug(policy)
    s3_client.put_bucket_policy(
        Bucket=context.resources.dagma.s3_bucket,
        Policy=policy,
    )


def _seed_intermediate_results(context):
    intermediate_results = {}
    return context.resources.dagma.storage.put_object(
        key=get_input_key(context, 0),
        body=serialize(intermediate_results),
    )


# FIXME only do this *once* -- actually, this can live in a publicly accessible S3 bucket of its
# own
def _construct_deployment_package_for_step(step_idx, step, context):
    python_dependencies = [
        'boto3', 'cloudpickler', 'git+ssh://git@github.com/dagster-io/dagster.git'
        '@lambda_engine#egg=dagma&subdirectory=python_modules/dagma'
    ]

    deployment_package_dir = tempfile.mkdtemp()
    TEMPDIR_REGISTRY.append(deployment_package_dir)

    for python_dependency in python_dependencies:
        process = subprocess.Popen(
            ['pip', 'install', python_dependency, '--target', deployment_package_dir],
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE
        )
        for line in iter(process.stdout.readline, b''):
            context.debug(line.decode('utf-8'))

    archive_dir = tempfile.mkdtemp()
    TEMPDIR_REGISTRY.append(archive_dir)
    archive_path = os.path.join(tempfile.mkdtemp(), get_deployment_package_key(context, step_idx))

    try:
        pwd = os.getcwd()
        os.chdir(deployment_package_dir)
        zip_folder('.', archive_path)
        context.debug(
            'Zipped archive at {archive_path}: {size} bytes'.format(
                archive_path=archive_path, size=os.path.getsize(archive_path)
            )
        )
    finally:
        os.chdir(pwd)

    return archive_path


def _upload_deployment_package_for_step(context, deployment_package_path):
    with open(deployment_package_path, 'rb') as fd:
        return context.resources.dagma.storage.put_object(
            key=os.path.basename(deployment_package_path),
            body=fd,
        )


def _upload_step(s3, step_idx, step, context):
    return context.resources.dagma.storage.put_object(
        key=get_step_key(context, step_idx),
        body=serialize(step),
    )


def _create_lambda_step(aws_lambda, step_idx, deployment_package, context, role):
    res = aws_lambda.create_function(
        FunctionName=get_deployment_package_key(context, step_idx).split('.')[0],
        Runtime='python3.6',
        Role=role.arn,
        Handler='dagma.aws_lambda_handler',
        Code={
            'S3Bucket': context.resources.dagma.s3_bucket,
            'S3Key': deployment_package,
        },
        Description='Handler for run {run_id} step {step_idx}'.format(
            run_id=context.run_id, step_idx='0'
        ),
        Timeout=900,
        MemorySize=LAMBDA_MEMORY_SIZE,
        Publish=True,
        Tags={'dagster_lambda_run_id': context.run_id}
    )
    context.debug(str(res))
    return res


def _execute_step_async(lambda_client, lambda_step, context, payload):
    #   InvocationType='Event'|'RequestResponse'|'DryRun',
    # when we switch to Event, we'll need to poll Cloudwatch
    # log_group_name = '/aws/lambda/{function_name}'
    # .format(function_name='{run_id}_hello_world'.format(run_id=run_id))
    # aws_cloudwatch_client.get_log_events(
    # logGroupName='/aws/lambda/{function_name}'
    # .format(function_name='{run_id}_hello_world'.format(run_id=run_id)))
    # aws_cloudwatch_client.describe_log_streams(
    #     logGroupName=log_group_name,
    #     orderBy='LastEventTime',
    #     descending=True,
    # #     nextToken='string',
    # #     limit=123
    # )
    pass


def _execute_step_sync(lambda_client, lambda_step, context, payload):
    res = lambda_client.invoke(
        FunctionName=lambda_step['FunctionArn'],
        Payload=json.dumps({
            'config': list(payload)
        }),
        InvocationType='RequestResponse',
        LogType='Tail',
    )

    for line in base64.b64decode(res['LogResult']).split(b'\n'):
        if True:
            context.info(str(line))
            #  FIXME switch on the log type
        else:
            context.info(line)


def execute_plan(context, execution_plan, cleanup_lambda_functions=True, local=False):
    """Core executor."""
    check.inst_param(context, 'context', RuntimeExecutionContext)
    check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)

    steps = list(execution_plan.topological_steps())

    if not steps:
        context.debug(
            'Pipeline {pipeline} has no nodes and no execution will happen'.format(
                pipeline=context.pipeline
            )
        )
        return

    context.debug(
        'About to compile the compute node graph to lambda in the following order {order}'.format(
            order=[step.key for step in steps]
        )
    )

    check.invariant(len(steps[0].step_inputs) == 0)

    aws_lambda_client = context.resources.dagma.session.client('lambda')
    aws_iam_client = context.resources.dagma.session.client('iam')
    aws_iam_resource = context.resources.dagma.session.resource('iam')
    aws_cloudwatch_client = context.resources.dagma.session.client('logs')
    aws_s3_client = context.resources.dagma.session.client('s3')
    aws_region_name = context.resources.dagma.aws_region_name

    context.debug('Creating IAM role')
    role = _get_or_create_iam_role(aws_iam_client, aws_iam_resource)

    context.debug('Creating S3 bucket')
    _get_or_create_s3_bucket(aws_s3_client, aws_region_name, role, context)

    context.debug('Seeding intermediate results')
    _seed_intermediate_results(context)

    context.debug('Uploading execution_context')
    context.resources.dagma.storage.put_object(
        key=get_resources_key(context),
        body=serialize(context.resources),
    )

    deployment_packages = []
    try:
        for step_idx, step in enumerate(steps):
            if local:
                continue
            context.debug(
                'Constructing deployment package for step {step_key}'.format(step_key=step.key)
            )
            deployment_packages.append(
                _construct_deployment_package_for_step(step_idx, step, context)
            )
        for step_idx, step in enumerate(steps):
            context.debug(
                'Uploading deployment package for step {step_key}: {s3_key}'.format(
                    step_key=step.key, s3_key=get_deployment_package_key(context, step_idx)
                )
            )
            _upload_deployment_package_for_step(context, deployment_packages[step_idx])

            context.debug(
                'Uploading step {step_key}: {s3_key}'.format(
                    step_key=step.key, s3_key=get_step_key(context, step_idx)
                )
            )
            _upload_step(aws_s3_client, step_idx, step, context)

    finally:
        for tempdir in TEMPDIR_REGISTRY:
            context.debug('Cleaning up deployment package: {tempdir}'.format(tempdir=tempdir))
            try:
                shutil.rmtree(tempdir)
            except IOError as e:
                context.debug(
                    'FileNotFoundError when cleaning up deployment package %s: %s', tempdir,
                    e.strerror
                )

    lambda_steps = []
    try:
        for step_idx, step in enumerate(steps):
            lambda_steps.append(
                _create_lambda_step(
                    aws_lambda_client,
                    step_idx,
                    os.path.basename(deployment_packages[step_idx]),
                    context,
                    role,
                )
            )

    # 'LambdaInvocationPayload', 'run_id step_idx key s3_bucket s3_key_inputs s3_key_body'
    # 's3_key_resources s3_key_outputs'

        for step_idx, lambda_step in enumerate(lambda_steps):
            payload = LambdaInvocationPayload(
                context.run_id,
                step_idx,
                steps[step_idx].key,
                context.resources.dagma.s3_bucket,
                get_input_key(context, step_idx),
                get_step_key(context, step_idx),
                get_resources_key(context),
                get_input_key(context, step_idx + 1),
            )

            _execute_step_sync(aws_lambda_client, lambda_step, context, payload)
            # _poll_for_completion(step_handle, context)  # TODO: Need an error handling path here

        final_results_object = context.resources.dagma.storage.get_object(
            key=get_input_key(context, step_idx + 1)
        )

        final_results = deserialize(final_results_object['Body'].read())

        return final_results

    finally:
        if cleanup_lambda_functions:
            for lambda_step in lambda_steps:
                context.debug(
                    'Deleting lambda function: {name}'.format(name=lambda_step['FunctionName'])
                )
                aws_lambda_client.delete_function(FunctionName=lambda_step['FunctionName'])
