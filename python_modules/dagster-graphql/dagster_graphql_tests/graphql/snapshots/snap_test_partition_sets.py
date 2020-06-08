# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['test_get_all_partition_sets 1'] = {
    'partitionSetsOrError': {
        '__typename': 'PartitionSets',
        'results': [
            {
                'mode': 'foo_mode',
                'name': 'partition_based_multi_mode_decorator_partitions',
                'pipelineName': 'multi_mode_with_loggers',
                'solidSelection': None
            },
            {
                'mode': 'default',
                'name': 'solid_selection_daily_decorator_partitions',
                'pipelineName': 'no_config_chain_pipeline',
                'solidSelection': [
                    'return_foo'
                ]
            },
            {
                'mode': 'default',
                'name': 'solid_selection_hourly_decorator_partitions',
                'pipelineName': 'no_config_chain_pipeline',
                'solidSelection': [
                    'return_foo'
                ]
            },
            {
                'mode': 'default',
                'name': 'solid_selection_monthly_decorator_partitions',
                'pipelineName': 'no_config_chain_pipeline',
                'solidSelection': [
                    'return_foo'
                ]
            },
            {
                'mode': 'default',
                'name': 'solid_selection_weekly_decorator_partitions',
                'pipelineName': 'no_config_chain_pipeline',
                'solidSelection': [
                    'return_foo'
                ]
            },
            {
                'mode': 'default',
                'name': 'environment_dict_error_schedule_partitions',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': None
            },
            {
                'mode': 'default',
                'name': 'integer_partition',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': [
                    'return_hello'
                ]
            },
            {
                'mode': 'default',
                'name': 'partition_based_decorator_partitions',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': None
            },
            {
                'mode': 'default',
                'name': 'scheduled_integer_partitions',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': None
            },
            {
                'mode': 'default',
                'name': 'should_execute_error_schedule_partitions',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': None
            },
            {
                'mode': 'default',
                'name': 'tags_error_schedule_partitions',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': None
            },
            {
                'mode': 'default',
                'name': 'enum_partition',
                'pipelineName': 'noop_pipeline',
                'solidSelection': None
            }
        ]
    }
}

snapshots['test_get_partition_sets_for_pipeline 1'] = {
    'partitionSetsOrError': {
        '__typename': 'PartitionSets',
        'results': [
            {
                'mode': 'default',
                'name': 'environment_dict_error_schedule_partitions',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': None
            },
            {
                'mode': 'default',
                'name': 'integer_partition',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': [
                    'return_hello'
                ]
            },
            {
                'mode': 'default',
                'name': 'partition_based_decorator_partitions',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': None
            },
            {
                'mode': 'default',
                'name': 'scheduled_integer_partitions',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': None
            },
            {
                'mode': 'default',
                'name': 'should_execute_error_schedule_partitions',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': None
            },
            {
                'mode': 'default',
                'name': 'tags_error_schedule_partitions',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': None
            }
        ]
    }
}

snapshots['test_get_partition_sets_for_pipeline 2'] = {
    'partitionSetsOrError': {
        '__typename': 'PipelineNotFoundError',
        'message': 'Could not find Pipeline <<in_process>>.test_repo.invalid_pipeline'
    }
}

snapshots['test_get_partition_set 1'] = {
    'partitionSetOrError': {
        '__typename': 'PartitionSet',
        'mode': 'default',
        'name': 'integer_partition',
        'partitions': {
            'results': [
                {
                    'name': '0'
                },
                {
                    'name': '1'
                },
                {
                    'name': '2'
                },
                {
                    'name': '3'
                },
                {
                    'name': '4'
                },
                {
                    'name': '5'
                },
                {
                    'name': '6'
                },
                {
                    'name': '7'
                },
                {
                    'name': '8'
                },
                {
                    'name': '9'
                }
            ]
        },
        'pipelineName': 'no_config_pipeline',
        'solidSelection': [
            'return_hello'
        ]
    }
}

