from abc import ABCMeta, abstractmethod, abstractproperty

import six

from dagster import check
from dagster.core.execution.context.system import SystemPipelineExecutionContext
from dagster.core.execution.plan.objects import StepOutputHandle
from dagster.core.types.dagster_type import DagsterType
from dagster.utils.backcompat import canonicalize_backcompat_args

from .intermediate_store import IntermediateStore


class IntermediatesManager(six.with_metaclass(ABCMeta)):  # pylint: disable=no-init
    @abstractmethod
    def get_intermediate(
        self, context, dagster_type=None, step_output_handle=None, runtime_type=None
    ):
        pass

    @abstractmethod
    def set_intermediate(
        self, context, dagster_type=None, step_output_handle=None, value=None, runtime_type=None
    ):
        pass

    @abstractmethod
    def has_intermediate(self, context, step_output_handle):
        pass

    @abstractmethod
    def copy_intermediate_from_prev_run(self, context, previous_run_id, step_output_handle):
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
            for source_handle in step_input.source_handles:
                if not self.has_intermediate(context, source_handle):
                    uncovered_inputs.append(source_handle)
        return uncovered_inputs


class InMemoryIntermediatesManager(IntermediatesManager):
    def __init__(self):

        self.values = {}

    # Note:
    # For the in-memory manager context and runtime are currently optional
    # because they are not strictly required. So we allow one to access
    # these values in places where those are not immediately avaiable
    # but one wants to inspect intermediates. This is useful in test contexts
    # especially

    def get_intermediate(
        self, context, dagster_type=None, step_output_handle=None, runtime_type=None
    ):
        canonicalize_dagster_type = canonicalize_backcompat_args(
            dagster_type, 'dagster_type', runtime_type, 'runtime_type',
        )  # TODO to deprecate in 0.8.0
        check.opt_inst_param(context, 'context', SystemPipelineExecutionContext)
        check.opt_inst_param(canonicalize_dagster_type, 'dagster_type', DagsterType)
        check.inst_param(step_output_handle, 'step_output_handle', StepOutputHandle)
        return self.values[step_output_handle]

    def set_intermediate(
        self, context, dagster_type=None, step_output_handle=None, value=None, runtime_type=None
    ):
        canonicalize_dagster_type = canonicalize_backcompat_args(
            dagster_type, 'dagster_type', runtime_type, 'runtime_type',
        )  # TODO to deprecate in 0.8.0
        check.opt_inst_param(context, 'context', SystemPipelineExecutionContext)
        check.opt_inst_param(canonicalize_dagster_type, 'dagster_type', DagsterType)
        check.inst_param(step_output_handle, 'step_output_handle', StepOutputHandle)
        self.values[step_output_handle] = value

    def has_intermediate(self, context, step_output_handle):
        check.opt_inst_param(context, 'context', SystemPipelineExecutionContext)
        check.inst_param(step_output_handle, 'step_output_handle', StepOutputHandle)
        return step_output_handle in self.values

    def copy_intermediate_from_prev_run(self, context, previous_run_id, step_output_handle):
        check.failed('not implemented in in memory')

    @property
    def is_persistent(self):
        return False


class IntermediateStoreIntermediatesManager(IntermediatesManager):
    def __init__(self, intermediate_store):
        self._intermediate_store = check.inst_param(
            intermediate_store, 'intermediate_store', IntermediateStore
        )

    def _get_paths(self, step_output_handle):
        return ['intermediates', step_output_handle.step_key, step_output_handle.output_name]

    def get_intermediate(
        self, context, dagster_type=None, step_output_handle=None, runtime_type=None
    ):
        canonicalize_dagster_type = canonicalize_backcompat_args(
            dagster_type, 'dagster_type', runtime_type, 'runtime_type',
        )  # TODO to deprecate in 0.8.0
        check.inst_param(context, 'context', SystemPipelineExecutionContext)
        check.inst_param(canonicalize_dagster_type, 'dagster_type', DagsterType)
        check.inst_param(step_output_handle, 'step_output_handle', StepOutputHandle)
        check.invariant(self.has_intermediate(context, step_output_handle))

        return self._intermediate_store.get_value(
            context=context,
            dagster_type=canonicalize_dagster_type,
            paths=self._get_paths(step_output_handle),
        )

    def set_intermediate(
        self, context, dagster_type=None, step_output_handle=None, value=None, runtime_type=None
    ):
        canonicalize_dagster_type = canonicalize_backcompat_args(
            dagster_type, 'dagster_type', runtime_type, 'runtime_type',
        )  # TODO to deprecate in 0.8.0
        check.inst_param(context, 'context', SystemPipelineExecutionContext)
        check.inst_param(canonicalize_dagster_type, 'dagster_type', DagsterType)
        check.inst_param(step_output_handle, 'step_output_handle', StepOutputHandle)

        if self.has_intermediate(context, step_output_handle):
            context.log.warning(
                'Replacing existing intermediate for %s.%s'
                % (step_output_handle.step_key, step_output_handle.output_name)
            )

        return self._intermediate_store.set_value(
            obj=value,
            context=context,
            dagster_type=canonicalize_dagster_type,
            paths=self._get_paths(step_output_handle),
        )

    def has_intermediate(self, context, step_output_handle):
        check.inst_param(context, 'context', SystemPipelineExecutionContext)
        check.inst_param(step_output_handle, 'step_output_handle', StepOutputHandle)

        return self._intermediate_store.has_object(context, self._get_paths(step_output_handle))

    def copy_intermediate_from_prev_run(self, context, previous_run_id, step_output_handle):
        return self._intermediate_store.copy_object_from_prev_run(
            context, previous_run_id, self._get_paths(step_output_handle)
        )

    @property
    def is_persistent(self):
        return True
