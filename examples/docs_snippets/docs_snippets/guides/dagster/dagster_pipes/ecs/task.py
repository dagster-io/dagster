from dagster_pipes import (
    PipesEnvVarParamsLoader,
    PipesS3ContextLoader,
    open_dagster_pipes,
)


def main():
    with open_dagster_pipes() as pipes:
        pipes.log.info("Hello from AWS ECS task!")
        pipes.report_asset_materialization(
            metadata={"some_metric": {"raw_value": 0, "type": "int"}},
            data_version="alpha",
        )


if __name__ == "__main__":
    main()
