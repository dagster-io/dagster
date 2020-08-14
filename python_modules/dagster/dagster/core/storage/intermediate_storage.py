from abc import ABCMeta, abstractmethod, abstractproperty

import six

from dagster import check
from dagster.core.execution.context.system import SystemExecutionContext
from dagster.core.execution.plan.objects import StepOutputHandle
from dagster.core.types.dagster_type import DagsterType, resolve_dagster_type

from .object_store import FilesystemObjectStore, InMemoryObjectStore, ObjectStore
from .type_storage import TypeStoragePluginRegistry


class IntermediateStorage(six.with_metaclass(ABCMeta)):  # pylint: disable=no-init
    @abstractmethod
    def get_intermediate(self, context, dagster_type=None, step_output_handle=None):
        pass

    @abstractmethod
    def set_intermediate(self, context, dagster_type=None, step_output_handle=None, value=None):
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

    def all_inputs_covered(self, context, step):
        return len(self.uncovered_inputs(context, step)) == 0

    def uncovered_inputs(self, context, step):
        from dagster.core.execution.plan.objects import ExecutionStep

        check.inst_param(step, 'step', ExecutionStep)
        uncovered_inputs = []
        for step_input in step.step_inputs:

            if step_input.is_from_single_output:
                for source_handle in step_input.source_handles:
                    if not self.has_intermediate(context, source_handle):
                        uncovered_inputs.append(source_handle)

            elif step_input.is_from_multiple_outputs:
                missing_source_handles = [
                    source_handle
                    for source_handle in step_input.source_handles
                    if not self.has_intermediate(context, source_handle)
                ]
                # only report as uncovered if all are missing from a multi-dep input
                if len(missing_source_handles) == len(step_input.source_handles):
                    uncovered_inputs = uncovered_inputs + missing_source_handles

        return uncovered_inputs


class InMemoryIntermediateStorage(IntermediateStorage):
    def __init__(self):

        self.values = {}

    # Note:
    # For the in-memory manager context and runtime are currently optional
    # because they are not strictly required. So we allow one to access
    # these values in places where those are not immediately available
    # but one wants to inspect intermediates. This is useful in test contexts
    # especially

    def get_intermediate(
        self, context, dagster_type=None, step_output_handle=None,
    ):
        check.opt_inst_param(context, 'context', SystemExecutionContext)
        check.opt_inst_param(dagster_type, 'dagster_type', DagsterType)
        check.inst_param(step_output_handle, 'step_output_handle', StepOutputHandle)
        return self.values[step_output_handle]

    def set_intermediate(
        self, context, dagster_type=None, step_output_handle=None, value=None,
    ):
        check.opt_inst_param(context, 'context', SystemExecutionContext)
        check.opt_inst_param(dagster_type, 'dagster_type', DagsterType)
        check.inst_param(step_output_handle, 'step_output_handle', StepOutputHandle)
        self.values[step_output_handle] = value

    def has_intermediate(self, context, step_output_handle):
        check.opt_inst_param(context, 'context', SystemExecutionContext)
        check.inst_param(step_output_handle, 'step_output_handle', StepOutputHandle)
        return step_output_handle in self.values

    def copy_intermediate_from_run(self, context, run_id, step_output_handle):
        check.failed('not implemented in in memory')

    @property
    def is_persistent(self):
        return False


