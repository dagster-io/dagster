from dagster import (
    DependencyDefinition,
    ExpectationResult,
    PipelineDefinition,
    solid,
    Materialization,
    Result,
    ModeDefinition,
    Nothing,
    OutputDefinition,
    InputDefinition,
    ExpectationDefinition,
    String,
    MultiDependencyDefinition,
)

from dagster.utils import merge_dicts

raw_files = [
    'raw_file_users',
    'raw_file_groups',
    'raw_file_events',
    'raw_file_friends',
    'raw_file_pages',
    'raw_file_fans',
    'raw_file_event_admins',
    'raw_file_group_admins',
]


def create_raw_file_solid(name):
    def do_expectation(_context, _value):
        return ExpectationResult(
            success=True, name='output_table_exists', message='Checked {name} exists'
        )

    @solid(
        name=name,
        outputs=[
            OutputDefinition(
                String,
                expectations=[
                    ExpectationDefinition(name='something', expectation_fn=do_expectation)
                ],
            )
        ],
        description='Inject raw file for input to table {} and do expectation on output'.format(
            name
        ),
    )
    def _f(_context):
        yield Materialization(path='/path/to/{}.raw'.format(name))
        yield Result(name)

    return _f


raw_tables = [
    'raw_users',
    'raw_groups',
    'raw_events',
    'raw_friends',
    'raw_pages',
    'raw_fans',
    'raw_event_admins',
    'raw_group_admins',
]


def create_raw_file_solids():
    return list(map(create_raw_file_solid, raw_files))


def input_name_for_raw_file(raw_file):
    return raw_file + '_ready'


@solid(
    inputs=[InputDefinition('start', Nothing)],
    outputs=[OutputDefinition(Nothing)],
    description='Load a bunch of raw tables from corresponding files',
)
def many_table_materializations(_context):
    for table in raw_tables:
        yield Materialization(path='/path/to/{}'.format(table), description='This is a table.')


@solid(
    inputs=[InputDefinition('start', Nothing)],
    outputs=[OutputDefinition(Nothing)],
    description='This simulates a solid that would wrap something like dbt, '
    'where it emits a bunch of tables and then say an expectation on each table, '
    'all in one solid',
)
def many_materializations_and_passing_expectations(_context):
    tables = [
        'users',
        'groups',
        'events',
        'friends',
        'pages',
        'fans',
        'event_admins',
        'group_admins',
    ]

    for table in tables:
        yield Materialization(path='/path/to/{}'.format(table), description='This is a table.')
        yield ExpectationResult(
            success=True,
            name='{table}.row_count'.format(table=table),
            message='Row count passed for {table}'.format(table=table),
        )


@solid(
    inputs=[InputDefinition('start', Nothing)],
    outputs=[],
    description='A solid that just does a couple inline expectations, one of which fails',
)
def check_users_and_groups_one_fails_one_succeeds(_context):
    yield ExpectationResult(
        success=True,
        name='user_expectations',
        message='Battery of expectations for user',
        result_metadata={
            'columns': {
                'name': {'nulls': 0, 'empty': 0, 'values': 123, 'average_length': 3.394893},
                'time_created': {'nulls': 1, 'empty': 2, 'values': 120, 'average': 1231283},
            }
        },
    )

    yield ExpectationResult(
        success=False,
        name='groups_expectations',
        message='Battery of expectations for groups',
        result_metadata={
            'columns': {
                'name': {'nulls': 1, 'empty': 0, 'values': 122, 'average_length': 3.394893},
                'time_created': {'nulls': 1, 'empty': 2, 'values': 120, 'average': 1231283},
            }
        },
    )


@solid(
    inputs=[InputDefinition('start', Nothing)],
    outputs=[],
    description='A solid that just does a couple inline expectations',
)
def check_admins_both_succeed(_context):
    yield ExpectationResult(success=True, message='Group admins check out')
    yield ExpectationResult(success=True, message='Event admins check out')


def define_many_events_pipeline():
    return PipelineDefinition(
        name='many_events',
        solids=[
            many_table_materializations,
            many_materializations_and_passing_expectations,
            check_users_and_groups_one_fails_one_succeeds,
            check_admins_both_succeed,
        ]
        + create_raw_file_solids(),
        dependencies=merge_dicts(
            {'many_table_materializations': {}},
            {
                'many_table_materializations': {
                    'start': MultiDependencyDefinition(
                        [DependencyDefinition(raw_file) for raw_file in raw_files]
                    )
                },
                'many_materializations_and_passing_expectations': {
                    'start': DependencyDefinition('many_table_materializations')
                },
                'check_users_and_groups_one_fails_one_succeeds': {
                    'start': DependencyDefinition('many_materializations_and_passing_expectations')
                },
                'check_admins_both_succeed': {
                    'start': DependencyDefinition('many_materializations_and_passing_expectations')
                },
            },
        ),
        mode_definitions=[ModeDefinition()],
    )
