from __future__ import (absolute_import, division, print_function, unicode_literals)
from builtins import *  # pylint: disable=W0622,W0401

from dagster import check
from dagster.core import types
from dagster.core.execution import DagsterExecutionContext

from .definitions import (InputDefinition, Solid, create_dagster_single_file_input)
from .graph import DagsterPipeline

from dagster.core.execution import DagsterExecutionContext
import json


def pipeline(**kwargs):
    return DagsterPipeline(**kwargs)


def input_definition(**kwargs):
    return InputDefinition(**kwargs)


def file_input_definition(argument_def_dict=None, **kwargs):
    check.param_invariant(argument_def_dict is None, 'Should not provide argument_def_dict')
    return InputDefinition(argument_def_dict={'path': types.PATH}, **kwargs)


def create_json_input(name):
    import json
    check.str_param(name, 'name')

    #Note: I don't understand the function of check_path.
    def check_path(context, path):
        check.inst_param(context, 'context', DagsterExecutionContext)
        check.str_param(path, 'path')
        json_obj = json.load(open(path))
        # context.metric('rows', df.shape[0])
        return json_obj

    return create_dagster_single_file_input(name, check_path)