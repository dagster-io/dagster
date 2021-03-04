import os
import pickle
import uuid

from dagster import (
    AssetMaterialization,
    ExpectationResult,
    Failure,
    Materialization,
    ModeDefinition,
    PipelineDefinition,
    SolidDefinition,
    TypeCheck,
    check,
    seven,
)
from dagster.core.definitions.dependency import SolidHandle
from dagster.core.definitions.reconstructable import ReconstructablePipeline
from dagster.core.definitions.resource import ScopedResourcesBuilder
from dagster.core.execution.api import create_execution_plan, scoped_pipeline_context
from dagster.core.execution.resources_init import (
    get_required_resource_keys_to_init,
    resource_initialization_event_generator,
)
from dagster.core.instance import DagsterInstance
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus
from dagster.core.utils import make_new_run_id
from dagster.loggers import colored_console_logger
from dagster.serdes import unpack_value
from dagster.utils import EventGenerationManager

from .context import DagstermillExecutionContext, DagstermillRuntimeExecutionContext
from .errors import DagstermillError
from .serialize import PICKLE_PROTOCOL, read_value, write_value


class DagstermillResourceEventGenerationManager(EventGenerationManager):
    """Utility class to explicitly manage setup/teardown of resource events. Overrides the default
    `generate_teardown_events` method so that teardown is deferred until explicitly called by the
    dagstermill Manager
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
        self.pipeline = None
        self.solid_def = None
        self.in_pipeline = False
        self.marshal_dir = None
        self.context = None
        self.resource_manager = None

    def _setup_resources(
        self,
        execution_plan,
        environment_config,
        pipeline_run,
        log_manager,
        resource_keys_to_init,
        instance,
        resource_instances_to_override,
    ):
        """
        Drop-in replacement for
        `dagster.core.execution.resources_init.resource_initialization_manager`.  It uses a
        `DagstermillResourceEventGenerationManager` and explicitly calls `teardown` on it
        """
        generator = resource_initialization_event_generator(
            execution_plan,
            environment_config,
            pipeline_run,
            log_manager,
            resource_keys_to_init,
            instance,
            resource_instances_to_override,
        )
        self.resource_manager = DagstermillResourceEventGenerationManager(
            generator, ScopedResourcesBuilder
        )
        return self.resource_manager

    def reconstitute_pipeline_context(
        self,
        output_log_path=None,
        marshal_dir=None,
        run_config=None,
        executable_dict=None,
        pipeline_run_dict=None,
        solid_handle_kwargs=None,
        instance_ref_dict=None,
    ):
        """Reconstitutes a context for dagstermill-managed execution.

        You'll see this function called to reconstruct a pipeline context within the ``injected
        parameters`` cell of a dagstermill output notebook. Users should not call this function
        interactively except when debugging output notebooks.

        Use :func:`dagstermill.get_context` in the ``parameters`` cell of your notebook to define a
        context for interactive exploration and development. This call will be replaced by one to
        :func:`dagstermill.reconstitute_pipeline_context` when the notebook is executed by
        dagstermill.
        """
        check.opt_str_param(output_log_path, "output_log_path")
        check.opt_str_param(marshal_dir, "marshal_dir")
        run_config = check.opt_dict_param(run_config, "run_config", key_type=str)
        check.dict_param(pipeline_run_dict, "pipeline_run_dict")
        check.dict_param(executable_dict, "executable_dict")
        check.dict_param(solid_handle_kwargs, "solid_handle_kwargs")
        check.dict_param(instance_ref_dict, "instance_ref_dict")

        pipeline = ReconstructablePipeline.from_dict(executable_dict)
        pipeline_def = pipeline.get_definition()

        try:
            instance_ref = unpack_value(instance_ref_dict)
            instance = DagsterInstance.from_ref(instance_ref)
        except Exception as err:  # pylint: disable=broad-except
            raise DagstermillError(
                "Error when attempting to resolve DagsterInstance from serialized InstanceRef"
            ) from err

        pipeline_run = unpack_value(pipeline_run_dict)

        solid_handle = SolidHandle.from_dict(solid_handle_kwargs)
        solid_def = pipeline_def.get_solid(solid_handle).definition

        self.marshal_dir = marshal_dir
        self.in_pipeline = True
        self.solid_def = solid_def
        self.pipeline = pipeline

        execution_plan = create_execution_plan(
            self.pipeline,
            run_config,
            mode=pipeline_run.mode,
            step_keys_to_execute=pipeline_run.step_keys_to_execute,
        )

        with scoped_pipeline_context(
            execution_plan,
            run_config,
            pipeline_run,
            instance,
            scoped_resources_builder_cm=self._setup_resources,
            # Set this flag even though we're not in test for clearer error reporting
            raise_on_error=True,
        ) as pipeline_context:
            self.context = DagstermillRuntimeExecutionContext(
                pipeline_context=pipeline_context,
                solid_config=run_config.get("solids", {}).get(solid_def.name, {}).get("config"),
                resource_keys_to_init=get_required_resource_keys_to_init(
                    execution_plan,
                    pipeline_context.intermediate_storage_def,
                ),
                solid_name=solid_def.name,
            )

        return self.context

    def get_context(self, solid_config=None, mode_def=None, run_config=None):
        """Get a dagstermill execution context for interactive exploration and development.

        Args:
            solid_config (Optional[Any]): If specified, this value will be made available on the
                context as its ``solid_config`` property.
            mode_def (Optional[:class:`dagster.ModeDefinition`]): If specified, defines the mode to
                use to construct the context. Specify this if you would like a context constructed
                with specific ``resource_defs`` or ``logger_defs``. By default, an ephemeral mode
                with a console logger will be constructed.
            run_config(Optional[dict]): The environment config dict with which to construct
                the context.

        Returns:
            :py:class:`~dagstermill.DagstermillExecutionContext`
        """
        check.opt_inst_param(mode_def, "mode_def", ModeDefinition)
        run_config = check.opt_dict_param(run_config, "run_config", key_type=str)

        # If we are running non-interactively, and there is already a context reconstituted, return
        # that context rather than overwriting it.
        if self.context is not None and isinstance(
            self.context, DagstermillRuntimeExecutionContext
        ):
            return self.context

        if not mode_def:
            mode_def = ModeDefinition(logger_defs={"dagstermill": colored_console_logger})
            run_config["loggers"] = {"dagstermill": {}}

        solid_def = SolidDefinition(
            name="this_solid",
            input_defs=[],
            compute_fn=lambda *args, **kwargs: None,
            output_defs=[],
            description="Ephemeral solid constructed by dagstermill.get_context()",
            required_resource_keys=mode_def.resource_key_set,
        )

        pipeline_def = PipelineDefinition(
            [solid_def], mode_defs=[mode_def], name="ephemeral_dagstermill_pipeline"
        )

        run_id = make_new_run_id()

        # construct stubbed PipelineRun for notebook exploration...
        # The actual pipeline run during pipeline execution will be serialized and reconstituted
        # in the `reconstitute_pipeline_context` call
        pipeline_run = PipelineRun(
            pipeline_name=pipeline_def.name,
            run_id=run_id,
            run_config=run_config,
            mode=mode_def.name,
            step_keys_to_execute=None,
            status=PipelineRunStatus.NOT_STARTED,
            tags=None,
        )

        self.in_pipeline = False
        self.solid_def = solid_def
        self.pipeline = pipeline_def

        execution_plan = create_execution_plan(self.pipeline, run_config, mode=mode_def.name)
        with scoped_pipeline_context(
            execution_plan,
            run_config,
            pipeline_run,
            DagsterInstance.ephemeral(),
            scoped_resources_builder_cm=self._setup_resources,
        ) as pipeline_context:

            self.context = DagstermillExecutionContext(
                pipeline_context=pipeline_context,
                solid_config=solid_config,
                resource_keys_to_init=get_required_resource_keys_to_init(
                    execution_plan,
                    pipeline_context.intermediate_storage_def,
                ),
                solid_name=solid_def.name,
            )

        return self.context

    def yield_result(self, value, output_name="result"):
        """Yield a result directly from notebook code.

        When called interactively or in development, returns its input.

        Args:
            value (Any): The value to yield.
            output_name (Optional[str]): The name of the result to yield (default: ``'result'``).
        """
        if not self.in_pipeline:
            return value

        # deferred import for perf
        import scrapbook

        if not self.solid_def.has_output(output_name):
            raise DagstermillError(
                f"Solid {self.solid_def.name} does not have output named {output_name}."
                f"Expected one of {[str(output_def.name) for output_def in self.solid_def.output_defs]}"
            )

        dagster_type = self.solid_def.output_def_named(output_name).dagster_type

        out_file = os.path.join(self.marshal_dir, f"output-{output_name}")
        scrapbook.glue(output_name, write_value(dagster_type, value, out_file))

    def yield_event(self, dagster_event):
        """Yield a dagster event directly from notebook code.

        When called interactively or in development, returns its input.

        Args:
            dagster_event (Union[:class:`dagster.Materialization`, :class:`dagster.ExpectationResult`, :class:`dagster.TypeCheck`, :class:`dagster.Failure`]):
                An event to yield back to Dagster.
        """
        check.inst_param(
            dagster_event,
            "dagster_event",
            (AssetMaterialization, Materialization, ExpectationResult, TypeCheck, Failure),
        )

        if not self.in_pipeline:
            return dagster_event

        # deferred import for perf
        import scrapbook

        event_id = "event-{event_uuid}".format(event_uuid=str(uuid.uuid4()))
        out_file_path = os.path.join(self.marshal_dir, event_id)
        with open(out_file_path, "wb") as fd:
            fd.write(pickle.dumps(dagster_event, PICKLE_PROTOCOL))

        scrapbook.glue(event_id, out_file_path)

    def teardown_resources(self):
        if self.resource_manager is not None:
            self.resource_manager.teardown()

    def load_parameter(self, input_name, input_value):
        input_def = self.solid_def.input_def_named(input_name)
        return read_value(input_def.dagster_type, seven.json.loads(input_value))


MANAGER_FOR_NOTEBOOK_INSTANCE = Manager()
