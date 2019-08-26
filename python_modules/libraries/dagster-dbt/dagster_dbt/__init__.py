import io
import os
import re
import shlex
import subprocess
from collections import namedtuple

from dagster import (
    EventMetadataEntry,
    ExpectationResult,
    Failure,
    InputDefinition,
    Materialization,
    Nothing,
    Output,
    OutputDefinition,
    check,
    solid,
)

CREATE_VIEW_REGEX = re.compile(r'OK created view model (\w+)\.(\w+)\.* \[CREATE VIEW')
CREATE_TABLE_REGEX = re.compile(r'OK created table model (\w+)\.(\w+)\.* \[SELECT (\d+)')
ANSI_ESCAPE = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')
TEST_PASS_REGEX = re.compile(r'PASS (\w+)\.* \[PASS')
TEST_FAIL_REGEX = re.compile(r'FAIL (\d+) (\w+)\.* \[FAIL')


def try_parse_create_view(text):
    view_match = CREATE_VIEW_REGEX.search(text)

    if not view_match:
        return None

    return Materialization(
        label='create_view',
        description=text,
        metadata_entries=[
            EventMetadataEntry.text(view_match.group(1), 'schema'),
            EventMetadataEntry.text(view_match.group(2), 'view'),
        ],
    )


def try_parse_create_table(text):
    table_match = CREATE_TABLE_REGEX.search(text)

    if not table_match:
        return None

    return Materialization(
        label='create_table',
        description=text,
        metadata_entries=[
            EventMetadataEntry.text(table_match.group(1), 'schema'),
            EventMetadataEntry.text(table_match.group(2), 'table'),
            EventMetadataEntry.text(table_match.group(3), 'row_count'),
        ],
    )


def try_parse_run(text):
    for parser in [try_parse_create_view, try_parse_create_table]:
        mat = parser(text)
        if mat:
            return mat


def create_dbt_solid(project_dir, name=None, profiles_dir=None):
    check.str_param(project_dir, 'project_dir')
    check.opt_str_param(name, 'name')
    check.opt_str_param(profiles_dir, 'profiles_dir')

    @solid(
        name=name if name else os.path.basename(project_dir),
        output_defs=[OutputDefinition(dagster_type=Nothing, name='run_complete')],
    )
    def dbt_solid(_):
        cmd = 'dbt run --project-dir {}'.format(project_dir)
        if profiles_dir:
            cmd += ' --profiles-dir {}'.format(profiles_dir)

        args = shlex.split(cmd)
        proc = subprocess.Popen(args, stdout=subprocess.PIPE)

        # if https://github.com/fishtown-analytics/dbt/issues/1237 gets done
        # we should definitely switch to parsing the json output, as that
        # would be much more reliable/resilient
        for line in io.TextIOWrapper(proc.stdout, encoding='utf-8'):
            text = line.rstrip()
            if not text:
                continue

            # print to stdout
            print(text)

            # remove colors
            text = ANSI_ESCAPE.sub('', text)

            mat = try_parse_run(text)
            if mat:
                yield mat

        proc.wait()

        if proc.returncode != 0:
            raise Failure('Dbt invocation errored')

        yield Output(value=None, output_name='run_complete')

    return dbt_solid


def try_parse_pass(text):
    pass_match = TEST_PASS_REGEX.search(text)

    if not pass_match:
        return None

    test_name = pass_match.group(1)

    return ExpectationResult(
        success=True,
        label='dbt_test',
        description='Dbt test {} passed'.format(test_name),
        metadata_entries=[EventMetadataEntry.text(label='dbt_test_name', text=test_name)],
    )


def try_parse_fail(text):
    fail_match = TEST_FAIL_REGEX.search(text)

    if not fail_match:
        return None

    failure_count = fail_match.group(1)
    test_name = fail_match.group(2)

    return ExpectationResult(
        success=False,
        label='dbt_test',
        description='Dbt test {} failed'.format(test_name),
        metadata_entries=[
            EventMetadataEntry.text(label='dbt_test_name', text=test_name),
            EventMetadataEntry.text(label='failure_count', text=failure_count),
        ],
    )


def try_parse_test(text):
    for parser in [try_parse_pass, try_parse_fail]:
        expect = parser(text)
        if expect:
            return expect


def create_dbt_test_solid(project_dir, name=None, profiles_dir=None):
    check.str_param(project_dir, 'project_dir')
    check.opt_str_param(name, 'name')
    check.opt_str_param(profiles_dir, 'profiles_dir')

    @solid(
        name=name if name else os.path.basename(project_dir) + '_test',
        input_defs=[InputDefinition('test_start', Nothing)],
        output_defs=[OutputDefinition(dagster_type=Nothing, name='test_complete')],
    )
    def dbt_test_solid(_):
        cmd = 'dbt test --project-dir {}'.format(project_dir)
        if profiles_dir:
            cmd += ' --profiles-dir {}'.format(profiles_dir)
        args = shlex.split(cmd)
        proc = subprocess.Popen(args, stdout=subprocess.PIPE)
        for line in io.TextIOWrapper(proc.stdout, encoding='utf-8'):
            text = line.rstrip()
            if not text:
                continue

            # print to stdout
            print(text)

            # remove colors
            text = ANSI_ESCAPE.sub('', text)

            expt = try_parse_test(text)

            if expt:
                yield expt

        yield Output(value=None, output_name='test_complete')

    return dbt_test_solid
