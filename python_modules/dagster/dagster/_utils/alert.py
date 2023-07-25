import datetime
import smtplib
import ssl
from typing import TYPE_CHECKING, Callable, Optional, Sequence, Union

from dagster._core.definitions.sensor_definition import DefaultSensorStatus, SensorDefinition
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._utils.backcompat import deprecation_warning

if TYPE_CHECKING:
    from dagster._core.definitions.graph_definition import GraphDefinition
    from dagster._core.definitions.job_definition import JobDefinition
    from dagster._core.definitions.run_status_sensor_definition import RunFailureSensorContext
    from dagster._core.definitions.selector import JobSelector, RepositorySelector
    from dagster._core.definitions.unresolved_asset_job_definition import (
        UnresolvedAssetJobDefinition,
    )


def _default_failure_email_body(context: "RunFailureSensorContext") -> str:
    from dagster._core.host_representation.external_data import DEFAULT_MODE_NAME

    return "<br>".join(
        [
            f"Pipeline {context.dagster_run.job_name} failed!",
            f"Run ID: {context.dagster_run.run_id}",
            f"Mode: {DEFAULT_MODE_NAME}",
            f"Error: {context.failure_event.message}",
        ]
    )


def _default_failure_email_subject(context) -> str:
    return f"Dagster Run Failed: {context.pipeline_run.job_name}"


EMAIL_MESSAGE = """From: {email_from}
To: {email_to}
MIME-Version: 1.0
Content-type: text/html
Subject: {email_subject}

{email_body}

<!-- this ensures Gmail doesn't trim the email -->
<span style="opacity: 0"> {randomness} </span>
"""


def send_email_via_ssl(
    email_from: str,
    email_password: str,
    email_to: Sequence[str],
    message: str,
    smtp_host: str,
    smtp_port: int,
):
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as server:
        server.login(email_from, email_password)
        server.sendmail(email_from, email_to, message)


def send_email_via_starttls(
    email_from: str,
    email_password: str,
    email_to: Sequence[str],
    message: str,
    smtp_host: str,
    smtp_port: int,
):
    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls(context=context)
        server.login(email_from, email_password)
        server.sendmail(email_from, email_to, message)


