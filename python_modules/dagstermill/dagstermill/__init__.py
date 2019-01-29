from __future__ import absolute_import, division, print_function, unicode_literals
from builtins import *  # pylint: disable=W0622,W0401

import base64
import copy
import json
import os
import subprocess
import uuid

import nbformat

import six

from future.utils import raise_from

import papermill as pm
from papermill.translators import translate_parameters
from papermill.iorw import load_notebook_node, write_ipynb
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
from dagster.core.types.marshal import serialize_to_file, deserialize_from_file
from dagster.core.types.runtime import RuntimeType

from dagster.core.definitions.dependency import Solid
from dagster.core.events import construct_json_event_logger, EventRecord, EventType
from dagster.core.definitions.environment_configs import construct_environment_config
from dagster.core.execution import yield_context
from dagster.core.execution_context import ExecutionMetadata

# magic incantation for syncing up notebooks to enclosing virtual environment.
# I don't claim to understand it.
# ipython kernel install --name "dagster" --user
# python3 -m ipykernel install --user


class DagstermillError(Exception):
    pass


class Manager:
    def __init__(self):
        self.repository_def = None
        self.solid_def_name = None
        self.solid_def = None
        self.populated_by_papermill = False
        self.marshal_dir = None
        self.info = None

    def declare_as_solid(self, repository_def, solid_def_name):
        self.repository_def = repository_def
        self.solid_def = self.repository_def.solid_def_named(solid_def_name)
        self.solid_def_name = check.str_param(solid_def_name, 'solid_def_name')

    def define_out_of_pipeline_info(self, context_config):
        check.str_param(self.solid_def_name, 'solid_def_name')
        solid = Solid(self.solid_def_name, self.solid_def)
        pipeline_def = PipelineDefinition([self.solid_def], name="Ephemeral Notebook Pipeline")
        from dagster.core.execution import create_typed_context

        typed_context = create_typed_context(
            pipeline_def, {} if context_config is None else context_config
        )
        from dagster.core.system_config.objects import EnvironmentConfig

        dummy_environment_config = EnvironmentConfig(context=typed_context)
        with yield_context(
            pipeline_def, dummy_environment_config, ExecutionMetadata(run_id='')
        ) as context:
            self.info = TransformExecutionInfo(context, None, solid, pipeline_def)
        return self.info

    def get_pipeline(self, name):
        check.str_param(name, 'name')
        return self.repository_def.get_pipeline(name)

    def yield_result(self, value, output_name):
        if not self.solid_def.has_output(output_name):
            raise DagstermillError(
                'Solid {solid_name} does not have output named {output_name}'.format(
                    solid_name=self.solid_def.name, output_name=output_name
                )
            )
        if not self.populated_by_papermill:
            return value

        runtime_type = self.solid_def.output_def_named(output_name).runtime_type

        out_file = os.path.join(self.marshal_dir, 'output-{}'.format(output_name))
        pm.record(output_name, write_value(runtime_type, value, out_file))

    def populate_context(
        self, run_id, pipeline_def, marshal_dir, environment_config, output_log_path
    ):
        check.dict_param(environment_config, 'environment_config')
        check.invariant(pipeline_def.has_solid_def(self.solid_def_name))

        self.marshal_dir = marshal_dir
        self.populated_by_papermill = True
        loggers = None
        if output_log_path != 0:
            event_logger = construct_json_event_logger(output_log_path)
            loggers = [event_logger]
        # do not include event_callback in ExecutionMetadata,
        # since that'll be taken care of by side-channel established by event_logger
        execution_metadata = ExecutionMetadata(run_id, loggers=loggers)
        solid = Solid(self.solid_def_name, self.solid_def)
        typed_environment = construct_environment_config(environment_config)
        with yield_context(pipeline_def, typed_environment, execution_metadata) as context:
            solid_config = None
            self.info = TransformExecutionInfo(context, solid_config, solid, pipeline_def)

        return self.info


class DagsterTranslator(pm.translators.PythonTranslator):
    @classmethod
    def codify(cls, parameters):
        assert "dm_context" in parameters
        content = '{}\n'.format(cls.comment('Parameters'))
        content += "{}\n".format("import json")
        content += '{}\n'.format(
            cls.assign(
                'info',
                'dm.populate_context(json.loads(\'{dm_context}\'))'.format(
                    dm_context=parameters['dm_context']
                ),
            )
        )

        for name, val in parameters.items():
            if name == "dm_context":
                continue
            dm_unmarshal_call = 'dm.load_parameter("{name}", {val})'.format(
                name=name, val='"{val}"'.format(val=val) if isinstance(val, str) else val
            )
            content += '{}\n'.format(cls.assign(name, dm_unmarshal_call))

        return content


MANAGER_FOR_NOTEBOOK_INSTANCE = Manager()
pm.translators.papermill_translators.register("python", DagsterTranslator)


