import warnings
from abc import ABC, abstractmethod, abstractproperty

from dagster import check
from dagster.core.definitions.events import ObjectStoreOperation, ObjectStoreOperationType
from dagster.core.errors import DagsterObjectStoreError, DagsterStepOutputNotFoundError
from dagster.core.execution.context.system import SystemExecutionContext
from dagster.core.execution.plan.outputs import StepOutputHandle
from dagster.core.storage.io_manager import IOManager
from dagster.core.types.dagster_type import DagsterType, resolve_dagster_type

from .object_store import FilesystemObjectStore, InMemoryObjectStore, ObjectStore
from .type_storage import TypeStoragePluginRegistry


class IntermediateStorage(ABC):  # pylint: disable=no-init
    @abstractmethod
    def get_intermediate(self, context, dagster_type=None, step_output_handle=None):
        pass

    @abstractmethod
    def set_intermediate(
        self, context, dagster_type=None, step_output_handle=None, value=None, version=None
    ):
        pass

    @abstractmethod
    def has_intermediate(self, context, step_output_handle):
        pass

    @abstractmethod
    def copy_intermediate_from_run(self, context, run_id, step_output_handle):
        pass

    @abstractproperty
    def is_persistent(self):
        pass


class IntermediateStorageAdapter(IOManager):
    def __init__(self, intermediate_storage):
        self.intermediate_storage = check.inst_param(
            intermediate_storage, "intermediate_storage", IntermediateStorage
        )
        warnings.warn(
            "Intermediate Storages are deprecated in 0.10.0 and will be removed in 0.11.0. "
            "Use IO Managers instead, which gives you better control over how inputs and "
            "outputs are handled and loaded."
        )

    def handle_output(self, context, obj):
        res = self.intermediate_storage.set_intermediate(
            context=context.step_context,
            dagster_type=context.dagster_type,
            step_output_handle=StepOutputHandle(
                context.step_key, context.name, context.mapping_key
            ),
            value=obj,
            version=context.version,
        )

        # Stopgap https://github.com/dagster-io/dagster/issues/3368
        if isinstance(res, ObjectStoreOperation):
            context.log.debug(
                (
                    'Stored output "{output_name}" in {object_store_name}object store{serialization_strategy_modifier} '
                    "at {address}"
                ).format(
                    output_name=context.name,
                    object_store_name=res.object_store_name,
                    serialization_strategy_modifier=(
                        " using {serialization_strategy_name}".format(
                            serialization_strategy_name=res.serialization_strategy_name
                        )
                        if res.serialization_strategy_name
                        else ""
                    ),
                    address=res.key,
                )
            )

    def load_input(self, context):
        step_context = context.step_context
        source_handle = StepOutputHandle(
            context.upstream_output.step_key,
            context.upstream_output.name,
            context.upstream_output.mapping_key,
        )

        # backcompat behavior: copy intermediate from parent run to the current run destination
        if (
            context.upstream_output
            and context.upstream_output.run_id == step_context.pipeline_run.parent_run_id
        ):
            if not self.intermediate_storage.has_intermediate(step_context, source_handle):
                operation = self.intermediate_storage.copy_intermediate_from_run(
                    step_context, step_context.pipeline_run.parent_run_id, source_handle
                )

                context.log.debug(
                    "Copied object for input {input_name} from {key} to {dest_key}".format(
                        input_name=context.name, key=operation.key, dest_key=operation.dest_key
                    )
                )

        if not self.intermediate_storage.has_intermediate(step_context, source_handle):
            raise DagsterStepOutputNotFoundError(
                (
                    "When executing {step}, discovered required output missing "
                    "from previous step: {previous_step}"
                ).format(previous_step=source_handle.step_key, step=step_context.step.key),
                step_key=source_handle.step_key,
                output_name=source_handle.output_name,
            )
        res = self.intermediate_storage.get_intermediate(
            context=step_context,
            dagster_type=context.dagster_type,
            step_output_handle=source_handle,
        )

        # Stopgap https://github.com/dagster-io/dagster/issues/3368
        if isinstance(res, ObjectStoreOperation):
            context.log.debug(
                (
                    "Loaded input {input_name} in {object_store_name}object store{serialization_strategy_modifier} "
                    "from {address}"
                ).format(
                    input_name=context.name,
                    object_store_name=res.object_store_name,
                    serialization_strategy_modifier=(
                        " using {serialization_strategy_name}".format(
                            serialization_strategy_name=res.serialization_strategy_name
                        )
                        if res.serialization_strategy_name
                        else ""
                    ),
                    address=res.key,
                )
            )
            return res.obj
        else:
            return res


