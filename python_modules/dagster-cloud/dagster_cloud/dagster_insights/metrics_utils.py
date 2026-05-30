import os
import tempfile
from typing import NamedTuple

import requests
from dagster import AssetExecutionContext, DagsterInstance, OpExecutionContext
from dagster._annotations import beta
from dagster_cloud_cli.core.errors import raise_http_error
from dagster_cloud_cli.core.headers.auth import DagsterCloudInstanceScope

from dagster_cloud.instance import DagsterCloudAgentInstance


@beta
class DagsterMetric(NamedTuple):
    """Beta: This class gives information about a Metric.

    Args:
        metric_name (str): name of the metric
        metric_value (float): value of the metric
    """

    metric_name: str
    metric_value: float


def get_url_and_token_from_instance(instance: DagsterInstance) -> tuple[str, str]:
    if not isinstance(instance, DagsterCloudAgentInstance):
        raise RuntimeError("This asset only functions in a running Dagster Cloud instance")

    return f"{instance.dagit_url}graphql", instance.dagster_cloud_agent_token


def get_insights_upload_request_params(
    instance: DagsterInstance,
) -> tuple[requests.Session, str, dict[str, str], int, dict[str, str] | None]:
    if not isinstance(instance, DagsterCloudAgentInstance):
        raise RuntimeError("This asset only functions in a running Dagster Cloud instance")

    return (
        instance.requests_managed_retries_session,
        instance.dagster_cloud_gen_insights_url_url,
        instance.dagster_cloud_api_headers(DagsterCloudInstanceScope.DEPLOYMENT),
        instance.dagster_cloud_api_timeout,
        instance.dagster_cloud_api_proxies,
    )


def upload_cost_information(
    context: OpExecutionContext | AssetExecutionContext,
    metric_name: str,
    cost_information: list[tuple[str, float, str]],
):
    import pyarrow as pa
    import pyarrow.parquet as pq

    with tempfile.TemporaryDirectory() as temp_dir:
        opaque_ids = pa.array([opaque_id for opaque_id, _, _ in cost_information])
        costs = pa.array([cost for _, cost, _ in cost_information])
        query_ids = pa.array([query_id for _, _, query_id in cost_information])
        metric_names = pa.array([metric_name for _, _, _ in cost_information])

        cost_pq_file = os.path.join(temp_dir, "cost.parquet")
        pq.write_table(
            pa.Table.from_arrays(
                [opaque_ids, costs, metric_names, query_ids],
                ["opaque_id", "cost", "metric_name", "query_id"],
            ),
            cost_pq_file,
        )

        instance = context.instance
        session, url, headers, timeout, proxies = get_insights_upload_request_params(instance)

        resp = session.get(url, headers=headers, timeout=timeout, proxies=proxies)
        raise_http_error(resp)
        resp_data = resp.json()

        assert "url" in resp_data and "fields" in resp_data, resp_data

        with open(cost_pq_file, "rb") as f:
            session.post(
                resp_data["url"],
                data=resp_data["fields"],
                files={"file": f},
            )


@beta
def put_cost_information(
    context: OpExecutionContext | AssetExecutionContext,
    metric_name: str,
    cost_information: list[tuple[str, float, str]],
    start: float,
    end: float,
) -> None:
    try:
        upload_cost_information(context, metric_name, cost_information)
    except ImportError as e:
        raise Exception(
            "Dagster insights dependencies not installed. Install dagster-cloud[insights] to use this feature."
        ) from e
