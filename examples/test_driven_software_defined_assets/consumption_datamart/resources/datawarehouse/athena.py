import sqlalchemy
from pandas import DataFrame

from consumption_datamart.resources.datawarehouse.base import _BaseDatawarehouseResource


class AthenaDatawarehouseResource(_BaseDatawarehouseResource):

    def __init__(self, log_manager, echo_sql, pid_group="default::Athena"):
        raise NotImplementedError()

    @property
    def datawarehouse_uri(self):
        pass

    def create_engine(self, echo_sql) -> sqlalchemy.engine.Engine:
        pass

    def delete_partition(self, connection, schema, table, meta_partition, meta_partition_type):
        pass

    def row_hash(self, columns):
        pass

    def add_to_lake(self, df: DataFrame, destination_table: str):
        pass

    def update_view(self, schema: str, view_name: str, view_query: str, comment: str = ""):
        pass

    def load_table_data(self, df_data_to_load: DataFrame, connection, schema: str, table: str):
        pass

    def update_scd2_insert_statement_hook(self, schema, table, data_columns):
        pass

    def refresh(self, schema, table):
        pass

    def optimise_table(self, schema: str, table: str):
        pass
