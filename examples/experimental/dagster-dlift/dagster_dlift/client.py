import time
from collections.abc import Iterator, Mapping, Sequence
from typing import Any, Optional

import requests

from dagster_dlift.gql_queries import (
    GET_DBT_MODELS_QUERY,
    GET_DBT_SOURCES_QUERY,
    GET_DBT_TESTS_QUERY,
    VERIFICATION_QUERY,
)

ENVIRONMENTS_SUBPATH = "environments/"
LIST_JOBS_INDIVIDUAL_REQUEST_LIMIT = 100


class UnscopedDbtCloudClient:
    def __init__(
        self,
        # Can be found on the Account Info page of dbt.
        account_id: int,
        # Can be either a personal token or a service token.
        token: str,
        # Can be found on the
        access_url: str,
        discovery_api_url: str,
    ):
        self.account_id = account_id
        self.token = token
        self.access_url = access_url
        self.discovery_api_url = discovery_api_url

    def get_api_v2_url(self) -> str:
        return f"{self.access_url}/api/v2/accounts/{self.account_id}"

    def get_discovery_api_url(self) -> str:
        return f"{self.discovery_api_url}/graphql"

    def get_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update(
            {
                "Accept": "application/json",
                "Authorization": f"Token {self.token}",
            }
        )
        return session

    def get_artifact_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update(
            {
                "Authorization": f"Token {self.token}",
                "Content-Type": "application/json",
            }
        )
        return session

    def make_access_api_request(
        self, subpath: str, params: Optional[Mapping[str, Any]] = None
    ) -> Mapping[str, Any]:
        session = self.get_session()
        return self.ensure_valid_response(
            session.get(f"{self.get_api_v2_url()}/{subpath}", params=params)
        ).json()

    def ensure_valid_response(
        self, response: requests.Response, expected_code: int = 200
    ) -> requests.Response:
        if response.status_code != expected_code:
            raise Exception(f"Request to DBT Cloud failed: {response.text}")
        return response

    def make_discovery_api_query(self, query: str, variables: Mapping[str, Any]):
        session = self.get_session()
        return self.ensure_valid_response(
            session.post(
                self.get_discovery_api_url(),
                json={"query": query, "variables": variables},
            )
        ).json()

    def list_environment_ids(self) -> Sequence[int]:
        return [
            environment["id"]
            for environment in self.make_access_api_request(ENVIRONMENTS_SUBPATH)["data"]
        ]

    def get_environment_id_by_name(self, environment_name: str) -> int:
        return next(
            iter(
                [
                    environment["id"]
                    for environment in self.make_access_api_request(ENVIRONMENTS_SUBPATH)["data"]
                    if environment["name"] == environment_name
                ]
            )
        )

    def verify_connections(self) -> None:
        # Verifies connection to both the access and discovery APIs.
        for environment_id in self.list_environment_ids():
            response = self.make_discovery_api_query(
                VERIFICATION_QUERY, {"environmentId": environment_id}
            )
            try:
                if response["data"]["environment"]["__typename"] != "Environment":
                    raise Exception(
                        f"Failed to verify connection to environment {environment_id}. Response: {response}"
                    )
            except KeyError:
                raise Exception(
                    f"Failed to verify connection to environment {environment_id}. Response: {response}"
                )

    def definition_response_iterator(
        self, query: str, variables: Mapping[str, Any], key: str
    ) -> Iterator[Mapping[str, Any]]:
        page_size = 100
        start_cursor = None
        while response := self.make_discovery_api_query(
            query,
            {**variables, "first": page_size, "after": start_cursor},
        ):
            yield from response["data"]["environment"]["definition"][key]["edges"]
            if not response["data"]["environment"]["definition"][key]["pageInfo"]["hasNextPage"]:
                break
            start_cursor = response["data"]["environment"]["definition"][key]["pageInfo"][
                "endCursor"
            ]

    def get_dbt_models(self, environment_id: int) -> Sequence[Mapping[str, Any]]:
        return [
            model["node"]
            for model in self.definition_response_iterator(
                GET_DBT_MODELS_QUERY, {"environmentId": environment_id}, key="models"
            )
        ]

    def get_dbt_sources(self, environment_id: int) -> Sequence[Mapping[str, Any]]:
        return [
            source["node"]
            for source in self.definition_response_iterator(
                GET_DBT_SOURCES_QUERY, {"environmentId": environment_id}, key="sources"
            )
        ]

    def get_dbt_tests(self, environment_id: int) -> Sequence[Mapping[str, Any]]:
        return [
            test["node"]
            for test in self.definition_response_iterator(
                GET_DBT_TESTS_QUERY, {"environmentId": environment_id}, key="tests"
            )
        ]

    def create_job(self, *, environment_id: int, project_id: int, job_name: str) -> int:
        """Creats a dbt cloud job spec'ed to do what dagster expects."""
        session = self.get_session()
        response = self.ensure_valid_response(
            session.post(
                f"{self.get_api_v2_url()}/jobs/",
                json={
                    "account_id": self.account_id,
                    "environment_id": environment_id,
                    "project_id": project_id,
                    "name": job_name,
                    "description": "A job that runs dbt models, sources, and tests.",
                    "job_type": "other",
                },
            ),
            expected_code=201,
        ).json()
        return response["data"]["id"]

    def destroy_dagster_job(self, job_id: int) -> None:
        """Destroys a dagster job."""
        session = self.get_session()
        self.ensure_valid_response(session.delete(f"{self.get_api_v2_url()}/jobs/{job_id}"))

    def destroy_job(self, job_id: int) -> None:
        session = self.get_session()
        self.ensure_valid_response(session.delete(f"{self.get_api_v2_url()}/jobs/{job_id}"))

    def get_job_info_by_id(self, job_id: int) -> Mapping[str, Any]:
        session = self.get_session()
        return self.ensure_valid_response(
            session.get(f"{self.get_api_v2_url()}/jobs/{job_id}")
        ).json()

    def list_jobs(self, environment_id: int) -> Sequence[Mapping[str, Any]]:
        results = []
        while jobs := self.make_access_api_request(
            "/jobs/",
            params={
                "environment_id": environment_id,
                "limit": LIST_JOBS_INDIVIDUAL_REQUEST_LIMIT,
                "offset": len(results),
            },
        )["data"]:
            results.extend(jobs)
            if len(jobs) < LIST_JOBS_INDIVIDUAL_REQUEST_LIMIT:
                break
        return results

    def trigger_job(self, job_id: int, steps: Optional[Sequence[str]] = None) -> Mapping[str, Any]:
        session = self.get_session()
        response = self.ensure_valid_response(
            session.post(
                f"{self.get_api_v2_url()}/jobs/{job_id}/run/",
                json={"steps_override": steps, "cause": "Triggered by dagster."},
            )
        )
        return response.json()

    def get_job_run_info(self, job_run_id: int) -> Mapping[str, Any]:
        session = self.get_session()
        return self.ensure_valid_response(
            session.get(f"{self.get_api_v2_url()}/runs/{job_run_id}")
        ).json()

    def poll_for_run_completion(self, job_run_id: int, timeout: int = 60) -> int:
        start_time = time.time()
        while time.time() - start_time < timeout:
            run_info = self.get_job_run_info(job_run_id)
            if run_info["data"]["status"] in {10, 20, 30}:
                return run_info["data"]["status"]
            time.sleep(0.1)
        raise Exception(f"Run {job_run_id} did not complete within {timeout} seconds.")

    def get_run_results_json(self, job_run_id: int) -> Mapping[str, Any]:
        session = self.get_artifact_session()
        return self.ensure_valid_response(
            session.get(f"{self.get_api_v2_url()}/runs/{job_run_id}/artifacts/run_results.json")
        ).json()
