from dagster import IOManager, io_manager
from dagster_pandas import DataFrame


class LakeIOManager(IOManager):

    def __init__(self, datawarehouse_resource) -> None:
        super().__init__()
        self.datawarehouse_resource = datawarehouse_resource

    def handle_output(self, context, obj: DataFrame):
        pass

    def load_input(self, context):
        # TODO: Figure out a more elegant wat to pass the datawarehouse_resource to the type loader
        context.resources.datawarehouse = self.datawarehouse_resource
        typed_df = context.dagster_type.loader.construct_from_config_value(context, {})

        return typed_df


@io_manager(
    required_resource_keys={'datawarehouse'},
)
def lake_input_manager(init_context):
    return LakeIOManager(datawarehouse_resource=init_context.resources.datawarehouse)
