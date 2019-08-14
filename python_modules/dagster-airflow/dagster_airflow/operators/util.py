import json
import os

import dateutil.parser
from airflow.exceptions import AirflowSkipException

from dagster import check, DagsterEventType
from dagster.core.events import DagsterEvent
from dagster.seven.json import JSONDecodeError


def skip_self_if_necessary(events):
    '''Using AirflowSkipException is a canonical way for tasks to skip themselves; see example
    here: http://bit.ly/2YtigEm
    '''
    check.list_param(events, 'events', of_type=DagsterEvent)

    skipped = any([e.event_type_value == DagsterEventType.STEP_SKIPPED.value for e in events])

    if skipped:
        raise AirflowSkipException('Dagster emitted skip event, skipping execution in Airflow')


def construct_variables(mode, environment_dict, pipeline_name, run_id, ts, step_keys):
    check.str_param(mode, 'mode')
    # env dict could be either string 'REDACTED' or dict
    check.str_param(pipeline_name, 'pipeline_name')
    check.str_param(run_id, 'run_id')
    check.opt_str_param(ts, 'ts')
    check.list_param(step_keys, 'step_keys', of_type=str)

    variables = {
        'executionParams': {
            'environmentConfigData': environment_dict,
            'mode': mode,
            'selector': {'name': pipeline_name},
            'executionMetadata': {'runId': run_id},
            'stepKeys': step_keys,
        }
    }

    # If an Airflow timestamp string is provided, stash it (and the converted version) in tags
    if ts is not None:
        variables['executionParams']['executionMetadata']['tags'] = [
            {'key': 'airflow_ts', 'value': ts},
            {
                'key': 'execution_epoch_time',
                'value': '%f' % convert_airflow_datestr_to_epoch_ts(ts),
            },
        ]

    return variables


def parse_raw_res(raw_res):
    res = None
    # FIXME
    # Unfortunately, log lines don't necessarily come back in order...
    # This is error-prone, if something else logs JSON
    lines = list(filter(None, reversed(raw_res.split('\n'))))

    for line in lines:
        try:
            res = json.loads(line)
            break
        # If we don't get a GraphQL response, check the next line
        except JSONDecodeError:
            continue

    return res


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
