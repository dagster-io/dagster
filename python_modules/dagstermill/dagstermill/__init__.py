from __future__ import (absolute_import, division, print_function, unicode_literals)
from builtins import *  # pylint: disable=W0622,W0401

import os
import uuid

import base64
import pickle

from future.utils import raise_from

import papermill as pm

from dagster import (
    DagsterEvaluateValueError,
    InputDefinition,
    OutputDefinition,
    Result,
    SolidDefinition,
    check,
)

# magic incantation for syncing up notebooks to enclosing virtual environment.
# I don't claim to understand it.
# ipython kernel install --name "dagster" --user
# python3 -m ipykernel install --user


class InMemoryInputs:
    def __init__(self, args):
        self.args = args


class InMemoryConfig:
    def __init__(self, value):
        self.value = value


class DagstermillError(Exception):
    pass


class Manager:
    def __init__(self, solid_def=None):
        self.solid_def = check.opt_inst_param(solid_def, 'solid_def', SolidDefinition)
        self.cache = {}

        if solid_def is not None:
            check.invariant(
                'notebook_path' in solid_def.metadata,
                'Must include metadata about notebook_path',
            )

            self.notebook_dir = os.path.dirname(
                os.path.abspath(solid_def.metadata['notebook_path'])
            )
        else:
            self.notebook_dir = None

    def _typecheck_evaluate_inputs(self, inputs):
        if not self.solid_def:
            return inputs

        new_inputs = {}

        for input_name, input_value in inputs.items():
            if not self.solid_def.has_input(input_name):
                raise DagstermillError(
                    'Solid {solid_name} does not have input {input_name}'.format(
                        solid_name=self.solid_def.name,
                        input_name=input_name,
                    )
                )

            input_def = self.solid_def.input_def_named(input_name)
            try:
                new_inputs[input_name] = input_def.dagster_type.evaluate_value(input_value)
            except DagsterEvaluateValueError as de:
                raise_from(
                    DagstermillError(
                        'Input {input_name} failed type check on value {value}'.format(
                            input_name=input_name,
                            value=repr(input_value),
                        )
                    ),
                    de,
                )

        return new_inputs

    def define_inputs(self, **kwargs):
        return InMemoryInputs(self._typecheck_evaluate_inputs(kwargs))

    def _get_cached_inputs_dict(self, inputs):
        if isinstance(inputs, InMemoryInputs):
            return inputs.args

        if inputs in self.cache:
            return self.cache[inputs]

        ddict = deserialize_dm_object(inputs)
        self.cache[inputs] = self._typecheck_evaluate_inputs(ddict)
        return ddict

    def get_path(self, path):
        check.str_param(path, 'path')
        if not self.notebook_dir:
            return path

        return os.path.join(self.notebook_dir, path)

    def get_input(self, serialized_inputs, input_name):
        inputs_dict = self._get_cached_inputs_dict(serialized_inputs)
        return inputs_dict[input_name]

    def get_inputs(self, serialized_inputs, *input_names):
        inputs_dict = self._get_cached_inputs_dict(serialized_inputs)
        return tuple([inputs_dict[input_name] for input_name in input_names])

    def yield_result(self, value, output_name='result'):
        if not self.solid_def:
            return pm.record(output_name, serialize_dm_object(value))

        if not self.solid_def.has_output(output_name):
            raise DagstermillError(
                'Solid {solid_name} does not have output named {output_name}'.format(
                    solid_name=self.solid_def.name,
                    output_name=output_name,
                )
            )

        output_def = self.solid_def.output_def_named(output_name)

        try:
            return pm.record(
                output_name,
                serialize_dm_object(output_def.dagster_type.evaluate_value(value)),
            )
        except DagsterEvaluateValueError as de:
            raise_from(
                DagstermillError(
                    (
                        'Solid {solid_name} output {output_name} output_type {output_type} ' +
                        'failed type check on value {value}'
                    ).format(
                        solid_name=self.solid_def.name,
                        output_name=output_name,
                        output_type=output_def.dagster_type.name,
                        value=repr(value),
                    )
                ),
                de,
            )

    def define_config(self, value):
        if not self.solid_def:
            return InMemoryConfig(value)

        try:
            return InMemoryConfig(self.solid_def.config_def.config_type.evaluate_value(value))
        except DagsterEvaluateValueError as de:
            raise_from(
                DagstermillError(
                    'Config for solid {solid} failed type check on value {value}'.format(
                        solid=self.solid_def.name, value=repr(value)
                    ),
                ),
                de,
            )

    def get_config(self, value):
        if isinstance(value, InMemoryConfig):
            return value.value
        return deserialize_dm_object(value)


def define_manager(solid_def=None):
    return Manager(solid_def)


def deserialize_dm_object(dm_object):
    return pickle.loads(base64.b64decode(dm_object.encode('ascii')))


def serialize_dm_object(dm_object):
    return base64.b64encode(pickle.dumps(dm_object)).decode('ascii')


def define_dagstermill_solid(
    name,
    notebook_path,
    inputs=None,
    outputs=None,
    config_def=None,
):
    check.str_param(name, 'name')
    check.str_param(notebook_path, 'notebook_path')
    inputs = check.opt_list_param(inputs, 'input_defs', of_type=InputDefinition)
    outputs = check.opt_list_param(outputs, 'output_defs', of_type=OutputDefinition)

    do_cleanup = False  # for now

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

            info.context.debug(
                'Notebook execution complete for {name}. Data is {data}'.format(
                    name=name,
                    data=output_nb.data,
                )
            )

            for output_def in info.solid_def.output_defs:
                if output_def.name in output_nb.data:
                    yield Result(
                        deserialize_dm_object(output_nb.data[output_def.name]),
                        output_def.name,
                    )

        finally:
            if do_cleanup and os.path.exists(temp_path):
                os.remove(temp_path)

    return SolidDefinition(
        name=name,
        inputs=inputs,
        transform_fn=_t_fn,
        outputs=outputs,
        config_def=config_def,
        description='This solid is backed by the notebook at {path}'.format(path=notebook_path),
        metadata={
            'notebook_path': notebook_path,
        }
    )
