from dagster_cube import CubeResource

import dagster as dg


@dg.asset
def cube_query_workflow(cube: CubeResource):
    response = cube.make_request(
        method="POST",
        endpoint="load",
        data={"query": {"measures": ["Orders.count"], "dimensions": ["Orders.status"]}},
    )

    return response


defs = dg.Definitions(
    assets=[cube_query_workflow],
    resources={
        "cube": CubeResource(
            instance_url="https://<<INSTANCE>>.cubecloudapp.dev/cubejs-api/v1/",
            api_key=dg.EnvVar("CUBE_API_KEY"),
        )
    },
)
