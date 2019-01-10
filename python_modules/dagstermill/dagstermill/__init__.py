from __future__ import absolute_import, division, print_function, unicode_literals
from builtins import *  # pylint: disable=W0622,W0401

import base64
import json
import os
import uuid

import six

from future.utils import raise_from

import papermill as pm

from dagster import (
    DagsterRuntimeCoercionError,
    InputDefinition,
    OutputDefinition,
    RepositoryDefinition,
    Result,
    PipelineDefinition,
    SolidDefinition,
    check,
    types,
)

from dagster.core.definitions import TransformExecutionInfo
from dagster.core.types.runtime import RuntimeType

# magic incantation for syncing up notebooks to enclosing virtual environment.
# I don't claim to understand it.
# ipython kernel install --name "dagster" --user
# python3 -m ipykernel install --user


class InMemoryDagstermillContext:
    def __init__(self, pipeline_def, solid_def, inputs):
        self.pipeline_def = pipeline_def
        self.solid_def = solid_def
        self.inputs = inputs


class RemotedDagstermillContext:
    def __init__(self, pipeline_def, solid_def, inputs, marshal_dir):
        self.pipeline_def = pipeline_def
        self.solid_def = solid_def
        self.inputs = inputs
        self.marshal_dir = marshal_dir


class DagstermillError(Exception):
    pass


class Manager:
    def __init__(self):
        self.serialized_context = None
        self.cached_context = None
        self.repository_def = None
        self.solid_def_name = None
        self.solid_def = None

    def declare_as_solid(self, repository_def, solid_def_name):
        self.repository_def = repository_def
        self.solid_def = self.repository_def.solid_def_named(solid_def_name)
        self.solid_def_name = check.str_param(solid_def_name, 'solid_def_name')

    def define_context(self, inputs=None):
        return InMemoryDagstermillContext(
            pipeline_def=None,
            solid_def=self.solid_def,
            inputs=check.opt_dict_param(inputs, 'inputs'),
        )

    def get_pipeline(self, name):
        check.str_param(name, 'name')
        return self.repository_def.get_pipeline(name)

    def _get_cached_dagstermill_context(self, context_or_serialized):
        # inputs is either a 1) InMemoryInputs (the in-notebook experience)
        # or a serialized dictionary (json-encoded) that is used to
        # to marshal inputs into the notebook process
        if isinstance(context_or_serialized, InMemoryDagstermillContext):
            return context_or_serialized

        serialized_context = context_or_serialized

        if self.serialized_context is None:
            self.serialized_context = context_or_serialized
        else:
            check.invariant(self.serialized_context == serialized_context)

        if self.cached_context is not None:
            return self.cached_context

        self.cached_context = deserialize_dm_context(serialized_context)
        return self.cached_context

    def get_input(self, context_or_serialized, input_name):
        ctx = self._get_cached_dagstermill_context(context_or_serialized)
        return ctx.inputs[input_name]

    def get_inputs(self, context_or_serialized, *input_names):
        ctx = self._get_cached_dagstermill_context(context_or_serialized)
        return tuple([ctx.inputs[input_name] for input_name in input_names])

    def yield_result(self, context_or_serialized, value, output_name='result'):
        dm_context = self._get_cached_dagstermill_context(context_or_serialized)

        if isinstance(dm_context, InMemoryDagstermillContext):
            return value

        solid_def = dm_context.solid_def

        if not solid_def.has_output(output_name):
            raise DagstermillError(
                'Solid {solid_name} does not have output named {output_name}'.format(
                    solid_name=solid_def.name, output_name=output_name
                )
            )

        runtime_type = solid_def.output_def_named(output_name).runtime_type

        out_file = os.path.join(dm_context.marshal_dir, 'output-{}'.format(output_name))
        pm.record(output_name, marshal_value(runtime_type, value, out_file))


def marshal_value(runtime_type, value, target_file):
    check.inst_param(runtime_type, 'runtime_type', RuntimeType)
    if runtime_type.is_scalar:
        return value
    elif runtime_type.is_any and is_json_serializable(value):
        return value
    elif runtime_type.marshalling_strategy:
        runtime_type.marshalling_strategy.marshal_value(value, target_file)
        return target_file
    else:
        check.failed('Unsupported type {name}'.format(name=runtime_type.name))


MANAGER_FOR_NOTEBOOK_INSTANCE = Manager()


def declare_as_solid(pipeline_def, solid_def_name):
    return MANAGER_FOR_NOTEBOOK_INSTANCE.declare_as_solid(pipeline_def, solid_def_name)


