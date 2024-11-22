import os
from typing import List

import dagster_aws.s3 as s3
import jinja2
import pydantic
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
class AwsConfig(pydantic.BaseModel):
    access_key_id: str
    secret_access_key: str

    def to_resource(self) -> s3.S3Resource:
        return s3.S3Resource(
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
        )


class JobConfig(pydantic.BaseModel):
    bucket: str
    source: str
    target: str
    sql: str

    def to_etl_job(self, s3_resource: s3.S3Resource) -> dg.Definitions:
        return build_etl_job(
            s3_resource=s3_resource,
            bucket=self.bucket,
            source_object=self.source,
            target_object=self.target,
            sql=self.sql,
        )


class EtlJobsConfig(pydantic.BaseModel):
    aws: AwsConfig
    etl_jobs: list[JobConfig]

    def to_definitions(self) -> dg.Definitions:
        s3_resource = self.aws.to_resource()
        return dg.Definitions.merge(
            *[job.to_etl_job(s3_resource) for job in self.etl_jobs]
        )


def load_etl_jobs_from_yaml(yaml_path: str) -> dg.Definitions:
    yaml_template = jinja2.Environment().from_string(open(yaml_path).read())
    config = yaml.safe_load(yaml_template.render(env=os.environ))
    return EtlJobsConfig.model_validate(config).to_definitions()


# highlight-end


defs = load_etl_jobs_from_yaml("etl_jobs_with_jinja.yaml")