snapshots['test_get_partition_set 2'] = {
    'partitionSetOrError': {
        '__typename': 'PartitionSetNotFoundError'
    }
}

snapshots['TestSolidSelections.test_get_all_partition_sets[readonly_in_memory_instance_in_process_env] 1'] = {
    'partitionSetsOrError': {
        '__typename': 'PartitionSets',
        'results': [
            {
                'mode': 'foo_mode',
                'name': 'partition_based_multi_mode_decorator_partitions',
                'pipelineName': 'multi_mode_with_loggers',
                'solidSelection': None
            },
            {
                'mode': 'default',
                'name': 'solid_selection_daily_decorator_partitions',
                'pipelineName': 'no_config_chain_pipeline',
                'solidSelection': [
                    'return_foo'
                ]
            },
            {
                'mode': 'default',
                'name': 'solid_selection_hourly_decorator_partitions',
                'pipelineName': 'no_config_chain_pipeline',
                'solidSelection': [
                    'return_foo'
                ]
            },
            {
                'mode': 'default',
                'name': 'solid_selection_monthly_decorator_partitions',
                'pipelineName': 'no_config_chain_pipeline',
                'solidSelection': [
                    'return_foo'
                ]
            },
            {
                'mode': 'default',
                'name': 'solid_selection_weekly_decorator_partitions',
                'pipelineName': 'no_config_chain_pipeline',
                'solidSelection': [
                    'return_foo'
                ]
            },
            {
                'mode': 'default',
                'name': 'environment_dict_error_schedule_partitions',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': None
            },
            {
                'mode': 'default',
                'name': 'integer_partition',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': [
                    'return_hello'
                ]
            },
            {
                'mode': 'default',
                'name': 'partition_based_decorator_partitions',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': None
            },
            {
                'mode': 'default',
                'name': 'scheduled_integer_partitions',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': None
            },
            {
                'mode': 'default',
                'name': 'should_execute_error_schedule_partitions',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': None
            },
            {
                'mode': 'default',
                'name': 'tags_error_schedule_partitions',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': None
            },
            {
                'mode': 'default',
                'name': 'enum_partition',
                'pipelineName': 'noop_pipeline',
                'solidSelection': None
            }
        ]
    }
}

snapshots['TestSolidSelections.test_get_all_partition_sets[readonly_in_memory_instance_out_of_process_env] 1'] = {
    'partitionSetsOrError': {
        '__typename': 'PythonError',
        'message': '''dagster.check.CheckError: Invariant failed. Description: [legacy] must be in process loc
''',
        'stack': [
            '''  File "/Users/sashankthupukari/projects/dagster/python_modules/dagster-graphql/dagster_graphql/implementation/utils.py", line 14, in _fn
    return fn(*args, **kwargs)
''',
            '''  File "/Users/sashankthupukari/projects/dagster/python_modules/dagster-graphql/dagster_graphql/implementation/fetch_partition_sets.py", line 12, in get_partition_sets_or_error
    results=_get_partition_sets(graphene_info, pipeline_name)
''',
            '''  File "/Users/sashankthupukari/projects/dagster/python_modules/dagster-graphql/dagster_graphql/implementation/fetch_partition_sets.py", line 43, in _get_partition_sets
    key=lambda partition_set: (
''',
            '''  File "/Users/sashankthupukari/projects/dagster/python_modules/dagster-graphql/dagster_graphql/implementation/fetch_partition_sets.py", line 41, in <listcomp>
    for external_partition_set in sorted(
''',
            '''  File "/Users/sashankthupukari/projects/dagster/python_modules/dagster-graphql/dagster_graphql/implementation/context.py", line 130, in legacy_get_repository_definition
    '[legacy] must be in process loc',
''',
            '''  File "/Users/sashankthupukari/projects/dagster/python_modules/dagster/dagster/check/__init__.py", line 166, in invariant
    CheckError('Invariant failed. Description: {desc}'.format(desc=desc))
''',
            '''  File "/Users/sashankthupukari/.pyenv/versions/3.7.5/envs/dagster-3.7.5/lib/python3.7/site-packages/future/utils/__init__.py", line 446, in raise_with_traceback
    raise exc.with_traceback(traceback)
'''
        ]
    }
}

