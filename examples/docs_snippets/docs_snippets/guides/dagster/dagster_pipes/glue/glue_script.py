import boto3
from dagster_pipes import (
    PipesCliArgsParamsLoader,
    PipesS3ContextLoader,
    open_dagster_pipes,
)


def main():
    with open_dagster_pipes(
        params_loader=PipesCliArgsParamsLoader(),
        context_loader=PipesS3ContextLoader(client=boto3.client("s3")),
    ) as pipes:
        pipes.log.info("Hello from external process!")


if __name__ == "__main__":
    main()
