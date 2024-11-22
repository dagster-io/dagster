from functools import cached_property, lru_cache
from typing import NamedTuple, Sequence, Type, Union

from dagster import AssetCheckSpec, AssetSpec

from dagster_dlift.client import UnscopedDbtCloudClient
from dagster_dlift.compute import compute_environment_data
from dagster_dlift.env_client import EnvScopedDbtCloudClient
from dagster_dlift.translator import DagsterDbtCloudTranslator, DbtCloudProjectEnvironmentData


class DbtCloudCredentials(NamedTuple):
    account_id: int
    token: str
    access_url: str
    discovery_api_url: str


# Eventually a configurable resource
class DBTCloudProjectEnvironment:
    """Represents an environment within a project of dbt cloud."""

    def __init__(self, credentials: DbtCloudCredentials, project_id: int, environment_id: int):
        self.credentials = credentials
        self.project_id = project_id
        self.environment_id = environment_id

    @property
    def unique_id(self) -> str:
        return f"{self.project_id}-{self.environment_id}"

    @cached_property
    def _unscoped_client(self) -> UnscopedDbtCloudClient:
        return UnscopedDbtCloudClient(
            account_id=self.credentials.account_id,
            token=self.credentials.token,
            access_url=self.credentials.access_url,
            discovery_api_url=self.credentials.discovery_api_url,
        )

    def get_client(
        self, translator_cls: type[DagsterDbtCloudTranslator] = DagsterDbtCloudTranslator
    ) -> EnvScopedDbtCloudClient:
        env_data = self.get_or_compute_data()
        return EnvScopedDbtCloudClient(
            dbt_client=self._unscoped_client,
            env_data=env_data,
            translator=translator_cls(context=env_data),
        )

    def compute_data(self) -> "DbtCloudProjectEnvironmentData":
        return compute_environment_data(
            project_id=self.project_id,
            environment_id=self.environment_id,
            client=self._unscoped_client,
        )

    def get_or_compute_data(self) -> "DbtCloudProjectEnvironmentData":
        from dagster_dlift.loader import DbtCloudProjectEnvironmentDefsLoader

        return DbtCloudProjectEnvironmentDefsLoader(project_environment=self).get_or_fetch_state()

    # Cache spec retrieval for a specific translator class.
    @lru_cache(maxsize=1)
    def get_specs(
        self, translator_cls: type[DagsterDbtCloudTranslator]
    ) -> Sequence[Union[AssetSpec, AssetCheckSpec]]:
        data = self.get_or_compute_data()
        translator = translator_cls(context=data)
        all_external_data = [
            *data.models_by_unique_id.values(),
            *data.sources_by_unique_id.values(),
            *data.tests_by_unique_id.values(),
        ]
        return [translator.get_spec(data) for data in all_external_data]

    def get_asset_specs(
        self, translator_cls: type[DagsterDbtCloudTranslator] = DagsterDbtCloudTranslator
    ) -> Sequence[AssetSpec]:
        return [spec for spec in self.get_specs(translator_cls) if isinstance(spec, AssetSpec)]

    def get_check_specs(
        self, translator_cls: type[DagsterDbtCloudTranslator] = DagsterDbtCloudTranslator
    ) -> Sequence[AssetCheckSpec]:
        return [spec for spec in self.get_specs(translator_cls) if isinstance(spec, AssetCheckSpec)]