snapshots['TestSolidSelections.test_get_all_partition_sets[readonly_sqlite_instance_in_process_env] 1'] = {
    'partitionSetsOrError': {
        '__typename': 'PartitionSets',
        'results': [
            {
                'mode': 'foo_mode',
                'name': 'partition_based_multi_mode_decorator_partitions',
                'pipelineName': 'multi_mode_with_loggers',
                'solidSelection': None
            },
            {
                'mode': 'default',
                'name': 'solid_selection_daily_decorator_partitions',
                'pipelineName': 'no_config_chain_pipeline',
                'solidSelection': [
                    'return_foo'
                ]
            },
            {
                'mode': 'default',
                'name': 'solid_selection_hourly_decorator_partitions',
                'pipelineName': 'no_config_chain_pipeline',
                'solidSelection': [
                    'return_foo'
                ]
            },
            {
                'mode': 'default',
                'name': 'solid_selection_monthly_decorator_partitions',
                'pipelineName': 'no_config_chain_pipeline',
                'solidSelection': [
                    'return_foo'
                ]
            },
            {
                'mode': 'default',
                'name': 'solid_selection_weekly_decorator_partitions',
                'pipelineName': 'no_config_chain_pipeline',
                'solidSelection': [
                    'return_foo'
                ]
            },
            {
                'mode': 'default',
                'name': 'environment_dict_error_schedule_partitions',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': None
            },
            {
                'mode': 'default',
                'name': 'integer_partition',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': [
                    'return_hello'
                ]
            },
            {
                'mode': 'default',
                'name': 'partition_based_decorator_partitions',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': None
            },
            {
                'mode': 'default',
                'name': 'scheduled_integer_partitions',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': None
            },
            {
                'mode': 'default',
                'name': 'should_execute_error_schedule_partitions',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': None
            },
            {
                'mode': 'default',
                'name': 'tags_error_schedule_partitions',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': None
            },
            {
                'mode': 'default',
                'name': 'enum_partition',
                'pipelineName': 'noop_pipeline',
                'solidSelection': None
            }
        ]
    }
}

snapshots['TestSolidSelections.test_get_all_partition_sets[readonly_sqlite_instance_out_of_process_env] 1'] = {
    'partitionSetsOrError': {
        '__typename': 'PythonError',
        'message': '''dagster.check.CheckError: Invariant failed. Description: [legacy] must be in process loc
''',
        'stack': [
            '''  File "/Users/sashankthupukari/projects/dagster/python_modules/dagster-graphql/dagster_graphql/implementation/utils.py", line 14, in _fn
    return fn(*args, **kwargs)
''',
            '''  File "/Users/sashankthupukari/projects/dagster/python_modules/dagster-graphql/dagster_graphql/implementation/fetch_partition_sets.py", line 12, in get_partition_sets_or_error
    results=_get_partition_sets(graphene_info, pipeline_name)
''',
            '''  File "/Users/sashankthupukari/projects/dagster/python_modules/dagster-graphql/dagster_graphql/implementation/fetch_partition_sets.py", line 43, in _get_partition_sets
    key=lambda partition_set: (
''',
            '''  File "/Users/sashankthupukari/projects/dagster/python_modules/dagster-graphql/dagster_graphql/implementation/fetch_partition_sets.py", line 41, in <listcomp>
    for external_partition_set in sorted(
''',
            '''  File "/Users/sashankthupukari/projects/dagster/python_modules/dagster-graphql/dagster_graphql/implementation/context.py", line 130, in legacy_get_repository_definition
    '[legacy] must be in process loc',
''',
            '''  File "/Users/sashankthupukari/projects/dagster/python_modules/dagster/dagster/check/__init__.py", line 166, in invariant
    CheckError('Invariant failed. Description: {desc}'.format(desc=desc))
''',
            '''  File "/Users/sashankthupukari/.pyenv/versions/3.7.5/envs/dagster-3.7.5/lib/python3.7/site-packages/future/utils/__init__.py", line 446, in raise_with_traceback
    raise exc.with_traceback(traceback)
'''
        ]
    }
}

