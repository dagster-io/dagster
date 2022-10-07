from airflow.models import BaseOperatorLink, TaskInstance

LINK_FMT = "https://dagster.cloud/{organization_id}/{deployment_name}/instance/runs/{run_id}"


class DagsterLink(BaseOperatorLink):
    name = "Dagster Cloud"

    def get_link(self, operator, dttm):
        ti = TaskInstance(task=operator, execution_date=dttm)
        run_id = ti.xcom_pull(task_ids=operator.task_id, key="run_id")
        organization_id = ti.xcom_pull(task_ids=operator.task_id, key="organization_id")
        deployment_name = ti.xcom_pull(task_ids=operator.task_id, key="deployment_name")

        if run_id and organization_id and deployment_name:
            return LINK_FMT.format(
                organization_id=organization_id, deployment_name=deployment_name, run_id=run_id
            )
        else:
            return ""
