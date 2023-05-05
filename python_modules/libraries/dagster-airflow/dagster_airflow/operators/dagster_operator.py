import json

from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults

from dagster_airflow.hooks.dagster_hook import DagsterHook
from dagster_airflow.links.dagster_link import LINK_FMT, DagsterLink
from dagster_airflow.utils import is_airflow_2_loaded_in_environment


class DagsterOperator(BaseOperator):
    """DagsterOperator.

    Uses the dagster graphql api to run and monitor dagster jobs on remote dagster infrastructure

    Parameters:
        repository_name (str): the name of the repository to use
        repostitory_location_name (str): the name of the repostitory location to use
        job_name (str): the name of the job to run
        run_config (Optional[Dict[str, Any]]): the run config to use for the job run
        dagster_conn_id (Optional[str]): the id of the dagster connection, airflow 2.0+ only
        organization_id (Optional[str]): the id of the dagster cloud organization
        deployment_name (Optional[str]): the name of the dagster cloud deployment
        user_token (Optional[str]): the dagster cloud user token to use
    """

    template_fields = ["run_config"]
    template_ext = (".yaml", ".yml", ".json")
    ui_color = "#663399"
    ui_fgcolor = "#e0e3fc"
    operator_extra_links = (DagsterLink(),)

    @apply_defaults
    def __init__(
        self,
        dagster_conn_id="dagster_default",
        run_config=None,
        repository_name="",
        repostitory_location_name="",
        job_name="",
        # params for airflow < 2.0.0 were custom connections aren't supported
        deployment_name="prod",
        user_token=None,
        organization_id="",
        url="https://dagster.cloud/",
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.run_id = None
        self.dagster_conn_id = dagster_conn_id if is_airflow_2_loaded_in_environment() else None
        self.run_config = run_config or {}
        self.repository_name = repository_name
        self.repostitory_location_name = repostitory_location_name
        self.job_name = job_name

        self.user_token = user_token
        self.url = url
        self.organization_id = organization_id
        self.deployment_name = deployment_name

        self.hook = DagsterHook(
            dagster_conn_id=self.dagster_conn_id,
            user_token=self.user_token,
            url=f"{self.url}{self.organization_id}/{self.deployment_name}/graphql",
        )

    def _is_json(self, blob):
        try:
            json.loads(blob)
        except ValueError:
            return False
        return True

    def pre_execute(self, context):
        # force re-rendering to ensure run_config renders any templated
        # content from run_config that couldn't be accessed on init
        setattr(
            self,
            "run_config",
            self.render_template(self.run_config, context),
        )

    def on_kill(self):
        self.log.info("Terminating Run")
        self.hook.terminate_run(
            run_id=self.run_id,
        )

    def execute(self, context):
        try:
            return self._execute(context)
        except Exception as e:
            raise e

    def _execute(self, context):
        self.run_id = self.hook.launch_run(
            repository_name=self.repository_name,
            repostitory_location_name=self.repostitory_location_name,
            job_name=self.job_name,
            run_config=self.run_config,
        )
        # save relevant info in xcom for use in links
        context["task_instance"].xcom_push(key="run_id", value=self.run_id)
        context["task_instance"].xcom_push(
            key="organization_id",
            value=self.hook.organization_id if self.dagster_conn_id else self.organization_id,
        )
        context["task_instance"].xcom_push(
            key="deployment_name",
            value=self.hook.deployment_name if self.dagster_conn_id else self.deployment_name,
        )

        self.log.info("Run Starting....")
        self.log.info(
            "Run tracking: %s",
            LINK_FMT.format(
                organization_id=self.hook.organization_id,
                deployment_name=self.hook.deployment_name,
                run_id=self.run_id,
            ),
        )
        self.hook.wait_for_run(
            run_id=self.run_id,
        )


class DagsterCloudOperator(DagsterOperator):
    """DagsterCloudOperator.

    Uses the dagster cloud graphql api to run and monitor dagster jobs on dagster cloud

    Parameters:
        repository_name (str): the name of the repository to use
        repostitory_location_name (str): the name of the repostitory location to use
        job_name (str): the name of the job to run
        run_config (Optional[Dict[str, Any]]): the run config to use for the job run
        dagster_conn_id (Optional[str]): the id of the dagster connection, airflow 2.0+ only
        organization_id (Optional[str]): the id of the dagster cloud organization
        deployment_name (Optional[str]): the name of the dagster cloud deployment
        user_token (Optional[str]): the dagster cloud user token to use
    """