snapshots['TestSolidSelections.test_get_partition_sets_for_pipeline[readonly_in_memory_instance_in_process_env] 1'] = {
    'partitionSetsOrError': {
        '__typename': 'PartitionSets',
        'results': [
            {
                'mode': 'default',
                'name': 'environment_dict_error_schedule_partitions',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': None
            },
            {
                'mode': 'default',
                'name': 'integer_partition',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': [
                    'return_hello'
                ]
            },
            {
                'mode': 'default',
                'name': 'partition_based_decorator_partitions',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': None
            },
            {
                'mode': 'default',
                'name': 'scheduled_integer_partitions',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': None
            },
            {
                'mode': 'default',
                'name': 'should_execute_error_schedule_partitions',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': None
            },
            {
                'mode': 'default',
                'name': 'tags_error_schedule_partitions',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': None
            }
        ]
    }
}

snapshots['TestSolidSelections.test_get_partition_sets_for_pipeline[readonly_in_memory_instance_in_process_env] 2'] = {
    'partitionSetsOrError': {
        '__typename': 'PipelineNotFoundError',
        'message': 'Could not find Pipeline <<in_process>>.test_repo.invalid_pipeline'
    }
}

snapshots['TestSolidSelections.test_get_partition_sets_for_pipeline[readonly_in_memory_instance_out_of_process_env] 1'] = {
    'partitionSetsOrError': {
        '__typename': 'PythonError',
        'message': '''dagster.check.CheckError: Invariant failed. Description: [legacy] must be in process loc
''',
        'stack': [
            '''  File "/Users/sashankthupukari/projects/dagster/python_modules/dagster-graphql/dagster_graphql/implementation/utils.py", line 14, in _fn
    return fn(*args, **kwargs)
''',
            '''  File "/Users/sashankthupukari/projects/dagster/python_modules/dagster-graphql/dagster_graphql/implementation/fetch_partition_sets.py", line 12, in get_partition_sets_or_error
    results=_get_partition_sets(graphene_info, pipeline_name)
''',
            '''  File "/Users/sashankthupukari/projects/dagster/python_modules/dagster-graphql/dagster_graphql/implementation/fetch_partition_sets.py", line 43, in _get_partition_sets
    key=lambda partition_set: (
''',
            '''  File "/Users/sashankthupukari/projects/dagster/python_modules/dagster-graphql/dagster_graphql/implementation/fetch_partition_sets.py", line 41, in <listcomp>
    for external_partition_set in sorted(
''',
            '''  File "/Users/sashankthupukari/projects/dagster/python_modules/dagster-graphql/dagster_graphql/implementation/context.py", line 130, in legacy_get_repository_definition
    '[legacy] must be in process loc',
''',
            '''  File "/Users/sashankthupukari/projects/dagster/python_modules/dagster/dagster/check/__init__.py", line 166, in invariant
    CheckError('Invariant failed. Description: {desc}'.format(desc=desc))
''',
            '''  File "/Users/sashankthupukari/.pyenv/versions/3.7.5/envs/dagster-3.7.5/lib/python3.7/site-packages/future/utils/__init__.py", line 446, in raise_with_traceback
    raise exc.with_traceback(traceback)
'''
        ]
    }
}

