from typing import Optional

from dagster_aws.s3.utils import construct_s3_client
from dagster_dbt.cli.resources import dbt_cli_resource

from dagster._core.definitions.configured_adapters import ConfiguredResourceAdapter


def build_s3_session(
    *,
    max_attempts: int = 5,
    use_unsigned_session: bool = False,
    region_name: Optional[str] = None,
    endpoint_url: Optional[str] = None,
    profile_name: Optional[str] = None,
):
    return construct_s3_client(
        max_attempts=max_attempts,
        use_unsigned_session=use_unsigned_session,
        region_name=region_name,
        endpoint_url=endpoint_url,
        profile_name=profile_name,
    )


class DbtCliResource(ConfiguredResourceAdapter):
    def __init__(
        self,
        *,
        profiles_dir: Optional[str] = None,
        project_dir: Optional[str] = None,
        target: Optional[str] = None,
    ):
        super().__init__(
            parent_resource=dbt_cli_resource,
            args={
                "profiles-dir": profiles_dir,
                "project-dir": project_dir,
                "target": target,
            },
        )
