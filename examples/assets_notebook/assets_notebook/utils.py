from papermill_origami.client import NoteableClient
from papermill_origami.util import removeprefix
from papermill_origami.noteable_dagstermill.context import SerializableExecutionContext
from dagster import (
    op,
    job,
    In,
    Field,
    Int,
    define_asset_job,
    Out,
    fs_io_manager,
    repository,
    ResourceDefinition,
    IOManagerDefinition,
    DagsterType,
    PartitionsDefinition,
    AssetIn,
    Out,
    OpDefinition
)
import dagstermill as dm
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Union, cast

from dagster._core.definitions import AssetsDefinition
from dagster._core.definitions.decorators.asset_decorator import _Asset, _make_asset_keys
from dagster._core.definitions.events import AssetKey, CoercibleToAssetKeyPrefix
import dagster._check as check
from dagster._core.definitions.utils import validate_tags

import copy
import os
import sys
import tempfile
import uuid
from base64 import b64encode
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Union, cast

import cloudpickle as pickle
import nbformat
import papermill
from dagster import In, OpDefinition, Out
from dagster import _check as check
from dagster._core.definitions.events import AssetMaterialization, Failure, Output, RetryRequested
from dagster._core.definitions.metadata import MetadataValue
from dagster._core.definitions.utils import validate_tags
from dagster._core.execution.context.compute import SolidExecutionContext
from dagster._core.execution.context.input import build_input_context
from dagster._core.execution.context.system import StepExecutionContext
from dagster._core.execution.plan.outputs import StepOutputHandle
from dagster._core.storage.file_manager import FileHandle
from dagster._legacy import InputDefinition, OutputDefinition, SolidDefinition
from dagster._utils import safe_tempfile_path
from dagster._utils.backcompat import rename_warning
from dagster._utils.error import serializable_error_info_from_exc_info
from dagstermill import _load_input_parameter, _reconstitute_pipeline_context
from dagstermill.compat import ExecutionError
from dagstermill.factory import _find_first_tagged_cell_index, get_papermill_parameters
from jupyter_client.utils import run_sync
from origami.client import ClientConfig
from papermill.iorw import load_notebook_node, write_ipynb
from papermill.translators import PythonTranslator



