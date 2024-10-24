from functools import cached_property, lru_cache
from typing import NamedTuple, Sequence, Type, Union

from dagster import AssetCheckSpec, AssetSpec

from dagster_dlift.client import DbtCloudClient
from dagster_dlift.compute import compute_environment_data
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
    def client(self) -> DbtCloudClient:
        return DbtCloudClient(
            account_id=self.credentials.account_id,
            token=self.credentials.token,
            access_url=self.credentials.access_url,
            discovery_api_url=self.credentials.discovery_api_url,
        )

    def compute_data(self) -> "DbtCloudProjectEnvironmentData":
        return compute_environment_data(
            project_id=self.project_id, environment_id=self.environment_id, client=self.client
        )

    # Cache spec retrieval for a specific translator class.
    @lru_cache(maxsize=1)
    def get_specs(
        self, translator_cls: Type[DagsterDbtCloudTranslator]
    ) -> Sequence[Union[AssetSpec, AssetCheckSpec]]:
        from dagster_dlift.loader import DbtCloudProjectEnvironmentDefsLoader

        data = DbtCloudProjectEnvironmentDefsLoader(project_environment=self).get_or_fetch_state()
        translator = translator_cls(context=data)
        all_external_data = [
            *data.models_by_unique_id.values(),
            *data.sources_by_unique_id.values(),
            *data.tests_by_unique_id.values(),
        ]
        return [translator.get_spec(data) for data in all_external_data]

    def get_asset_specs(
        self, translator_cls: Type[DagsterDbtCloudTranslator] = DagsterDbtCloudTranslator
    ) -> Sequence[AssetSpec]:
        return [spec for spec in self.get_specs(translator_cls) if isinstance(spec, AssetSpec)]

    def get_check_specs(
        self, translator_cls: Type[DagsterDbtCloudTranslator] = DagsterDbtCloudTranslator
    ) -> Sequence[AssetCheckSpec]:
        return [spec for spec in self.get_specs(translator_cls) if isinstance(spec, AssetCheckSpec)]
