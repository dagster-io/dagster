from dagster_pipes import open_dagster_pipes


def main(pipes) -> None:
    pipes.log.info("Hello from asset two.")
    pipes.report_asset_materialization(metadata={"metadata": "value_one"})


if __name__ == "__main__":
    with open_dagster_pipes() as pipes:
        main(pipes)