def _dm_compute(
    dagster_factory_name,
    name,
    notebook_path,
    output_notebook_name=None,
    asset_key_prefix=None,
    output_notebook=None,
):
    check.str_param(name, "name")
    check.str_param(notebook_path, "notebook_path")
    check.opt_str_param(output_notebook_name, "output_notebook_name")
    check.opt_list_param(asset_key_prefix, "asset_key_prefix")
    check.opt_str_param(output_notebook, "output_notebook")

    def _t_fn(context, **inputs):
        check.inst_param(context, "context", SolidExecutionContext)
        check.param_invariant(
            isinstance(context.run_config, dict),
            "context",
            "StepExecutionContext must have valid run_config",
        )

        step_execution_context: StepExecutionContext = context.get_step_execution_context()

        with tempfile.TemporaryDirectory() as output_notebook_dir:
            with safe_tempfile_path() as output_log_path:

                prefix = str(uuid.uuid4())
                parameterized_notebook_path = os.path.join(
                    output_notebook_dir, f"{prefix}-inter.ipynb"
                )

                executed_notebook_path = os.path.join(output_notebook_dir, f"{prefix}-out.ipynb")

                # noteable specific client
                noteable_client = NoteableClient(config=ClientConfig())
                # needs to be done before `load_notebook_node`
                run_sync(noteable_client.__aenter__)()

                # Scaffold the registration here
                nb = load_notebook_node(notebook_path)
                compute_descriptor = (
                    "solid" if dagster_factory_name == "define_dagstermill_solid" else "op"
                )

                base_parameters = get_papermill_parameters(
                    step_execution_context,
                    inputs,
                    output_log_path,
                    compute_descriptor,
                )
                job_definition_id = step_execution_context.job_name
                job_instance_id = step_execution_context.run_id
                file_id = removeprefix(notebook_path, "noteable://")
                noteable_parameters = {
                    'job_definition_id': job_definition_id,
                    'job_instance_id': job_instance_id,
                    'file_id': file_id,
                }
                context_args = base_parameters["__dm_context"]
                pipeline_context_args = dict(
                    executable_dict=base_parameters["__dm_executable_dict"],
                    pipeline_run_dict=base_parameters["__dm_pipeline_run_dict"],
                    solid_handle_kwargs=base_parameters["__dm_solid_handle_kwargs"],
                    instance_ref_dict=base_parameters["__dm_instance_ref_dict"],
                    step_key=base_parameters["__dm_step_key"],
                    **context_args,
                )
                reconstituted_pipeline_context = _reconstitute_pipeline_context(
                    **pipeline_context_args
                )
                serializable_ctx = SerializableExecutionContext(
                    pipeline_tags=reconstituted_pipeline_context._pipeline_context.log.logging_metadata.pipeline_tags,
                    op_config=reconstituted_pipeline_context.op_config,
                    resources=reconstituted_pipeline_context.resources,
                    run_id=reconstituted_pipeline_context.run_id,
                    run=reconstituted_pipeline_context.run,
                    solid_handle=reconstituted_pipeline_context.solid_handle,
                )
                serialized = serializable_ctx.dumps()
                serialized_context_b64 = b64encode(serialized).decode("utf-8")
                load_input_template = "cloudpickle.loads(b64decode({serialized_val}))"
                input_params_list = [
                    PythonTranslator().codify(noteable_parameters, "Noteable provided parameters"),
                    "\n# Dagster provided parameter inputs\n",
                    "\n".join(
                        [
                            f"{input_name} = {load_input_template.format(serialized_val=b64encode(pickle.dumps(_load_input_parameter(input_name))))}"  # noqa: E501
                            for input_name in base_parameters["__dm_input_names"]
                        ]
                    ),
                ]
                input_parameters = "".join(input_params_list)

                template = f"""# Injected parameters
import cloudpickle
from base64 import b64decode

serialized_context_b64 = "{serialized_context_b64}"
serialized_context = b64decode(serialized_context_b64)

context = cloudpickle.loads(serialized_context)
{input_parameters}
"""

                nb_no_parameters = copy.deepcopy(nb)
                newcell = nbformat.v4.new_code_cell(source=template)
                newcell.metadata["tags"] = ["injected-parameters"]

                param_cell_index = _find_first_tagged_cell_index(nb_no_parameters, "parameters")
                injected_cell_index = _find_first_tagged_cell_index(
                    nb_no_parameters, "injected-parameters"
                )
                if injected_cell_index >= 0:
                    # Replace the injected cell with a new version
                    before = nb_no_parameters.cells[:injected_cell_index]
                    after = nb_no_parameters.cells[injected_cell_index + 1 :]
                    check.int_value_param(param_cell_index, -1, "param_cell_index")
                    # We should have blown away the parameters cell if there is an injected-parameters cell
                elif param_cell_index >= 0:
                    # Replace the parameter cell with the injected-parameters cell
                    before = nb_no_parameters.cells[:param_cell_index]
                    after = nb_no_parameters.cells[param_cell_index + 1 :]
                else:
                    # Inject to the top of the notebook, presumably first cell includes dagstermill import
                    before = []
                    after = nb_no_parameters.cells
                nb_no_parameters.cells = before + [newcell] + after
                # nb_no_parameters.metadata.papermill["parameters"] = _seven.json.dumps(parameters)

                write_ipynb(nb_no_parameters, parameterized_notebook_path)

                try:
                    papermill.execute_notebook(
                        input_path=parameterized_notebook_path,
                        output_path=executed_notebook_path,
                        engine_name="noteable-dagstermill",  # noteable specific
                        log_output=True,
                        # noteable specific args
                        file_id=file_id,
                        client=noteable_client,
                        job_metadata={
                            'job_definition_id': job_definition_id,
                            'job_instance_id': job_instance_id,
                        },
                        logger=step_execution_context.log,
                    )
                except Exception as ex:
                    step_execution_context.log.warn(
                        f"Error when attempting to materialize executed notebook: {serializable_error_info_from_exc_info(sys.exc_info())}"  # noqa: E501
                    )
                    # pylint: disable=no-member
                    # compat:
                    if isinstance(ex, ExecutionError) and (
                        ex.ename == "RetryRequested" or ex.ename == "Failure"
                    ):
                        step_execution_context.log.warn(
                            f"Encountered raised {ex.ename} in notebook. Use dagstermill.yield_event "
                            "with RetryRequested or Failure to trigger their behavior."
                        )

                    raise
                finally:
                    run_sync(noteable_client.__aexit__)(None, None, None)

            step_execution_context.log.debug(
                f"Notebook execution complete for {name} at {executed_notebook_path}."
            )
            if output_notebook_name is not None:
                # yield output notebook binary stream as a solid output
                with open(executed_notebook_path, "rb") as fd:
                    yield Output(fd.read(), output_notebook_name)

            else:
                # backcompat
                executed_notebook_file_handle = None
                try:
                    # use binary mode when when moving the file since certain file_managers such as S3
                    # may try to hash the contents
                    with open(executed_notebook_path, "rb") as fd:
                        executed_notebook_file_handle = context.resources.file_manager.write(
                            fd, mode="wb", ext="ipynb"
                        )
                        executed_notebook_materialization_path = (
                            executed_notebook_file_handle.path_desc
                        )

                    yield AssetMaterialization(
                        asset_key=(asset_key_prefix + [f"{name}_output_notebook"]),
                        description="Location of output notebook in file manager",
                        metadata={
                            "path": MetadataValue.path(executed_notebook_materialization_path),
                        },
                    )

                except Exception:
                    # if file manager writing errors, e.g. file manager is not provided, we throw a warning
                    # and fall back to the previously stored temp executed notebook.
                    context.log.warning(
                        "Error when attempting to materialize executed notebook using file manager: "
                        f"{str(serializable_error_info_from_exc_info(sys.exc_info()))}"
                        f"\nNow falling back to local: notebook execution was temporarily materialized at {executed_notebook_path}"  # noqa: E501
                        "\nIf you have supplied a file manager and expect to use it for materializing the "
                        'notebook, please include "file_manager" in the `required_resource_keys` argument '
                        f"to `{dagster_factory_name}`"
                    )

                if output_notebook is not None:
                    yield Output(executed_notebook_file_handle, output_notebook)

            # deferred import for perf
            import scrapbook

            output_nb = scrapbook.read_notebook(executed_notebook_path)

            for (
                output_name,
                _,
            ) in step_execution_context.solid_def.output_dict.items():
                data_dict = output_nb.scraps.data_dict
                if output_name in data_dict:
                    # read outputs that were passed out of process via io manager from `yield_result`
                    step_output_handle = StepOutputHandle(
                        step_key=step_execution_context.step.key,
                        output_name=output_name,
                    )
                    output_context = step_execution_context.get_output_context(step_output_handle)
                    io_manager = step_execution_context.get_io_manager(step_output_handle)
                    value = io_manager.load_input(
                        build_input_context(
                            upstream_output=output_context, dagster_type=output_context.dagster_type
                        )
                    )

                    yield Output(value, output_name)

            for key, value in output_nb.scraps.items():
                if key.startswith("event-"):
                    with open(value.data, "rb") as fd:
                        event = pickle.loads(fd.read())
                        if isinstance(event, (Failure, RetryRequested)):
                            raise event
                        else:
                            yield event

    return _t_fn





