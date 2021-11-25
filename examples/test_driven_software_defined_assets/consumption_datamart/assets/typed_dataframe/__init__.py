import dagster_pandas
from consumption_datamart.assets.typed_dataframe.pandas_constraints import decimal_column

# Monkey patch PandasColumn to support decimal_column
dagster_pandas.PandasColumn.decimal_column = decimal_column