snapshots['TestSolidSelections.test_get_partition_sets_for_pipeline[readonly_in_memory_instance_out_of_process_env] 2'] = {
    'partitionSetsOrError': {
        '__typename': 'PipelineNotFoundError',
        'message': 'Could not find Pipeline test.test_repo.invalid_pipeline'
    }
}

snapshots['TestSolidSelections.test_get_partition_sets_for_pipeline[readonly_sqlite_instance_in_process_env] 1'] = {
    'partitionSetsOrError': {
        '__typename': 'PartitionSets',
        'results': [
            {
                'mode': 'default',
                'name': 'environment_dict_error_schedule_partitions',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': None
            },
            {
                'mode': 'default',
                'name': 'integer_partition',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': [
                    'return_hello'
                ]
            },
            {
                'mode': 'default',
                'name': 'partition_based_decorator_partitions',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': None
            },
            {
                'mode': 'default',
                'name': 'scheduled_integer_partitions',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': None
            },
            {
                'mode': 'default',
                'name': 'should_execute_error_schedule_partitions',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': None
            },
            {
                'mode': 'default',
                'name': 'tags_error_schedule_partitions',
                'pipelineName': 'no_config_pipeline',
                'solidSelection': None
            }
        ]
    }
}

snapshots['TestSolidSelections.test_get_partition_sets_for_pipeline[readonly_sqlite_instance_in_process_env] 2'] = {
    'partitionSetsOrError': {
        '__typename': 'PipelineNotFoundError',
        'message': 'Could not find Pipeline <<in_process>>.test_repo.invalid_pipeline'
    }
}

snapshots['TestSolidSelections.test_get_partition_sets_for_pipeline[readonly_sqlite_instance_out_of_process_env] 1'] = {
    'partitionSetsOrError': {
        '__typename': 'PythonError',
        'message': '''dagster.check.CheckError: Invariant failed. Description: [legacy] must be in process loc
''',
        'stack': [
            '''  File "/Users/sashankthupukari/projects/dagster/python_modules/dagster-graphql/dagster_graphql/implementation/utils.py", line 14, in _fn
    return fn(*args, **kwargs)
''',
            '''  File "/Users/sashankthupukari/projects/dagster/python_modules/dagster-graphql/dagster_graphql/implementation/fetch_partition_sets.py", line 12, in get_partition_sets_or_error
    results=_get_partition_sets(graphene_info, pipeline_name)
''',
            '''  File "/Users/sashankthupukari/projects/dagster/python_modules/dagster-graphql/dagster_graphql/implementation/fetch_partition_sets.py", line 43, in _get_partition_sets
    key=lambda partition_set: (
''',
            '''  File "/Users/sashankthupukari/projects/dagster/python_modules/dagster-graphql/dagster_graphql/implementation/fetch_partition_sets.py", line 41, in <listcomp>
    for external_partition_set in sorted(
''',
            '''  File "/Users/sashankthupukari/projects/dagster/python_modules/dagster-graphql/dagster_graphql/implementation/context.py", line 130, in legacy_get_repository_definition
    '[legacy] must be in process loc',
''',
            '''  File "/Users/sashankthupukari/projects/dagster/python_modules/dagster/dagster/check/__init__.py", line 166, in invariant
    CheckError('Invariant failed. Description: {desc}'.format(desc=desc))
''',
            '''  File "/Users/sashankthupukari/.pyenv/versions/3.7.5/envs/dagster-3.7.5/lib/python3.7/site-packages/future/utils/__init__.py", line 446, in raise_with_traceback
    raise exc.with_traceback(traceback)
'''
        ]
    }
}

snapshots['TestSolidSelections.test_get_partition_sets_for_pipeline[readonly_sqlite_instance_out_of_process_env] 2'] = {
    'partitionSetsOrError': {
        '__typename': 'PipelineNotFoundError',
        'message': 'Could not find Pipeline test.test_repo.invalid_pipeline'
    }
}

