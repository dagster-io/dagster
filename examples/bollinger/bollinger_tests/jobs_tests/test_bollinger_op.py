from bollinger.jobs.bollinger_op import load_sp500_prices, compute_anomalous_events, compute_bollinger_bands
from bollinger.resources.csv_io_manager import local_csv_io_manager
from dagster import job



def test_bollinger_op():
    @job
    def bollinger_op():
        prices = load_sp500_prices()
        compute_anomalous_events(prices, compute_bollinger_bands(prices))
    bollinger_op.execute_in_process()
