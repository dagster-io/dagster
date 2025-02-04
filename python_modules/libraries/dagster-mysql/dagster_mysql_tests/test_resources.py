from urllib.parse import urlparse

from dagster import asset, materialize_to_memory
from dagster_mysql import MySQLResource


def test_resource(hostname, conn_string):
    @asset
    def mysql_create_table(mysql: MySQLResource):
        with mysql.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "CREATE TABLE IF NOT EXISTS films ("
                    " title VARCHAR(40) NOT NULL,"
                    " year INT NOT NULL, "
                    " PRIMARY KEY (title));"
                )
                cur.execute(
                    "INSERT INTO films (title, year)"
                    " VALUES ('the matrix', 1999)"
                    " ON DUPLICATE KEY UPDATE title=title;"
                )
                cur.execute(
                    "INSERT INTO films (title, year)"
                    " VALUES ('fight club', 1999)"
                    " ON DUPLICATE KEY UPDATE title=title;"
                )

            conn.commit()

    @asset
    def mysql_query_table(mysql: MySQLResource):
        with mysql.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM films;")
                assert len(cur.fetchall()) == 2

    conn_info = urlparse(conn_string)

    result = materialize_to_memory(
        [mysql_create_table, mysql_query_table],
        resources={
            "mysql": MySQLResource(
                user=conn_info.username,
                password=conn_info.password,
                host=conn_info.hostname,
                port=conn_info.port,
                database="test",
            )
        },
    )

    assert result.success
