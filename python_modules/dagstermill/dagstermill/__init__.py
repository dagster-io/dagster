from dagster import check
from dagster.core.types.marshal import PickleSerializationStrategy

from .errors import DagstermillError, DagsterUserCodeExecutionError
from .manager import Manager, MANAGER_FOR_NOTEBOOK_INSTANCE
from .serialize import SerializableRuntimeType, read_value
from .solids import define_dagstermill_solid

# magic incantation for syncing up notebooks to enclosing virtual environment.
# I don't claim to understand it.
# ipython kernel install --name "dagster" --user
# python3 -m ipykernel install --user


def register_repository(repo_def):
    return MANAGER_FOR_NOTEBOOK_INSTANCE.register_repository(repo_def)


def deregister_repository():
    return MANAGER_FOR_NOTEBOOK_INSTANCE.deregister_repository()


def yield_result(value, output_name='result'):
    '''Explicitly yield a Result.

    Args:
        value (Any): The value of the Result to yield.
        output_name (Optional[str]): The name of the Result to yield. Default: 'result'.

    '''
    return MANAGER_FOR_NOTEBOOK_INSTANCE.yield_result(value, output_name)


def yield_materialization(path, description=''):
    '''Explicitly yield an additional Materialization.

    Args:
        path (str): The path to the materialized artifact.
        description (Optional[str]): A description of the materialized artifact.

    '''

    return MANAGER_FOR_NOTEBOOK_INSTANCE.yield_materialization(path, description)


def populate_context(dm_context_data):
    check.dict_param(dm_context_data, 'dm_context_data')
    context = MANAGER_FOR_NOTEBOOK_INSTANCE.populate_context(**dm_context_data)
    return context


def load_parameter(input_name, input_value):
    check.invariant(MANAGER_FOR_NOTEBOOK_INSTANCE.populated_by_papermill, 'populated_by_papermill')
    if MANAGER_FOR_NOTEBOOK_INSTANCE.solid_def is None:
        check.invariant(
            MANAGER_FOR_NOTEBOOK_INSTANCE.input_name_type_dict is not None,
            'input_name_type_dict must not be None if solid_def is not defined!',
        )
        input_name_type_dict = MANAGER_FOR_NOTEBOOK_INSTANCE.input_name_type_dict
        runtime_type_enum = input_name_type_dict[input_name]
        if (
            runtime_type_enum == SerializableRuntimeType.SCALAR
            or runtime_type_enum == SerializableRuntimeType.JSON_SERIALIZABLE
        ):
            return input_value
        elif runtime_type_enum == SerializableRuntimeType.PICKLE_SERIALIZABLE:
            return PickleSerializationStrategy().deserialize_from_file(input_value)
        else:
            raise DagstermillError(
                "loading parameter {input_name} resulted in an error".format(input_name=input_name)
            )
    else:
        solid_def = MANAGER_FOR_NOTEBOOK_INSTANCE.solid_def
        input_def = solid_def.input_def_named(input_name)
        return read_value(input_def.runtime_type, input_value)


def get_context(config=None):
    if not MANAGER_FOR_NOTEBOOK_INSTANCE.populated_by_papermill:
        MANAGER_FOR_NOTEBOOK_INSTANCE.define_out_of_pipeline_context(config)
    return MANAGER_FOR_NOTEBOOK_INSTANCE.context


def teardown():
    MANAGER_FOR_NOTEBOOK_INSTANCE.teardown_resources()
