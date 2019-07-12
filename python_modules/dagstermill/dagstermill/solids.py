import copy
import os
import pickle
import tempfile
import threading
import uuid

import nbformat
import papermill
import six

from papermill.engines import papermill_engines
from papermill.parameterize import _find_first_tagged_cell_index
from papermill.iorw import load_notebook_node, write_ipynb

from dagster import (
    check,
    ExecutionTargetHandle,
    EventMetadataEntry,
    InputDefinition,
    Materialization,
    OutputDefinition,
    Output,
    SolidDefinition,
    seven,
)
from dagster.core.errors import user_code_error_boundary
from dagster.core.execution.context.system import SystemComputeExecutionContext
from dagster.core.execution.context.compute import ComputeExecutionContext
from dagster.core.types.field_utils import check_user_facing_opt_field_param
from dagster.utils import mkdir_p

from .engine import DagstermillNBConvertEngine
from .errors import DagstermillExecutionError, DagstermillError
from .logger import init_db, JsonSqlite3LogWatcher
from .serialize import read_value, write_value
from .translator import DagsterTranslator, RESERVED_INPUT_NAMES


# This is based on papermill.parameterize.parameterize_notebook
# Typically, papermill injects the injected-parameters cell *below* the parameters cell
# but we want to *replace* the parameters cell, which is what this function does.
def replace_parameters(context, nb, parameters):
    '''Assigned parameters into the appropiate place in the input notebook

    Args:
        nb (NotebookNode): Executable notebook object
        parameters (dict): Arbitrary keyword arguments to pass to the notebook parameters.
    '''
    check.dict_param(parameters, 'parameters')

    # Copy the nb object to avoid polluting the input
    nb = copy.deepcopy(nb)

    # papermill method chooses translator based on kernel_name and language, but we just call the
    # DagsterTranslator to generate parameter content based on the kernel_name
    param_content = DagsterTranslator.codify(parameters)

    newcell = nbformat.v4.new_code_cell(source=param_content)
    newcell.metadata['tags'] = ['injected-parameters']

    param_cell_index = _find_first_tagged_cell_index(nb, 'parameters')
    injected_cell_index = _find_first_tagged_cell_index(nb, 'injected-parameters')
    if injected_cell_index >= 0:
        # Replace the injected cell with a new version
        before = nb.cells[:injected_cell_index]
        after = nb.cells[injected_cell_index + 1 :]
        check.int_value_param(param_cell_index, -1, 'param_cell_index')
        # We should have blown away the parameters cell if there is an injected-parameters cell
    elif param_cell_index >= 0:
        # Replace the parameter cell with the injected-parameters cell
        before = nb.cells[:param_cell_index]
        after = nb.cells[param_cell_index + 1 :]
    else:
        # Inject to the top of the notebook, presumably first cell includes dagstermill import
        context.log.debug(
            (
                'Executing notebook with no tagged parameters cell: injecting boilerplate in first '
                'cell.'
            )
        )
        before = nb.cells[:1]
        after = nb.cells[1:]

    nb.cells = before + [newcell] + after
    nb.metadata.papermill['parameters'] = parameters

    return nb


def get_papermill_parameters(compute_context, inputs, output_log_path):
    check.inst_param(compute_context, 'compute_context', SystemComputeExecutionContext)
    check.param_invariant(
        isinstance(compute_context.environment_dict, dict),
        'compute_context',
        'SystemComputeExecutionContext must have valid environment_dict',
    )
    check.dict_param(inputs, 'inputs', key_type=six.string_types)

    run_id = compute_context.run_id

    marshal_dir = '/tmp/dagstermill/{run_id}/marshal'.format(run_id=run_id)
    mkdir_p(marshal_dir)

    handle = ExecutionTargetHandle.get_handle(compute_context.pipeline_def)

    if not handle:
        raise DagstermillError(
            'Can\'t execute a dagstermill solid from a pipeline that wasn\'t instantiated using '
            'an ExecutionTargetHandle'
        )

    dm_handle_kwargs = handle.data._asdict()

    dm_handle_kwargs['pipeline_name'] = compute_context.pipeline_def.name

    dm_context_dict = {
        'output_log_path': output_log_path,
        'marshal_dir': marshal_dir,
        'environment_dict': compute_context.environment_dict,
    }

    dm_run_config_kwargs = {'run_id': run_id, 'mode': compute_context.mode_def.name}

    dm_solid_handle_kwargs = compute_context.solid_handle._asdict()

    parameters = {}

    input_def_dict = compute_context.solid_def.input_dict
    for input_name, input_value in inputs.items():
        assert (
            input_name not in RESERVED_INPUT_NAMES
        ), 'Dagstermill solids cannot have inputs named {input_name}'.format(input_name=input_name)
        runtime_type = input_def_dict[input_name].runtime_type
        parameter_value = write_value(
            runtime_type, input_value, os.path.join(marshal_dir, 'input-{}'.format(input_name))
        )
        parameters[input_name] = parameter_value

    parameters['__dm_context'] = seven.json.dumps(dm_context_dict)
    parameters['__dm_handle_kwargs'] = seven.json.dumps(dm_handle_kwargs)
    parameters['__dm_run_config_kwargs'] = seven.json.dumps(dm_run_config_kwargs)
    parameters['__dm_solid_handle_kwargs'] = seven.json.dumps(dm_solid_handle_kwargs)

    return parameters


