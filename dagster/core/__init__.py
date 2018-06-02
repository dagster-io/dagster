from __future__ import (absolute_import, division, print_function, unicode_literals)
from builtins import *  # pylint: disable=W0622,W0401

import json

from dagster import check
from dagster.core import types
from dagster.core.execution import DagsterExecutionContext

from .definitions import (
    InputDefinition, create_dagster_single_file_input, create_single_source_input
)
from .graph import DagsterPipeline


def pipeline(**kwargs):
    return DagsterPipeline(**kwargs)


def input_definition(**kwargs):
    return create_single_source_input(**kwargs)


def file_input_definition(argument_def_dict=None, **kwargs):
    check.param_invariant(argument_def_dict is None, 'Should not provide argument_def_dict')
    return create_single_source_input(argument_def_dict={'path': types.PATH}, **kwargs)


def create_json_input(name):
    check.str_param(name, 'name')

    def load_file(context, path):
        check.inst_param(context, 'context', DagsterExecutionContext)
        check.str_param(path, 'path')
        with open(path) as ff:
            return json.load(ff)

    return create_dagster_single_file_input(name, load_file, source_type='JSON')
