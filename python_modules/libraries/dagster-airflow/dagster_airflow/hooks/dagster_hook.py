import json
import logging
import time
from collections.abc import Mapping
from typing import Any, Optional, cast

# Type errors ignored because some of these imports target deprecated modules for compatibility with
# airflow 1.x and 2.x.
import requests
from airflow.exceptions import AirflowException
from airflow.hooks.base_hook import BaseHook  # type: ignore
from airflow.models import Connection
from dagster._annotations import superseded
from dagster._core.storage.dagster_run import DagsterRunStatus

from dagster_airflow.utils import is_airflow_2_loaded_in_environment


@superseded(
    additional_warn_text=(
        "`DagsterHook` has been superseded by the functionality in the `dagster-airlift` library."
    )
)
class DagsterHook(BaseHook):
    conn_name_attr = "dagster_conn_id"
    default_conn_name = "dagster_default"
    conn_type = "dagster"
    hook_name = "Dagster"

    @staticmethod
    def get_ui_field_behaviour() -> Mapping[str, Any]:
        """Returns custom field behaviour."""
        return {
            "hidden_fields": ["port", "schema", "extra"],
            "relabeling": {
                "description": "Dagster Cloud Organization ID",
                "host": "Dagster Cloud Deployment Name",
                "login": "Dagster URL",
                "password": "Dagster Cloud User Token",
            },
            "placeholders": {
                "password": "",
                "login": "https://dagster.cloud/",
                "description": "",
                "host": "prod",
            },
        }

    def get_conn(self) -> None:
        pass

    def get_pandas_df(self, _sql) -> None:
        pass

    def get_records(self, _sql) -> None:
        pass

    def run(self, _sql) -> None:
        pass

    def __init__(
        self,
        dagster_conn_id: Optional[str] = "dagster_default",
        organization_id: Optional[str] = None,
        deployment_name: Optional[str] = None,
        url: str = "",
        user_token: Optional[str] = None,
    ) -> None:
        if is_airflow_2_loaded_in_environment():
            super().__init__()
        else:
            super().__init__(source=None)
        self.url = url
        self.user_token = user_token
        self.organization_id = organization_id
        self.deployment_name = deployment_name
        if (deployment_name or organization_id) and dagster_conn_id:
            raise AirflowException(
                "Cannot set both dagster_conn_id and organization_id/deployment_name"
            )
        if dagster_conn_id is not None and is_airflow_2_loaded_in_environment():
            conn = self.get_connection(dagster_conn_id)
            base_url = conn.login if conn.login else "https://dagster.cloud/"
            if base_url == "https://dagster.cloud/":
                self.set_hook_for_cloud(conn)
            else:
                self.set_hook_for_oss(conn)

        if self.user_token is None:
            raise AirflowException(
                "Cannot get user_token: No valid user_token or dagster_conn_id supplied."
            )

        if self.url == "":
            raise AirflowException(
                "Cannot get dagster url: No valid url or dagster_conn_id supplied."
            )

    def set_hook_for_cloud(self, conn: Connection):
        self.organization_id = conn.description
        self.deployment_name = conn.host
        self.user_token = conn.get_password()
        base_url = conn.login if conn.login else "https://dagster.cloud/"
        if self.organization_id is None or self.deployment_name is None:
            raise AirflowException(
                "Dagster Cloud connection requires organization_id and deployment_name to be set"
            )
        self.url = f"{base_url}{self.organization_id}/{self.deployment_name}/graphql"

    def set_hook_for_oss(self, conn: Connection):
        self.url = cast(str, conn.login)

    def launch_run(
        self,
        repository_name: str = "my_dagster_project",
        repostitory_location_name: str = "example_location",
        job_name: str = "all_assets_job",
        run_config: Optional[Mapping[str, Any]] = None,
    ) -> str:
        query = """
mutation LaunchJobExecution($executionParams: ExecutionParams!) {
  launchPipelineExecution(executionParams: $executionParams) {
    __typename
    ... on LaunchRunSuccess {
      run {
        id
        __typename
      }
      __typename
    }
    ... on PipelineNotFoundError {
      message
      __typename
    }
    ... on InvalidSubsetError {
      message
      __typename
    }
    ... on RunConfigValidationInvalid {
      errors {
        message
        __typename
      }
      __typename
    }
    ...PythonErrorFragment
  }
}

fragment PythonErrorFragment on PythonError {
  __typename
  message
  stack
  causes {
    message
    stack
    __typename
  }
}
        """
        variables = {
            "executionParams": {
                "runConfigData": json.dumps({} if run_config is None else run_config),
                "selector": {
                    "repositoryName": repository_name,
                    "repositoryLocationName": repostitory_location_name,
                    "jobName": job_name,
                },
                "mode": "default",
                "executionMetadata": {"tags": [{"key": "dagster/solid_selection", "value": "*"}]},
            }
        }
        headers = {"Dagster-Cloud-Api-Token": self.user_token if self.user_token else ""}
        response = requests.post(
            url=self.url, json={"query": query, "variables": variables}, headers=headers
        )
        response.raise_for_status()
        response_json = response.json()
        if response_json["data"]["launchPipelineExecution"]["__typename"] == "LaunchRunSuccess":
            run = response_json["data"]["launchPipelineExecution"]["run"]
            logging.info(f"Run {run['id']} launched successfully")
            return run["id"]
        else:
            raise AirflowException(
                "Error launching run:"
                f" {response_json['data']['launchPipelineExecution']['message']}"
            )

    def wait_for_run(
        self,
        run_id: str,
    ) -> None:
        query = """
query RunQuery($runId: ID!) {
	runOrError(runId: $runId) {
		__typename
		...PythonErrorFragment
		...NotFoundFragment
		... on Run {
			id
			status
			__typename
		}
	}
}
fragment NotFoundFragment on RunNotFoundError {
	__typename
	message
}
fragment PythonErrorFragment on PythonError {
	__typename
	message
	stack
	causes {
		message
		stack
		__typename
	}
}
      """
        variables = {"runId": run_id}
        headers = {"Dagster-Cloud-Api-Token": self.user_token if self.user_token else ""}
        status = ""
        while status not in [
            DagsterRunStatus.SUCCESS.value,
            DagsterRunStatus.FAILURE.value,
            DagsterRunStatus.CANCELED.value,
        ]:
            response = requests.post(
                url=self.url, json={"query": query, "variables": variables}, headers=headers
            )
            response.raise_for_status()
            response_json = response.json()

            if response_json["data"]["runOrError"]["__typename"] == "Run":
                status = response_json["data"]["runOrError"]["status"]
            else:
                raise AirflowException(
                    f'Error fetching run status: {response_json["data"]["runOrError"]["message"]}'
                )

            if status == DagsterRunStatus.SUCCESS.value:
                logging.info(f"Run {run_id} completed successfully")
            elif status == DagsterRunStatus.FAILURE.value:
                raise AirflowException(f"Run {run_id} failed")
            elif status == DagsterRunStatus.CANCELED.value:
                raise AirflowException(f"Run {run_id} was cancelled")
            time.sleep(5)

    def terminate_run(
        self,
        run_id: str,
    ):
        query = """
mutation Terminate($runId: String!, $terminatePolicy: TerminateRunPolicy) {
  terminatePipelineExecution(runId: $runId, terminatePolicy: $terminatePolicy) {
    __typename
    ... on TerminateRunFailure {
      message
      __typename
    }
    ... on RunNotFoundError {
      message
      __typename
    }
    ... on TerminateRunSuccess {
      run {
        id
        runId
        canTerminate
        __typename
      }
      __typename
    }
    ...PythonErrorFragment
  }
}
fragment PythonErrorFragment on PythonError {
  __typename
  message
  stack
  causes {
    message
    stack
    __typename
  }
}
      """
        variables = {"runId": run_id, "terminatePolicy": "MARK_AS_CANCELED_IMMEDIATELY"}
        headers = {"Dagster-Cloud-Api-Token": self.user_token if self.user_token else ""}
        response = requests.post(
            url=self.url, json={"query": query, "variables": variables}, headers=headers
        )
        response.raise_for_status()
        response_json = response.json()

        if (
            response_json["data"]["terminatePipelineExecution"]["__typename"]
            != "TerminateRunSuccess"
        ):
            raise AirflowException(
                "Error terminating run:"
                f" {response_json['data']['terminatePipelineExecution']['message']}"
            )