snapshots['TestSolidSelections.test_get_partition_set[readonly_in_memory_instance_in_process_env] 1'] = {
    'partitionSetOrError': {
        '__typename': 'PartitionSet',
        'mode': 'default',
        'name': 'integer_partition',
        'partitions': {
            'results': [
                {
                    'name': '0'
                },
                {
                    'name': '1'
                },
                {
                    'name': '2'
                },
                {
                    'name': '3'
                },
                {
                    'name': '4'
                },
                {
                    'name': '5'
                },
                {
                    'name': '6'
                },
                {
                    'name': '7'
                },
                {
                    'name': '8'
                },
                {
                    'name': '9'
                }
            ]
        },
        'pipelineName': 'no_config_pipeline',
        'solidSelection': [
            'return_hello'
        ]
    }
}

snapshots['TestSolidSelections.test_get_partition_set[readonly_in_memory_instance_in_process_env] 2'] = {
    'partitionSetOrError': {
        '__typename': 'PartitionSetNotFoundError'
    }
}

snapshots['TestSolidSelections.test_get_partition_set[readonly_in_memory_instance_out_of_process_env] 1'] = {
    'partitionSetOrError': {
        '__typename': 'PythonError',
        'message': '''dagster.check.CheckError: Invariant failed. Description: [legacy] must be in process loc
''',
        'stack': [
            '''  File "/Users/sashankthupukari/projects/dagster/python_modules/dagster-graphql/dagster_graphql/implementation/utils.py", line 14, in _fn
    return fn(*args, **kwargs)
''',
            '''  File "/Users/sashankthupukari/projects/dagster/python_modules/dagster-graphql/dagster_graphql/implementation/fetch_partition_sets.py", line 60, in get_partition_set
    partition_set_def=graphene_info.context.legacy_get_repository_definition().get_partition_set_def(
''',
            '''  File "/Users/sashankthupukari/projects/dagster/python_modules/dagster-graphql/dagster_graphql/implementation/context.py", line 130, in legacy_get_repository_definition
    '[legacy] must be in process loc',
''',
            '''  File "/Users/sashankthupukari/projects/dagster/python_modules/dagster/dagster/check/__init__.py", line 166, in invariant
    CheckError('Invariant failed. Description: {desc}'.format(desc=desc))
''',
            '''  File "/Users/sashankthupukari/.pyenv/versions/3.7.5/envs/dagster-3.7.5/lib/python3.7/site-packages/future/utils/__init__.py", line 446, in raise_with_traceback
    raise exc.with_traceback(traceback)
'''
        ]
    }
}

snapshots['TestSolidSelections.test_get_partition_set[readonly_in_memory_instance_out_of_process_env] 2'] = {
    'partitionSetOrError': {
        '__typename': 'PartitionSetNotFoundError'
    }
}

snapshots['TestSolidSelections.test_get_partition_set[readonly_sqlite_instance_in_process_env] 1'] = {
    'partitionSetOrError': {
        '__typename': 'PartitionSet',
        'mode': 'default',
        'name': 'integer_partition',
        'partitions': {
            'results': [
                {
                    'name': '0'
                },
                {
                    'name': '1'
                },
                {
                    'name': '2'
                },
                {
                    'name': '3'
                },
                {
                    'name': '4'
                },
                {
                    'name': '5'
                },
                {
                    'name': '6'
                },
                {
                    'name': '7'
                },
                {
                    'name': '8'
                },
                {
                    'name': '9'
                }
            ]
        },
        'pipelineName': 'no_config_pipeline',
        'solidSelection': [
            'return_hello'
        ]
    }
}

snapshots['TestSolidSelections.test_get_partition_set[readonly_sqlite_instance_in_process_env] 2'] = {
    'partitionSetOrError': {
        '__typename': 'PartitionSetNotFoundError'
    }
}

