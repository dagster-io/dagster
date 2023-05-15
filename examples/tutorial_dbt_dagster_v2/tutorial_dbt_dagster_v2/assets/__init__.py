import json

from dagster import file_relative_path

DBT_PROJECT_DIR = file_relative_path(__file__, "../../jaffle_shop")
DBT_PROFILES_DIR = file_relative_path(__file__, "../../jaffle_shop")
MANIFEST_PATH = file_relative_path(__file__, "../../jaffle_shop/target/manifest.json")

with open(MANIFEST_PATH) as f:
    raw_manifest: dict = json.load(f)
