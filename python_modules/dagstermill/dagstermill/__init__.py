from __future__ import (absolute_import, division, print_function, unicode_literals)
from builtins import *  # pylint: disable=W0622,W0401

import os
import uuid

import base64
import pickle

import papermill as pm

from dagster import (
    InputDefinition,
    OutputDefinition,
    Result,
    SolidDefinition,
    check,
)

CACHE = {}

# ipython kernel install --name "dagster" --user
# python3 -m ipykernel install --user


class InMemoryInputs:
    def __init__(self, args):
        self.args = args


def define_inputs(**kwargs):
    return InMemoryInputs(kwargs)


def _get_cached_inputs_dict(inputs):
    if isinstance(inputs, InMemoryInputs):
        return inputs.args

    if inputs in CACHE:
        return CACHE[inputs]

    ddict = deserialize_dm_object(inputs)
    CACHE[inputs] = ddict
    return ddict


def deserialize_dm_object(dm_object):
    return pickle.loads(base64.b64decode(dm_object.encode('ascii')))


def serialize_dm_object(dm_object):
    return base64.b64encode(pickle.dumps(dm_object)).decode('ascii')


def get_input(serialized_inputs, input_name):
    inputs_dict = _get_cached_inputs_dict(serialized_inputs)
    return inputs_dict[input_name]


def get_inputs(serialized_inputs, *input_names):
    inputs_dict = _get_cached_inputs_dict(serialized_inputs)
    return tuple([inputs_dict[input_name] for input_name in input_names])


class InMemoryConfig:
    def __init__(self, value):
        self.value = value


def define_config(value):
    return InMemoryConfig(value)


def get_config(value):
    if isinstance(value, InMemoryConfig):
        return value.value
    return deserialize_dm_object(value)


def yield_result(value, output_name='result'):
    pm.record(output_name, value)


def define_dagstermill_solid(
    name,
    notebook_path,
    input_defs=None,
    output_defs=None,
    config_def=None,
):
    check.str_param(name, 'name')
    check.str_param(notebook_path, 'notebook_path')
    input_defs = check.opt_list_param(input_defs, 'input_defs', of_type=InputDefinition)
    output_defs = check.opt_list_param(output_defs, 'output_defs', of_type=OutputDefinition)

    def _t_fn(info, inputs):
        if not os.path.exists('/tmp/dagstermill/'):
            os.mkdir('/tmp/dagstermill/')

        temp_path = '/tmp/dagstermill/{prefix}-out.ipynb'.format(prefix=str(uuid.uuid4()))

        try:
            _source_nb = pm.execute_notebook(
                notebook_path,
                temp_path,
                parameters=dict(
                    inputs=serialize_dm_object(inputs),
                    config=serialize_dm_object(info.config),
                ),
            )

            output_nb = pm.read_notebook(temp_path)

            for output_def in info.solid_def.output_defs:
                if output_def.name in output_nb.data:
                    yield Result(output_nb.data[output_def.name], output_def.name)

        finally:
            pass
            # if os.path.exists(temp_path):
            #     os.remove(temp_path)

    return SolidDefinition(
        name=name,
        inputs=input_defs,
        transform_fn=_t_fn,
        outputs=output_defs,
        config_def=config_def,
        description='This solid is backed by the notebook at {path}'.format(path=notebook_path),
    )
