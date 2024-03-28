import os
import pickle
import uuid
from typing import TYPE_CHECKING, AbstractSet, Any, Mapping, Optional, cast

from dagster import (
    AssetMaterialization,
    AssetObservation,
    ExpectationResult,
    Failure,
    LoggerDefinition,
    ResourceDefinition,
    StepExecutionContext,
    TypeCheck,
    _check as check,
)
from dagster._core.definitions.dependency import NodeHandle
from dagster._core.definitions.events import RetryRequested
from dagster._core.definitions.graph_definition import GraphDefinition
from dagster._core.definitions.job_base import InMemoryJob
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.op_definition import OpDefinition
from dagster._core.definitions.reconstruct import ReconstructableJob
from dagster._core.definitions.resource_definition import ScopedResourcesBuilder
from dagster._core.events import DagsterEvent
from dagster._core.execution.api import create_execution_plan, scoped_job_context
from dagster._core.execution.plan.outputs import StepOutputHandle
from dagster._core.execution.plan.plan import ExecutionPlan
from dagster._core.execution.plan.state import KnownExecutionState
from dagster._core.execution.plan.step import ExecutionStep
from dagster._core.execution.resources_init import (
    get_required_resource_keys_to_init,
    resource_initialization_event_generator,
)
from dagster._core.instance import DagsterInstance
from dagster._core.instance.ref import InstanceRef
from dagster._core.log_manager import DagsterLogManager
from dagster._core.storage.dagster_run import DagsterRun, DagsterRunStatus
from dagster._core.system_config.objects import ResolvedRunConfig, ResourceConfig
from dagster._core.utils import make_new_run_id
from dagster._loggers import colored_console_logger
from dagster._serdes import unpack_value
from dagster._utils import EventGenerationManager

from .context import DagstermillExecutionContext, DagstermillRuntimeExecutionContext
from .errors import DagstermillError
from .serialize import PICKLE_PROTOCOL

if TYPE_CHECKING:
    from dagster._core.definitions.node_definition import NodeDefinition


class DagstermillResourceEventGenerationManager(EventGenerationManager):
    """Utility class to explicitly manage setup/teardown of resource events. Overrides the default
    `generate_teardown_events` method so that teardown is deferred until explicitly called by the
    dagstermill Manager.
    """

    def generate_teardown_events(self):
        return iter(())

    def teardown(self):
        return [
            teardown_event
            for teardown_event in super(
                DagstermillResourceEventGenerationManager, self
            ).generate_teardown_events()
        ]


