import json
import dateutil.parser

from airflow.exceptions import AirflowException

from dagster import check
from dagster.seven.json import JSONDecodeError


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


def airflow_storage_exception(tmp_dir):
    return AirflowException(
        'No storage config found -- must configure either filesystem or s3 storage for '
        'the DagsterPythonOperator. Ex.: \n'
        'storage:\n'
        '  filesystem:\n'
        '    base_dir: \'{tmp_dir}\''
        '\n\n --or--\n\n'
        'storage:\n'
        '  s3:\n'
        '    s3_bucket: \'my-s3-bucket\'\n'.format(tmp_dir=tmp_dir)
    )
