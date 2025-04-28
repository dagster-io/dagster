from dagster import Definitions
from dagster._annotations import preview
from dagster._core.definitions.definitions_load_context import StateBackedDefinitionsLoader
from dagster._record import record

from dagster_dlift.project import DBTCloudProjectEnvironment
from dagster_dlift.translator import DbtCloudProjectEnvironmentData

DBT_CLOUD_RECONSTRUCTION_METADATA_KEY_PREFIX = "__dbt_cloud"


@preview
@record
class DbtCloudProjectEnvironmentDefsLoader(
    StateBackedDefinitionsLoader[DbtCloudProjectEnvironmentData]
):
    project_environment: DBTCloudProjectEnvironment

    @property
    def defs_key(self) -> str:
        return (
            f"{DBT_CLOUD_RECONSTRUCTION_METADATA_KEY_PREFIX}.{self.project_environment.unique_id}"
        )

    def fetch_state(self) -> DbtCloudProjectEnvironmentData:
        return self.project_environment.compute_data()

    def defs_from_state(self, state: DbtCloudProjectEnvironmentData) -> Definitions:
        raise NotImplementedError("Not used")
