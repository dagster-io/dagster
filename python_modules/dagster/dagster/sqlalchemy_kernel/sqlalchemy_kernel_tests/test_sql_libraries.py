import sqlite3
import sqlalchemy as sa


def test_raw_sqlite():
    conn = sqlite3.connect(':memory:')
    conn.cursor().execute('''CREATE TABLE num_table(num1 int, num2 int)''')
    conn.cursor().execute('''INSERT INTO num_table VALUES(1, 2)''')
    conn.cursor().execute('''INSERT INTO num_table VALUES(3, 4)''')
    conn.commit()

    fetch_cursor = conn.cursor()
    fetch_cursor.execute('SELECT * FROM num_table')
    results = fetch_cursor.fetchall()
    assert results == [(1, 2), (3, 4)]


def test_sqlalchemy_ddl():
    engine = sa.create_engine('sqlite://')
    create_num_table(engine)

    conn = engine.connect()
    results = conn.execute('SELECT * FROM num_table').fetchall()
    assert results == [(1, 2), (3, 4)]


def test_sqlalchemy_create_table_from_select():
    engine = sa.create_engine('sqlite://')

    create_num_table(engine)

    conn = engine.connect()

    conn.execute(
        '''CREATE TABLE sum_table AS SELECT num1, num2, num1 + num2 as sum FROM num_table'''
    )

    results = conn.execute('SELECT * FROM sum_table').fetchall()
    assert results == [(1, 2, 3), (3, 4, 7)]


def create_num_table(engine):
    metadata = sa.MetaData(engine)

    table = sa.Table(
        'num_table',
        metadata,
        sa.Column('num1', sa.Integer),
        sa.Column('num2', sa.Integer),
    )

    table.create()

    conn = engine.connect()

    conn.execute('''INSERT INTO num_table VALUES(1, 2)''')
    conn.execute('''INSERT INTO num_table VALUES(3, 4)''')
