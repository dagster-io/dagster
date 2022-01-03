import os
import re
from abc import ABC, abstractmethod
from datetime import datetime, date

import pandas
import sqlalchemy.engine
from pandas import DataFrame

SCD2_FAR_FUTURE_DATE = '9999-12-31'


def unix_timestamp(at_date):
    return int(pandas.Timestamp(at_date).timestamp())


def utc_timestamp():
    return datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')


def date_trunc(date_part, the_date):
    timestamp = pandas.Timestamp(the_date)
    if date_part.upper() == 'DAY':
        return timestamp.floor('D').strftime('%Y-%m-%d')
    if date_part.upper() == 'MONTH':
        return timestamp.replace(day=1).strftime('%Y-%m-%d')
    else:
        raise NotImplementedError()


def regexp_extract(subject, pattern, index):
    pattern_sanitized = pattern.replace(r'\\', '\\')  # Handle some weird escaping that causes  '.*:(\\S+?)$' to become '.*:(\\\\S+?)$'
    m = re.match(pattern_sanitized, subject)
    if m:
        return m.group(index)
    return f'Unable to find {pattern_sanitized} in {subject}'


class _BaseDatawarehouseResource(ABC):
    __db_engine_for_pid = {}

    def __init__(self, log_manager, echo_sql, pid_group="default"):
        self.echo_sql = echo_sql
        self.log = log_manager
        self.pid_group = pid_group

    @property
    def engine(self) -> sqlalchemy.engine.Engine:
        # Ensure we have one engine per group per process - https://docs.sqlalchemy.org/en/14/core/pooling.html#pooling-multiprocessing
        current_pid_id = f"{self.pid_group}:{os.getpid()}"
        if current_pid_id not in _BaseDatawarehouseResource.__db_engine_for_pid:
            self.log.debug(f"Initialising SQLAlchemy Engine() for pid: {current_pid_id}")
            _BaseDatawarehouseResource.__db_engine_for_pid[current_pid_id] = self.create_engine(self.echo_sql)

        return _BaseDatawarehouseResource.__db_engine_for_pid[current_pid_id]

    @property
    @abstractmethod
    def datawarehouse_uri(self):
        pass

    @abstractmethod
    def create_engine(self, echo_sql) -> sqlalchemy.engine.Engine:
        pass

    def read_sql_query(self, query: str, params: tuple = None, parse_dates: list = None):
        with self.engine.connect() as connection:
            return pandas.read_sql_query(query, connection, params=params, parse_dates=parse_dates)

    def execute(self, query, *multiparams, **params):
        with self.engine.connect() as connection:
            return connection.execute(query, *multiparams, **params)

    @abstractmethod
    def delete_partition(self, connection, schema, table, meta_partition, meta_partition_type):
        pass

    @abstractmethod
    def add_to_lake(self, df: DataFrame, destination_table: str):
        pass

    @abstractmethod
    def update_view(self, schema: str, view_name: str, view_query: str, comment: str = ""):
        raise NotImplementedError()

    @abstractmethod
    def load_table_data(self, df_data_to_load: DataFrame, connection, schema: str, table: str):
        pass

    def update_snapshot_partition(self, df: DataFrame, schema: str, table: str, at_date: datetime):
        df_n = df.copy()
        df_n['dim__day_ts'] = at_date
        df_n['meta__partition_type'] = meta_partition_type = 'day'
        df_n['meta__partition'] = meta_partition = unix_timestamp(date_trunc(meta_partition_type, at_date))

        with self.engine.connect() as connection:
            self.delete_partition(connection, schema, table, meta_partition, meta_partition_type)
            if len(df_n) > 0:
                self.load_table_data(df_n, connection, schema, table)

        return f"{schema}.{table} WHERE meta__partition={meta_partition} AND meta__partition_type='{meta_partition_type}'"

    @abstractmethod
    def refresh(self, schema, table):
        pass

    @abstractmethod
    def optimise_table(self, schema: str, table: str):
        pass