snapshots['TestSolidSelections.test_get_partition_set[readonly_sqlite_instance_out_of_process_env] 1'] = {
    'partitionSetOrError': {
        '__typename': 'PythonError',
        'message': '''dagster.check.CheckError: Invariant failed. Description: [legacy] must be in process loc
''',
        'stack': [
            '''  File "/Users/sashankthupukari/projects/dagster/python_modules/dagster-graphql/dagster_graphql/implementation/utils.py", line 14, in _fn
    return fn(*args, **kwargs)
''',
            '''  File "/Users/sashankthupukari/projects/dagster/python_modules/dagster-graphql/dagster_graphql/implementation/fetch_partition_sets.py", line 60, in get_partition_set
    partition_set_def=graphene_info.context.legacy_get_repository_definition().get_partition_set_def(
''',
            '''  File "/Users/sashankthupukari/projects/dagster/python_modules/dagster-graphql/dagster_graphql/implementation/context.py", line 130, in legacy_get_repository_definition
    '[legacy] must be in process loc',
''',
            '''  File "/Users/sashankthupukari/projects/dagster/python_modules/dagster/dagster/check/__init__.py", line 166, in invariant
    CheckError('Invariant failed. Description: {desc}'.format(desc=desc))
''',
            '''  File "/Users/sashankthupukari/.pyenv/versions/3.7.5/envs/dagster-3.7.5/lib/python3.7/site-packages/future/utils/__init__.py", line 446, in raise_with_traceback
    raise exc.with_traceback(traceback)
'''
        ]
    }
}

snapshots['TestSolidSelections.test_get_partition_set[readonly_sqlite_instance_out_of_process_env] 2'] = {
    'partitionSetOrError': {
        '__typename': 'PartitionSetNotFoundError'
    }
}

snapshots['TestSolidSelections.test_get_all_partition_sets[readonly_sqlite_instance_multi_location] 1'] = {
    'partitionSetsOrError': {
        '__typename': 'PythonError',
        'message': '''dagster.check.CheckError: Invariant failed. Description: [legacy] must be in process loc
''',
        'stack': [
            '''  File "/Users/sashankthupukari/projects/dagster/python_modules/dagster-graphql/dagster_graphql/implementation/utils.py", line 14, in _fn
    return fn(*args, **kwargs)
''',
            '''  File "/Users/sashankthupukari/projects/dagster/python_modules/dagster-graphql/dagster_graphql/implementation/fetch_partition_sets.py", line 12, in get_partition_sets_or_error
    results=_get_partition_sets(graphene_info, pipeline_name)
''',
            '''  File "/Users/sashankthupukari/projects/dagster/python_modules/dagster-graphql/dagster_graphql/implementation/fetch_partition_sets.py", line 43, in _get_partition_sets
    key=lambda partition_set: (
''',
            '''  File "/Users/sashankthupukari/projects/dagster/python_modules/dagster-graphql/dagster_graphql/implementation/fetch_partition_sets.py", line 41, in <listcomp>
    for external_partition_set in sorted(
''',
            '''  File "/Users/sashankthupukari/projects/dagster/python_modules/dagster-graphql/dagster_graphql/implementation/context.py", line 130, in legacy_get_repository_definition
    '[legacy] must be in process loc',
''',
            '''  File "/Users/sashankthupukari/projects/dagster/python_modules/dagster/dagster/check/__init__.py", line 166, in invariant
    CheckError('Invariant failed. Description: {desc}'.format(desc=desc))
''',
            '''  File "/Users/sashankthupukari/.pyenv/versions/3.7.5/envs/dagster-3.7.5/lib/python3.7/site-packages/future/utils/__init__.py", line 446, in raise_with_traceback
    raise exc.with_traceback(traceback)
'''
        ]
    }
}

