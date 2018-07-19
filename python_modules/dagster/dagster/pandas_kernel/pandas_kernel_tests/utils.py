import dagster.pandas_kernel as dagster_pd


def simple_csv_input(name):
    return dagster_pd.dataframe_input(name, sources=[dagster_pd.csv_dataframe_source()])
