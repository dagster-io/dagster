import hashlib
from abc import ABC, abstractmethod
from collections import namedtuple

from dagster import check
from dagster.core.definitions import Failure, RetryRequested
from dagster.core.definitions.input import InputDefinition
from dagster.core.errors import (
    DagsterExecutionLoadInputError,
    DagsterTypeLoadingError,
    user_code_error_boundary,
)
from dagster.core.storage.io_manager import IOManager
from dagster.serdes import whitelist_for_serdes
from dagster.utils import ensure_gen

from .objects import TypeCheckData
from .outputs import StepOutputHandle, UnresolvedStepOutputHandle
from .utils import build_resources_for_manager


@whitelist_for_serdes
class StepInputData(namedtuple("_StepInputData", "input_name type_check_data")):
    """"Serializable payload of information for the result of processing a step input"""

    def __new__(cls, input_name, type_check_data):
        return super(StepInputData, cls).__new__(
            cls,
            input_name=check.str_param(input_name, "input_name"),
            type_check_data=check.opt_inst_param(type_check_data, "type_check_data", TypeCheckData),
        )


class StepInput(namedtuple("_StepInput", "name dagster_type source")):
    """Holds information for how to prepare an input for an ExecutionStep"""

    def __new__(
        cls, name, dagster_type, source,
    ):
        from dagster.core.types.dagster_type import DagsterType

        return super(StepInput, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            dagster_type=check.inst_param(dagster_type, "dagster_type", DagsterType),
            source=check.inst_param(source, "source", StepInputSource),
        )

    @property
    def dependency_keys(self):
        return self.source.step_key_dependencies

    def get_step_output_handle_dependencies(self):
        return self.source.step_output_handle_dependencies


def join_and_hash(*args):
    lst = [check.opt_str_param(elem, "elem") for elem in args]
    if None in lst:
        return None
    else:
        unhashed = "".join(sorted(lst))
        return hashlib.sha1(unhashed.encode("utf-8")).hexdigest()


class StepInputSource(ABC):
    """How to load the data for a step input"""

    @property
    def step_key_dependencies(self):
        return set()

    @property
    def step_output_handle_dependencies(self):
        return []

    @abstractmethod
    def load_input_object(self, step_context):
        raise NotImplementedError()

    def required_resource_keys(self):
        return set()

    @abstractmethod
    def compute_version(self, step_versions):
        """See resolve_step_versions in resolve_versions.py for explanation of step_versions"""
        raise NotImplementedError()


class FromRootInputManager(
    namedtuple("_FromRootInputManager", "input_def config_data"), StepInputSource,
):
    def load_input_object(self, step_context):
        from dagster.core.events import DagsterEvent

        loader = getattr(step_context.resources, self.input_def.root_manager_key)
        load_input_context = step_context.for_input_manager(
            self.input_def.name,
            self.config_data,
            metadata=self.input_def.metadata,
            dagster_type=self.input_def.dagster_type,
            resource_config=step_context.environment_config.resources[
                self.input_def.root_manager_key
            ].get("config", {}),
            resources=build_resources_for_manager(self.input_def.root_manager_key, step_context),
        )
        yield _load_input_with_input_manager(loader, load_input_context)
        yield DagsterEvent.loaded_input(
            step_context,
            input_name=self.input_def.name,
            manager_key=self.input_def.root_manager_key,
        )

    def compute_version(self, step_versions):
        # TODO: support versioning for root loaders
        return None

    def required_resource_keys(self):
        return {self.input_def.root_manager_key}


class FromStepOutput(
    namedtuple("_FromStepOutput", "step_output_handle input_def config_data fan_in"),
    StepInputSource,
):
    """This step input source is the output of a previous step"""

    def __new__(cls, step_output_handle, input_def, config_data, fan_in):
        return super(FromStepOutput, cls).__new__(
            cls,
            step_output_handle=check.inst_param(
                step_output_handle, "step_output_handle", StepOutputHandle
            ),
            input_def=check.inst_param(input_def, "input_def", InputDefinition),
            config_data=config_data,
            fan_in=check.bool_param(fan_in, "fan_in"),
        )

    def _input_dagster_type(self):
        if self.fan_in:
            return self.input_def.dagster_type.get_inner_type_for_fan_in()
        else:
            return self.input_def.dagster_type

    @property
    def step_key_dependencies(self):
        return {self.step_output_handle.step_key}

    @property
    def step_output_handle_dependencies(self):
        return [self.step_output_handle]

    def get_load_context(self, step_context):
        io_manager_key = step_context.execution_plan.get_manager_key(self.step_output_handle)
        resource_config = step_context.environment_config.resources[io_manager_key].get(
            "config", {}
        )
        resources = build_resources_for_manager(io_manager_key, step_context)

        return step_context.for_input_manager(
            self.input_def.name,
            self.config_data,
            self.input_def.metadata,
            self.input_def.dagster_type,
            self.step_output_handle,
            resource_config,
            resources,
        )

    def load_input_object(self, step_context):
        from dagster.core.events import DagsterEvent

        source_handle = self.step_output_handle
        manager_key = step_context.execution_plan.get_manager_key(source_handle)
        input_manager = step_context.get_output_manager(source_handle)
        check.invariant(
            isinstance(input_manager, IOManager),
            f'Input "{self.input_def.name}" for step "{step_context.step.key}" is depending on '
            f'the manager of upstream output "{source_handle.output_name}" from step '
            f'"{source_handle.step_key}" to load it, but that manager is not an IOManager. '
            f"Please ensure that the resource returned for resource key "
            f'"{manager_key}" is an IOManager.',
        )
        yield _load_input_with_input_manager(input_manager, self.get_load_context(step_context))
        yield DagsterEvent.loaded_input(
            step_context,
            input_name=self.input_def.name,
            manager_key=manager_key,
            upstream_output_name=source_handle.output_name,
            upstream_step_key=source_handle.step_key,
        )

    def compute_version(self, step_versions):
        if (
            self.step_output_handle.step_key not in step_versions
            or not step_versions[self.step_output_handle.step_key]
        ):
            return None
        else:
            return join_and_hash(
                step_versions[self.step_output_handle.step_key], self.step_output_handle.output_name
            )

    def required_resource_keys(self):
        return set()