def is_json_serializable(value):
    try:
        json.dumps(value)
        return True
    except TypeError:
        return False


def write_value(runtime_type, value, target_file):
    check.inst_param(runtime_type, 'runtime_type', RuntimeType)
    if runtime_type.is_scalar:
        return value
    elif runtime_type.is_any and is_json_serializable(value):
        return value
    elif runtime_type.serialization_strategy:
        serialize_to_file(runtime_type.serialization_strategy, value, target_file)
        return target_file
    else:
        check.failed('Unsupported type {name}'.format(name=runtime_type.name))


def declare_as_solid(repo_def, solid_def_name):
    return MANAGER_FOR_NOTEBOOK_INSTANCE.declare_as_solid(repo_def, solid_def_name)


def yield_result(value, output_name='result'):
    return MANAGER_FOR_NOTEBOOK_INSTANCE.yield_result(value, output_name)


def populate_context(dm_context_data):
    check.dict_param(dm_context_data, "dm_context_data")
    pipeline_def = MANAGER_FOR_NOTEBOOK_INSTANCE.get_pipeline(dm_context_data['pipeline_name'])
    check.inst(pipeline_def, PipelineDefinition)
    return MANAGER_FOR_NOTEBOOK_INSTANCE.populate_context(
        dm_context_data['run_id'],
        pipeline_def,
        dm_context_data['marshal_dir'],
        dm_context_data['environment_config'],
        dm_context_data['output_log_path'],
    )


def load_parameter(input_name, input_value):
    solid_def = MANAGER_FOR_NOTEBOOK_INSTANCE.solid_def
    input_def = solid_def.input_def_named(input_name)
    return read_value(input_def.runtime_type, input_value)


def read_value(runtime_type, value):
    check.inst_param(runtime_type, 'runtime_type', RuntimeType)
    if runtime_type.is_scalar:
        return value
    elif runtime_type.is_any and is_json_serializable(value):
        return value
    elif runtime_type.serialization_strategy:
        return deserialize_from_file(runtime_type.serialization_strategy, value)
    else:
        check.failed(
            'Unsupported type {name}: no persistence strategy defined'.format(
                name=runtime_type.name
            )
        )


def get_papermill_parameters(transform_execution_info, inputs, output_log_path):
    check.inst_param(transform_execution_info, 'transform_execution_info', TransformExecutionInfo)
    check.param_invariant(
        isinstance(transform_execution_info.context.environment_config, dict),
        'transform_execution_info',
        'TransformExecutionInfo must have valid environment_config',
    )
    check.dict_param(inputs, 'inputs', key_type=six.string_types)

    run_id = transform_execution_info.context.run_id

    marshal_dir = '/tmp/dagstermill/{run_id}/marshal'.format(run_id=run_id)
    if not os.path.exists(marshal_dir):
        os.makedirs(marshal_dir)

    if not transform_execution_info.context.has_event_callback:
        transform_execution_info.log.info("get_papermill_parameters.context has no event_callback!")
        output_log_path = 0  # stands for null

    dm_context_dict = {
        'run_id': run_id,
        'pipeline_name': transform_execution_info.pipeline_def.name,
        'solid_def_name': transform_execution_info.solid.definition.name,
        'marshal_dir': marshal_dir,
        'environment_config': transform_execution_info.context.environment_config,
        'output_log_path': output_log_path,
    }

    parameters = dict(dm_context=json.dumps(dm_context_dict))

    input_defs = transform_execution_info.solid_def.input_defs
    input_def_dict = {inp.name: inp for inp in input_defs}
    for input_name, input_value in inputs.items():
        assert (
            input_name != "dm_context"
        ), "Dagstermill solids cannot have inputs named 'dm_context'"
        runtime_type = input_def_dict[input_name].runtime_type
        parameter_value = write_value(
            runtime_type, input_value, os.path.join(marshal_dir, 'input-{}'.format(input_name))
        )
        parameters[input_name] = parameter_value

    return parameters


