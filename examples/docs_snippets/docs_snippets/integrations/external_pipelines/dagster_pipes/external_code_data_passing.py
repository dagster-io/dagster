from dagster_pipes import PipesContext, open_dagster_pipes


def main():
    with open_dagster_pipes():
        # get the context
        context = PipesContext.get()

        # do some work
        ...

        # send some logs to Dagster
        context.log.info("doing some stuff")

        # report asset materialization metadata to Dagster
        context.report_asset_materialization(metadata={"total_orders": 2})


if __name__ == "__main__":
    main()
