from typing import Any, Mapping, Sequence, Type, Union

from dagster import AssetCheckResult, AssetMaterialization
from dagster._record import record

from dagster_dlift.client import DbtCloudClient
from dagster_dlift.translator import (
    DagsterDbtCloudRuntimeTranslator,
    DagsterDbtCloudTranslator,
    DbtCloudProjectEnvironmentData,
)


@record
class DbtCloudJobRun:
    """Represents a dbt Cloud job run."""

    job_id: int
    run_id: int
    client: DbtCloudClient
    translator: DagsterDbtCloudTranslator
    env_data: DbtCloudProjectEnvironmentData

    def wait_for_success(self) -> int:
        return self.client.poll_for_run_completion(self.run_id)

    def get_run_results(self) -> Mapping[str, Any]:
        return self.client.get_run_results_json(self.run_id)

    def get_asset_events(
        self,
        runtime_translator_cls: Type[
            DagsterDbtCloudRuntimeTranslator
        ] = DagsterDbtCloudRuntimeTranslator,
    ) -> Sequence[Union[AssetMaterialization, AssetCheckResult]]:
        runtime_translator = runtime_translator_cls()
        self.wait_for_success()
        run_results = self.get_run_results()
        asset_events = []
        for result in run_results["results"]:
            data = self.env_data.get_from_unique_id(result["unique_id"])
            spec = self.translator.get_spec(data)
            asset_events.append(runtime_translator.get_asset_event(spec, result))
        return asset_events


@record
class DbtCloudEnvClient:
    dbt_client: DbtCloudClient
    env_data: DbtCloudProjectEnvironmentData
    translator: DagsterDbtCloudTranslator

    def cli(self, args: Sequence[str]) -> DbtCloudJobRun:
        """Run a dbt cli command with the dbt Cloud client."""
        response = self.dbt_client.trigger_job(
            self.env_data.job_id, steps=[" ".join(["dbt", *args])]
        )
        return DbtCloudJobRun(
            job_id=self.env_data.job_id,
            run_id=response["data"]["id"],
            client=self.dbt_client,
            translator=self.translator,
            env_data=self.env_data,
        )
