from __future__ import (absolute_import, division, print_function, unicode_literals)
from builtins import *  # pylint: disable=W0622,W0401

import json

from dagster import check
from dagster.core import types
from dagster.core.execution import ExecutionContext

from .definitions import (
    InputDefinition,
    create_dagster_single_file_input,
    create_custom_source_input,
    PipelineContextDefinition,
    PipelineDefinition,
)


def input_definition(**kwargs):
    return create_custom_source_input(**kwargs)


def create_json_input(name):
    check.str_param(name, 'name')

    def load_file(context, path):
        check.inst_param(context, 'context', ExecutionContext)
        check.str_param(path, 'path')
        with open(path) as ff:
            return json.load(ff)

    return create_dagster_single_file_input(name, load_file, source_type='JSON')
