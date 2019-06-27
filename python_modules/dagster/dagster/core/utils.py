import datetime
import uuid
import toposort as toposort_

AIRFLOW_TS_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%f+00:00"


def convert_airflow_datestr_to_epoch_ts(airflow_ts):
    '''convert_airflow_datestr_to_epoch_ts
    Converts Airflow time strings (e.g. 2019-06-26T17:19:09.989485) to epoch timestamps.

    See: https://stackoverflow.com/a/50650878/11295366
    dt.timestamp() is not available in py2
    '''
    dt = datetime.datetime.strptime(airflow_ts, AIRFLOW_TS_DATETIME_FORMAT)
    return (dt - datetime.datetime(1970, 1, 1)).total_seconds()


def toposort(data):
    return [sorted(list(level)) for level in toposort_.toposort(data)]


def toposort_flatten(data):
    return [item for level in toposort(data) for item in level]


def make_new_run_id():
    return str(uuid.uuid4())