def make_email_on_run_failure_sensor(
    email_from: str,
    email_password: str,
    email_to: Sequence[str],
    email_body_fn: Callable[["RunFailureSensorContext"], str] = _default_failure_email_body,
    email_subject_fn: Callable[["RunFailureSensorContext"], str] = _default_failure_email_subject,
    smtp_host: str = "smtp.gmail.com",
    smtp_type: str = "SSL",
    smtp_port: Optional[int] = None,
    name: Optional[str] = None,
    webserver_base_url: Optional[str] = None,
    monitored_jobs: Optional[
        Sequence[
            Union[
                "JobDefinition",
                "GraphDefinition",
                "UnresolvedAssetJobDefinition",
                "RepositorySelector",
                "JobSelector",
            ]
        ]
    ] = None,
    job_selection: Optional[
        Sequence[
            Union[
                "JobDefinition",
                "GraphDefinition",
                "UnresolvedAssetJobDefinition",
                "RepositorySelector",
                "JobSelector",
            ]
        ]
    ] = None,
    monitor_all_repositories: bool = False,
    default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED,
) -> SensorDefinition:
    """Create a job failure sensor that sends email via the SMTP protocol.

    Args:
        email_from (str): The sender email address to send the message from.
        email_password (str): The password of the sender.
        email_to (List[str]): The receipt email addresses to send the message to.
        email_body_fn (Optional(Callable[[RunFailureSensorContext], str])): Function which
            takes in the ``RunFailureSensorContext`` outputs the email body you want to send.
            Defaults to the plain text that contains error message, job name, and run ID.
        email_subject_fn (Optional(Callable[[RunFailureSensorContext], str])): Function which
            takes in the ``RunFailureSensorContext`` outputs the email subject you want to send.
            Defaults to "Dagster Run Failed: <job_name>".
        smtp_host (str): The hostname of the SMTP server. Defaults to "smtp.gmail.com".
        smtp_type (str): The protocol; either "SSL" or "STARTTLS". Defaults to SSL.
        smtp_port (Optional[int]): The SMTP port. Defaults to 465 for SSL, 587 for STARTTLS.
        name: (Optional[str]): The name of the sensor. Defaults to "email_on_job_failure".
        webserver_base_url: (Optional[str]): The base url of your dagster-webserver instance. Specify this to allow
            messages to include deeplinks to the failed run.
        monitored_jobs (Optional[List[Union[JobDefinition, GraphDefinition, JobDefinition, RepositorySelector, JobSelector]]]):
            The jobs that will be monitored by this failure sensor. Defaults to None, which means the alert will
            be sent when any job in the repository fails. To monitor jobs in external repositories,
            use RepositorySelector and JobSelector.
        monitor_all_repositories (bool): If set to True, the sensor will monitor all runs in the
            Dagster instance. If set to True, an error will be raised if you also specify
            monitored_jobs or job_selection. Defaults to False.
        job_selection (Optional[List[Union[JobDefinition, GraphDefinition, JobDefinition,  RepositorySelector, JobSelector]]]):
            (deprecated in favor of monitored_jobs) The jobs that will be monitored by this failure
            sensor. Defaults to None, which means the alert will be sent when any job in the repository fails.
        default_status (DefaultSensorStatus): Whether the sensor starts as running or not. The default
            status can be overridden from the Dagster UI or via the GraphQL API.

    Examples:
        .. code-block:: python

            email_on_run_failure = make_email_on_run_failure_sensor(
                email_from="no-reply@example.com",
                email_password=os.getenv("ALERT_EMAIL_PASSWORD"),
                email_to=["xxx@example.com"],
            )

            @repository
            def my_repo():
                return [my_job + email_on_run_failure]

        .. code-block:: python

            def my_message_fn(context: RunFailureSensorContext) -> str:
                return (
                    f"Job {context.pipeline_run.job_name} failed!"
                    f"Error: {context.failure_event.message}"
                )

            email_on_run_failure = make_email_on_run_failure_sensor(
                email_from="no-reply@example.com",
                email_password=os.getenv("ALERT_EMAIL_PASSWORD"),
                email_to=["xxx@example.com"],
                email_body_fn=my_message_fn,
                email_subject_fn=lambda _: "Dagster Alert",
                webserver_base_url="http://mycoolsite.com",
            )


    """
    from dagster._core.definitions.run_status_sensor_definition import (
        RunFailureSensorContext,
        run_failure_sensor,
    )

    if job_selection:
        deprecation_warning("job_selection", "2.0.0", "Use monitored_jobs instead.")
    jobs = monitored_jobs if monitored_jobs else job_selection

    @run_failure_sensor(
        name=name,
        monitored_jobs=jobs,
        default_status=default_status,
        monitor_all_repositories=monitor_all_repositories,
    )
    def email_on_run_failure(context: RunFailureSensorContext):
        email_body = email_body_fn(context)
        if webserver_base_url:
            email_body += (
                f'<p><a href="{webserver_base_url}/runs/{context.dagster_run.run_id}">View in'
                " the Dagster UI</a></p>"
            )

        message = EMAIL_MESSAGE.format(
            email_to=",".join(email_to),
            email_from=email_from,
            email_subject=email_subject_fn(context),
            email_body=email_body,
            randomness=datetime.datetime.now(),
        )

        if smtp_type == "SSL":
            send_email_via_ssl(
                email_from, email_password, email_to, message, smtp_host, smtp_port=smtp_port or 465
            )
        elif smtp_type == "STARTTLS":
            send_email_via_starttls(
                email_from, email_password, email_to, message, smtp_host, smtp_port=smtp_port or 587
            )
        else:
            raise DagsterInvalidDefinitionError(f'smtp_type "{smtp_type}" is not supported.')

    return email_on_run_failure
