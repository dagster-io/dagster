from typing import Any

import pandas as pd
from dagster import ConfigurableResource


class S3Resource(ConfigurableResource):
    bucket: str
    region: str = "us-east-1"
    access_key_id: str | None = None
    secret_access_key: str | None = None

    def _get_client(self) -> Any:
        import boto3

        kwargs: dict[str, Any] = {"region_name": self.region}
        if self.access_key_id and self.secret_access_key:
            kwargs["aws_access_key_id"] = self.access_key_id
            kwargs["aws_secret_access_key"] = self.secret_access_key
        return boto3.client("s3", **kwargs)

    def write_parquet(self, key: str, df: pd.DataFrame) -> str:
        import io

        buffer = io.BytesIO()
        df.to_parquet(buffer, index=False)
        buffer.seek(0)

        client = self._get_client()
        client.put_object(Bucket=self.bucket, Key=key, Body=buffer.getvalue())
        return f"s3://{self.bucket}/{key}"

    def read_parquet(self, key: str) -> pd.DataFrame:
        import io

        client = self._get_client()
        response = client.get_object(Bucket=self.bucket, Key=key)
        buffer = io.BytesIO(response["Body"].read())
        return pd.read_parquet(buffer)

    def write(self, path: str, data: Any) -> None:
        if isinstance(data, pd.DataFrame):
            self.write_parquet(path, data)
        else:
            client = self._get_client()
            client.put_object(Bucket=self.bucket, Key=path, Body=str(data))

    def read(self, path: str) -> Any:
        if path.endswith(".parquet"):
            return self.read_parquet(path)
        client = self._get_client()
        response = client.get_object(Bucket=self.bucket, Key=path)
        return response["Body"].read().decode("utf-8")


class SnowflakeResource(ConfigurableResource):
    account: str
    user: str
    password: str
    database: str
    warehouse: str = ""
    schema_name: str = "PUBLIC"
    role: str | None = None

    def _get_connection(self) -> Any:
        from snowflake import connector as snowflake_connector

        return snowflake_connector.connect(
            account=self.account,
            user=self.user,
            password=self.password,
            database=self.database,
            warehouse=self.warehouse,
            schema=self.schema_name,
            role=self.role,
        )

    def query(self, sql: str) -> pd.DataFrame:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            columns = [str(desc[0]) for desc in cursor.description] if cursor.description else []
            data = cursor.fetchall()
            return pd.DataFrame(data, columns=columns)  # type: ignore[arg-type]

    def execute(self, sql: str) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)

    def write_table(self, table_name: str, df: pd.DataFrame, if_exists: str = "replace") -> None:
        from snowflake.connector.pandas_tools import write_pandas

        with self._get_connection() as conn:
            if if_exists == "replace":
                cursor = conn.cursor()
                cursor.execute(f"DROP TABLE IF EXISTS {table_name}")

            write_pandas(conn, df, table_name.upper(), auto_create_table=True)


class DatabricksResource(ConfigurableResource):
    server_hostname: str
    http_path: str
    access_token: str

    def _get_connection(self) -> Any:
        from databricks import sql as databricks_sql

        return databricks_sql.connect(
            server_hostname=self.server_hostname,
            http_path=self.http_path,
            access_token=self.access_token,
        )

    def query(self, sql: str) -> pd.DataFrame:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            columns = [str(desc[0]) for desc in cursor.description] if cursor.description else []
            data = cursor.fetchall()
            return pd.DataFrame(data, columns=columns)  # type: ignore[arg-type]

    def execute(self, sql: str) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