class ObjectStoreIntermediateStorage(IntermediateStorage):
    def __init__(self, object_store, root_for_run_id, run_id, type_storage_plugin_registry):
        self.root_for_run_id = check.callable_param(root_for_run_id, "root_for_run_id")
        self.run_id = check.str_param(run_id, "run_id")
        self.object_store = check.inst_param(object_store, "object_store", ObjectStore)
        self.type_storage_plugin_registry = check.inst_param(
            type_storage_plugin_registry, "type_storage_plugin_registry", TypeStoragePluginRegistry
        )

    def _get_paths(self, step_output_handle):
        if step_output_handle.mapping_key:
            return [
                "intermediates",
                step_output_handle.step_key,
                step_output_handle.output_name,
                step_output_handle.mapping_key,
            ]
        return ["intermediates", step_output_handle.step_key, step_output_handle.output_name]

    def get_intermediate_object(self, dagster_type, step_output_handle):
        check.inst_param(dagster_type, "dagster_type", DagsterType)
        check.inst_param(step_output_handle, "step_output_handle", StepOutputHandle)
        paths = self._get_paths(step_output_handle)
        check.param_invariant(len(paths) > 0, "paths")

        key = self.object_store.key_for_paths([self.root] + paths)

        try:
            obj, uri = self.object_store.get_object(
                key, serialization_strategy=dagster_type.serialization_strategy
            )
        except Exception as error:  # pylint: disable=broad-except
            raise DagsterObjectStoreError(
                _object_store_operation_error_message(
                    step_output_handle=step_output_handle,
                    op=ObjectStoreOperationType.GET_OBJECT,
                    object_store_name=self.object_store.name,
                    serialization_strategy_name=dagster_type.serialization_strategy.name,
                )
            ) from error

        return ObjectStoreOperation(
            op=ObjectStoreOperationType.GET_OBJECT,
            key=uri,
            dest_key=None,
            obj=obj,
            serialization_strategy_name=dagster_type.serialization_strategy.name,
            object_store_name=self.object_store.name,
        )

    def get_intermediate(
        self,
        context,
        dagster_type=None,
        step_output_handle=None,
    ):
        dagster_type = resolve_dagster_type(dagster_type)
        check.opt_inst_param(context, "context", SystemExecutionContext)
        check.inst_param(dagster_type, "dagster_type", DagsterType)
        check.inst_param(step_output_handle, "step_output_handle", StepOutputHandle)
        check.invariant(self.has_intermediate(context, step_output_handle))

        if self.type_storage_plugin_registry.is_registered(dagster_type):
            return self.type_storage_plugin_registry.get(
                dagster_type.unique_name
            ).get_intermediate_object(self, context, dagster_type, step_output_handle)
        elif not dagster_type.has_unique_name:
            self.type_storage_plugin_registry.check_for_unsupported_composite_overrides(
                dagster_type
            )

        return self.get_intermediate_object(dagster_type, step_output_handle)

    def set_intermediate_object(self, dagster_type, step_output_handle, value, version=None):
        check.inst_param(dagster_type, "dagster_type", DagsterType)
        check.inst_param(step_output_handle, "step_output_handle", StepOutputHandle)
        paths = self._get_paths(step_output_handle)
        check.param_invariant(len(paths) > 0, "paths")

        key = self.object_store.key_for_paths([self.root] + paths)

        try:
            uri = self.object_store.set_object(
                key, value, serialization_strategy=dagster_type.serialization_strategy
            )
        except Exception as error:  # pylint: disable=broad-except
            raise DagsterObjectStoreError(
                _object_store_operation_error_message(
                    step_output_handle=step_output_handle,
                    op=ObjectStoreOperationType.SET_OBJECT,
                    object_store_name=self.object_store.name,
                    serialization_strategy_name=dagster_type.serialization_strategy.name,
                )
            ) from error

        return ObjectStoreOperation(
            op=ObjectStoreOperationType.SET_OBJECT,
            key=uri,
            dest_key=None,
            obj=value,
            serialization_strategy_name=dagster_type.serialization_strategy.name,
            object_store_name=self.object_store.name,
            version=version,
        )

    def set_intermediate(
        self,
        context,
        dagster_type=None,
        step_output_handle=None,
        value=None,
        version=None,
    ):
        dagster_type = resolve_dagster_type(dagster_type)
        check.opt_inst_param(context, "context", SystemExecutionContext)
        check.inst_param(dagster_type, "dagster_type", DagsterType)
        check.inst_param(step_output_handle, "step_output_handle", StepOutputHandle)
        check.opt_str_param(version, "version")

        if self.has_intermediate(context, step_output_handle):
            context.log.warning(
                "Replacing existing intermediate for %s.%s"
                % (step_output_handle.step_key, step_output_handle.output_name)
            )

        if self.type_storage_plugin_registry.is_registered(dagster_type):
            return self.type_storage_plugin_registry.get(
                dagster_type.unique_name
            ).set_intermediate_object(self, context, dagster_type, step_output_handle, value)
        elif not dagster_type.has_unique_name:
            self.type_storage_plugin_registry.check_for_unsupported_composite_overrides(
                dagster_type
            )

        return self.set_intermediate_object(dagster_type, step_output_handle, value, version)

    def has_intermediate(self, context, step_output_handle):
        check.opt_inst_param(context, "context", SystemExecutionContext)
        check.inst_param(step_output_handle, "step_output_handle", StepOutputHandle)
        paths = self._get_paths(step_output_handle)
        check.list_param(paths, "paths", of_type=str)
        check.param_invariant(len(paths) > 0, "paths")

        key = self.object_store.key_for_paths([self.root] + paths)
        return self.object_store.has_object(key)

    def rm_intermediate(self, context, step_output_handle):
        check.opt_inst_param(context, "context", SystemExecutionContext)
        check.inst_param(step_output_handle, "step_output_handle", StepOutputHandle)
        paths = self._get_paths(step_output_handle)
        check.param_invariant(len(paths) > 0, "paths")
        key = self.object_store.key_for_paths([self.root] + paths)

        uri = self.object_store.rm_object(key)
        return ObjectStoreOperation(
            op=ObjectStoreOperationType.RM_OBJECT,
            key=uri,
            dest_key=None,
            obj=None,
            serialization_strategy_name=None,
            object_store_name=self.object_store.name,
        )

    def copy_intermediate_from_run(self, context, run_id, step_output_handle):
        check.opt_inst_param(context, "context", SystemExecutionContext)
        check.str_param(run_id, "run_id")
        check.inst_param(step_output_handle, "step_output_handle", StepOutputHandle)
        paths = self._get_paths(step_output_handle)

        src = self.object_store.key_for_paths([self.root_for_run_id(run_id)] + paths)
        dst = self.object_store.key_for_paths([self.root] + paths)

        src_uri, dst_uri = self.object_store.cp_object(src, dst)
        return ObjectStoreOperation(
            op=ObjectStoreOperationType.CP_OBJECT,
            key=src_uri,
            dest_key=dst_uri,
            object_store_name=self.object_store.name,
        )

    def uri_for_paths(self, paths, protocol=None):
        check.list_param(paths, "paths", of_type=str)
        check.param_invariant(len(paths) > 0, "paths")
        key = self.key_for_paths(paths)
        return self.object_store.uri_for_key(key, protocol)

    def key_for_paths(self, paths):
        return self.object_store.key_for_paths([self.root] + paths)

    @property
    def is_persistent(self):
        if isinstance(self.object_store, InMemoryObjectStore):
            return False
        return True

    @property
    def root(self):
        return self.root_for_run_id(self.run_id)


