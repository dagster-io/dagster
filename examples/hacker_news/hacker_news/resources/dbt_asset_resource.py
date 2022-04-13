from typing import Any, Dict, List, Mapping

import pandas
from dagster_dbt import DbtOutput

from dagster import AssetKey, AssetMaterialization, MetadataValue
from dagster.core.definitions.metadata import RawMetadataValue

from .snowflake_io_manager import connect_snowflake


class DbtAssetResource:
    """
    This class defines a resource that is capable of producing a list of AssetMaterializations from
    a DbtOutput. It has one public function, get_asset_materializations(), which finds all the
    generated models in the dbt output and produces corresponding asset materializations.

    Putting this logic in a resource makes it easier to swap out between modes. You probably want
    your local testing / development pipelines to produce different assets than your production
    pipelines, as they will ideally be writing to different tables (with different dbt profiles).
    """

    def __init__(self, asset_key_prefix: List[str]):
        self._asset_key_prefix = asset_key_prefix

    def _get_metadata(self, result: Dict[str, Any]) -> Mapping[str, RawMetadataValue]:
        return {"Execution Time (seconds)": result["execution_time"]}

    def get_asset_materializations(self, dbt_output: DbtOutput) -> List[AssetMaterialization]:
        ret = []

        # dbt_output.result contains the parsed contents of the results.json file
        # Note that the json schema can change from version to version. This is written for
        # https://schemas.getdbt.com/dbt/run-results/v2.json (also will work with v1.json)
        for result in dbt_output.result["results"]:
            if result["status"] != "success":
                continue
            unique_id = result["unique_id"]

            # Here, we choose a naming scheme for our asset keys that will look something like
            # <asset prefix> / model / <dbt project> / <model name>, but this is pretty arbitrary
            asset_key = AssetKey(self._asset_key_prefix + unique_id.split("."))

            # create an AssetMaterialization with our key and metadata
            ret.append(
                AssetMaterialization(
                    description=f"dbt node: {unique_id}",
                    metadata=self._get_metadata(result),
                    asset_key=asset_key,
                )
            )

        return ret


class SnowflakeQueryDbtAssetResource(DbtAssetResource):
    """
    This resource allows us to add in some extra information to these AssetMaterialization events.
    Because the relevant dbt project is configured for a Snowflake cluster, we can query the output
    models to get some additional information that we might want Dagster to track over time.

    Of course, this is completely optional.
    """

    def __init__(self, snowflake_config: Dict[str, str], dbt_schema: str):
        self._snowflake_config = snowflake_config
        self._dbt_schema = dbt_schema
        super().__init__(asset_key_prefix=["snowflake", dbt_schema])

    def _get_metadata(self, result: Dict[str, Any]) -> Mapping[str, RawMetadataValue]:
        """
        Here, we run queries against our output Snowflake database tables to add additional context
        to our asset materializations.
        """

        table_name = result["unique_id"].split(".")[-1]
        with connect_snowflake(config=self._snowflake_config, schema=self._dbt_schema) as con:
            n_rows = pandas.read_sql_query(f"SELECT COUNT(*) FROM {table_name}", con)
            sample_rows = pandas.read_sql_query(
                f"SELECT * FROM {table_name} SAMPLE ROW (10 rows)", con
            )
        return {
            **super()._get_metadata(result),
            "dbt Model Number of Rows": int(n_rows.iloc[0][0]),
            "dbt Model Sample Rows": MetadataValue.md(sample_rows.astype("str").to_markdown()),
        }
