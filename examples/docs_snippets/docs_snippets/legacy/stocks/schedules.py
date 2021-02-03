import datetime

from dagster.core.definitions.decorators import monthly_schedule


@monthly_schedule(
    pipeline_name="compute_total_stock_volume",
    start_date=datetime.datetime(2018, 1, 1),
)
def daily_stock_schedule(date):

    previous_month_last_day = date - datetime.timedelta(days=1)
    previous_month_first_day = previous_month_last_day.replace(day=1)

    return {
        "solids": {
            "get_stock_data": {
                "config": {
                    "ds_start": previous_month_first_day.strftime("%Y-%m-%d"),
                    "ds_end": previous_month_last_day.strftime("%Y-%m-%d"),
                    "symbol": "AAPL",
                }
            }
        }
    }


def define_schedules():
    return [daily_stock_schedule]
