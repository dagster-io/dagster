import csv
import io
import os
import time
import uuid
from typing import Optional
from urllib.parse import urlparse

import boto3
from botocore.stub import Stubber
from dagster import (
    ConfigurableResource,
    _check as check,
    resource,
)
from dagster._annotations import deprecated
from dagster._core.definitions.resource_definition import dagster_maintained_resource
from dagster._core.execution.context.init import InitResourceContext
from pydantic import Field


class AthenaError(Exception):
    pass


class AthenaTimeout(AthenaError):
    pass


class AthenaClient:
    def __init__(self, client, workgroup="primary", polling_interval=5, max_polls=120):
        check.invariant(
            polling_interval >= 0, "polling_interval must be greater than or equal to 0"
        )
        check.invariant(max_polls > 0, "max_polls must be greater than 0")
        self.client = client
        self.workgroup = workgroup
        self.max_polls = max_polls
        self.polling_interval = polling_interval

    def execute_query(self, query, fetch_results=False):
        """Synchronously execute a single query against Athena. If fetch_results is set to true,
        will return a list of rows, where each row is a tuple of stringified values,
        e.g. SELECT 1 will return [("1",)].

        Args:
            query (str): The query to execute.
            fetch_results (Optional[bool]): Whether to return the results of executing the query.
                Defaults to False, in which case the query will be executed without retrieving the
                results.

        Returns:
            Optional[List[Tuple[Optional[str], ...]]]: Results of the query, as a list of tuples,
                when fetch_results is set. Otherwise, return None. All items in the tuple are
                represented as strings except for empty columns which are represented as None.
        """
        check.str_param(query, "query")
        check.bool_param(fetch_results, "fetch_results")
        execution_id = self.client.start_query_execution(
            QueryString=query, WorkGroup=self.workgroup
        )["QueryExecutionId"]
        self._poll(execution_id)
        if fetch_results:
            return self._results(execution_id)

    def _poll(self, execution_id):
        retries = self.max_polls
        state = "QUEUED"

        while retries > 0:
            execution = self.client.get_query_execution(QueryExecutionId=execution_id)[
                "QueryExecution"
            ]
            state = execution["Status"]["State"]
            if state not in ["QUEUED", "RUNNING"]:
                break

            retries -= 1
            time.sleep(self.polling_interval)

        if retries <= 0:
            raise AthenaTimeout()

        if state != "SUCCEEDED":
            raise AthenaError(execution["Status"]["StateChangeReason"])  # pyright: ignore[reportPossiblyUnboundVariable]

    def _results(self, execution_id):
        execution = self.client.get_query_execution(QueryExecutionId=execution_id)["QueryExecution"]
        s3 = boto3.resource("s3")
        output_location = execution["ResultConfiguration"]["OutputLocation"]
        bucket = urlparse(output_location).netloc
        prefix = urlparse(output_location).path.lstrip("/")

        results = []
        rows = s3.Bucket(bucket).Object(prefix).get()["Body"].read().decode("utf-8").splitlines()
        reader = csv.reader(rows)
        next(reader)  # Skip the CSV's header row
        for row in reader:
            results.append(tuple(row))

        return results


@deprecated(breaking_version="2.0", additional_warn_text="Use AthenaClientResource instead.")
class AthenaResource(AthenaClient):
    """This class was used by the function-style Athena resource."""


