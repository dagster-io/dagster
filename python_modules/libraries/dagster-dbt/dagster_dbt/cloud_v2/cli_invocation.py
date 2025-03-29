from collections.abc import Iterator, Sequence
from typing import TYPE_CHECKING, Union

from dagster import AssetCheckEvaluation, AssetMaterialization
from dagster._annotations import preview

from dagster_dbt.cloud_v2.run_handler import DbtCloudJobRunHandler, DbtCloudJobRunResults
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator

if TYPE_CHECKING:
    from dagster_dbt.cloud_v2.resources import DbtCloudWorkspace


@preview
class DbtCloudCliInvocation:
    """Represents a dbt Cloud cli invocation."""

    def __init__(
        self,
        args: Sequence[str],
        workspace: "DbtCloudWorkspace",
        dagster_dbt_translator: DagsterDbtTranslator,
        run_handler: DbtCloudJobRunHandler,
    ):
        self.args = args
        self.workspace = workspace
        self.dagster_dbt_translator = dagster_dbt_translator
        self.run_handler = run_handler

    @classmethod
    def run(
        cls,
        args: Sequence[str],
        workspace: "DbtCloudWorkspace",
        dagster_dbt_translator: DagsterDbtTranslator,
    ) -> "DbtCloudCliInvocation":
        workspace_data = workspace.fetch_workspace_data()
        run_handler = DbtCloudJobRunHandler.run(
            job_id=workspace_data.job_id,
            args=args,
            client=workspace.get_client(),
        )
        return DbtCloudCliInvocation(
            args=args,
            workspace=workspace,
            dagster_dbt_translator=dagster_dbt_translator,
            run_handler=run_handler,
        )

    def wait(self) -> Iterator[Union[AssetMaterialization, AssetCheckEvaluation]]:
        self.run_handler.wait_for_success()
        if "run_results.json" not in self.run_handler.list_run_artifacts():
            return
        run_results = DbtCloudJobRunResults.from_run_results_json(
            run_results_json=self.run_handler.get_run_results()
        )
        yield from run_results.to_default_asset_events(
            workspace=self.workspace, dagster_dbt_translator=self.dagster_dbt_translator
        )
