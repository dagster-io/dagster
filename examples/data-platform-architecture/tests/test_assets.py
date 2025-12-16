from datetime import datetime, timedelta
from typing import Any, ClassVar

import pandas as pd
from dagster import ConfigurableResource, materialize
from data_platform_architecture.defs.assets.elt_pipeline import (
    extract_raw_clickstream,
    load_raw_to_warehouse,
    transform_in_warehouse,
)
from data_platform_architecture.defs.assets.etl_pipeline import (
    extract_sales_data,
    load_to_warehouse as etl_load_to_warehouse,
    transform_sales_data,
)
from data_platform_architecture.defs.assets.lakehouse_pipeline import (
    extract_sensor_data,
    load_bronze_layer,
)


class MockPostgresResource(ConfigurableResource):
    def query(self, sql: str) -> pd.DataFrame:
        base_date = datetime.now() - timedelta(days=30)
        data = [
            {
                "sale_id": f"sale-{i:04d}",
                "customer_id": f"cust-{i % 100:03d}",
                "product_id": f"prod-{i % 50:03d}",
                "amount": 10.0 + (i % 100) * 5.0,
                "sale_date": base_date + timedelta(days=i % 30),
                "region": ["North", "South", "East", "West"][i % 4],
            }
            for i in range(100)
        ]
        return pd.DataFrame(data)


class MockAPIResource(ConfigurableResource):
    def get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        base_time = datetime.now()

        if "clickstream" in endpoint:
            data = [
                {
                    "event_id": f"event-{i:04d}",
                    "user_id": f"user-{i % 100:03d}",
                    "timestamp": (base_time - timedelta(minutes=500 - i)).isoformat(),
                    "event_type": ["page_view", "click", "purchase"][i % 3],
                }
                for i in range(100)
            ]
            return {"data": data}

        if "sensor" in endpoint:
            data = [
                {
                    "sensor_id": f"sensor-{i % 50:03d}",
                    "timestamp": (base_time - timedelta(minutes=1000 - i)).isoformat(),
                    "temperature": 20.0 + (i % 30) * 0.5,
                    "humidity": 50.0 + (i % 40) * 0.3,
                    "region": ["North", "South", "East", "West"][i % 4],
                }
                for i in range(100)
            ]
            return {"data": data}

        return {"data": []}


class MockSnowflakeResource(ConfigurableResource):
    def query(self, sql: str) -> pd.DataFrame:
        return pd.DataFrame()

    def execute(self, sql: str) -> None:
        pass

    def write_table(self, table_name: str, df: pd.DataFrame, if_exists: str = "replace") -> None:
        pass


class MockS3Resource(ConfigurableResource):
    bucket: str = "test-bucket"
    _storage: ClassVar[dict[str, Any]] = {}

    def write_parquet(self, key: str, df: pd.DataFrame) -> str:
        MockS3Resource._storage[key] = df
        return f"s3://{self.bucket}/{key}"

    def read_parquet(self, key: str) -> pd.DataFrame:
        return MockS3Resource._storage.get(key, pd.DataFrame())

    def write(self, path: str, data: Any) -> None:
        MockS3Resource._storage[path] = data

    def read(self, path: str) -> Any:
        return MockS3Resource._storage.get(path)


def test_etl_extract_sales_data():
    result = materialize(
        [extract_sales_data],
        resources={"database": MockPostgresResource()},
    )
    assert result.success
    output = result.output_for_node("extract_sales_data")
    assert output is not None
    assert len(output) > 0


def test_elt_extract_raw_clickstream():
    result = materialize(
        [extract_raw_clickstream],
        resources={"api": MockAPIResource()},
    )
    assert result.success


def test_lakehouse_extract_sensor_data():
    result = materialize(
        [extract_sensor_data],
        resources={"api": MockAPIResource()},
    )
    assert result.success


def test_etl_pipeline_graph():
    result = materialize(
        [extract_sales_data, transform_sales_data, etl_load_to_warehouse],
        resources={
            "database": MockPostgresResource(),
            "snowflake": MockSnowflakeResource(),
        },
    )
    assert result.success


def test_elt_pipeline_graph():
    result = materialize(
        [extract_raw_clickstream, load_raw_to_warehouse, transform_in_warehouse],
        resources={
            "api": MockAPIResource(),
            "snowflake": MockSnowflakeResource(),
        },
    )
    assert result.success


def test_lakehouse_pipeline_graph():
    result = materialize(
        [extract_sensor_data, load_bronze_layer],
        resources={
            "api": MockAPIResource(),
            "storage": MockS3Resource(),
        },
    )
    assert result.success
