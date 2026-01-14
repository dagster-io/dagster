import random
import time
from typing import Any

import dagster as dg

"""
Repo of assets and ops that are useful for testing alerts
"""


def generate_random_schema(column_names: list[str]):
    column_types = ["string", "int", "timestamp", "float"]
    tags = [{"priority": "high"}, {"team": "marketing"}, {"region": "eu"}]
    columns = [
        dg.TableColumn(
            name=column_name,
            type=random.choice(column_types),
            tags=random.choice(tags),
            constraints=dg.TableColumnConstraints(
                nullable=random.choice([True, False]), unique=random.choice([True, False])
            ),
        )
        for column_name in column_names
    ]

    return dg.TableSchema(columns=columns)


@dg.asset
def schema_change_asset(context):
    random.seed(time.time())
    columns = ["name", "email", "age", "city", "country", "phone", "job_title", "pet_name"]

    return dg.MaterializeResult(
        metadata={
            "dagster/column_schema": generate_random_schema(
                random.sample(columns, random.randint(4, len(columns)))
            )
        }
    )


class CustomMetadataConfig(dg.Config):
    custom_metadata: dict[str, Any]


@dg.asset
def custom_metadata_asset(config: CustomMetadataConfig):
    return dg.MaterializeResult(metadata={**config.custom_metadata})


def get_assets_and_checks():
    return [schema_change_asset, custom_metadata_asset]
