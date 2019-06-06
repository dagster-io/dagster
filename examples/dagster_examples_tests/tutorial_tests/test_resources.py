import runpy
import sys
import warnings

from dagster import execute_pipeline, RunConfig
from dagster_examples.intro_tutorial.resources_full import define_resources_pipeline


def has_message(events, message):
    for event in events:
        if message == event.user_message:
            return True

    return False


def test_run_local():
    result = execute_pipeline(
        define_resources_pipeline(),
        run_config=RunConfig(mode='local'),
        environment_dict={'resources': {'say_hi': {'config': {'output': '/tmp/dagster-messages'}}}},
    )

    assert result.success

    with open('/tmp/dagster-messages', 'rb') as f:
        assert b'#dagster -- Hello from Dagster!' in f.read()


def test_resources():
    # Why?!? Because
    # http://python-notes.curiousefficiency.org/en/latest/python_concepts/import_traps.html#the-double-import-trap
    # (Nothing to see here)
    if not sys.warnoptions:  # allow overriding with `-W` option
        warnings.filterwarnings('ignore', category=RuntimeWarning, module='runpy')

    runpy.run_module('dagster_examples.intro_tutorial.resources_full', run_name='__main__')