class FakeAthenaClient(AthenaClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.polling_interval = 0
        self.stubber = Stubber(self.client)

        s3 = boto3.resource("s3", region_name="us-east-1")
        self.bucket = s3.Bucket("fake-athena-results-bucket")
        self.bucket.create()

    def execute_query(
        self, query, fetch_results=False, expected_states=None, expected_results=None
    ):
        """Fake for execute_query; stubs the expected Athena endpoints, polls against the provided
        expected query execution states, and returns the provided results as a list of tuples.

        Args:
            query (str): The query to execute.
            fetch_results (Optional[bool]): Whether to return the results of executing the query.
                Defaults to False, in which case the query will be executed without retrieving the
                results.
            expected_states (list[str]): The expected query execution states.
                Defaults to successfully passing through QUEUED, RUNNING, and SUCCEEDED.
            expected_results ([List[Tuple[Any, ...]]]): The expected results. All non-None items
                are cast to strings.
                Defaults to [(1,)].

        Returns:
            Optional[List[Tuple[Optional[str], ...]]]: The expected_resutls when fetch_resutls is
                set. Otherwise, return None. All items in the tuple are represented as strings except
                for empty columns which are represented as None.
        """
        if not expected_states:
            expected_states = ["QUEUED", "RUNNING", "SUCCEEDED"]
        if not expected_results:
            expected_results = [("1",)]

        self.stubber.activate()

        execution_id = str(uuid.uuid4())
        self._stub_start_query_execution(execution_id, query)
        self._stub_get_query_execution(execution_id, expected_states)
        if expected_states[-1] == "SUCCEEDED" and fetch_results:
            self._fake_results(execution_id, expected_results)

        result = super().execute_query(query, fetch_results=fetch_results)

        self.stubber.deactivate()
        self.stubber.assert_no_pending_responses()

        return result

    def _stub_start_query_execution(self, execution_id, query):
        self.stubber.add_response(
            method="start_query_execution",
            service_response={"QueryExecutionId": execution_id},
            expected_params={"QueryString": query, "WorkGroup": self.workgroup},
        )

    def _stub_get_query_execution(self, execution_id, states):
        for state in states:
            self.stubber.add_response(
                method="get_query_execution",
                service_response={
                    "QueryExecution": {
                        "Status": {"State": state, "StateChangeReason": "state change reason"},
                    }
                },
                expected_params={"QueryExecutionId": execution_id},
            )

    def _fake_results(self, execution_id, expected_results):
        with io.StringIO() as results:
            writer = csv.writer(results)
            # Athena adds a header row to its CSV output
            writer.writerow([])
            for row in expected_results:
                # Athena writes all non-null columns as strings in its CSV output
                stringified = tuple([str(item) for item in row if item])
                writer.writerow(stringified)
            results.seek(0)

            self.bucket.Object(execution_id + ".csv").put(Body=results.read())

        self.stubber.add_response(
            method="get_query_execution",
            service_response={
                "QueryExecution": {
                    "ResultConfiguration": {
                        "OutputLocation": os.path.join(
                            "s3://", self.bucket.name, execution_id + ".csv"
                        )
                    }
                }
            },
            expected_params={"QueryExecutionId": execution_id},
        )


@deprecated(breaking_version="2.0", additional_warn_text="Use FakeAthenaClientResource instead.")
class FakeAthenaResource(FakeAthenaClient):
    """This class was used by the function-style fake Athena resource."""


class ResourceWithAthenaConfig(ConfigurableResource):
    workgroup: str = Field(
        default="primary",
        description=(
            "The Athena WorkGroup to use."
            " https://docs.aws.amazon.com/athena/latest/ug/manage-queries-control-costs-with-workgroups.html"
        ),
    )
    polling_interval: int = Field(
        default=5,
        description=(
            "Time in seconds between checks to see if a query execution is finished. 5 seconds"
            " by default. Must be non-negative."
        ),
    )
    max_polls: int = Field(
        default=120,
        description=(
            "Number of times to poll before timing out. 120 attempts by default. When coupled"
            " with the default polling_interval, queries will timeout after 10 minutes (120 * 5"
            " seconds). Must be greater than 0."
        ),
    )
    aws_access_key_id: Optional[str] = Field(
        default=None, description="AWS access key ID for authentication purposes."
    )
    aws_secret_access_key: Optional[str] = Field(
        default=None, description="AWS secret access key for authentication purposes."
    )


class AthenaClientResource(ResourceWithAthenaConfig):
    """This resource enables connecting to AWS Athena and issuing queries against it.

    Example:
        .. code-block:: python

                from dagster import Definitions, asset
                from dagster_aws.athena import AthenaClientResource

                @asset
                def example_athena_asset(athena: AthenaClientResource):
                    return athena.get_client().execute_query("SELECT 1", fetch_results=True)

                defs = Definitions(
                    assets=[example_athena_asset],
                    resources={"athena": AthenaClientResource()}
                )

    """

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    def get_client(self) -> AthenaClient:
        """Returns an Athena client object."""
        client = boto3.client(
            "athena",
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
        )
        return AthenaClient(
            client=client,
            workgroup=self.workgroup,
            polling_interval=self.polling_interval,
            max_polls=self.max_polls,
        )


@dagster_maintained_resource
@resource(
    config_schema=ResourceWithAthenaConfig.to_config_schema(),
    description="Resource for connecting to AWS Athena",
)
def athena_resource(context: InitResourceContext) -> AthenaClient:
    """This resource enables connecting to AWS Athena and issuing queries against it.

    Example:
        .. code-block:: python

                from dagster import build_op_context, op
                from dagster_aws.athena import athena_resource

                @op(required_resource_keys={"athena"})
                def example_athena_op(context):
                    return context.resources.athena.execute_query("SELECT 1", fetch_results=True)

                context = build_op_context(resources={"athena": athena_resource})
                assert example_athena_op(context) == [("1",)]

    """
    return AthenaClientResource.from_resource_context(context).get_client()


@dagster_maintained_resource
@resource(
    config_schema=ResourceWithAthenaConfig.to_config_schema(),
    description="Fake resource for connecting to AWS Athena",
)
def fake_athena_resource(context: InitResourceContext) -> AthenaClient:
    return FakeAthenaClient(
        client=boto3.client("athena", region_name="us-east-1"),
        workgroup=context.resource_config.get("workgroup"),
        polling_interval=context.resource_config.get("polling_interval"),
        max_polls=context.resource_config.get("max_polls"),
    )
