import datetime
import json
import logging
import time
from typing import Any, Dict, List, Optional, cast
from urllib.parse import urlencode, urljoin

import requests
from requests.exceptions import RequestException

from dagster import Failure, Field, MetadataValue, StringSource, __version__
from dagster import _check as check
from dagster import get_dagster_logger, resource
from dagster._utils.merger import deep_merge_dicts

from .types import DbtCloudOutput

DBT_DEFAULT_HOST = "https://cloud.getdbt.com/"
DBT_ACCOUNTS_PATH = "api/v2/accounts/"

# default polling interval (in seconds)
DEFAULT_POLL_INTERVAL = 10


class DbtCloudResourceV2:
    """This class exposes methods on top of the dbt Cloud REST API v2.

    For a complete set of documentation on the dbt Cloud Administrative REST API, including expected
    response JSON schemae, see the `dbt Cloud API Docs <https://docs.getdbt.com/dbt-cloud/api-v2>`_.
    """

    def __init__(
        self,
        auth_token: str,
        account_id: int,
        disable_schedule_on_trigger: bool = True,
        request_max_retries: int = 3,
        request_retry_delay: float = 0.25,
        dbt_cloud_host: str = DBT_DEFAULT_HOST,
        log: logging.Logger = get_dagster_logger(),
        log_requests: bool = False,
    ):
        self._auth_token = auth_token
        self._account_id = account_id
        self._disable_schedule_on_trigger = disable_schedule_on_trigger

        self._request_max_retries = request_max_retries
        self._request_retry_delay = request_retry_delay

        self._dbt_cloud_host = dbt_cloud_host
        self._log = log
        self._log_requests = log_requests

    @property
    def api_base_url(self) -> str:
        return urljoin(self._dbt_cloud_host, DBT_ACCOUNTS_PATH)

    def make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        return_text: bool = False,
    ) -> Any:
        """
        Creates and sends a request to the desired dbt Cloud API endpoint.

        Args:
            method (str): The http method to use for this request (e.g. "POST", "GET", "PATCH").
            endpoint (str): The dbt Cloud API endpoint to send this request to.
            data (Optional[str]): JSON-formatted data string to be included in the request.
            return_text (bool): Override default behavior and return unparsed {"text": response.text}
                blob instead of json.
        Returns:
            Dict[str, Any]: Parsed json data from the response to this request
        """

        headers = {
            "User-Agent": f"dagster-dbt/{__version__}",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._auth_token}",
        }
        url = urljoin(self.api_base_url, endpoint)

        if self._log_requests:
            self._log.debug(f"Making Request: method={method} url={url} data={data}")

        num_retries = 0
        while True:
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    headers=headers,
                    data=json.dumps(data),
                    allow_redirects=False,
                )
                response.raise_for_status()
                return {"text": response.text} if return_text else response.json()["data"]
            except RequestException as e:
                self._log.error("Request to dbt Cloud API failed: %s", e)
                if num_retries == self._request_max_retries:
                    break
                num_retries += 1
                time.sleep(self._request_retry_delay)

        raise Failure("Exceeded max number of retries.")

    def get_job(self, job_id: int) -> Dict[str, Any]:
        """
        Gets details about a given dbt job from the dbt Cloud API.

        Args:
            job_id (int): The ID of the relevant dbt Cloud job. You can find this value by going to
                the details page of your job in the dbt Cloud UI. It will be the final number in the
                url, e.g.: ``https://cloud.getdbt.com/#/accounts/{account_id}/projects/{project_id}/jobs/{job_id}/``
        Returns:
            Dict[str, Any]: Parsed json data from the response to this request
        """
        return self.make_request("GET", f"{self._account_id}/jobs/{job_id}/")

    def update_job(self, job_id: int, **kwargs) -> Dict[str, Any]:
        """
        Updates specific properties of a dbt job. Documentation on the full set of potential
        parameters can be found here: https://docs.getdbt.com/dbt-cloud/api-v2#operation/updateJobById

        Args:
            job_id (int): The ID of the relevant dbt Cloud job. You can find this value by going to
                the details page of your job in the dbt Cloud UI. It will be the final number in the
                url, e.g.: ``https://cloud.getdbt.com/#/accounts/{account_id}/projects/{project_id}/jobs/{job_id}/``
            kwargs: Passed in as the properties to be changed.
        Returns:
            Dict[str, Any]: Parsed json data from the response to this request

        Examples:

        .. code-block:: python

            # disable schedule for job with id=12345
            my_dbt_cloud_resource.update_job(12345, triggers={"schedule": False})
        """
        # API requires you to supply a bunch of values, so we can just use the current state
        # as the defaults
        job_data = self.get_job(job_id)
        return self.make_request(
            "POST", f"{self._account_id}/jobs/{job_id}/", data=deep_merge_dicts(job_data, kwargs)
        )

    def run_job(self, job_id: int, **kwargs) -> Dict[str, Any]:
        """
        Initializes a run for a job. Overrides for specific properties can be set by passing in
        values to the kwargs. A full list of overridable properties can be found here:
        https://docs.getdbt.com/dbt-cloud/api-v2#operation/triggerRun

        Args:
            job_id (int): The ID of the relevant dbt Cloud job. You can find this value by going to
                the details page of your job in the dbt Cloud UI. It will be the final number in the
                url, e.g.: ``https://cloud.getdbt.com/#/accounts/{account_id}/projects/{project_id}/jobs/{job_id}/``
            kwargs: Passed in as the properties to be overridden.

        Returns:
            Dict[str, Any]: Parsed json data from the response to this request
        """
        if self._disable_schedule_on_trigger:
            self._log.info("Disabling dbt Cloud job schedule.")
            self.update_job(job_id, triggers={"schedule": False})
        self._log.info(f"Initializing run for job with job_id={job_id}")
        if "cause" not in kwargs:
            kwargs["cause"] = "Triggered via Dagster"
        resp = self.make_request("POST", f"{self._account_id}/jobs/{job_id}/run/", data=kwargs)
        self._log.info(
            f"Run initialized with run_id={resp['id']}. View this run in "
            f"the dbt Cloud UI: {resp['href']}"
        )
        return resp

    def get_runs(
        self,
        include_related: Optional[List[str]] = None,
        job_id: Optional[int] = None,
        order_by: Optional[str] = "-id",
        offset: int = 0,
        limit: int = 100,
    ) -> List[Dict[str, object]]:
        """
        Returns a list of runs from dbt Cloud. This can be optionally filtered to a specific job
        using the job_definition_id. It supports pagination using offset and limit as well and
        can be configured to load a variety of related information about the runs.

        Args:
            include_related (Optional[List[str]]): A list of resources to include in the response
                from dbt Cloud. This is technically a required field according to the API, but it
                can be passed with an empty list where it will only load the default run
                information. Valid values are "trigger", "job", "repository", and "environment".
            job_definition_id (Optional[int]): This method can be optionally filtered to only
                load runs for a specific job id if it is included here. If omitted it will pull
                runs for every job.
            order_by (Optional[str]): An identifier designated by dbt Cloud in which to sort the
                results before returning them. Useful when combined with offset and limit to load
                runs for a job. Defaults to "-id" where "-" designates reverse order and "id" is
                the key to filter on.
            offset (int): An offset to apply when listing runs. Can be used to paginate results
                when combined with order_by and limit. Defaults to 0.
            limit (int): Limits the amount of rows returned by the API. Defaults to 100.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing the runs and any included
                related information.
        """
        query_dict = {
            "include_related": include_related or [],
            "order_by": order_by,
            "offset": offset,
            "limit": limit,
        }
        if job_id:
            query_dict["job_definition_id"] = job_id
        return self.make_request("GET", f"{self._account_id}/runs/?{urlencode(query_dict)}")

    def get_run(self, run_id: int, include_related: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Gets details about a specific job run.

        Args:
            run_id (int): The ID of the relevant dbt Cloud run. You can find this value by going to
                the details page of your run in the dbt Cloud UI. It will be the final number in the
                url, e.g.: ``https://cloud.getdbt.com/#/accounts/{account_id}/projects/{project_id}/runs/{run_id}/``
            include_related (List[str]): List of related fields to pull with the run. Valid values
                are "trigger", "job", and "debug_logs".

        Returns:
            Dict[str, Any]: A dictionary containing the parsed contents of the dbt Cloud run details.
                See: https://docs.getdbt.com/dbt-cloud/api-v2#operation/getRunById for schema.
        """
        query_params = f"?include_related={','.join(include_related)}" if include_related else ""
        return self.make_request(
            "GET",
            f"{self._account_id}/runs/{run_id}/{query_params}",
        )

    def get_run_steps(self, run_id: int) -> List[str]:
        """
        Gets the steps of an initialized dbt Cloud run.

        Args:
            run_id (int): The ID of the relevant dbt Cloud run. You can find this value by going to
                the details page of your run in the dbt Cloud UI. It will be the final number in the
                url, e.g.: ``https://cloud.getdbt.com/#/accounts/{account_id}/projects/{project_id}/runs/{run_id}/``

        Returns:
            List[str, Any]: List of commands for each step of the run.
        """
        run_details = self.get_run(run_id, include_related=["trigger", "job"])
        steps = run_details["job"]["execute_steps"]
        steps_override = run_details["trigger"]["steps_override"]
        return steps_override or steps

    def cancel_run(self, run_id: int) -> Dict[str, Any]:
        """
        Cancels a dbt Cloud run.

        Args:
            run_id (int): The ID of the relevant dbt Cloud run. You can find this value by going to
                the details page of your run in the dbt Cloud UI. It will be the final number in the
                url, e.g.: ``https://cloud.getdbt.com/#/accounts/{account_id}/projects/{project_id}/runs/{run_id}/``

        Returns:
            Dict[str, Any]: A dictionary containing the parsed contents of the dbt Cloud run details.
                See: https://docs.getdbt.com/dbt-cloud/api-v2#operation/getRunById for schema.
        """
        self._log.info(f"Cancelling run with id '{run_id}'")
        return self.make_request("POST", f"{self._account_id}/runs/{run_id}/cancel/")

    def list_run_artifacts(self, run_id: int, step: Optional[int] = None) -> List[str]:
        """
        Lists the paths of the available run artifacts from a completed dbt Cloud run.

        Args:
            run_id (int): The ID of the relevant dbt Cloud run. You can find this value by going to
                the details page of your run in the dbt Cloud UI. It will be the final number in the
                url, e.g.: ``https://cloud.getdbt.com/#/accounts/{account_id}/projects/{project_id}/runs/{run_id}/``
            step (int): The index of the step in the run to query for artifacts. The first step in
                the run has the index 1. If the step parameter is omitted, then this endpoint will
                return the artifacts compiled for the last step in the run

        Returns:
            List[str]: List of the paths of the available run artifacts
        """
        query_params = f"?step={step}" if step else ""
        return cast(
            list,
            self.make_request(
                "GET",
                f"{self._account_id}/runs/{run_id}/artifacts/{query_params}",
                data={"step": step} if step else None,
            ),
        )

    def get_run_artifact(self, run_id: int, path: str, step: Optional[int] = None) -> str:
        """
        The string contents of a run artifact from a dbt Cloud run.

        Args:
            run_id (int): The ID of the relevant dbt Cloud run. You can find this value by going to
                the details page of your run in the dbt Cloud UI. It will be the final number in the
                url, e.g.: ``https://cloud.getdbt.com/#/accounts/{account_id}/projects/{project_id}/runs/{run_id}/``
            path (str): The path to this run artifact (e.g. 'run/my_new_project/models/example/my_first_dbt_model.sql')
            step (int): The index of the step in the run to query for artifacts. The first step in
                the run has the index 1. If the step parameter is omitted, then this endpoint will
                return the artifacts compiled for the last step in the run.

        Returns:
            List[str]: List of the names of the available run artifacts
        """
        query_params = f"?step={step}" if step else ""
        return self.make_request(
            "GET",
            f"{self._account_id}/runs/{run_id}/artifacts/{path}{query_params}",
            data={"step": step} if step else None,
            return_text=True,
        )["text"]

    def get_manifest(self, run_id: int, step: Optional[int] = None) -> Dict[str, Any]:
        """
        The parsed contents of a manifest.json file created by a completed run.

        Args:
            run_id (int): The ID of the relevant dbt Cloud run. You can find this value by going to
                the details page of your run in the dbt Cloud UI. It will be the final number in the
                url, e.g.: ``https://cloud.getdbt.com/#/accounts/{account_id}/projects/{project_id}/runs/{run_id}/``
            step (int): The index of the step in the run to query for artifacts. The first step in
                the run has the index 1. If the step parameter is omitted, then this endpoint will
                return the artifacts compiled for the last step in the run.

        Returns:
            Dict[str, Any]: Parsed contents of the manifest.json file
        """
        return json.loads(self.get_run_artifact(run_id, "manifest.json", step=step))

    def get_run_results(self, run_id: int, step: Optional[int] = None) -> Dict[str, Any]:
        """
        The parsed contents of a run_results.json file created by a completed run.

        Args:
            run_id (int): The ID of the relevant dbt Cloud run. You can find this value by going to
                the details page of your run in the dbt Cloud UI. It will be the final number in the
                url, e.g.: ``https://cloud.getdbt.com/#/accounts/{account_id}/projects/{project_id}/runs/{run_id}/``
            step (int): The index of the step in the run to query for artifacts. The first step in
                the run has the index 1. If the step parameter is omitted, then this endpoint will
                return the artifacts compiled for the last step in the run.

        Returns:
            Dict[str, Any]: Parsed contents of the run_results.json file
        """
        return json.loads(self.get_run_artifact(run_id, "run_results.json", step=step))

    def poll_run(
        self,
        run_id: int,
        poll_interval: float = DEFAULT_POLL_INTERVAL,
        poll_timeout: Optional[float] = None,
        href: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Polls a dbt Cloud job run until it completes. Will raise a `dagster.Failure` exception if the
        run does not complete successfully.

        Args:
            run_id (int): The ID of the relevant dbt Cloud run. You can find this value by going to
                the details page of your run in the dbt Cloud UI. It will be the final number in the
                url, e.g.: ``https://cloud.getdbt.com/#/accounts/{account_id}/projects/{project_id}/runs/{run_id}/``
            poll_interval (float): The time (in seconds) that should be waited between successive
                polls of the dbt Cloud API.
            poll_timeout (float): The maximum time (in seconds) that should be waited for this run
                to complete. If this threshold is exceeded, the run will be cancelled and an
                exception will be thrown. By default, this will poll forver.
            href (str): For internal use, generally should not be set manually.

        Returns:
            Dict[str, Any]: A dictionary containing the parsed contents of the dbt Cloud run details.
                See: https://docs.getdbt.com/dbt-cloud/api-v2#operation/getRunById for schema.
        """

        if href is None:
            href = self.get_run(run_id).get("href")
        assert isinstance(href, str), "Run must have an href"

        poll_start = datetime.datetime.now()
        while True:
            run_details = self.get_run(run_id)
            status = run_details["status_humanized"]
            self._log.info(f"Polled run {run_id}. Status: [{status}]")

            # completed successfully
            if status == "Success":
                return self.get_run(run_id, include_related=["job", "trigger"])
            elif status in ["Error", "Cancelled"]:
                break
            elif status not in ["Queued", "Starting", "Running"]:
                check.failed(f"Received unexpected status '{status}'. This should never happen")

            if poll_timeout and datetime.datetime.now() > poll_start + datetime.timedelta(
                seconds=poll_timeout
            ):
                self.cancel_run(run_id)
                raise Failure(
                    f"Run {run_id} timed out after "
                    f"{datetime.datetime.now() - poll_start}. Attempted to cancel.",
                    metadata={"run_page_url": MetadataValue.url(href)},
                )

            # Sleep for the configured time interval before polling again.
            time.sleep(poll_interval)

        run_details = self.get_run(run_id, include_related=["trigger"])
        raise Failure(
            f"Run {run_id} failed. Status Message: {run_details['status_message']}",
            metadata={
                "run_details": MetadataValue.json(run_details),
                "run_page_url": MetadataValue.url(href),
            },
        )

    def run_job_and_poll(
        self,
        job_id: int,
        poll_interval: float = DEFAULT_POLL_INTERVAL,
        poll_timeout: Optional[float] = None,
    ) -> DbtCloudOutput:
        """
        Runs a dbt Cloud job and polls until it completes. Will raise a `dagster.Failure` exception
        if the run does not complete successfully.

        Args:
            job_id (int): The ID of the relevant dbt Cloud job. You can find this value by going to
                the details page of your job in the dbt Cloud UI. It will be the final number in the
                url, e.g.: ``https://cloud.getdbt.com/#/accounts/{account_id}/projects/{project_id}/jobs/{job_id}/``
            poll_interval (float): The time (in seconds) that should be waited between successive
                polls of the dbt Cloud API.
            poll_timeout (float): The maximum time (in seconds) that should be waited for this run
                to complete. If this threshold is exceeded, the run will be cancelled and an
                exception will be thrown. By default, this will poll forver.

        Returns:
            :py:class:`~DbtCloudOutput`: Class containing details about the specific job run and the
                parsed run results.
        """
        run_details = self.run_job(job_id)
        run_id = run_details["id"]
        href = run_details["href"]
        final_run_details = self.poll_run(
            run_id, poll_interval=poll_interval, poll_timeout=poll_timeout, href=href
        )
        output = DbtCloudOutput(run_details=final_run_details, result=self.get_run_results(run_id))
        if output.docs_url:
            self._log.info(f"Docs for this run can be viewed here: {output.docs_url}")
        return output


@resource(
    config_schema={
        "auth_token": Field(
            StringSource,
            is_required=True,
            description="dbt Cloud API Token. User tokens can be found in the "
            "[dbt Cloud UI](https://cloud.getdbt.com/#/profile/api/), or see the "
            "[dbt Cloud Docs](https://docs.getdbt.com/docs/dbt-cloud/dbt-cloud-api/service-tokens) "
            "for instructions on creating a Service Account token.",
        ),
        "account_id": Field(
            int,
            is_required=True,
            description="dbt Cloud Account ID. This value can be found in the url of a variety of "
            "views in the dbt Cloud UI, e.g. https://cloud.getdbt.com/#/accounts/{account_id}/settings/.",
        ),
        "disable_schedule_on_trigger": Field(
            bool,
            default_value=True,
            description="Specifies if you would like any job that is triggered using this "
            "resource to automatically disable its schedule.",
        ),
        "request_max_retries": Field(
            int,
            default_value=3,
            description="The maximum number of times requests to the dbt Cloud API should be retried "
            "before failing.",
        ),
        "request_retry_delay": Field(
            float,
            default_value=0.25,
            description="Time (in seconds) to wait between each request retry.",
        ),
        "dbt_cloud_host": Field(
            config=StringSource,
            default_value=DBT_DEFAULT_HOST,
            description="The hostname where dbt cloud is being hosted (e.g. https://my_org.cloud.getdbt.com/).",
        ),
    },
    description="This resource helps interact with dbt Cloud connectors",
)
def dbt_cloud_resource(context) -> DbtCloudResourceV2:
    """
    This resource allows users to programatically interface with the dbt Cloud Administrative REST
    API (v2) to launch jobs and monitor their progress. This currently implements only a subset of
    the functionality exposed by the API.

    For a complete set of documentation on the dbt Cloud Administrative REST API, including expected
    response JSON schemae, see the `dbt Cloud API Docs <https://docs.getdbt.com/dbt-cloud/api-v2>`_.

    To configure this resource, we recommend using the `configured
    <https://docs.dagster.io/concepts/configuration/configured>`_ method.

    **Examples:**

    .. code-block:: python

        from dagster import job
        from dagster_dbt import dbt_cloud_resource

        my_dbt_cloud_resource = dbt_cloud_resource.configured(
            {
                "auth_token": {"env": "DBT_CLOUD_AUTH_TOKEN"},
                "account_id": 30000,
            }
        )

        @job(resource_defs={"dbt_cloud":my_dbt_cloud_resource})
        def my_dbt_cloud_job():
            ...
    """
    return DbtCloudResourceV2(
        auth_token=context.resource_config["auth_token"],
        account_id=context.resource_config["account_id"],
        disable_schedule_on_trigger=context.resource_config["disable_schedule_on_trigger"],
        request_max_retries=context.resource_config["request_max_retries"],
        request_retry_delay=context.resource_config["request_retry_delay"],
        log=context.log,
        dbt_cloud_host=context.resource_config["dbt_cloud_host"],
    )
