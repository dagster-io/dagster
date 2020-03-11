'''As an open source project, we collect usage statistics to inform development priorities.
For more information, check out the docs at https://docs.dagster.io/latest/install/telemetry/'

To see the logs we send, inspect $DAGSTER_HOME/logs/ if $DAGSTER_HOME is set or ~/.dagster/logs/

In fn `log_action`, we log:
  instance_id - Unique id for dagster instance
  action - Name of function called i.e. `execute_pipeline_started` (see: fn telemetry_wrapper)
  client_time - Client time
  elapsed_time - Time elapsed between start of function and end of function call
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
import yaml

from dagster.core.instance.config import DAGSTER_CONFIG_YAML_FILENAME

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


def get_log_dir():
    '''
    Get the directory where we store log files, creating the directory if needed.
    If $DAGSTER_HOME is set, return $DAGSTER_HOME/logs/
    Otherwise, return ~/.dagster/logs/
    '''
    dagster_home_path = _dagster_home_if_set()
    if dagster_home_path is None:
        dagster_home_path = os.path.expanduser(DAGSTER_HOME_FALLBACK)

    dagster_home_logs_path = dagster_home_path + '/logs/'
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
    os.path.join(get_log_dir(), 'event.log'), maxBytes=MAX_BYTES, backupCount=10
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
    if os.getenv('DAGSTER_TELEMETRY_ENABLED') == 'False':
        return

    try:
        (instance_id, dagster_telemetry_enabled) = _get_instance_id()

        if dagster_telemetry_enabled is False:
            return

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
        dagster_log_dir = get_log_dir()
        dagster_log_queue_dir = get_log_queue_dir()
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
                dagster_log_dir = get_log_dir()
                dagster_log_queue_dir = get_log_queue_dir()
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


def _get_instance_id():
    '''
    Get the instance id.

    If $DAGSTER_HOME is not set, use uuid.getnode() to generate unique id.
    If $DAGSTER_HOME is set, then access $DAGSTER_HOME/dagster.yaml to get telemetry.instance_id
    and telemetry.enabled. If telemetry.enabled is not False, then generate and save
    telemetry.instance_id and set telemetry.enabled to True.
    '''
    instance_id = None
    dagster_telemetry_enabled = None
    dagster_home_path = _dagster_home_if_set()

    if dagster_home_path is None:
        return (uuid.getnode(), True)

    instance_config_path = os.path.join(dagster_home_path, DAGSTER_CONFIG_YAML_FILENAME)

    if not os.path.exists(instance_config_path):
        with open(instance_config_path, 'w') as f:
            instance_id = str(uuid.getnode())
            dagster_telemetry_enabled = True
            yaml.dump(
                {
                    TELEMETRY_STR: {
                        INSTANCE_ID_STR: instance_id,
                        ENABLED_STR: dagster_telemetry_enabled,
                    }
                },
                f,
            )
    else:
        with open(instance_config_path, 'r') as f:
            instance_profile_json = yaml.load(f, Loader=yaml.FullLoader)
            if instance_profile_json is None:
                instance_profile_json = {}

            if TELEMETRY_STR in instance_profile_json:
                if INSTANCE_ID_STR in instance_profile_json[TELEMETRY_STR]:
                    instance_id = instance_profile_json[TELEMETRY_STR][INSTANCE_ID_STR]
                if ENABLED_STR in instance_profile_json[TELEMETRY_STR]:
                    dagster_telemetry_enabled = instance_profile_json[TELEMETRY_STR][ENABLED_STR]

        if not dagster_telemetry_enabled is False and (
            instance_id is None or dagster_telemetry_enabled is None
        ):
            if instance_id is None:
                instance_id = str(uuid.uuid4())
                instance_profile_json[TELEMETRY_STR][INSTANCE_ID_STR] = instance_id
            if dagster_telemetry_enabled is None:
                dagster_telemetry_enabled = True
                instance_profile_json[TELEMETRY_STR][ENABLED_STR] = dagster_telemetry_enabled

            with open(instance_config_path, 'w') as f:
                yaml.dump(instance_profile_json, f)

    return (instance_id, dagster_telemetry_enabled)


def execute_reset_telemetry_profile():
    '''
    Generate new instance_id in $DAGSTER_HOME/dagster.yaml. Must set $DAGSTER_HOME.
    '''
    dagster_home_path = _dagster_home_if_set()
    if not dagster_home_path:
        print('Must set $DAGSTER_HOME environment variable to reset profile')
        return

    instance_config_path = os.path.join(dagster_home_path, DAGSTER_CONFIG_YAML_FILENAME)
    if not os.path.exists(instance_config_path):
        with open(instance_config_path, 'w') as f:
            yaml.dump({TELEMETRY_STR: {INSTANCE_ID_STR: str(uuid.uuid4())}}, f)

    else:
        with open(instance_config_path, 'r') as f:
            instance_profile_json = yaml.load(f, Loader=yaml.FullLoader)
            if TELEMETRY_STR in instance_profile_json:
                instance_profile_json[TELEMETRY_STR][INSTANCE_ID_STR] = str(uuid.uuid4())
            else:
                instance_profile_json[TELEMETRY_STR] = {INSTANCE_ID_STR: str(uuid.uuid4())}

            with open(instance_config_path, 'w') as f:
                yaml.dump(instance_profile_json, f)


def execute_disable_telemetry():
    '''
    Disable telemetry by setting telemetry.enabled = False in $DAGSTER_HOME/dagster.yaml
    Must set $DAGSTER_HOME.
    '''
    _toggle_telemetry(False)


def execute_enable_telemetry():
    '''
    ENABLE telemetry by setting telemetry.enabled = True in $DAGSTER_HOME/dagster.yaml
    Must set $DAGSTER_HOME.
    '''
    _toggle_telemetry(True)


def _toggle_telemetry(enable_telemetry):
    dagster_home_path = _dagster_home_if_set()
    if not dagster_home_path:
        print(
            'Must set $DAGSTER_HOME environment variable to {enable_telemetry} telemetry'.format(
                enable_telemetry='enable' if enable_telemetry else 'disable'
            )
        )
        return

    instance_config_path = os.path.join(dagster_home_path, DAGSTER_CONFIG_YAML_FILENAME)

    if not os.path.exists(instance_config_path):
        with open(instance_config_path, 'w') as f:
            yaml.dump({TELEMETRY_STR: {ENABLED_STR: enable_telemetry}}, f)

    else:
        with open(instance_config_path, 'r') as f:
            instance_profile_json = yaml.load(f, Loader=yaml.FullLoader)
            if TELEMETRY_STR in instance_profile_json:
                instance_profile_json[TELEMETRY_STR][ENABLED_STR] = enable_telemetry
            else:
                instance_profile_json[TELEMETRY_STR] = {ENABLED_STR: enable_telemetry}

            with open(instance_config_path, 'w') as f:
                yaml.dump(instance_profile_json, f)
