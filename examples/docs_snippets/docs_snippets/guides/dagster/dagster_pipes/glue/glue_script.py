import boto3
from dagster_pipes import (
    PipesCliArgsParamsLoader,
    PipesS3ContextLoader,
    PipesS3MessageWriter,
    open_dagster_pipes,
)

client = boto3.client("s3")
context_loader = PipesS3ContextLoader(client)
message_writer = PipesS3MessageWriter(client)
params_loader = PipesCliArgsParamsLoader()


def main():
    with open_dagster_pipes(
        context_loader=context_loader,
        message_writer=message_writer,
        params_loader=params_loader,
    ) as pipes:
        pipes.log.info("Hello from AWS Glue job!")


if __name__ == "__main__":
    main()
