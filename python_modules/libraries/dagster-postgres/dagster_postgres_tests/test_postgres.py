import datetime


def test_insert_select(conn):  # pylint: disable=redefined-outer-name,unused-argument
    with conn.cursor() as curs:

        dt_now = datetime.datetime.now()

        body = 'contents'

        row_to_insert = ('message_id', 'run_id', dt_now, body)

        curs.execute(
            '''
            INSERT INTO run_events (message_id, run_id, timestamp, event_body)
            VALUES(%s, %s, %s, %s);
            ''',
            row_to_insert,
        )

        curs.execute('SELECT * from run_events')
        rows = curs.fetchall()
        assert len(rows) == 1
        assert rows[0] == row_to_insert
