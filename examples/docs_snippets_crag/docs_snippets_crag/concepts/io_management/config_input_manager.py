# pylint: disable=unused-argument
from dagster import (
    InputDefinition,
    ModeDefinition,
    execute_pipeline,
    pipeline,
    root_input_manager,
    solid,
)


def read_dataframe_from_table(**_kwargs):
    pass


@solid(input_defs=[InputDefinition("dataframe", root_manager_key="my_root_manager")])
def my_solid(dataframe):
    """Do some stuff"""


# def_start_marker
@root_input_manager(input_config_schema={"table_name": str})
def table_loader(context):
    return read_dataframe_from_table(name=context.config["table_name"])


# def_end_marker


def execute_with_config():
    # execute_start_marker
    @pipeline(mode_defs=[ModeDefinition(resource_defs={"my_root_manager": table_loader})])
    def my_pipeline():
        my_solid()

    execute_pipeline(
        my_pipeline,
        run_config={"solids": {"my_solid": {"inputs": {"dataframe": {"table_name": "table1"}}}}},
    )

    # execute_end_marker
