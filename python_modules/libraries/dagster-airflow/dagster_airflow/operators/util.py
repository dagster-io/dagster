import logging
import os

import dateutil.parser
from airflow.exceptions import AirflowException, AirflowSkipException
from dagster_graphql.client.mutations import execute_execute_plan_mutation
from dagster_graphql.client.query import EXECUTE_PLAN_MUTATION
from dagster_graphql.client.util import construct_execute_plan_variables

from dagster import DagsterEventType, check, seven
from dagster.core.events import DagsterEvent
from dagster.core.instance import AIRFLOW_EXECUTION_DATE_STR, DagsterInstance
from dagster.utils.hosted_user_process import create_in_process_ephemeral_workspace


def check_events_for_failures(events):
    check.list_param(events, 'events', of_type=DagsterEvent)
    for event in events:
        if event.event_type_value == 'STEP_FAILURE':
            raise AirflowException(
                'step failed with error: %s' % event.event_specific_data.error.to_string()
            )


# Using AirflowSkipException is a canonical way for tasks to skip themselves; see example
# here: http://bit.ly/2YtigEm
def check_events_for_skips(events):
    check.list_param(events, 'events', of_type=DagsterEvent)
    skipped = any([e.event_type_value == DagsterEventType.STEP_SKIPPED.value for e in events])
    if skipped:
        raise AirflowSkipException('Dagster emitted skip event, skipping execution in Airflow')


def convert_airflow_datestr_to_epoch_ts(airflow_ts):
    '''convert_airflow_datestr_to_epoch_ts
    Converts Airflow time strings (e.g. 2019-06-26T17:19:09+00:00) to epoch timestamps.
    '''
    dt = dateutil.parser.parse(airflow_ts)
    return (dt - dateutil.parser.parse('1970-01-01T00:00:00+00:00')).total_seconds()


def get_aws_environment():
    '''
    Return AWS environment variables for Docker and Kubernetes execution.
    '''
    default_env = {}

    # Note that if these env vars are set in Kubernetes, anyone with access to pods in that
    # namespace can retrieve them. This may not be appropriate for all environments.

    # Also, if these env vars are set as blank vars, the behavior depends on boto version:
    # https://github.com/boto/botocore/pull/1687
    # It's safer to check-and-set since if interpreted as blank strings they'll break the
    # cred retrieval chain (such as on-disk or metadata-API creds).
    aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')

    # The creds _also_ break if you only set one of them.
    if aws_access_key_id and aws_secret_access_key:
        # TODO: also get region env var this way, since boto commands may fail without it
        default_env.update(
            {'AWS_ACCESS_KEY_ID': aws_access_key_id, 'AWS_SECRET_ACCESS_KEY': aws_secret_access_key}
        )
    elif aws_access_key_id or aws_secret_access_key:
        raise ValueError(
            'If `propagate_aws_vars=True`, must provide either both of AWS_ACCESS_KEY_ID '
            'and AWS_SECRET_ACCESS_KEY env vars, or neither.'
        )

    return default_env


def check_storage_specified(run_config, error_message_base_dir_ex='\'/tmp/special_place\''):
    if 'storage' not in run_config:
        raise AirflowException(
            'No storage config found -- must configure storage accessible from all nodes (e.g. s3) '
            'Ex.: \n'
            'storage:\n'
            '  filesystem:\n'
            '    base_dir: {error_message_base_dir_ex}'
            '\n\n --or--\n\n'
            'storage:\n'
            '  s3:\n'
            '    s3_bucket: \'my-s3-bucket\'\n'
            '\n\n --or--\n\n'
            'storage:\n'
            '  gcs:\n'
            '    gcs_bucket: \'my-gcs-bucket\'\n'.format(
                error_message_base_dir_ex=error_message_base_dir_ex
            )
        )

    check.invariant(
        'in_memory' not in run_config.get('storage', {}),
        'Cannot use in-memory storage with Airflow. Must use storage '
        'available from all nodes (e.g. s3)',
    )
    return


def invoke_steps_within_python_operator(
    invocation_args, ts, dag_run, **kwargs
):  # pylint: disable=unused-argument
    mode = invocation_args.mode
    pipeline_name = invocation_args.pipeline_name
    step_keys = invocation_args.step_keys
    instance_ref = invocation_args.instance_ref
    run_config = invocation_args.run_config
    recon_repo = invocation_args.recon_repo
    pipeline_snapshot = invocation_args.pipeline_snapshot
    execution_plan_snapshot = invocation_args.execution_plan_snapshot
    parent_pipeline_snapshot = invocation_args.parent_pipeline_snapshot

    run_id = dag_run.run_id

    variables = construct_execute_plan_variables(
        recon_repo, mode, run_config, pipeline_name, run_id, step_keys
    )

    logging.info(
        'Executing GraphQL query: {query}\n'.format(query=EXECUTE_PLAN_MUTATION)
        + 'with variables:\n'
        + seven.json.dumps(variables, indent=2)
    )
    instance = DagsterInstance.from_ref(instance_ref) if instance_ref else None
    if instance:
        tags = {AIRFLOW_EXECUTION_DATE_STR: ts} if ts else {}
        instance.register_managed_run(
            pipeline_name=pipeline_name,
            run_id=run_id,
            run_config=run_config,
            mode=mode,
            solids_to_execute=None,
            step_keys_to_execute=None,
            tags=tags,
            root_run_id=None,
            parent_run_id=None,
            pipeline_snapshot=pipeline_snapshot,
            execution_plan_snapshot=execution_plan_snapshot,
            parent_pipeline_snapshot=parent_pipeline_snapshot,
        )

        workspace = create_in_process_ephemeral_workspace(pointer=recon_repo.pointer)
        events = execute_execute_plan_mutation(workspace, variables, instance_ref=instance_ref,)
        check_events_for_failures(events)
        check_events_for_skips(events)
        return events


def airflow_tags_for_ts(ts):
    ''' Converts an Airflow timestamp string to a list of tags.
    '''
    check.opt_str_param(ts, 'ts')

    return [
        {'key': AIRFLOW_EXECUTION_DATE_STR, 'value': ts},
    ]
