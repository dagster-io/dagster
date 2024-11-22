from typing import Dict, Sequence

from dagster import (
    AssetCheckSpec,
    AssetKey,
    AssetSpec,
    _check as check,
)
from dagster._core.definitions.asset_dep import AssetDep
from dagster_dlift.client import UnscopedDbtCloudClient
from dagster_dlift.project import DbtCloudCredentials, DBTCloudProjectEnvironment
from dagster_dlift.test.utils import get_env_var

ENV_NAME = "test"
EXPECTED_TAG = "demo"


def get_unscoped_client() -> UnscopedDbtCloudClient:
    return UnscopedDbtCloudClient(
        account_id=int(get_env_var("KS_DBT_CLOUD_ACCOUNT_ID")),
        token=get_env_var("KS_DBT_CLOUD_TOKEN"),
        access_url=get_env_var("KS_DBT_CLOUD_ACCESS_URL"),
        discovery_api_url=get_env_var("KS_DBT_CLOUD_DISCOVERY_API_URL"),
    )


def get_environment_id() -> int:
    return get_unscoped_client().get_environment_id_by_name(ENV_NAME)


def get_project_id() -> int:
    return int(get_env_var("KS_DBT_CLOUD_PROJECT_ID"))


def get_project() -> DBTCloudProjectEnvironment:
    return DBTCloudProjectEnvironment(
        credentials=DbtCloudCredentials(
            account_id=int(get_env_var("KS_DBT_CLOUD_ACCOUNT_ID")),
            token=get_env_var("KS_DBT_CLOUD_TOKEN"),
            access_url=get_env_var("KS_DBT_CLOUD_ACCESS_URL"),
            discovery_api_url=get_env_var("KS_DBT_CLOUD_DISCOVERY_API_URL"),
        ),
        project_id=get_project_id(),
        environment_id=get_environment_id(),
    )


def filter_specs_by_tag(specs: Sequence[AssetSpec], tag: str) -> dict[AssetKey, AssetSpec]:
    return {
        spec.key: spec for spec in specs if tag in check.not_none(spec.metadata)["raw_data"]["tags"]
    }


def add_dep_to_spec(spec: AssetSpec, dep: AssetKey) -> AssetSpec:
    return spec._replace(deps=[*spec.deps, AssetDep(dep)])


def key_for_uid(specs: Sequence[AssetSpec], uid: str) -> AssetKey:
    return next(spec.key for spec in specs if spec.metadata["raw_data"]["uniqueId"] == uid)


def relevant_check_specs(
    specs: Sequence[AssetSpec], check_specs: Sequence[AssetCheckSpec]
) -> Sequence[AssetCheckSpec]:
    spec_map = {spec.key: spec for spec in specs}
    return [spec for spec in check_specs if spec.key.asset_key in spec_map]


def add_deps(
    uid_to_dep_mapping: dict[str, AssetKey], specs: dict[AssetKey, AssetSpec]
) -> Sequence[AssetSpec]:
    specs = dict(specs)
    for uid, dep in uid_to_dep_mapping.items():
        specs[key_for_uid(list(specs.values()), uid)] = add_dep_to_spec(
            specs[key_for_uid(list(specs.values()), uid)], dep
        )
    return list(specs.values())
