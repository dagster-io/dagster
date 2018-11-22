from __future__ import (absolute_import, division, print_function, unicode_literals)
from builtins import *  # pylint: disable=W0622,W0401

import base64
import json
import os
import pickle
import uuid

import six

from future.utils import raise_from

import papermill as pm

from dagster import (
    DagsterRuntimeCoercionError,
    InputDefinition,
    OutputDefinition,
    Result,
    SolidDefinition,
    check,
    types,
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

        path = '/tmp/dagstermill/{some_id}/values'.format(some_id=str(uuid.uuid4()))
        os.makedirs(path)
        self.base_path = path

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
                new_inputs[input_name] = input_def.dagster_type.coerce_runtime_value(input_value)
            except DagsterRuntimeCoercionError as de:
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

        ddict = deserialize_inputs(
            inputs,
            self.solid_def.input_defs if self.solid_def else None,
            self.base_path,
        )
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
            dagster_type = types.Any
        else:
            if not self.solid_def.has_output(output_name):
                raise DagstermillError(
                    'Solid {solid_name} does not have output named {output_name}'.format(
                        solid_name=self.solid_def.name,
                        output_name=output_name,
                    )
                )

            dagster_type = self.solid_def.output_def_named(output_name).dagster_type

        try:
            return pm.record(
                output_name,
                serialize_dm_object(dagster_type.coerce_runtime_value(value)),
            )
        except DagsterRuntimeCoercionError as de:
            raise_from(
                DagstermillError(
                    (
                        'Output {output_name} output_type {output_type} ' +
                        'failed type check on value {value}'
                    ).format(
                        output_name=output_name,
                        output_type=dagster_type.name,
                        value=repr(value),
                    )
                ),
                de,
            )

    def define_config(self, value):
        if not self.solid_def:
            return InMemoryConfig(value)

        try:
            return InMemoryConfig(
                self.solid_def.config_field.dagster_type.coerce_runtime_value(value)
            )
        except DagsterRuntimeCoercionError as de:
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


def serialize_inputs(inputs, input_defs, scratch_dir):
    check.dict_param(inputs, 'inputs', key_type=six.string_types)
    input_defs = check.opt_list_param(input_defs, 'input_defs', of_type=InputDefinition)
    check.str_param(scratch_dir, 'scratch_dir')

    type_values = {}
    input_def_dict = {inp.name: inp for inp in input_defs}
    for input_name, input_value in inputs.items():
        dagster_type = input_def_dict[input_name].dagster_type if input_defs else types.Any
        type_value = dagster_type.create_serializable_type_value(input_value, scratch_dir)
        type_values[input_name] = type_value

    return serialize_dm_object(type_values)


def deserialize_inputs(inputs_str, input_defs, scratch_dir):
    check.str_param(inputs_str, 'inputs_str')
    input_defs = check.opt_list_param(input_defs, 'input_defs', of_type=InputDefinition)
    check.str_param(scratch_dir, 'scratch_dir')

    type_values = deserialize_dm_object(inputs_str)
    input_def_dict = {inp.name: inp for inp in input_defs} if input_defs else None
    inputs = {}
    for name, type_value in type_values.items():
        dagster_type = input_def_dict[name].dagster_type if input_def_dict else types.Any
        inputs[name] = dagster_type.deserialize_from_type_value(type_value, scratch_dir)
    return inputs


def _dm_solid_transform(name, notebook_path):
    check.str_param(name, 'name')
    check.str_param(notebook_path, 'notebook_path')

    do_cleanup = False  # for now

    def _t_fn(info, inputs):
        base_dir = '/tmp/dagstermill/{run_id}/'.format(run_id=info.context.run_id)
        output_notebook_dir = os.path.join(base_dir, 'output_notebooks/')

        if not os.path.exists(output_notebook_dir):
            os.makedirs(output_notebook_dir)

        temp_path = os.path.join(
            output_notebook_dir, '{prefix}-out.ipynb'.format(prefix=str(uuid.uuid4()))
        )

        values_dir = os.path.join(base_dir, 'values/')

        if not os.path.exists(values_dir):
            os.makedirs(values_dir)

        try:
            _source_nb = pm.execute_notebook(
                notebook_path,
                temp_path,
                parameters=dict(
                    inputs=serialize_inputs(inputs, info.solid_def.input_defs, values_dir),
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
                    value = deserialize_dm_object(output_nb.data[output_def.name])
                    yield Result(
                        value,
                        output_def.name,
                    )

        finally:
            if do_cleanup and os.path.exists(temp_path):
                os.remove(temp_path)

    return _t_fn


def define_dagstermill_solid(
    name,
    notebook_path,
    inputs=None,
    outputs=None,
    config_field=None,
):
    check.str_param(name, 'name')
    check.str_param(notebook_path, 'notebook_path')
    inputs = check.opt_list_param(inputs, 'input_defs', of_type=InputDefinition)
    outputs = check.opt_list_param(outputs, 'output_defs', of_type=OutputDefinition)

    return SolidDefinition(
        name=name,
        inputs=inputs,
        transform_fn=_dm_solid_transform(name, notebook_path),
        outputs=outputs,
        config_field=config_field,
        description='This solid is backed by the notebook at {path}'.format(path=notebook_path),
        metadata={
            'notebook_path': notebook_path,
            'kind': 'ipynb',
        }
    )
