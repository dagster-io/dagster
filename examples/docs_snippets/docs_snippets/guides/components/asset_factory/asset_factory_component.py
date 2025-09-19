import tempfile

import dagster_aws.s3 as s3
import duckdb

import dagster as dg


# start_etl_job_model
class EtlJob(dg.Model):
    bucket: str = dg.Field
    source_object: str = dg.Field
    target_object: str = dg.Field
    sql: str = dg.Field


# end_etl_job_model


# start_asset_factory_component
class AssetFactory(dg.Component, dg.Model, dg.Resolvable):
    # highlight-start
    access_key_id: str = dg.Field
    secret_access_key: str = dg.Field

    etl_job: list[EtlJob]
    # highlight-end

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        _assets = []

        for etl in self.etl_job:
            asset_key = f"etl_{etl.bucket}_{etl.target_object}".replace(".", "_")

            def create_etl_asset(etl_config):
                @dg.asset(name=asset_key)
                def _etl_asset(context):
                    s3_client = s3.get_client()
                    with tempfile.TemporaryDirectory() as root:
                        source_path = f"{root}/{etl_config.source_object}"
                        target_path = f"{root}/{etl_config.target_object}"

                        # these steps could be split into separate assets, but
                        # for brevity we will keep them together.
                        # 1. extract
                        s3_client.download_file(
                            etl_config.bucket, etl_config.source_object, source_path
                        )

                        # 2. transform
                        db = duckdb.connect(":memory:")
                        db.execute(
                            f"CREATE TABLE source AS SELECT * FROM read_csv('{source_path}');"
                        )
                        db.query(etl_config.sql).to_csv(target_path)

                        # 3. load
                        s3_client.upload_file(
                            etl_config.bucket, etl_config.target_object, target_path
                        )

                return _etl_asset

            _assets.append(create_etl_asset(etl))

        _resources = {
            "s3": s3.S3Resource(
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
            )
        }

        # highlight-start
        return dg.Definitions(assets=_assets, resources=_resources)
        # highlight-end


# end_asset_factory_component
