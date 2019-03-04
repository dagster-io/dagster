import runpy
import sys
import warnings

from dagster import execute_pipeline, RunConfig
from dagster.tutorials.intro_tutorial.resources import define_resource_test_pipeline


def has_message(events, message):
    for event in events:
        if message == event.user_message:
            return True

    return False


def test_run_local():
    events = []

    def _event_callback(ev):
        events.append(ev)

    result = execute_pipeline(
        define_resource_test_pipeline(),
        environment_dict={
            'context': {'local': {}},
            'solids': {'add_ints': {'inputs': {'num_one': {'value': 2}, 'num_two': {'value': 3}}}},
        },
        run_config=RunConfig(event_callback=_event_callback),
    )

    assert result.success
    assert result.result_for_solid('add_ints').transformed_value() == 5

    assert has_message(events, 'Setting key=add value=5 in memory')
    assert not has_message(events, 'Setting key=add value=5 in cloud')


def test_run_cloud():
    events = []

    def _event_callback(ev):
        events.append(ev)

    result = execute_pipeline(
        define_resource_test_pipeline(),
        environment_dict={
            'context': {
                'cloud': {
                    'resources': {
                        'store': {'config': {'username': 'some_user', 'password': 'some_password'}}
                    }
                }
            },
            'solids': {'add_ints': {'inputs': {'num_one': {'value': 2}, 'num_two': {'value': 6}}}},
        },
        run_config=RunConfig(event_callback=_event_callback),
    )

    assert result.success
    assert result.result_for_solid('add_ints').transformed_value() == 8

    assert not has_message(events, 'Setting key=add value=8 in memory')
    assert has_message(events, 'Setting key=add value=8 in cloud')


def test_resources():
    # Why?!? Because
    # http://python-notes.curiousefficiency.org/en/latest/python_concepts/import_traps.html#the-double-import-trap
    # (Nothing to see here)
    if not sys.warnoptions:  # allow overriding with `-W` option
        warnings.filterwarnings('ignore', category=RuntimeWarning, module='runpy')

    runpy.run_module('dagster.tutorials.intro_tutorial.resources', run_name='__main__')
