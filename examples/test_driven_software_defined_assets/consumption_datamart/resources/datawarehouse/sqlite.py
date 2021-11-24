import re
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List

import sqlalchemy
from pandas import DataFrame
from sqlalchemy import text
from sqlalchemy.pool import SingletonThreadPool

from consumption_datamart.resources.datawarehouse.base import _BaseDatawarehouseResource, unix_timestamp, utc_timestamp, date_trunc, regexp_extract


def concat(str1, str2):
    """Emulate SQL CONCAT function.
    Ignores NULL/None strings per https://stackoverflow.com/a/15361064/13238"""
    return ''.join([str(x) for x in (str1, str2) if x])


def concat3(str1, str2, str3):
    """Emulate SQL CONCAT function.
    Ignores NULL/None strings per https://stackoverflow.com/a/15361064/13238"""
    return ''.join([str(x) for x in (str1, str2, str3) if x])


def concat4(str1, str2, str3, str4):
    """Emulate SQL CONCAT function.
    Ignores NULL/None strings per https://stackoverflow.com/a/15361064/13238"""
    return ''.join([str(x) for x in (str1, str2, str3, str4) if x])


@sqlalchemy.event.listens_for(sqlalchemy.engine.Engine, 'connect')
def sqlite_engine_connect(connection, _):
    if type(connection) is sqlite3.Connection:
        connection.create_function("UNIX_TIMESTAMP", 1, unix_timestamp)
        connection.create_function("UTC_TIMESTAMP", 0, utc_timestamp)
        connection.create_function("DATE_TRUNC", 2, date_trunc)
        connection.create_function("CONCAT", 2, concat)
        connection.create_function("CONCAT", 3, concat3)
        connection.create_function("CONCAT", 4, concat4)
        connection.create_function("REGEXP_EXTRACT", 3, regexp_extract)


@dataclass
class SQLiteSchema:
    name: str
    uri: str
    init_sql_file: str = None


class SQLiteDatawarehouseResource(_BaseDatawarehouseResource):

    def __init__(self, log_manager, echo_sql, schemas: List[SQLiteSchema], pid_group="default"):
        super().__init__(log_manager, echo_sql, pid_group=pid_group)
        self.schemas = schemas

    def create_engine(self, echo_sql) -> sqlalchemy.engine.Engine:
        engine = sqlalchemy.create_engine('sqlite:///:memory:?uri=true', echo=echo_sql, poolclass=SingletonThreadPool)
        # ?uri=true ensures that following the ATTACH DATABASE statements can use sqlite URI params like ?mode=memory
        # See https://docs.sqlalchemy.org/en/14/dialects/sqlite.html#uri-connections
        with engine.connect() as connection:
            for schema in self.schemas:
                self.log.debug(f"ATTACHing sqlite+{schema.uri} AS {schema.name}")
                connection.execute(f"ATTACH DATABASE '{schema.uri}' AS {schema.name};")
                if schema.init_sql_file is not None:
                    self.log.debug(f"Executing init_sql_file:{schema.init_sql_file}")
                    with open(schema.init_sql_file) as file:
                        statements = re.split(r';\s*$', file.read(), flags=re.MULTILINE)
                        for statement in statements:
                            if statement:
                                if not re.match(r'\n(BEGIN TRANSACTION|COMMIT)', statement):  # Avoid nested transactions
                                    sql_with_schema_names = self.add_table_schema(statement, schema.name)
                                    connection.execute(text(sql_with_schema_names))
        return engine

    @staticmethod
    def add_table_schema(sql, schema_name):
        def inject_schema(match):
            return f'{match.group()} {schema_name}.'

        return re.sub(r'(CREATE TABLE IF NOT EXISTS|CREATE TABLE|INSERT INTO)\s+', inject_schema, sql)

    @property
    def datawarehouse_uri(self):
        return f"sqlite+{self.schemas[0].uri}"

    # noinspection SqlResolve
    def delete_partition(self, connection, schema, table, meta_partition, meta_partition_type):
        connection.execute(
            f"DELETE FROM {schema}.{table} WHERE meta__partition=:meta_partition AND meta__partition_type=:meta_partition_type",
            {'meta_partition': meta_partition, 'meta_partition_type': meta_partition_type}
        )

    def load_table_data(self, df_data_to_load: DataFrame, connection, schema: str, table: str):
        columns = df_data_to_load.columns.to_list()
        self.log.debug(f"LOADing {len(df_data_to_load)} rows into {schema}.{table} ({','.join(columns)}")
        df_data_to_load.to_sql(table, schema=schema, con=connection, index=False, if_exists='append')

    def update_view(self, schema: str, view_name: str, view_query: str, comment: str = ""):
        with self.engine.connect() as connection:
            connection.execute(f"DROP VIEW IF EXISTS {schema}.{view_name}")
            connection.execute(f"""
                CREATE VIEW {schema}.{view_name}
                    --COMMENT '{comment}'
                AS
                {view_query}
            """)

    def add_to_lake(self, df: DataFrame, destination_table: str):
        at_date = datetime.now(timezone.utc)
        at_date_day = at_date.replace(hour=0, minute=0, second=0, microsecond=0)
        pa__collection_id = f"tanzu-dm-daily|{at_date.timestamp()}"

        df['id'] = df.apply(lambda x: f"auto:{uuid.uuid4()}", axis=1)
        df['pa__arrival_ts'] = at_date
        df['pa__arrival_day'] = at_date_day.timestamp()
        df['pa__collection_id'] = pa__collection_id

        with self.engine.connect() as connection:
            df.to_sql(destination_table, schema='tanzu_lake_restricted_staging', con=connection, index=False, if_exists='append')

    def optimise_table(self, schema: str, table: str):
        # No optimisations for SQLite
        pass

    def refresh(self, schema, table):
        # No refresh for SQLite
        pass
