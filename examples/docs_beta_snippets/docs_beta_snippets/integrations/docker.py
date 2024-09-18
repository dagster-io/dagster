from dagster_docker import PipesDockerClient

import dagster as dg


@dg.asset
def docker_pipes_asset(
    context: dg.AssetExecutionContext, docker_pipes_client: PipesDockerClient
):
    docker_image = "python:3.9-slim"
    return docker_pipes_client.run(
        image=docker_image,
        command=[
            "python",
            "-m",
            "my_module",
        ],
        context=context,
    ).get_results()


defs = dg.Definitions(
    assets=[docker_pipes_asset],
    resources={
        "docker_pipes_client": PipesDockerClient(),
    },
)
