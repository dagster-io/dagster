from __future__ import (absolute_import, division, print_function, unicode_literals)
from builtins import *  # pylint: disable=W0622,W0401

from dagster import check

from .definitions import SolidInputDefinition
from .graph import DagsterPipeline
from .types import SolidPath


def pipeline(**kwargs):
    return DagsterPipeline(**kwargs)


def input_definition(**kwargs):
    return SolidInputDefinition(**kwargs)


def file_input_definition(argument_def_dict=None, **kwargs):
    check.param_invariant(argument_def_dict is None, 'Should not provide argument_def_dict')
    return SolidInputDefinition(argument_def_dict={'path': SolidPath}, **kwargs)


PATH = SolidPath
