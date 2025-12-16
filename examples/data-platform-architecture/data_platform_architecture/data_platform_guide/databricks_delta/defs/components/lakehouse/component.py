import json
from datetime import datetime, timedelta

import dagster._check as check
import pandas as pd
from dagster import (
    AssetExecutionContext,
    AssetKey,
    Component,
    Definitions,
    Model,
    Resolvable,
    asset,
)


class LakehouseComponentParams(Model):
    demo_mode: bool = False
    source_api_url: str = "https://api.example.com/sensors"
    storage_path: str = "data/delta"


class LakehouseComponent(Component, LakehouseComponentParams, Resolvable):
    def build_defs(self, context) -> Definitions:
        from ...resources import DatabricksResource, DeltaStorageResource

        databricks = DatabricksResource(
            server_hostname="demo",
            demo_mode=self.demo_mode,
        )
        delta_storage = DeltaStorageResource(
            storage_path=self.storage_path,
            demo_mode=self.demo_mode,
        )

        @asset(
            key=AssetKey(["bronze", "sensor_data"]),
            kinds={"databricks", "delta"},
        )
        def bronze_sensor_data(
            context: AssetExecutionContext,
            delta_storage: DeltaStorageResource,
        ) -> str:
            base_time = datetime.now()
            data = []
            for i in range(1000):
                data.append(
                    {
                        "sensor_id": f"sensor-{i % 50:03d}",
                        "timestamp": (base_time - timedelta(minutes=1000 - i)).isoformat(),
                        "temperature": 20.0 + (i % 30) * 0.5,
                        "humidity": 50.0 + (i % 40) * 0.3,
                        "region": ["North", "South", "East", "West"][i % 4],
                        "raw_metadata": json.dumps({"firmware_version": "1.2.3"}),
                    }
                )

            df = pd.DataFrame(data)

            table_path = delta_storage.write_delta_table(
                "bronze_sensor_data",
                df,
                mode="overwrite",
            )

            context.log.info(f"Loaded {len(df)} records to bronze layer: {table_path}")
            context.add_output_metadata(
                {
                    "record_count": len(df),
                    "table_path": table_path,
                    "layer": "bronze",
                }
            )

            return table_path

        @asset(
            key=AssetKey(["silver", "sensor_data"]),
            deps=[bronze_sensor_data],
            kinds={"databricks", "delta"},
        )
        def silver_sensor_data(
            context: AssetExecutionContext,
            delta_storage: DeltaStorageResource,
        ) -> str:
            df = delta_storage.read_delta_table("bronze_sensor_data")

            if df.empty:
                if self.demo_mode:
                    base_time = datetime.now()
                    data = []
                    for i in range(1000):
                        data.append(
                            {
                                "sensor_id": f"sensor-{i % 50:03d}",
                                "timestamp": (base_time - timedelta(minutes=1000 - i)).isoformat(),
                                "temperature": 20.0 + (i % 30) * 0.5,
                                "humidity": 50.0 + (i % 40) * 0.3,
                                "region": ["North", "South", "East", "West"][i % 4],
                            }
                        )
                    df = pd.DataFrame(data)
                else:
                    raise ValueError("No data in bronze layer to process")

            df_clean = df[df["temperature"].notna()].copy()
            df_clean = df_clean.drop_duplicates(subset=["sensor_id", "timestamp"])  # type: ignore[call-overload]
            df_clean = df_clean[(df_clean["temperature"] >= -50) & (df_clean["temperature"] <= 100)]
            df_clean = df_clean[(df_clean["humidity"] >= 0) & (df_clean["humidity"] <= 100)]
            df_clean["timestamp"] = pd.to_datetime(df_clean["timestamp"])  # type: ignore[index]

            df_clean = check.inst(df_clean, pd.DataFrame)
            table_path = delta_storage.write_delta_table(
                "silver_sensor_data",
                df_clean,
                mode="overwrite",
            )

            context.log.info(
                f"Processed to silver layer: {table_path} "
                f"({len(df_clean)} records, {len(df) - len(df_clean)} removed)"
            )
            context.add_output_metadata(
                {
                    "record_count": len(df_clean),
                    "records_removed": len(df) - len(df_clean),
                    "table_path": table_path,
                    "layer": "silver",
                }
            )

            return table_path

        @asset(
            key=AssetKey(["gold", "sensor_summary"]),
            deps=[silver_sensor_data],
            kinds={"databricks", "delta"},
        )
        def gold_sensor_summary(
            context: AssetExecutionContext,
            delta_storage: DeltaStorageResource,
        ) -> str:
            df = delta_storage.read_delta_table("silver_sensor_data")

            if df.empty:
                if self.demo_mode:
                    base_time = datetime.now()
                    data = []
                    for i in range(100):
                        data.append(
                            {
                                "sensor_id": f"sensor-{i % 50:03d}",
                                "timestamp": (base_time - timedelta(minutes=100 - i)).isoformat(),
                                "temperature": 20.0 + (i % 30) * 0.5,
                                "humidity": 50.0 + (i % 40) * 0.3,
                                "region": ["North", "South", "East", "West"][i % 4],
                            }
                        )
                    df = pd.DataFrame(data)
                    df["timestamp"] = pd.to_datetime(df["timestamp"])
                else:
                    raise ValueError("No data in silver layer to aggregate")

            df["hour"] = df["timestamp"].dt.floor("H")
            df_agg = (
                df.groupby(["region", "hour"])
                .agg(
                    {
                        "temperature": "mean",
                        "humidity": "mean",
                        "sensor_id": "count",
                    }
                )
                .reset_index()
            )
            df_agg.columns = ["region", "hour", "avg_temperature", "avg_humidity", "sensor_count"]

            table_path = delta_storage.write_delta_table(
                "gold_sensor_summary",
                df_agg,
                mode="overwrite",
            )

            context.log.info(f"Aggregated to gold layer: {table_path} ({len(df_agg)} summaries)")
            context.add_output_metadata(
                {
                    "summary_count": len(df_agg),
                    "table_path": table_path,
                    "layer": "gold",
                }
            )

            return table_path

        return Definitions(
            assets=[bronze_sensor_data, silver_sensor_data, gold_sensor_summary],
            resources={
                "databricks": databricks,
                "delta_storage": delta_storage,
            },
        )
