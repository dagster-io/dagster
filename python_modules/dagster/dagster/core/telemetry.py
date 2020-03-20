'''As an open source project, we collect usage statistics to inform development priorities.
For more information, check out the docs at https://docs.dagster.io/latest/install/telemetry/'

To see the logs we send, inspect $DAGSTER_HOME/logs/ if $DAGSTER_HOME is set or ~/.dagster/logs/

In fn `log_action`, we log:
  action - Name of function called i.e. `execute_pipeline_started` (see: fn telemetry_wrapper)
  client_time - Client time
  elapsed_time - Time elapsed between start of function and end of function call
  event_id - Unique id for the event
  instance_id - Unique id for dagster instance
  metadata - More information i.e. pipeline success (boolean), (see: fn telemetry_wrapper)

For local development:
  Spin up local telemetry server and set DAGSTER_TELEMETRY_URL = 'http://localhost:3000/actions'
  To test RotatingFileHandler, can set MAX_BYTES = 500
'''

import datetime
import json
import logging
import os
import time
import uuid
import zlib
from logging.handlers import RotatingFileHandler

import requests
import six
import yaml

from dagster.core.instance import DagsterInstance

TELEMETRY_STR = 'telemetry'
INSTANCE_ID_STR = 'instance_id'
ENABLED_STR = 'enabled'
DAGSTER_HOME_FALLBACK = '~/.dagster'
DAGSTER_TELEMETRY_URL = 'http://telemetry.dagster.io/actions'
MAX_BYTES = 10485760  # 10 MB = 10 * 1024 * 1024 bytes


def _dagster_home_if_set():
    dagster_home_path = os.getenv('DAGSTER_HOME')

    if not dagster_home_path:
        return None

    return os.path.expanduser(dagster_home_path)


def get_dir_from_dagster_home(target_dir):
    '''
    If $DAGSTER_HOME is set, return $DAGSTER_HOME/<target_dir>/
    Otherwise, return ~/.dagster/<target_dir>/

    The 'logs' directory is used to cache logs before upload

    The '.logs_queue' directory is used to temporarily store logs during upload. This is to prevent
    dropping events or double-sending events that occur during the upload process.

    The 'telemetry' directory is used to store the instance_id
    '''
    dagster_home_path = _dagster_home_if_set()
    if dagster_home_path is None:
        dagster_home_path = os.path.expanduser(DAGSTER_HOME_FALLBACK)

    dagster_home_logs_path = os.path.join(dagster_home_path, target_dir)
    if not os.path.exists(dagster_home_logs_path):
        os.makedirs(dagster_home_logs_path)
    return dagster_home_logs_path


def get_log_queue_dir():
    '''
    Get the directory where we store log queue files, creating the directory if needed.

    The log queue directory is used to temporarily store logs during upload. This is to prevent
    dropping events or double-sending events that occur during the upload process.

    If $DAGSTER_HOME is set, return $DAGSTER_HOME/.logs_queue/
    Otherwise, return ~/.dagster/.logs_queue/
    '''
    dagster_home_path = _dagster_home_if_set()
    if dagster_home_path is None:
        dagster_home_path = os.path.expanduser(DAGSTER_HOME_FALLBACK)

    dagster_home_logs_queue_path = dagster_home_path + '/.logs_queue/'
    if not os.path.exists(dagster_home_logs_queue_path):
        os.makedirs(dagster_home_logs_queue_path)

    return dagster_home_logs_queue_path


handler = RotatingFileHandler(
    os.path.join(get_dir_from_dagster_home('logs'), 'event.log'), maxBytes=MAX_BYTES, backupCount=10
)

logger = logging.getLogger('telemetry_logger')
logger.setLevel(logging.INFO)
logger.addHandler(handler)


def log_action(action, client_time, elapsed_time=None, metadata=None):
    '''
    Log action in log directory

    instance_id - Unique id for dagster instance
    action - Name of function called i.e. `execute_pipeline_started` (see: fn telemetry_wrapper)
    client_time - Client time
    elapsed_time - Time elapsed between start of function and end of function call
    metadata - More information i.e. pipeline success (boolean), (see: fn telemetry_wrapper)

    If $DAGSTER_HOME is set, then use $DAGSTER_HOME/logs/
    Otherwise, use ~/.dagster/logs/
    '''
    try:
        dagster_telemetry_enabled = DagsterInstance.get().telemetry_enabled
        if dagster_telemetry_enabled:
            instance_id = _get_telemetry_instance_id()
            if instance_id == None:
                instance_id = _set_telemetry_instance_id()

            logger.info(
                json.dumps(
                    {
                        'action': action,
                        'client_time': str(client_time),
                        'elapsed_time': str(elapsed_time),
                        'event_id': str(uuid.uuid4()),
                        'instance_id': instance_id,
                        'metadata': metadata,
                    }
                )
            )
    except Exception:  # pylint: disable=broad-except
        pass


