import os
import sqlite3

from lakehouse import SqlLiteLakehouse, construct_lakehouse_pipeline, input_table, sqlite_table

from dagster import execute_pipeline, file_relative_path


def create_sqllite_lakehouse_table(name, sql_text, input_tables=None):
    @sqlite_table(name=name, input_tables=input_tables)
    def Table(context, **_kwargs):
        context.resources.conn.execute(sql_text)
        context.resources.conn.commit()

    return Table


def test_basic_sqlite_pipeline():
    @sqlite_table
    def TableOne(context):
        context.resources.conn.execute('''CREATE TABLE TableOne AS SELECT 1 as num''')
        context.resources.conn.commit()

    @sqlite_table
    def TableTwo(context):
        context.resources.conn.execute('''CREATE TABLE TableTwo AS SELECT 2 as num''')
        context.resources.conn.commit()

    @sqlite_table(
        input_tables=[input_table('table_one', TableOne), input_table('table_two', TableTwo)]
    )
    def TableThree(context, **_kwargs):
        context.resources.conn.execute(
            'CREATE TABLE TableThree AS SELECT num from TableOne UNION SELECT num from TableTwo'
        )
        context.resources.conn.commit()

    conn = sqlite3.connect(':memory:')
    pipeline_def = construct_lakehouse_pipeline(
        name='sqllite_lakehouse_pipeline',
        lakehouse_tables=[TableOne, TableTwo, TableThree],
        resources={'conn': conn, 'lakehouse': SqlLiteLakehouse()},
    )

    result = execute_pipeline(pipeline_def)
    assert result.success

    assert conn.cursor().execute('SELECT * FROM TableThree').fetchall() == [(1,), (2,)]


def create_sqllite_table_from_file(path, input_tables=None):
    sql_file_name = os.path.basename(os.path.abspath(path))
    table_name, _sql_ext = os.path.splitext(sql_file_name)
    with open(path, 'r') as ff:
        sql_text = ff.read()
        return create_sqllite_lakehouse_table(table_name, sql_text, input_tables)


def test_file_based_sqlite_pipeline():
    def path_for_table(table_name):
        return file_relative_path(
            __file__, 'basic_sqllite_test_files/{table_name}.sql'.format(table_name=table_name)
        )

    TableOne = create_sqllite_table_from_file(path_for_table('TableOne'))
    TableTwo = create_sqllite_table_from_file(path_for_table('TableTwo'))
    TableThree = create_sqllite_table_from_file(
        path_for_table('TableThree'),
        input_tables=[input_table('table_one', TableOne), input_table('table_two', TableTwo)],
    )

    conn = sqlite3.connect(':memory:')
    pipeline_def = construct_lakehouse_pipeline(
        name='sqllite_lakehouse_pipeline',
        lakehouse_tables=[TableOne, TableTwo, TableThree],
        resources={'conn': conn, 'lakehouse': SqlLiteLakehouse()},
    )

    result = execute_pipeline(pipeline_def)
    assert result.success

    assert conn.cursor().execute('SELECT * FROM TableThree').fetchall() == [(1,), (2,)]
