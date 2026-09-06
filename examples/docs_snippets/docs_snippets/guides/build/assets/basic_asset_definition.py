import json
import os

from dagster import asset


@asset
def my_asset():
    os.makedirs("data", exist_ok=True)
    with open("data/my_asset.json", "w", encoding="utf-8") as f:
        json.dump([1, 2, 3], f)