def define_context(inputs=None):
    return MANAGER_FOR_NOTEBOOK_INSTANCE.define_context(inputs)


def get_input(dm_context, input_name):
    check.param_invariant(isinstance(dm_context, (InMemoryDagstermillContext, str)), 'dm_context')
    return MANAGER_FOR_NOTEBOOK_INSTANCE.get_input(dm_context, input_name)


def get_inputs(dm_context, *input_names):
    check.param_invariant(isinstance(dm_context, (InMemoryDagstermillContext, str)), 'dm_context')
    return MANAGER_FOR_NOTEBOOK_INSTANCE.get_inputs(dm_context, *input_names)


def yield_result(dm_context, value, output_name='result'):
    return MANAGER_FOR_NOTEBOOK_INSTANCE.yield_result(dm_context, value, output_name)


def serialize_dm_context(transform_execution_info, inputs):
    check.inst_param(transform_execution_info, 'transform_execution_info', TransformExecutionInfo)
    check.dict_param(inputs, 'inputs', key_type=six.string_types)

    run_id = transform_execution_info.context.run_id

    marshal_dir = '/tmp/dagstermill/{run_id}/marshal'.format(run_id=run_id)
    if not os.path.exists(marshal_dir):
        os.makedirs(marshal_dir)

    new_inputs_structure = {
        'pipeline_name': transform_execution_info.pipeline_def.name,
        'solid_def_name': transform_execution_info.solid.definition.name,
        'solid_name': transform_execution_info.solid.name,
        'inputs': {},
        'marshal_dir': marshal_dir,
    }

    input_defs = transform_execution_info.solid_def.input_defs
    input_def_dict = {inp.name: inp for inp in input_defs}
    for input_name, input_value in inputs.items():
        runtime_type = input_def_dict[input_name].runtime_type

        new_inputs_structure['inputs'][input_name] = marshal_value(
            runtime_type, input_value, os.path.join(marshal_dir, 'input-{}'.format(input_name))
        )

    return json.dumps(new_inputs_structure)


def unmarshal_value(runtime_type, value):
    check.inst_param(runtime_type, 'runtime_type', RuntimeType)
    if runtime_type.is_scalar:
        return value
    elif runtime_type.is_any and is_json_serializable(value):
        return value
    elif runtime_type.marshalling_strategy:
        return runtime_type.marshalling_strategy.unmarshal_value(value)
    else:
        check.failed('Unsupported type {name}'.format(name=runtime_type.name))


def deserialize_dm_context(serialized_dm_context):
    check.str_param(serialized_dm_context, 'inputs_str')

    dm_context_data = json.loads(serialized_dm_context)

    pipeline_def = MANAGER_FOR_NOTEBOOK_INSTANCE.get_pipeline(dm_context_data['pipeline_name'])

    check.inst(pipeline_def, PipelineDefinition)

    solid_def_name = dm_context_data['solid_def_name']

    check.invariant(pipeline_def.has_solid_def(solid_def_name))

    solid_def = pipeline_def.solid_def_named(solid_def_name)

    inputs_data = dm_context_data['inputs']
    inputs = {}
    for input_name, input_value in inputs_data.items():
        input_def = solid_def.input_def_named(input_name)
        inputs[input_name] = unmarshal_value(input_def.runtime_type, input_value)

    return RemotedDagstermillContext(
        pipeline_def=pipeline_def,
        solid_def=solid_def,
        inputs=inputs,
        marshal_dir=dm_context_data['marshal_dir'],
    )


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

        try:
            _source_nb = pm.execute_notebook(
                notebook_path,
                temp_path,
                parameters=dict(dm_context=serialize_dm_context(info, inputs)),
            )

            output_nb = pm.read_notebook(temp_path)

            info.context.debug(
                'Notebook execution complete for {name}. Data is {data}'.format(
                    name=name, data=output_nb.data
                )
            )

            for output_def in info.solid_def.output_defs:
                if output_def.name in output_nb.data:

                    value = unmarshal_value(
                        output_def.runtime_type, output_nb.data[output_def.name]
                    )

                    yield Result(value, output_def.name)

        finally:
            if do_cleanup and os.path.exists(temp_path):
                os.remove(temp_path)

    return _t_fn


def is_json_serializable(value):
    try:
        json.dumps(value)
        return True
    except TypeError:
        return False


def define_dagstermill_solid(name, notebook_path, inputs=None, outputs=None, config_field=None):
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
        metadata={'notebook_path': notebook_path, 'kind': 'ipynb'},
    )
