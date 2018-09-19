from __future__ import (absolute_import, division, print_function, unicode_literals)
from builtins import *  # pylint: disable=W0622,W0401

import base64
import pickle

import papermill as pm

CACHE = {}

# ipython kernel install --name "dagster" --user
# python3 -m ipykernel install --user


def define_inputs(**kwargs):
    return base64.b64encode(pickle.dumps(kwargs))


def _get_cached_inputs_dict(inputs):
    if inputs in CACHE:
        return CACHE[inputs]

    ddict = pickle.loads(base64.b64decode(inputs))
    CACHE[inputs] = ddict
    return ddict


def get_input(inputs, input_name):
    ddict = _get_cached_inputs_dict(inputs)
    return ddict[input_name]


def yield_result(value, output_name='result'):
    pm.record(output_name, value)