def replace_parameters(info, nb, parameters):
    # Uma: This is a copy-paste from papermill papermill/execute.py:104 (execute_parameters).
    # Typically, papermill injects the injected-parameters cell *below* the parameters cell
    # but we want to *replace* the parameters cell, which is what this function does.

    """Assigned parameters into the appropiate place in the input notebook
    Args:
        nb (NotebookNode): Executable notebook object
        parameters (dict): Arbitrary keyword arguments to pass to the notebook parameters.
    """

    # Copy the nb object to avoid polluting the input
    nb = copy.deepcopy(nb)

    # Generate parameter content based on the kernel_name
    param_content = DagsterTranslator.codify(parameters)
    # papermill method choosed translator based on kernel_name and language,
    # but we just call the DagsterTranslator
    # translate_parameters(kernel_name, language, parameters)

    newcell = nbformat.v4.new_code_cell(source=param_content)
    newcell.metadata['tags'] = ['injected-parameters']

    from papermill.execute import _find_first_tagged_cell_index

    param_cell_index = _find_first_tagged_cell_index(nb, 'parameters')
    injected_cell_index = _find_first_tagged_cell_index(nb, 'injected-parameters')
    if injected_cell_index >= 0:
        # Replace the injected cell with a new version
        before = nb.cells[:injected_cell_index]
        after = nb.cells[injected_cell_index + 1 :]
        check.int_value_param(param_cell_index, -1, "param_cell_index")
        # We should have blown away the parameters cell if there is an injected-parameters cell
    elif param_cell_index >= 0:
        # Replace the parameter cell with the injected-parameters cell
        before = nb.cells[:param_cell_index]
        after = nb.cells[param_cell_index + 1 :]
    else:
        # Inject to the top of the notebook, presumably first cell includes dagstermill import
        info.log.debug(
            (
                "Warning notebook has no parameters cell, "
                "so first cell must import dagstermill and call dm.declare_as_solid"
            )
        )
        before = nb.cells[:1]
        after = nb.cells[1:]

    nb.cells = before + [newcell] + after
    nb.metadata.papermill['parameters'] = parameters

    return nb


def get_solid_definition():
    return check.inst_param(MANAGER_FOR_NOTEBOOK_INSTANCE.solid_def, "solid_def", SolidDefinition)


def get_info(config=None):
    if not MANAGER_FOR_NOTEBOOK_INSTANCE.populated_by_papermill:
        MANAGER_FOR_NOTEBOOK_INSTANCE.define_out_of_pipeline_info(config)
    return MANAGER_FOR_NOTEBOOK_INSTANCE.info


def _dm_solid_transform(name, notebook_path):
    check.str_param(name, 'name')
    check.str_param(notebook_path, 'notebook_path')

    do_cleanup = False  # for now

    def _t_fn(info, inputs):
        check.param_invariant(
            isinstance(info.context.environment_config, dict),
            'info',
            'TransformExecutionInfo must have valid environment_config',
        )

        base_dir = '/tmp/dagstermill/{run_id}/'.format(run_id=info.context.run_id)
        output_notebook_dir = os.path.join(base_dir, 'output_notebooks/')

        if not os.path.exists(output_notebook_dir):
            os.makedirs(output_notebook_dir)

        temp_path = os.path.join(
            output_notebook_dir, '{prefix}-out.ipynb'.format(prefix=str(uuid.uuid4()))
        )

        output_log_path = os.path.join(base_dir, 'run.log')

        try:
            nb = load_notebook_node(notebook_path)
            nb_no_parameters = replace_parameters(
                info, nb, get_papermill_parameters(info, inputs, output_log_path)
            )
            intermediate_path = os.path.join(
                output_notebook_dir, '{prefix}-inter.ipynb'.format(prefix=str(uuid.uuid4()))
            )
            write_ipynb(nb_no_parameters, intermediate_path)

            with open(output_log_path, 'a') as f:
                f.close()

            # info.log.info("Output log path is {}".format(output_log_path))
            # info.log.info("info.context.event_callback {}".format(info.context.event_callback))

            process = subprocess.Popen(["papermill", intermediate_path, temp_path])
            # _source_nb = pm.execute_notebook(intermediate_path, temp_path)

            while process.poll() is None:  # while subprocess alive
                if info.context.event_callback:
                    with open(output_log_path, 'r') as ff:
                        current_time = os.path.getmtime(output_log_path)
                        while process.poll() is None:
                            new_time = os.path.getmtime(output_log_path)
                            if new_time != current_time:
                                line = ff.readline()
                                if not line:
                                    break
                                event_record_dict = json.loads(line)

                                event_record_dict['event_type'] = EventType(
                                    event_record_dict['event_type']
                                )
                                info.context.event_callback(EventRecord(**event_record_dict))
                                current_time = new_time

            if process.returncode != 0:
                # Throw event that is an execution error!
                info.log.debug("There was an error in Papermill!")
                info.log.debug('stderr was None' if process.stderr is None else process.stderr)
                exit()

            output_nb = pm.read_notebook(temp_path)

            info.log.debug(
                'Notebook execution complete for {name}. Data is {data}'.format(
                    name=name, data=output_nb.data
                )
            )

            info.log.info("Output notebook path is {}".format(output_notebook_dir))

            for output_def in info.solid_def.output_defs:
                if output_def.name in output_nb.data:

                    value = read_value(output_def.runtime_type, output_nb.data[output_def.name])

                    yield Result(value, output_def.name)

        finally:
            if do_cleanup and os.path.exists(temp_path):
                os.remove(temp_path)

    return _t_fn


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
