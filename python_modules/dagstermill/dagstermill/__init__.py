from dagster import check, RepositoryDefinition, PipelineDefinition, SolidDefinition
from dagster.core.types.marshal import PickleSerializationStrategy

from .errors import DagstermillError, DagsterUserCodeExecutionError
from .manager import Manager, MANAGER_FOR_NOTEBOOK_INSTANCE
from .serialize import read_value
from .solids import define_dagstermill_solid

# magic incantation for syncing up notebooks to enclosing virtual environment.
# I don't claim to understand it.
# ipython kernel install --name "dagster" --user
# python3 -m ipykernel install --user


yield_result = MANAGER_FOR_NOTEBOOK_INSTANCE.yield_result

yield_event = MANAGER_FOR_NOTEBOOK_INSTANCE.yield_event


def load_parameter(input_name, input_value):
    solid_def = MANAGER_FOR_NOTEBOOK_INSTANCE.solid_def
    input_def = solid_def.input_def_named(input_name)
    return read_value(input_def.runtime_type, input_value)


get_context = MANAGER_FOR_NOTEBOOK_INSTANCE.get_context

reconstitute_pipeline_context = MANAGER_FOR_NOTEBOOK_INSTANCE.reconstitute_pipeline_context

teardown = MANAGER_FOR_NOTEBOOK_INSTANCE.teardown_resources