snapshots['TestSolidSelections.test_get_partition_sets_for_pipeline[readonly_sqlite_instance_multi_location] 1'] = {
    'partitionSetsOrError': {
        '__typename': 'PythonError',
        'message': '''dagster.check.CheckError: Invariant failed. Description: [legacy] must be in process loc
''',
        'stack': [
            '''  File "/Users/sashankthupukari/projects/dagster/python_modules/dagster-graphql/dagster_graphql/implementation/utils.py", line 14, in _fn
    return fn(*args, **kwargs)
''',
            '''  File "/Users/sashankthupukari/projects/dagster/python_modules/dagster-graphql/dagster_graphql/implementation/fetch_partition_sets.py", line 12, in get_partition_sets_or_error
    results=_get_partition_sets(graphene_info, pipeline_name)
''',
            '''  File "/Users/sashankthupukari/projects/dagster/python_modules/dagster-graphql/dagster_graphql/implementation/fetch_partition_sets.py", line 43, in _get_partition_sets
    key=lambda partition_set: (
''',
            '''  File "/Users/sashankthupukari/projects/dagster/python_modules/dagster-graphql/dagster_graphql/implementation/fetch_partition_sets.py", line 41, in <listcomp>
    for external_partition_set in sorted(
''',
            '''  File "/Users/sashankthupukari/projects/dagster/python_modules/dagster-graphql/dagster_graphql/implementation/context.py", line 130, in legacy_get_repository_definition
    '[legacy] must be in process loc',
''',
            '''  File "/Users/sashankthupukari/projects/dagster/python_modules/dagster/dagster/check/__init__.py", line 166, in invariant
    CheckError('Invariant failed. Description: {desc}'.format(desc=desc))
''',
            '''  File "/Users/sashankthupukari/.pyenv/versions/3.7.5/envs/dagster-3.7.5/lib/python3.7/site-packages/future/utils/__init__.py", line 446, in raise_with_traceback
    raise exc.with_traceback(traceback)
'''
        ]
    }
}

snapshots['TestSolidSelections.test_get_partition_sets_for_pipeline[readonly_sqlite_instance_multi_location] 2'] = {
    'partitionSetsOrError': {
        '__typename': 'PipelineNotFoundError',
        'message': 'Could not find Pipeline test.test_repo.invalid_pipeline'
    }
}

snapshots['TestSolidSelections.test_get_partition_set[readonly_sqlite_instance_multi_location] 1'] = {
    'partitionSetOrError': {
        '__typename': 'PythonError',
        'message': '''dagster.check.CheckError: Invariant failed. Description: [legacy] must be in process loc
''',
        'stack': [
            '''  File "/Users/sashankthupukari/projects/dagster/python_modules/dagster-graphql/dagster_graphql/implementation/utils.py", line 14, in _fn
    return fn(*args, **kwargs)
''',
            '''  File "/Users/sashankthupukari/projects/dagster/python_modules/dagster-graphql/dagster_graphql/implementation/fetch_partition_sets.py", line 60, in get_partition_set
    partition_set_def=graphene_info.context.legacy_get_repository_definition().get_partition_set_def(
''',
            '''  File "/Users/sashankthupukari/projects/dagster/python_modules/dagster-graphql/dagster_graphql/implementation/context.py", line 130, in legacy_get_repository_definition
    '[legacy] must be in process loc',
''',
            '''  File "/Users/sashankthupukari/projects/dagster/python_modules/dagster/dagster/check/__init__.py", line 166, in invariant
    CheckError('Invariant failed. Description: {desc}'.format(desc=desc))
''',
            '''  File "/Users/sashankthupukari/.pyenv/versions/3.7.5/envs/dagster-3.7.5/lib/python3.7/site-packages/future/utils/__init__.py", line 446, in raise_with_traceback
    raise exc.with_traceback(traceback)
'''
        ]
    }
}

snapshots['TestSolidSelections.test_get_partition_set[readonly_sqlite_instance_multi_location] 2'] = {
    'partitionSetOrError': {
        '__typename': 'PartitionSetNotFoundError'
    }
}