def _generate_error_boundary_msg_for_step_input(context, input_name):
    return lambda: """Error occurred during input loading:
    input name: "{input_name}"
    step key: "{key}"
    solid invocation: "{solid}"
    solid definition: "{solid_def}"
    """.format(
        input_name=input_name,
        key=context.step.key,
        solid_def=context.solid_def.name,
        solid=context.solid.name,
    )


class FromConfig(namedtuple("_FromConfig", "config_data dagster_type input_name"), StepInputSource):
    """This step input source is configuration to be passed to a type loader"""

    def __new__(cls, config_data, dagster_type, input_name):
        return super(FromConfig, cls).__new__(
            cls, config_data=config_data, dagster_type=dagster_type, input_name=input_name
        )

    def load_input_object(self, step_context):
        with user_code_error_boundary(
            DagsterTypeLoadingError,
            msg_fn=_generate_error_boundary_msg_for_step_input(step_context, self.input_name),
        ):
            return self.dagster_type.loader.construct_from_config_value(
                step_context, self.config_data
            )

    def required_resource_keys(self):
        return (
            self.dagster_type.loader.required_resource_keys() if self.dagster_type.loader else set()
        )

    def compute_version(self, step_versions):
        return self.dagster_type.loader.compute_loaded_input_version(self.config_data)


class FromDefaultValue(namedtuple("_FromDefaultValue", "value"), StepInputSource):
    """This step input source is the default value declared on the InputDefinition"""

    def __new__(
        cls, value,
    ):
        return super(FromDefaultValue, cls).__new__(cls, value)

    def load_input_object(self, step_context):
        return self.value

    def compute_version(self, step_versions):
        return join_and_hash(repr(self.value))


class FromMultipleSources(namedtuple("_FromMultipleSources", "sources"), StepInputSource):
    """This step input is fans-in multiple sources in to a single input. The input will receive a list."""

    def __new__(cls, sources):
        check.list_param(sources, "sources", StepInputSource)
        for source in sources:
            check.invariant(
                not isinstance(source, FromMultipleSources),
                "Can not have multiple levels of FromMultipleSources StepInputSource",
            )
        return super(FromMultipleSources, cls).__new__(cls, sources=sources)

    @property
    def step_key_dependencies(self):
        keys = set()
        for source in self.sources:
            keys.update(source.step_key_dependencies)

        return keys

    @property
    def step_output_handle_dependencies(self):
        handles = []
        for source in self.sources:
            handles.extend(source.step_output_handle_dependencies)

        return handles

    def _step_output_handles_no_output(self, step_context):
        # FIXME https://github.com/dagster-io/dagster/issues/3511
        # this is a stopgap which asks the instance to check the event logs to find out step skipping
        step_output_handles_with_output = set()
        for event_record in step_context.instance.all_logs(step_context.run_id):
            if event_record.dagster_event and event_record.dagster_event.is_successful_output:
                step_output_handles_with_output.add(
                    event_record.dagster_event.event_specific_data.step_output_handle
                )
        return set(self.step_output_handle_dependencies).difference(step_output_handles_with_output)

    def load_input_object(self, step_context):
        from dagster.core.events import DagsterEvent

        values = []

        # some upstream steps may have skipped and we allow fan-in to continue in their absence
        source_handles_to_skip = self._step_output_handles_no_output(step_context)

        for inner_source in self.sources:
            if (
                inner_source.step_output_handle_dependencies
                and inner_source.step_output_handle in source_handles_to_skip
            ):
                continue

            for event_or_input_value in ensure_gen(inner_source.load_input_object(step_context)):
                if isinstance(event_or_input_value, DagsterEvent):
                    yield event_or_input_value
                else:
                    values.append(event_or_input_value)

        yield values

    def required_resource_keys(self):
        resource_keys = set()
        for source in self.sources:
            resource_keys = resource_keys.union(source.required_resource_keys())
        return resource_keys

    def compute_version(self, step_versions):
        return join_and_hash(
            *[inner_source.compute_version(step_versions) for inner_source in self.sources]
        )


