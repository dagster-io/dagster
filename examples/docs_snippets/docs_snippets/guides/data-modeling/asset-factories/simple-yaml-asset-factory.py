import dagster_aws.s3 as s3
import yaml

import dagster as dg


def build_etl_job(
    s3_resource: s3.S3Resource,
    bucket: str,
    source_object: str,
    target_object: str,
    sql: str,
) -> dg.Definitions:
    # Code from previous example omitted
    return dg.Definitions()


# highlight-start
def load_etl_jobs_from_yaml(yaml_path: str) -> dg.Definitions:
    config = yaml.safe_load(open(yaml_path))
    s3_resource = s3.S3Resource(
        aws_access_key_id=config["aws"]["access_key_id"],
        aws_secret_access_key=config["aws"]["secret_access_key"],
    )
    defs = []
    for job_config in config["etl_jobs"]:
        defs.append(
            build_etl_job(
                s3_resource=s3_resource,
                bucket=job_config["bucket"],
                source_object=job_config["source"],
                target_object=job_config["target"],
                sql=job_config["sql"],
            )
        )
    return dg.Definitions.merge(*defs)


defs = load_etl_jobs_from_yaml("etl_jobs.yaml")
# highlight-end
