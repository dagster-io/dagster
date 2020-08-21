from dagster import (
    Field,
    Int,
    ModeDefinition,
    execute_pipeline,
    pipeline,
    reconstructable,
    resource,
    solid,
)


def define_resource(num):
    @resource(config_schema=Field(Int, is_required=False))
    def a_resource(context):
        return num if context.resource_config is None else context.resource_config

    return a_resource


lots_of_resources = {"R" + str(r): define_resource(r) for r in range(20)}


@solid(required_resource_keys=set(lots_of_resources.keys()))
def all_resources(_):
    return 1


@solid(required_resource_keys={"R1"})
def one(context):
    return 1 + context.resources.R1


@solid(required_resource_keys={"R2"})
def two(_):
    return 1


@solid(required_resource_keys={"R1", "R2", "R3"})
def one_and_two_and_three(_):
    return 1


@pipeline(mode_defs=[ModeDefinition(resource_defs=lots_of_resources)])
def resource_pipeline():
    all_resources()
    one()
    two()
    one_and_two_and_three()


if __name__ == "__main__":
    result = execute_pipeline(
        reconstructable(resource_pipeline),
        run_config={"storage": {"filesystem": {}}, "execution": {"multiprocessing": {}}},
    )