class Manager:
    def __init__(self):
        self.job = None
        self.op_def: Optional[NodeDefinition] = None
        self.in_job: bool = False
        self.marshal_dir: Optional[str] = None
        self.context = None
        self.resource_manager = None

    def _setup_resources(
        self,
        resource_defs: Mapping[str, ResourceDefinition],
        resource_configs: Mapping[str, ResourceConfig],
        log_manager: DagsterLogManager,
        execution_plan: Optional[ExecutionPlan],
        dagster_run: Optional[DagsterRun],
        resource_keys_to_init: Optional[AbstractSet[str]],
        instance: Optional[DagsterInstance],
        emit_persistent_events: Optional[bool],
    ):
        """Drop-in replacement for
        `dagster._core.execution.resources_init.resource_initialization_manager`.  It uses a
        `DagstermillResourceEventGenerationManager` and explicitly calls `teardown` on it.
        """
        generator = resource_initialization_event_generator(
            resource_defs=resource_defs,
            resource_configs=resource_configs,
            log_manager=log_manager,
            execution_plan=execution_plan,
            dagster_run=dagster_run,
            resource_keys_to_init=resource_keys_to_init,
            instance=instance,
            emit_persistent_events=emit_persistent_events,
        )
        self.resource_manager = DagstermillResourceEventGenerationManager(
            generator, ScopedResourcesBuilder
        )
        return self.resource_manager

    def reconstitute_job_context(
        self,
        executable_dict: Mapping[str, Any],
        job_run_dict: Mapping[str, Any],
        node_handle_kwargs: Mapping[str, Any],
        instance_ref_dict: Mapping[str, Any],
        step_key: str,
        output_log_path: Optional[str] = None,
        marshal_dir: Optional[str] = None,
        run_config: Optional[Mapping[str, Any]] = None,
    ):
        """Reconstitutes a context for dagstermill-managed execution.

        You'll see this function called to reconstruct a job context within the ``injected
        parameters`` cell of a dagstermill output notebook. Users should not call this function
        interactively except when debugging output notebooks.

        Use :func:`dagstermill.get_context` in the ``parameters`` cell of your notebook to define a
        context for interactive exploration and development. This call will be replaced by one to
        :func:`dagstermill.reconstitute_job_context` when the notebook is executed by
        dagstermill.
        """
        check.opt_str_param(output_log_path, "output_log_path")
        check.opt_str_param(marshal_dir, "marshal_dir")
        run_config = check.opt_mapping_param(run_config, "run_config", key_type=str)
        check.mapping_param(job_run_dict, "job_run_dict")
        check.mapping_param(executable_dict, "executable_dict")
        check.mapping_param(node_handle_kwargs, "node_handle_kwargs")
        check.mapping_param(instance_ref_dict, "instance_ref_dict")
        check.str_param(step_key, "step_key")

        job = ReconstructableJob.from_dict(executable_dict)
        job_def = job.get_definition()

        try:
            instance_ref = unpack_value(instance_ref_dict, InstanceRef)
            instance = DagsterInstance.from_ref(instance_ref)
        except Exception as err:
            raise DagstermillError(
                "Error when attempting to resolve DagsterInstance from serialized InstanceRef"
            ) from err

        dagster_run = unpack_value(job_run_dict, DagsterRun)

        node_handle = NodeHandle.from_dict(node_handle_kwargs)
        op = job_def.get_node(node_handle)
        op_def = op.definition

        self.marshal_dir = marshal_dir
        self.in_job = True
        self.op_def = op_def
        self.job = job

        ResolvedRunConfig.build(job_def, run_config)

        execution_plan = create_execution_plan(
            self.job,
            run_config,
            step_keys_to_execute=dagster_run.step_keys_to_execute,
        )

        with scoped_job_context(
            execution_plan,
            job,
            run_config,
            dagster_run,
            instance,
            scoped_resources_builder_cm=self._setup_resources,
            # Set this flag even though we're not in test for clearer error reporting
            raise_on_error=True,
        ) as job_context:
            known_state = None
            if dagster_run.parent_run_id:
                known_state = KnownExecutionState.build_for_reexecution(
                    instance=instance,
                    parent_run=check.not_none(instance.get_run_by_id(dagster_run.parent_run_id)),
                )
            self.context = DagstermillRuntimeExecutionContext(
                job_context=job_context,
                job_def=job_def,
                op_config=run_config.get("ops", {}).get(op.name, {}).get("config"),
                resource_keys_to_init=get_required_resource_keys_to_init(
                    execution_plan,
                    job_def,
                ),
                op_name=op.name,
                node_handle=node_handle,
                step_context=cast(
                    StepExecutionContext,
                    job_context.for_step(
                        cast(ExecutionStep, execution_plan.get_step_by_key(step_key)),
                        known_state=known_state,
                    ),
                ),
            )

        return self.context

    def get_context(
        self,
        op_config: Any = None,
        resource_defs: Optional[Mapping[str, ResourceDefinition]] = None,
        logger_defs: Optional[Mapping[str, LoggerDefinition]] = None,
        run_config: Optional[dict] = None,
    ) -> DagstermillExecutionContext:
        """Get a dagstermill execution context for interactive exploration and development.

        Args:
            op_config (Optional[Any]): If specified, this value will be made available on the
                context as its ``op_config`` property.
            resource_defs (Optional[Mapping[str, ResourceDefinition]]): Specifies resources to provide to context.
            logger_defs (Optional[Mapping[str, LoggerDefinition]]): Specifies loggers to provide to context.
            run_config(Optional[dict]): The config dict with which to construct
                the context.

        Returns:
            :py:class:`~dagstermill.DagstermillExecutionContext`
        """
        run_config = check.opt_dict_param(run_config, "run_config", key_type=str)

        # If we are running non-interactively, and there is already a context reconstituted, return
        # that context rather than overwriting it.
        if self.context is not None and isinstance(
            self.context, DagstermillRuntimeExecutionContext
        ):
            return self.context

        if not logger_defs:
            logger_defs = {"dagstermill": colored_console_logger}
            run_config["loggers"] = {"dagstermill": {}}
        logger_defs = check.opt_mapping_param(logger_defs, "logger_defs")
        resource_defs = check.opt_mapping_param(resource_defs, "resource_defs")

        op_def = OpDefinition(
            name="this_op",
            compute_fn=lambda *args, **kwargs: None,
            description="Ephemeral op constructed by dagstermill.get_context()",
            required_resource_keys=set(resource_defs.keys()),
        )

        job_def = JobDefinition(
            graph_def=GraphDefinition(name="ephemeral_dagstermill_pipeline", node_defs=[op_def]),
            logger_defs=logger_defs,
            resource_defs=resource_defs,
        )

        run_id = make_new_run_id()

        # construct stubbed DagsterRun for notebook exploration...
        # The actual dagster run during job execution will be serialized and reconstituted
        # in the `reconstitute_job_context` call
        dagster_run = DagsterRun(
            job_name=job_def.name,
            run_id=run_id,
            run_config=run_config,
            step_keys_to_execute=None,
            status=DagsterRunStatus.NOT_STARTED,
            tags=None,
        )

        self.in_job = False
        self.op_def = op_def
        self.job = job_def

        job = InMemoryJob(job_def)
        execution_plan = create_execution_plan(job, run_config)

        with scoped_job_context(
            execution_plan,
            job,
            run_config,
            dagster_run,
            DagsterInstance.ephemeral(),
            scoped_resources_builder_cm=self._setup_resources,
        ) as job_context:
            self.context = DagstermillExecutionContext(
                job_context=job_context,
                job_def=job_def,
                op_config=op_config,
                resource_keys_to_init=get_required_resource_keys_to_init(
                    execution_plan,
                    job_def,
                ),
                op_name=op_def.name,
                node_handle=NodeHandle(op_def.name, parent=None),
            )

        return self.context

    def yield_result(self, value, output_name="result"):
        """Yield a result directly from notebook code.

        When called interactively or in development, returns its input.

        Args:
            value (Any): The value to yield.
            output_name (Optional[str]): The name of the result to yield (default: ``'result'``).
        """
        if not self.in_job:
            return value

        # deferred import for perf
        import scrapbook

        if not self.op_def.has_output(output_name):
            raise DagstermillError(
                f"Op {self.op_def.name} does not have output named {output_name}.Expected one of"
                f" {[str(output_def.name) for output_def in self.op_def.output_defs]}"
            )

        # pass output value cross process boundary using io manager
        step_context = self.context._step_context  # noqa: SLF001
        # Note: yield_result currently does not support DynamicOutput

        # dagstermill assets do not support yielding additional results within the notebook:
        if len(step_context.job_def.asset_layer.executable_asset_keys) > 0:
            raise DagstermillError(
                "dagstermill assets do not currently support dagstermill.yield_result"
            )

        step_output_handle = StepOutputHandle(
            step_key=step_context.step.key, output_name=output_name
        )
        output_context = step_context.get_output_context(step_output_handle)
        io_manager = step_context.get_io_manager(step_output_handle)

        # Note that we assume io manager is symmetric, i.e handle_input(handle_output(X)) == X
        io_manager.handle_output(output_context, value)

        # record that the output has been yielded
        scrapbook.glue(output_name, "")

    def yield_event(self, dagster_event):
        """Yield a dagster event directly from notebook code.

        When called interactively or in development, returns its input.

        Args:
            dagster_event (Union[:class:`dagster.AssetMaterialization`, :class:`dagster.ExpectationResult`, :class:`dagster.TypeCheck`, :class:`dagster.Failure`, :class:`dagster.RetryRequested`]):
                An event to yield back to Dagster.
        """
        valid_types = (
            AssetMaterialization,
            AssetObservation,
            ExpectationResult,
            TypeCheck,
            Failure,
            RetryRequested,
        )
        if not isinstance(dagster_event, valid_types):
            raise DagstermillError(
                f"Received invalid type {dagster_event} in yield_event. Expected a Dagster event"
                f" type, one of {valid_types}."
            )

        if not self.in_job:
            return dagster_event

        # deferred import for perf
        import scrapbook

        event_id = f"event-{uuid.uuid4()}"
        out_file_path = os.path.join(self.marshal_dir, event_id)
        with open(out_file_path, "wb") as fd:
            fd.write(pickle.dumps(dagster_event, PICKLE_PROTOCOL))

        scrapbook.glue(event_id, out_file_path)

    def teardown_resources(self):
        if self.resource_manager is not None:
            self.resource_manager.teardown()

    def load_input_parameter(self, input_name: str):
        # load input from source
        dm_context = check.not_none(self.context)
        if not isinstance(dm_context, DagstermillRuntimeExecutionContext):
            check.failed("Expected DagstermillRuntimeExecutionContext")
        step_context = dm_context.step_context
        step_input = step_context.step.step_input_named(input_name)
        input_def = step_context.op_def.input_def_named(input_name)
        for event_or_input_value in step_input.source.load_input_object(step_context, input_def):
            if isinstance(event_or_input_value, DagsterEvent):
                continue
            else:
                return event_or_input_value


MANAGER_FOR_NOTEBOOK_INSTANCE = Manager()