def _dm_solid_compute(name, notebook_path):
    check.str_param(name, 'name')
    check.str_param(notebook_path, 'notebook_path')

    def _t_fn(compute_context, inputs):
        check.inst_param(compute_context, 'compute_context', ComputeExecutionContext)
        check.param_invariant(
            isinstance(compute_context.environment_dict, dict),
            'context',
            'SystemComputeExecutionContext must have valid environment_dict',
        )

        system_compute_context = compute_context.get_system_context()

        base_dir = '/tmp/dagstermill/{run_id}/'.format(run_id=compute_context.run_id)
        output_notebook_dir = os.path.join(base_dir, 'output_notebooks/')
        mkdir_p(output_notebook_dir)

        temp_path = os.path.join(
            output_notebook_dir, '{prefix}-out.ipynb'.format(prefix=str(uuid.uuid4()))
        )

        with tempfile.NamedTemporaryFile() as output_log_file:
            output_log_path = output_log_file.name
            init_db(output_log_path)

            # Scaffold the registration here
            nb = load_notebook_node(notebook_path)
            nb_no_parameters = replace_parameters(
                system_compute_context,
                nb,
                get_papermill_parameters(system_compute_context, inputs, output_log_path),
            )
            intermediate_path = os.path.join(
                output_notebook_dir, '{prefix}-inter.ipynb'.format(prefix=str(uuid.uuid4()))
            )
            write_ipynb(nb_no_parameters, intermediate_path)

            # Although the type of is_done is threading._Event in py2, not threading.Event,
            # it is still constructed using the threading.Event() factory
            is_done = threading.Event()

            def log_watcher_thread_target():
                log_watcher = JsonSqlite3LogWatcher(
                    output_log_path, system_compute_context.log, is_done
                )
                log_watcher.watch()

            log_watcher_thread = threading.Thread(target=log_watcher_thread_target)

            log_watcher_thread.start()

            with user_code_error_boundary(
                DagstermillExecutionError,
                lambda: (
                    'Error occurred during the execution of Dagstermill solid '
                    '{solid_name}: {notebook_path}'.format(
                        solid_name=name, notebook_path=notebook_path
                    )
                ),
            ):
                try:
                    papermill_engines.register('dagstermill', DagstermillNBConvertEngine)
                    papermill.execute_notebook(
                        intermediate_path, temp_path, engine_name='dagstermill', log_output=True
                    )
                except Exception as exc:
                    yield Materialization(
                        label='output_notebook',
                        description='Location of output notebook on the filesystem',
                        metadata_entries=[EventMetadataEntry.fspath(temp_path)],
                    )
                    raise exc
                finally:
                    is_done.set()
                    log_watcher_thread.join()

            # deferred import for perf
            import scrapbook

            output_nb = scrapbook.read_notebook(temp_path)

            system_compute_context.log.debug(
                'Notebook execution complete for {name}. Data is {data}'.format(
                    name=name, data=output_nb.scraps
                )
            )

            yield Materialization(
                label='output_notebook',
                description='Location of output notebook on the filesystem',
                metadata_entries=[EventMetadataEntry.fspath(temp_path)],
            )

            for (output_name, output_def) in system_compute_context.solid_def.output_dict.items():
                data_dict = output_nb.scraps.data_dict
                if output_name in data_dict:
                    value = read_value(output_def.runtime_type, data_dict[output_name])

                    yield Output(value, output_name)

            for key, value in output_nb.scraps.items():
                if key.startswith('event-'):
                    with open(value.data, 'rb') as fd:
                        yield pickle.loads(fd.read())

    return _t_fn


def define_dagstermill_solid(
    name,
    notebook_path,
    input_defs=None,
    output_defs=None,
    config_field=None,
    required_resource_keys=None,
):
    '''Wrap a Jupyter notebook in a solid.

    Arguments:
        name (str): The name of the solid.
        notebook_path (str): Path to the backing notebook.
        input_defs (Optional[list[:class:`dagster.InputDefinition`]]): The solid's inputs.
        output_defs (Optional[list[:class:`dagster.OutputDefinition`]]): The solid's outputs.
        required_resource_keys (Optional[set[str]]): The string names of any required resources.

    Returns:
        :class:`dagster.SolidDefinition`
    '''
    check.str_param(name, 'name')
    check.str_param(notebook_path, 'notebook_path')
    input_defs = check.opt_list_param(input_defs, 'input_defs', of_type=InputDefinition)
    output_defs = check.opt_list_param(output_defs, 'output_defs', of_type=OutputDefinition)
    required_resource_keys = check.opt_set_param(
        required_resource_keys, 'required_resource_keys', of_type=str
    )
    config_field = check_user_facing_opt_field_param(
        config_field, 'config_field', 'of a dagstermill solid named "{name}"'.format(name=name)
    )

    return SolidDefinition(
        name=name,
        input_defs=input_defs,
        compute_fn=_dm_solid_compute(name, notebook_path),
        output_defs=output_defs,
        config_field=config_field,
        required_resource_keys=required_resource_keys,
        description='This solid is backed by the notebook at {path}'.format(path=notebook_path),
        metadata={'notebook_path': notebook_path, 'kind': 'ipynb'},
    )