def _load_input_with_input_manager(root_input_manager, context):
    with user_code_error_boundary(
        DagsterExecutionLoadInputError,
        control_flow_exceptions=[Failure, RetryRequested],
        msg_fn=lambda: (
            f"Error occurred during the loading of a step input:"
            f'    step key: "{context.step_context.step.key}"'
            f'    input name: "{context.name}"'
        ),
        step_key=context.step_context.step.key,
        input_name=context.name,
    ):
        value = root_input_manager.load_input(context)
    # close user code boundary before returning value
    return value


class UnresolvedStepInput(namedtuple("_UnresolvedStepInput", "name dagster_type source")):
    """Holds information for how to resolve a StepInput once the upstream mapping is done"""

    def __new__(
        cls, name, dagster_type, source,
    ):
        from dagster.core.types.dagster_type import DagsterType

        return super(UnresolvedStepInput, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            dagster_type=check.inst_param(dagster_type, "dagster_type", DagsterType),
            source=check.inst_param(
                source, "source", (FromPendingDynamicStepOutput, FromUnresolvedStepOutput)
            ),
        )

    @property
    def resolved_by_step_key(self):
        return self.source.resolved_by_step_key

    @property
    def resolved_by_output_name(self):
        return self.source.resolved_by_output_name

    def resolve(self, map_key):
        return StepInput(
            name=self.name, dagster_type=self.dagster_type, source=self.source.resolve(map_key),
        )

    def get_step_output_handle_deps_with_placeholders(self):
        """Return StepOutputHandles with placeholders, unresolved step keys and None mapping keys"""

        return [self.source.get_step_output_handle_dep_with_placeholder()]


class FromPendingDynamicStepOutput(
    namedtuple("_FromPendingDynamicStepOutput", "step_output_handle input_def config_data"),
):
    """
    This step input source models being directly downstream of a step with dynamic output.
    Once that step completes successfully, this will resolve once per DynamicOutput.
    """

    def __new__(cls, step_output_handle, input_def, config_data):
        # Model the unknown mapping key from known execution step
        # using a StepOutputHandle with None mapping_key.
        check.inst_param(step_output_handle, "step_output_handle", StepOutputHandle)
        check.invariant(step_output_handle.mapping_key is None)

        return super(FromPendingDynamicStepOutput, cls).__new__(
            cls,
            step_output_handle=step_output_handle,
            input_def=check.inst_param(input_def, "input_def", InputDefinition),
            config_data=config_data,
        )

    @property
    def resolved_by_step_key(self):
        return self.step_output_handle.step_key

    @property
    def resolved_by_output_name(self):
        return self.step_output_handle.output_name

    def resolve(self, mapping_key):
        check.str_param(mapping_key, "mapping_key")
        return FromStepOutput(
            step_output_handle=StepOutputHandle(
                step_key=self.step_output_handle.step_key,
                output_name=self.step_output_handle.output_name,
                mapping_key=mapping_key,
            ),
            input_def=self.input_def,
            config_data=self.config_data,
            fan_in=False,
        )

    def get_step_output_handle_dep_with_placeholder(self):
        # None mapping_key on StepOutputHandle acts as placeholder
        return self.step_output_handle

    def required_resource_keys(self):
        return set()


class FromUnresolvedStepOutput(
    namedtuple("_FromUnresolvedStepOutput", "unresolved_step_output_handle input_def config_data"),
):
    """
    This step input source models being downstream of another unresolved step,
    for example indirectly downstream from a step with dynamic output.
    """

    def __new__(cls, unresolved_step_output_handle, input_def, config_data):
        return super(FromUnresolvedStepOutput, cls).__new__(
            cls,
            unresolved_step_output_handle=check.inst_param(
                unresolved_step_output_handle,
                "unresolved_step_output_handle",
                UnresolvedStepOutputHandle,
            ),
            input_def=check.inst_param(input_def, "input_def", InputDefinition),
            config_data=config_data,
        )

    @property
    def resolved_by_step_key(self):
        return self.unresolved_step_output_handle.resolved_by_step_key

    @property
    def resolved_by_output_name(self):
        return self.unresolved_step_output_handle.resolved_by_output_name

    def resolve(self, mapping_key):
        check.str_param(mapping_key, "mapping_key")
        return FromStepOutput(
            step_output_handle=self.unresolved_step_output_handle.resolve(mapping_key),
            input_def=self.input_def,
            config_data=self.config_data,
            fan_in=False,
        )

    def get_step_output_handle_dep_with_placeholder(self):
        return self.unresolved_step_output_handle.get_step_output_handle_with_placeholder()

    def required_resource_keys(self):
        return set()
