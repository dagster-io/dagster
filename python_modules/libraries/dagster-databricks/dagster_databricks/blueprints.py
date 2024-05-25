from typing import AbstractSet, Any, Dict, Mapping, Optional

from dagster import AssetExecutionContext, MaterializeResult
from dagster._core.blueprints.base_asset_blueprint import BaseAssetBlueprint
from databricks.sdk.service.jobs import SubmitTask


class DatabricksTaskAssetBlueprint(BaseAssetBlueprint):
    """A blueprint for an asset definition whose materialization function is a databricks task.

    Requires the code location to include a "pipes_databricks_client" resource with type
    dagster_databricks.PipesDatabricksClient.

    Attributes:
        task (databricks.sdk.service.jobs.SubmitTask): Specification of the databricks
            task to run. Environment variables used by dagster-pipes will be set under the
            `spark_env_vars` key of the `new_cluster` field (if there is an existing dictionary
            here, the EXT environment variables will be merged in). Everything else will be
            passed unaltered under the `tasks` arg to `WorkspaceClient.jobs.submit`.
        submit_args (Optional[Mapping[str, str]]): Additional keyword arguments that will be
            forwarded as-is to `WorkspaceClient.jobs.submit`.
    """

    task: Dict[str, Any]
    submit_args: Optional[Mapping[str, str]] = None

    @staticmethod
    def get_required_resource_keys() -> AbstractSet[str]:
        return {"pipes_databricks_client"}

    def materialize(self, context: AssetExecutionContext) -> MaterializeResult:
        return context.resources.pipes_databricks_client.run(
            context=context, task=SubmitTask.from_dict(self.task), submit_args=self.submit_args
        ).get_materialize_result()
