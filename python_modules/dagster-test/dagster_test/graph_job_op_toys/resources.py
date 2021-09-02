from dagster import (
    Field,
    Int,
    reconstructable,
    resource,
    graph,
    op,
)


def define_resource(num):
    @resource(config_schema=Field(Int, is_required=False))
    def a_resource(context):
        return num if context.resource_config is None else context.resource_config

    return a_resource


lots_of_resources = {"R" + str(r): define_resource(r) for r in range(20)}


@op(required_resource_keys=set(lots_of_resources.keys()))
def all_resources():
    return 1


@op(required_resource_keys={"R1"})
def one(context):
    return 1 + context.resources.R1


@op(required_resource_keys={"R2"})
def two():
    return 1


@op(required_resource_keys={"R1", "R2", "R3"})
def one_and_two_and_three():
    return 1


@graph
def resource_graph():
    all_resources()
    one()
    two()
    one_and_two_and_three()


resource_job = resource_graph.to_job(resource_defs=lots_of_resources)

if __name__ == "__main__":
    result = reconstructable(resource_job).execute_in_process()
