import os
import runpy
import sys
import warnings

from dagster import execute_pipeline, RunConfig
from dagster_examples.intro_tutorial.resources_full import resources_pipeline, HELLO_MESSAGE


def has_message(events, message):
    for event in events:
        if message == event.user_message:
            return True

    return False


TEMP_DAGSTER_MESSAGE_DIR = '/tmp/dagster-messages'


def test_run_local():

    if os.path.exists(TEMP_DAGSTER_MESSAGE_DIR):
        os.unlink(TEMP_DAGSTER_MESSAGE_DIR)

    result = execute_pipeline(
        resources_pipeline,
        run_config=RunConfig(mode='local'),
        environment_dict={
            'resources': {'slack': {'config': {'output_path': TEMP_DAGSTER_MESSAGE_DIR}}}
        },
    )

    assert result.success

    with open('/tmp/dagster-messages', 'rb') as f:
        assert HELLO_MESSAGE.encode() in f.read()


def test_resources():
    # Why?!? Because
    # http://python-notes.curiousefficiency.org/en/latest/python_concepts/import_traps.html#the-double-import-trap
    # (Nothing to see here)
    if not sys.warnoptions:  # allow overriding with `-W` option
        warnings.filterwarnings('ignore', category=RuntimeWarning, module='runpy')

    runpy.run_module('dagster_examples.intro_tutorial.resources_full', run_name='__main__')
