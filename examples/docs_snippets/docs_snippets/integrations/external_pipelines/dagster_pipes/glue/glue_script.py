import boto3
from dagster_pipes import (
    PipesCliArgsParamsLoader,
    PipesS3ContextLoader,
    open_dagster_pipes,
)

client = boto3.client("s3")
context_loader = PipesS3ContextLoader(client)
params_loader = PipesCliArgsParamsLoader()


def main():
    with open_dagster_pipes(
        context_loader=context_loader,
        params_loader=params_loader,
    ) as pipes:
        pipes.log.info("Hello from AWS Glue job!")
        pipes.report_asset_materialization(
            metadata={"some_metric": {"raw_value": 0, "type": "int"}},
            data_version="alpha",
        )


if __name__ == "__main__":
    main()
