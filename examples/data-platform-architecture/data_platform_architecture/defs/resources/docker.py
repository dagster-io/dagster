from typing import Any

import pandas as pd
from dagster import ConfigurableResource


class PostgresResource(ConfigurableResource):
    host: str = "localhost"
    port: int = 5432
    user: str = "dagster"
    password: str = "dagster"
    database: str = "demo"

    def _get_connection(self) -> Any:
        import psycopg2

        return psycopg2.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database,
        )

    def query(self, sql: str) -> pd.DataFrame:
        with self._get_connection() as conn:
            return pd.read_sql(sql, conn)

    def execute(self, sql: str) -> None:
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
            conn.commit()

    def write_table(
        self,
        table_name: str,
        df: pd.DataFrame,
        if_exists: str = "replace",
    ) -> None:
        from typing import Literal, cast

        from sqlalchemy import create_engine

        url = f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
        engine = create_engine(url)
        df.to_sql(
            table_name,
            engine,
            if_exists=cast("Literal['fail', 'replace', 'append']", if_exists),
            index=False,
        )


class RESTAPIResource(ConfigurableResource):
    base_url: str = "http://localhost:8000"
    api_key: str | None = None
    timeout: float = 30.0

    def _get_headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        import httpx

        url = f"{self.base_url}{endpoint}"
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(url, params=params, headers=self._get_headers())
            response.raise_for_status()
            return response.json()

    def post(self, endpoint: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        import httpx

        url = f"{self.base_url}{endpoint}"
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(url, json=data, headers=self._get_headers())
            response.raise_for_status()
            return response.json()
