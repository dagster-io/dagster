import datetime
import smtplib
import ssl
from typing import TYPE_CHECKING, Callable, List, Optional, Union

from dagster.core.definitions.sensor_definition import DefaultSensorStatus
from dagster.core.errors import DagsterInvalidDefinitionError

if TYPE_CHECKING:
    from dagster.core.definitions.graph_definition import GraphDefinition
    from dagster.core.definitions.pipeline_definition import PipelineDefinition
    from dagster.core.definitions.run_status_sensor_definition import (
        PipelineFailureSensorContext,
        RunFailureSensorContext,
    )


def _default_failure_email_body(context) -> str:
    return "<br>".join(
        [
            f"Pipeline {context.pipeline_run.pipeline_name} failed!",
            f"Run ID: {context.pipeline_run.run_id}",
            f"Mode: {context.pipeline_run.mode}",
            f"Error: {context.failure_event.message}",
        ]
    )


def _default_failure_email_subject(context) -> str:
    return f"Dagster Run Failed: {context.pipeline_run.pipeline_name}"


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
    email_to: List[str],
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
    email_to: List[str],
    message: str,
    smtp_host: str,
    smtp_port: int,
):
    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls(context=context)
        server.login(email_from, email_password)
        server.sendmail(email_from, email_to, message)


def make_email_on_pipeline_failure_sensor(
    email_from: str,
    email_password: str,
    email_to: List[str],
    email_body_fn: Callable[["PipelineFailureSensorContext"], str] = _default_failure_email_body,
    email_subject_fn: Callable[
        ["PipelineFailureSensorContext"], str
    ] = _default_failure_email_subject,
    smtp_host: str = "smtp.gmail.com",
    smtp_type: str = "SSL",
    smtp_port: Optional[int] = None,
    pipeline_selection: Optional[List[str]] = None,
    name: Optional[str] = None,
    dagit_base_url: Optional[str] = None,
    default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED,
):
    """Create a pipeline failure sensor that sends email via the SMTP protocol.

    Args:
        email_from (str): The sender email address to send the message from.
        email_password (str): The password of the sender.
        email_to (List[str]): The receipt email addresses to send the message to.
        email_body_fn (Optional(Callable[[PipelineFailureSensorContext], str])): Function which
            takes in the ``PipelineFailureSensorContext`` outputs the email body you want to send.
            Defaults to the plain text that contains error message, pipeline name, and run ID.
        email_subject_fn (Optional(Callable[[PipelineFailureSensorContext], str])): Function which
            takes in the ``PipelineFailureSensorContext`` outputs the email subject you want to send.
            Defaults to "Dagster Run Failed: <pipeline_name>".
        smtp_host (str): The hostname of the SMTP server. Defaults to "smtp.gmail.com".
        smtp_type (str): The protocol; either "SSL" or "STARTTLS". Defaults to SSL.
        smtp_port (Optional[int]): The SMTP port. Defaults to 465 for SSL, 587 for STARTTLS.
        pipeline_selection (Optional[List[str]]): Names of the pipelines that will be monitored by
            this failure sensor. Defaults to None, which means the alert will be sent when any
            pipeline in the repository fails.
        name: (Optional[str]): The name of the sensor. Defaults to "email_on_pipeline_failure".
        dagit_base_url: (Optional[str]): The base url of your Dagit instance. Specify this to allow
            messages to include deeplinks to the failed pipeline run.
        default_status (DefaultSensorStatus): Whether the sensor starts as running or not. The default
            status can be overridden from Dagit or via the GraphQL API.
    Examples:

        .. code-block:: python

            email_on_pipeline_failure = make_email_on_pipeline_failure_sensor(
                email_from="no-reply@example.com",
                email_password=os.getenv("ALERT_EMAIL_PASSWORD"),
                email_to=["xxx@example.com"],
            )

            @repository
            def my_repo():
                return [my_pipeline + email_on_pipeline_failure]

        .. code-block:: python

            def my_message_fn(context: PipelineFailureSensorContext) -> str:
                return "Pipeline {pipeline_name} failed! Error: {error}".format(
                    pipeline_name=context.pipeline_run.pipeline_name,
                    error=context.failure_event.message,
                )

            email_on_pipeline_failure = make_email_on_pipeline_failure_sensor(
                email_from="no-reply@example.com",
                email_password=os.getenv("ALERT_EMAIL_PASSWORD"),
                email_to=["xxx@example.com"],
                email_body_fn=my_message_fn,
                email_subject_fn=lambda _: "Dagster Alert",
                dagit_base_url="http://mycoolsite.com",
            )


    """

    from dagster.core.definitions.run_status_sensor_definition import (
        PipelineFailureSensorContext,
        pipeline_failure_sensor,
    )

    @pipeline_failure_sensor(
        name=name, pipeline_selection=pipeline_selection, default_status=default_status
    )
    def email_on_pipeline_failure(context: PipelineFailureSensorContext):

        email_body = email_body_fn(context)
        if dagit_base_url:
            email_body += f'<p><a href="{dagit_base_url}/instance/runs/{context.pipeline_run.run_id}">View in Dagit</a></p>'

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

    return email_on_pipeline_failure


def make_email_on_run_failure_sensor(
    email_from: str,
    email_password: str,
    email_to: List[str],
    email_body_fn: Callable[["RunFailureSensorContext"], str] = _default_failure_email_body,
    email_subject_fn: Callable[["RunFailureSensorContext"], str] = _default_failure_email_subject,
    smtp_host: str = "smtp.gmail.com",
    smtp_type: str = "SSL",
    smtp_port: Optional[int] = None,
    name: Optional[str] = None,
    dagit_base_url: Optional[str] = None,
    job_selection: Optional[List[Union["PipelineDefinition", "GraphDefinition"]]] = None,
    default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED,
):
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
        dagit_base_url: (Optional[str]): The base url of your Dagit instance. Specify this to allow
            messages to include deeplinks to the failed run.
        job_selection (Optional[List[Union[JobDefinition, GraphDefinition, PipelineDefinition]]]): The jobs that
            will be monitored by this failure sensor. Defaults to None, which means the alert will
            be sent when any job in the repository fails.
        default_status (DefaultSensorStatus): Whether the sensor starts as running or not. The default
            status can be overridden from Dagit or via the GraphQL API.

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
                    f"Job {context.pipeline_run.pipeline_name} failed!"
                    f"Error: {context.failure_event.message}"
                )

            email_on_run_failure = make_email_on_run_failure_sensor(
                email_from="no-reply@example.com",
                email_password=os.getenv("ALERT_EMAIL_PASSWORD"),
                email_to=["xxx@example.com"],
                email_body_fn=my_message_fn,
                email_subject_fn=lambda _: "Dagster Alert",
                dagit_base_url="http://mycoolsite.com",
            )


    """

    from dagster.core.definitions.run_status_sensor_definition import (
        RunFailureSensorContext,
        run_failure_sensor,
    )

    @run_failure_sensor(name=name, job_selection=job_selection, default_status=default_status)
    def email_on_run_failure(context: RunFailureSensorContext):

        email_body = email_body_fn(context)
        if dagit_base_url:
            email_body += f'<p><a href="{dagit_base_url}/instance/runs/{context.pipeline_run.run_id}">View in Dagit</a></p>'

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