def _object_store_operation_error_message(
    op, step_output_handle, object_store_name, serialization_strategy_name
):
    if ObjectStoreOperationType(op) == ObjectStoreOperationType.GET_OBJECT:
        op_name = "retriving"
    elif ObjectStoreOperationType(op) == ObjectStoreOperationType.SET_OBJECT:
        op_name = "storing"
    else:
        op_name = ""

    return (
        'Error occurred during {op_name} output "{output_name}" for step "{step_key}" in '
        "{object_store_modifier}object store{serialization_strategy_modifier}."
    ).format(
        op_name=op_name,
        step_key=step_output_handle.step_key,
        output_name=step_output_handle.output_name,
        object_store_modifier=(
            '"{object_store_name}" '.format(object_store_name=object_store_name)
            if object_store_name
            else ""
        ),
        serialization_strategy_modifier=(
            ' using "{serialization_strategy_name}"'.format(
                serialization_strategy_name=serialization_strategy_name
            )
            if serialization_strategy_name
            else ""
        ),
    )


def build_in_mem_intermediates_storage(run_id, type_storage_plugin_registry=None):
    return ObjectStoreIntermediateStorage(
        InMemoryObjectStore(),
        lambda _: "",
        run_id,
        type_storage_plugin_registry
        if type_storage_plugin_registry
        else TypeStoragePluginRegistry(types_to_register=[]),
    )


def build_fs_intermediate_storage(root_for_run_id, run_id, type_storage_plugin_registry=None):
    return ObjectStoreIntermediateStorage(
        FilesystemObjectStore(),
        root_for_run_id,
        run_id,
        type_storage_plugin_registry
        if type_storage_plugin_registry
        else TypeStoragePluginRegistry(types_to_register=[]),
    )