# Gets the instance_id at $DAGSTER_HOME/telemetry/id.yaml
def _get_telemetry_instance_id():
    telemetry_id_path = os.path.join(get_dir_from_dagster_home(TELEMETRY_STR), 'id.yaml')
    if os.path.exists(telemetry_id_path):
        with open(telemetry_id_path, 'r') as telemetry_id_file:
            telemetry_id_yaml = yaml.safe_load(telemetry_id_file)
            if INSTANCE_ID_STR in telemetry_id_yaml:
                if isinstance(telemetry_id_yaml[INSTANCE_ID_STR], six.string_types):
                    return telemetry_id_yaml[INSTANCE_ID_STR]
    return None


# Sets the instance_id at $DAGSTER_HOME/telemetry/id.yaml
def _set_telemetry_instance_id():
    telemetry_id_path = os.path.join(get_dir_from_dagster_home(TELEMETRY_STR), 'id.yaml')
    instance_id = str(uuid.uuid4())
    with open(telemetry_id_path, 'w') as telemetry_id_file:
        yaml.dump({INSTANCE_ID_STR: instance_id}, telemetry_id_file, default_flow_style=False)
    return instance_id


def telemetry_wrapper(f):
    '''
    Wrapper around functions that are logged. Will log the function_name, client_time, and
    elapsed_time.
    '''

    def wrap(*args, **kwargs):
        start_time = datetime.datetime.now()
        log_action(action=f.__name__ + '_started', client_time=start_time)
        result = f(*args, **kwargs)
        end_time = datetime.datetime.now()
        log_action(
            action=f.__name__ + '_ended',
            client_time=end_time,
            elapsed_time=end_time - start_time,
            metadata={'success': getattr(result, 'success', None)},
        )
        return result

    return wrap


def upload_logs():
    '''Upload logs to telemetry server every hour, or when log directory size is > 10MB'''
    try:
        last_run = datetime.datetime.now() - datetime.timedelta(minutes=120)
        dagster_log_dir = get_dir_from_dagster_home('logs')
        dagster_log_queue_dir = get_dir_from_dagster_home('.logs_queue')
        in_progress = False
        while True:
            log_size = 0
            if os.path.isdir(dagster_log_dir):
                log_size = sum(
                    os.path.getsize(os.path.join(dagster_log_dir, f))
                    for f in os.listdir(dagster_log_dir)
                    if os.path.isfile(os.path.join(dagster_log_dir, f))
                )

            log_queue_size = 0
            if os.path.isdir(dagster_log_queue_dir):
                log_queue_size = sum(
                    os.path.getsize(os.path.join(dagster_log_queue_dir, f))
                    for f in os.listdir(dagster_log_queue_dir)
                    if os.path.isfile(os.path.join(dagster_log_queue_dir, f))
                )

            if log_size == 0 and log_queue_size == 0:
                return

            if not in_progress and (
                datetime.datetime.now() - last_run > datetime.timedelta(minutes=60)
                or log_size >= MAX_BYTES
                or log_queue_size >= MAX_BYTES
            ):
                in_progress = True  # Prevent concurrent _upload_logs invocations
                last_run = datetime.datetime.now()
                dagster_log_dir = get_dir_from_dagster_home('logs')
                dagster_log_queue_dir = get_dir_from_dagster_home('.logs_queue')
                _upload_logs(dagster_log_dir, log_size, dagster_log_queue_dir)
                in_progress = False

            time.sleep(600)  # Sleep for 10 minutes
    except Exception:  # pylint: disable=broad-except
        pass


def _upload_logs(dagster_log_dir, log_size, dagster_log_queue_dir):
    '''Send POST request to telemetry server with the contents of $DAGSTER_HOME/log.txt'''
    try:
        if log_size > 0:
            # Delete contents of dagster_log_queue_dir so that new logs can be copied over
            for f in os.listdir(dagster_log_queue_dir):
                # Todo: there is probably a way to try to upload these logs without introducing
                # too much complexity...
                os.remove(os.path.join(dagster_log_queue_dir, f))

            os.rename(dagster_log_dir, dagster_log_queue_dir)

        for curr_path in os.listdir(dagster_log_queue_dir):
            curr_full_path = os.path.join(dagster_log_queue_dir, curr_path)
            retry_num = 0
            max_retries = 3
            success = False

            while not success and retry_num <= max_retries:
                with open(curr_full_path, 'rb') as curr_file:
                    byte = curr_file.read()

                    data = zlib.compress(byte, zlib.Z_BEST_COMPRESSION)
                    headers = {'content-encoding': 'gzip'}
                    r = requests.post(DAGSTER_TELEMETRY_URL, data=data, headers=headers)
                    if r.status_code == 200:
                        success = True
                    retry_num += 1

            if success:
                os.remove(curr_full_path)

    except Exception:  # pylint: disable=broad-except
        pass