class ObjectStoreIntermediateStorage(IntermediateStorage):
    def __init__(self, object_store, root_for_run_id, run_id, type_storage_plugin_registry):
        self.root_for_run_id = check.callable_param(root_for_run_id, 'root_for_run_id')
        self.run_id = check.str_param(run_id, 'run_id')
        self.object_store = check.inst_param(object_store, 'object_store', ObjectStore)
        self.type_storage_plugin_registry = check.inst_param(
            type_storage_plugin_registry, 'type_storage_plugin_registry', TypeStoragePluginRegistry
        )

    def _get_paths(self, step_output_handle):
        return ['intermediates', step_output_handle.step_key, step_output_handle.output_name]

    def get_intermediate_object(self, dagster_type, step_output_handle):
        check.inst_param(dagster_type, 'dagster_type', DagsterType)
        check.inst_param(step_output_handle, 'step_output_handle', StepOutputHandle)
        paths = self._get_paths(step_output_handle)
        check.param_invariant(len(paths) > 0, 'paths')

        key = self.object_store.key_for_paths([self.root] + paths)
        return self.object_store.get_object(
            key, serialization_strategy=dagster_type.serialization_strategy
        )

    def get_intermediate(
        self, context, dagster_type=None, step_output_handle=None,
    ):
        dagster_type = resolve_dagster_type(dagster_type)
        check.opt_inst_param(context, 'context', SystemExecutionContext)
        check.inst_param(dagster_type, 'dagster_type', DagsterType)
        check.inst_param(step_output_handle, 'step_output_handle', StepOutputHandle)
        check.invariant(self.has_intermediate(context, step_output_handle))

        if self.type_storage_plugin_registry.is_registered(dagster_type):
            return self.type_storage_plugin_registry.get(dagster_type.name).get_intermediate_object(
                self, context, dagster_type, step_output_handle
            )
        elif dagster_type.name is None:
            self.type_storage_plugin_registry.check_for_unsupported_composite_overrides(
                dagster_type
            )

        return self.get_intermediate_object(dagster_type, step_output_handle)

    def set_intermediate_object(self, dagster_type, step_output_handle, value):
        check.inst_param(dagster_type, 'dagster_type', DagsterType)
        check.inst_param(step_output_handle, 'step_output_handle', StepOutputHandle)
        paths = self._get_paths(step_output_handle)
        check.param_invariant(len(paths) > 0, 'paths')

        key = self.object_store.key_for_paths([self.root] + paths)
        return self.object_store.set_object(
            key, value, serialization_strategy=dagster_type.serialization_strategy
        )

    def set_intermediate(
        self, context, dagster_type=None, step_output_handle=None, value=None,
    ):
        dagster_type = resolve_dagster_type(dagster_type)
        check.opt_inst_param(context, 'context', SystemExecutionContext)
        check.inst_param(dagster_type, 'dagster_type', DagsterType)
        check.inst_param(step_output_handle, 'step_output_handle', StepOutputHandle)

        if self.has_intermediate(context, step_output_handle):
            context.log.warning(
                'Replacing existing intermediate for %s.%s'
                % (step_output_handle.step_key, step_output_handle.output_name)
            )

        if self.type_storage_plugin_registry.is_registered(dagster_type):
            return self.type_storage_plugin_registry.get(dagster_type.name).set_intermediate_object(
                self, context, dagster_type, step_output_handle, value
            )
        elif dagster_type.name is None:
            self.type_storage_plugin_registry.check_for_unsupported_composite_overrides(
                dagster_type
            )

        return self.set_intermediate_object(dagster_type, step_output_handle, value)

    def has_intermediate(self, context, step_output_handle):
        check.opt_inst_param(context, 'context', SystemExecutionContext)
        check.inst_param(step_output_handle, 'step_output_handle', StepOutputHandle)
        paths = self._get_paths(step_output_handle)
        check.list_param(paths, 'paths', of_type=str)
        check.param_invariant(len(paths) > 0, 'paths')

        key = self.object_store.key_for_paths([self.root] + paths)
        return self.object_store.has_object(key)

    def rm_intermediate(self, context, step_output_handle):
        check.opt_inst_param(context, 'context', SystemExecutionContext)
        check.inst_param(step_output_handle, 'step_output_handle', StepOutputHandle)
        paths = self._get_paths(step_output_handle)
        check.param_invariant(len(paths) > 0, 'paths')
        key = self.object_store.key_for_paths([self.root] + paths)
        return self.object_store.rm_object(key)

    def copy_intermediate_from_run(self, context, run_id, step_output_handle):
        check.opt_inst_param(context, 'context', SystemExecutionContext)
        check.str_param(run_id, 'run_id')
        check.inst_param(step_output_handle, 'step_output_handle', StepOutputHandle)
        paths = self._get_paths(step_output_handle)

        src = self.object_store.key_for_paths([self.root_for_run_id(run_id)] + paths)
        dst = self.object_store.key_for_paths([self.root] + paths)

        return self.object_store.cp_object(src, dst)

    def uri_for_paths(self, paths, protocol=None):
        check.list_param(paths, 'paths', of_type=str)
        check.param_invariant(len(paths) > 0, 'paths')
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


def build_in_mem_intermediates_storage(run_id, type_storage_plugin_registry=None):
    return ObjectStoreIntermediateStorage(
        InMemoryObjectStore(),
        lambda _: '',
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
