from dagster import ModeDefinition, ObjectManager, execute_pipeline, object_manager, pipeline, solid


def connect():
    pass


def write_dataframe_to_table(**_kwargs):
    pass


def read_dataframe_from_table(**_kwargs):
    pass


@solid
def solid1(_):
    """Return a Pandas DataFrame"""


@solid
def solid2(_, _input_dataframe):
    """Return a Pandas DataFrame"""


# object_manager_start_marker
class MyObjectManager(ObjectManager):
    def handle_output(self, context, obj):
        table_name = context.config["table"]
        write_dataframe_to_table(name=table_name, dataframe=obj)

    def load_input(self, context):
        table_name = context.upstream_output.config["table"]
        return read_dataframe_from_table(name=table_name)


@object_manager(output_config_schema={"table": str})
def my_object_manager(_):
    return MyObjectManager()


# object_manager_end_marker


def execute_with_config():
    # execute_start_marker
    @pipeline(mode_defs=[ModeDefinition(resource_defs={"object_manager": my_object_manager})])
    def my_pipeline():
        solid2(solid1())

    execute_pipeline(
        my_pipeline,
        run_config={
            "solids": {
                "solid1": {"outputs": {"result": {"table": "table1"}}},
                "solid2": {"outputs": {"result": {"table": "table2"}}},
            }
        },
    )

    # execute_end_marker
