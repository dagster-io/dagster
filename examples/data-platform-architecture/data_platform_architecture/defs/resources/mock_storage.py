import json
from datetime import datetime, timedelta
from typing import Any

import pandas as pd


class MockDatabase:
    def __init__(self):
        self._data = self._generate_mock_sales_data()

    def _generate_mock_sales_data(self) -> list[dict[str, Any]]:
        base_date = datetime.now() - timedelta(days=30)
        data = []
        for i in range(1000):
            data.append(
                {
                    "sale_id": f"sale-{i:04d}",
                    "customer_id": f"cust-{i % 100:03d}",
                    "product_id": f"prod-{i % 50:03d}",
                    "amount": 10.0 + (i % 100) * 5.0,
                    "sale_date": (base_date + timedelta(days=i % 30)).isoformat(),
                    "region": ["North", "South", "East", "West"][i % 4],
                }
            )
        return data

    def query(self, sql: str) -> pd.DataFrame:
        if "CURRENT_DATE" in sql:
            cutoff = datetime.now() - timedelta(days=1)
            filtered = [d for d in self._data if datetime.fromisoformat(d["sale_date"]) >= cutoff]
            return pd.DataFrame(filtered)
        return pd.DataFrame(self._data)


class MockAPIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self._data = self._generate_mock_clickstream_data()

    def _generate_mock_clickstream_data(self) -> list[dict[str, Any]]:
        base_time = datetime.now()
        data = []
        for i in range(500):
            data.append(
                {
                    "event_id": f"event-{i:04d}",
                    "user_id": f"user-{i % 100:03d}",
                    "page_url": f"https://example.com/page-{i % 20}",
                    "timestamp": (base_time - timedelta(minutes=500 - i)).isoformat(),
                    "event_type": ["page_view", "click", "purchase"][i % 3],
                    "session_id": f"session-{i % 50:03d}",
                    "metadata": json.dumps({"device": "mobile", "browser": "chrome"}),
                }
            )
        return data

    def get_events(
        self, start_date: str | None = None, end_date: str | None = None
    ) -> list[dict[str, Any]]:
        return self._data


class MockS3Storage:
    def __init__(self):
        self._storage: dict[str, pd.DataFrame] = {}

    def write_parquet(self, path: str, df: pd.DataFrame) -> str:
        self._storage[path] = df.copy()
        return path

    def read_parquet(self, path: str) -> pd.DataFrame:
        return self._storage.get(path, pd.DataFrame())


class MockWarehouse:
    def __init__(self):
        self._tables: dict[str, pd.DataFrame] = {}

    def write_table(self, table_name: str, df: pd.DataFrame, if_exists: str = "replace") -> None:
        if if_exists == "replace" or table_name not in self._tables:
            self._tables[table_name] = df.copy()
        else:
            existing = self._tables[table_name]
            self._tables[table_name] = pd.concat([existing, df], ignore_index=True)

    def read_table(self, table_name: str) -> pd.DataFrame:
        return self._tables.get(table_name, pd.DataFrame())
