from typing import AbstractSet, Any, Dict, Literal, Mapping, Optional

from dagster import AssetExecutionContext
from databricks.sdk.service.jobs import SubmitTask
from pydantic import Field

from dagster_blueprints.blueprint_assets_definition import BlueprintAssetsDefinition


class DatabricksTaskBlueprint(BlueprintAssetsDefinition):
    """A blueprint for one or more assets whose shared materialization function is a databricks
    task.

    Requires the code location to include a "pipes_databricks_client" resource with type
    dagster_databricks.PipesDatabricksClient.
    """

    type: Literal["dagster_databricks/task"] = "dagster_databricks/task"
    task: Dict[str, Any] = Field(
        ...,
        description=(
            "Specification of the databricks task to run. Environment variables used by "
            "dagster-pipes will be set under the `spark_env_vars` key of the `new_cluster` field "
            "(if there is an existing dictionary here, the Pipes environment variables will be "
            "merged in). Everything else will be passed unaltered under the `tasks` arg to "
            "`WorkspaceClient.jobs.submit`."
        ),
    )
    submit_args: Optional[Mapping[str, str]] = Field(
        default=None,
        description="Additional keyword arguments that will be forwarded as-is to "
        "`WorkspaceClient.jobs.submit`.",
    )

    @staticmethod
    def get_required_resource_keys() -> AbstractSet[str]:
        return {"pipes_databricks_client"}

    def materialize(self, context: AssetExecutionContext):
        return context.resources.pipes_databricks_client.run(
            context=context, task=SubmitTask.from_dict(self.task), submit_args=self.submit_args
        ).get_results()
