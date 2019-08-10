from collections import namedtuple
import io
import os
import re
import shlex
import subprocess

from dagster import (
    check,
    EventMetadataEntry,
    Failure,
    Materialization,
    Nothing,
    Output,
    OutputDefinition,
    solid,
)

CREATE_VIEW_REGEX = re.compile(r'OK created view model (\w+)\.(\w+)\.* \[CREATE VIEW')
CREATE_TABLE_REGEX = re.compile(r'OK created table model (\w+)\.(\w+)\.* \[SELECT (\d+)')
ANSI_ESCAPE = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')


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


def try_parse(text):
    for parser in [try_parse_create_view, try_parse_create_table]:
        mat = parser(text)
        if mat:
            return mat


def create_dbt_solid(project_dir, name=None):
    check.str_param(project_dir, 'project_dir')
    check.opt_str_param(name, 'name')

    @solid(
        name=name if name else os.path.basename(project_dir),
        output_defs=[OutputDefinition(dagster_type=Nothing, name='run_complete')],
    )
    def dbt_solid(_):
        args = shlex.split('dbt run --project-dir {}'.format(project_dir))
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

            mat = try_parse(text)
            if mat:
                yield mat

        proc.wait()

        if proc.returncode != 0:
            raise Failure('Dbt invocation errored')

        yield Output(value=None, output_name='run_complete')

    return dbt_solid