def define_noteable_dagster_asset(
    name: str,
    notebook_path: str,
    notebook_url: str,
    key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
    ins: Optional[Mapping[str, AssetIn]] = None,
    non_argument_deps: Optional[Union[Set[AssetKey], Set[str]]] = None,
    metadata: Optional[Mapping[str, Any]] = None,
    config_schema: Optional[Union[Any, Dict[str, Any]]] = None,
    required_resource_keys: Optional[Set[str]] = None,
    resource_defs: Optional[Mapping[str, ResourceDefinition]] = None,
    io_manager_def: Optional[IOManagerDefinition] = None,
    io_manager_key: Optional[str] = None,
    description: Optional[str] = None,
    compute_kind: Optional[str] = None,
    dagster_type: Optional[DagsterType] = None,
    partitions_def: Optional[PartitionsDefinition] = None,
    op_tags: Optional[Dict[str, Any]] = None,
    group_name: Optional[str] = None,
    output_required: bool = True,
):

    # check.invariant(
    #     not (io_manager_key and io_manager_def),
    #     "Both io_manager_key and io_manager_def were provided to `@asset` decorator. Please provide one or the other. ",
    # )
    # if resource_defs is not None:
    #     experimental_arg_warning("resource_defs", "asset")

    # if io_manager_def is not None:
    #     experimental_arg_warning("io_manager_def", "asset")

    check.str_param(name, "name")
    check.str_param(notebook_path, "notebook_path")
    required_resource_keys = set(
        check.opt_set_param(required_resource_keys, "required_resource_keys", of_type=str)
    )
    ins = check.opt_mapping_param(ins, "ins", key_type=str, value_type=AssetIn)

    if isinstance(key_prefix, str):
        key_prefix = [key_prefix]

    key_prefix = check.opt_list_param(key_prefix, "key_prefix", of_type=str)

    default_description = f"This asset is backed by the notebook at {notebook_url}"
    description = check.opt_str_param(description, "description", default=default_description)

    user_tags = validate_tags(op_tags)
    if op_tags is not None:
        check.invariant(
            "notebook_path" not in op_tags,
            "user-defined op tags contains the `notebook_path` key, but the `notebook_path` key is reserved for use by Dagster",  # noqa: E501
        )
        check.invariant(
            "kind" not in op_tags,
            "user-defined op tags contains the `kind` key, but the `kind` key is reserved for use by Dagster",
        )
    default_tags = {"notebook_path": notebook_url, "kind": "noteable"}
    metadata = {"notebook_path": notebook_url}

    return _Asset(
        name=cast(Optional[str], name),  # (mypy bug that it can't infer name is Optional[str])
        key_prefix=key_prefix,
        ins=ins,
        non_argument_deps=_make_asset_keys(non_argument_deps),
        metadata=metadata,
        description=description,
        config_schema=config_schema,
        required_resource_keys=required_resource_keys,
        resource_defs=resource_defs,
        io_manager=io_manager_def or io_manager_key,
        compute_kind=check.opt_str_param(compute_kind, "compute_kind"),
        dagster_type=dagster_type,
        partitions_def=partitions_def,
        op_tags={**user_tags, **default_tags},
        group_name=group_name,
        output_required=output_required,
        ignore_ins_checking=True
    )(_dm_compute(
            "define_dagstermill_op",
            name,
            notebook_path,
            asset_key_prefix=key_prefix
        )
    )
