import dagster as dg


@dg.asset
def customer_data(): ...


@dg.asset
def sales_report(): ...


@dg.job
def daily_refresh():
    customer_data()
    sales_report()


# highlight-start
@dg.schedule(cron_schedule="0 0 * * *")
def daily_refresh_job(): ...


# highlight-end
