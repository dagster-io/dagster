from collections import namedtuple

from dagster import check


class StepInputSource:
    """How to load the data for a step input"""

    @property
    def step_key_dependencies(self):
        return set()

    @property
    def step_output_handle_dependencies(self):
        return []


class FromStepOutput(namedtuple("_FromStepOutput", "step_output_handle"), StepInputSource):
    """This step input source is the output of a previous step"""

    def __new__(
        cls, step_output_handle,
    ):
        from .objects import StepOutputHandle

        return super(FromStepOutput, cls).__new__(
            cls,
            step_output_handle=check.inst_param(
                step_output_handle, "step_output_handle", StepOutputHandle
            ),
        )

    @property
    def step_key_dependencies(self):
        return {self.step_output_handle.step_key}

    @property
    def step_output_handle_dependencies(self):
        return [self.step_output_handle]


class FromConfig(namedtuple("_FromConfig", "config_data"), StepInputSource):
    """This step input source is configuration to be passed to a type loader"""

    def __new__(
        cls, config_data,
    ):
        return super(FromConfig, cls).__new__(cls, config_data=config_data,)


class FromDefaultValue(namedtuple("_FromDefaultValue", "value"), StepInputSource):
    """This step input source is the default value declared on the InputDefinition"""

    def __new__(
        cls, value,
    ):
        return super(FromDefaultValue, cls).__new__(cls, value)


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


class StepInput(namedtuple("_StepInput", "name dagster_type source")):
    def __new__(
        cls, name, dagster_type, source,
    ):
        from dagster import DagsterType

        return super(StepInput, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            dagster_type=check.inst_param(dagster_type, "dagster_type", DagsterType),
            source=check.inst_param(source, "source", StepInputSource),
        )

    @property
    def dependency_keys(self):
        return self.source.step_key_dependencies
