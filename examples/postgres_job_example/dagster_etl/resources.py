import os
from dagster import resource
import psycopg2
from dotenv import load_dotenv


load_dotenv()


class PostgresDB:
    """Class for interacting with a PostgreSQL database"""
    def __init__(self):
        self.conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT"),
            dbname=os.getenv("POSTGRES_DATABASE"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
        )

    def execute_query(self, query):
        """Execute a SQL query"""
        with self.conn.cursor() as cursor:
            cursor.execute(query)
            if query.strip().lower().startswith('select'):
                return cursor.fetchall()
            self.conn.commit()



@resource()
def postgres_resource(context):
    """Resource for interacting with a PostgreSQL database"""
    return PostgresDB()