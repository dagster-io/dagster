from dagster import file_relative_path

MANIFEST_PATH = file_relative_path(__file__, "../dbt_project/manifest.json")
