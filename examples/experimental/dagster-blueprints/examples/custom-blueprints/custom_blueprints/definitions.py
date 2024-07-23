import tempfile
from pathlib import Path
from subprocess import Popen
from typing import Literal

from dagster import Definitions, asset
from dagster_blueprints import YamlBlueprintsLoader
from dagster_blueprints.blueprint import Blueprint


def local_csv_to_snowflake(table_name: str, csv_path: Path) -> None:
    """Left as an exercise to the reader."""


def curl_csv_to_snowflake(table_name: str, csv_url: str) -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "file.csv"
        command = ["curl", "-o", str(path), csv_url]
        process = Popen(command)
        process.wait()

        if process.returncode != 0:
            raise ValueError(f"External execution process failed with code {process.returncode}")

        local_csv_to_snowflake(table_name, path)


class CurlCsvSnowflakeAssetBlueprint(Blueprint):
    """Blueprint for an asset in Snowflake, populated from a CSV file on the internet."""

    type: Literal["curl_asset"]
    csv_url: str
    table_name: str

    def build_defs(self) -> Definitions:
        @asset(key=self.table_name)
        def _asset():
            curl_csv_to_snowflake(table_name=self.table_name, csv_url=self.csv_url)

        return Definitions(assets=[_asset])


loader = YamlBlueprintsLoader(
    per_file_blueprint_type=CurlCsvSnowflakeAssetBlueprint,
    path=Path(__file__).parent / "curl_assets",
)
defs = loader.load_defs()
