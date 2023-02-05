import datetime
import importlib
from contextlib import contextmanager, nullcontext
from unittest.mock import patch

import airflow
import dateutil
import lazy_object_proxy
import pendulum
from airflow import __version__ as airflow_version
from airflow.models import TaskInstance
from airflow.models.baseoperator import BaseOperator
from airflow.models.dag import DAG
from dagster import (
    DagsterInvariantViolationError,
    DependencyDefinition,
    Field,
    In,
    MultiDependencyDefinition,
    Nothing,
    Out,
    RetryPolicy,
    _check as check,
    op,
)
from dagster._core.definitions.op_definition import OpDefinition
from dagster._core.instance import AIRFLOW_EXECUTION_DATE_STR

from dagster_airflow.utils import normalized_name, replace_airflow_logger_handlers


def get_pipeline_definition_args(
    dag,
    use_airflow_template_context,
    unique_id=None,
    mock_xcom=False,
    use_ephemeral_airflow_db=False,
):
    check.inst_param(dag, "dag", DAG)
    check.bool_param(use_airflow_template_context, "use_airflow_template_context")
    unique_id = check.opt_int_param(unique_id, "unique_id")
    mock_xcom = check.opt_bool_param(mock_xcom, "mock_xcom")
    use_ephemeral_airflow_db = check.opt_bool_param(
        use_ephemeral_airflow_db, "use_ephemeral_airflow_db"
    )

    pipeline_dependencies = {}
    solid_defs = []
    seen_tasks = []

    # To enforce predictable iteration order
    dag_roots = sorted(dag.roots, key=lambda x: x.task_id)
    for task in dag_roots:
        _traverse_airflow_dag(
            dag=dag,
            task=task,
            seen_tasks=seen_tasks,
            pipeline_dependencies=pipeline_dependencies,
            solid_defs=solid_defs,
            use_airflow_template_context=use_airflow_template_context,
            unique_id=unique_id,
            mock_xcom=mock_xcom,
            use_ephemeral_airflow_db=use_ephemeral_airflow_db,
        )
    return (pipeline_dependencies, solid_defs)


def _traverse_airflow_dag(
    dag,
    task,
    seen_tasks,
    pipeline_dependencies,
    solid_defs,
    use_airflow_template_context,
    unique_id,
    mock_xcom,
    use_ephemeral_airflow_db,
):
    check.inst_param(dag, "dag", DAG)
    check.inst_param(task, "task", BaseOperator)
    check.list_param(seen_tasks, "seen_tasks", BaseOperator)
    check.list_param(solid_defs, "solid_defs", OpDefinition)
    check.bool_param(use_airflow_template_context, "use_airflow_template_context")
    unique_id = check.opt_int_param(unique_id, "unique_id")
    mock_xcom = check.opt_bool_param(mock_xcom, "mock_xcom")
    use_ephemeral_airflow_db = check.opt_bool_param(
        use_ephemeral_airflow_db, "use_ephemeral_airflow_db"
    )

    seen_tasks.append(task)
    current_solid = make_dagster_solid_from_airflow_task(
        dag=dag,
        task=task,
        use_airflow_template_context=use_airflow_template_context,
        unique_id=unique_id,
        mock_xcom=mock_xcom,
        use_ephemeral_airflow_db=use_ephemeral_airflow_db,
    )
    solid_defs.append(current_solid)

    if len(task.upstream_list) > 0:
        # To enforce predictable iteration order
        task_upstream_list = sorted(task.upstream_list, key=lambda x: x.task_id)

        pipeline_dependencies[current_solid.name] = {
            "airflow_task_ready": MultiDependencyDefinition(
                [
                    DependencyDefinition(
                        solid=normalized_name(task_upstream.task_id, unique_id),
                        output="airflow_task_complete",
                    )
                    for task_upstream in task_upstream_list
                ]
            )
        }

    # To enforce predictable iteration order
    task_downstream_list = sorted(task.downstream_list, key=lambda x: x.task_id)
    for child_task in task_downstream_list:
        if child_task not in seen_tasks:
            _traverse_airflow_dag(
                dag=dag,
                task=child_task,
                seen_tasks=seen_tasks,
                pipeline_dependencies=pipeline_dependencies,
                solid_defs=solid_defs,
                use_airflow_template_context=use_airflow_template_context,
                unique_id=unique_id,
                mock_xcom=mock_xcom,
                use_ephemeral_airflow_db=use_ephemeral_airflow_db,
            )


@contextmanager
def _mock_xcom():
    with patch("airflow.models.TaskInstance.xcom_push"):
        with patch("airflow.models.TaskInstance.xcom_pull"):
            yield


# If unique_id is not None, this id will be postpended to generated solid names, generally used
# to enforce unique solid names within a repo.
def make_dagster_solid_from_airflow_task(
    dag,
    task,
    use_airflow_template_context,
    unique_id=None,
    mock_xcom=False,
    use_ephemeral_airflow_db=False,
):
    check.inst_param(dag, "dag", DAG)
    check.inst_param(task, "task", BaseOperator)
    check.bool_param(use_airflow_template_context, "use_airflow_template_context")
    unique_id = check.opt_int_param(unique_id, "unique_id")
    mock_xcom = check.opt_bool_param(mock_xcom, "mock_xcom")
    use_ephemeral_airflow_db = check.opt_bool_param(
        use_ephemeral_airflow_db, "use_ephemeral_airflow_db"
    )

    @op(
        name=normalized_name(task.task_id, unique_id),
        required_resource_keys={"airflow_db"} if use_ephemeral_airflow_db else None,
        ins={"airflow_task_ready": In(Nothing)},
        out={"airflow_task_complete": Out(Nothing)},
        config_schema={
            "mock_xcom": Field(bool, default_value=mock_xcom),
            "use_ephemeral_airflow_db": Field(bool, default_value=use_ephemeral_airflow_db),
        },
        retry_policy=RetryPolicy(
            max_retries=task.retries if task.retries is not None else 0,
            delay=task.retry_delay.total_seconds() if task.retry_delay is not None else 0,
        ),
    )
    def _solid(context):  # pylint: disable=unused-argument
        # reloading forces picking up any config that's been set for execution
        importlib.reload(airflow)
        mock_xcom = context.op_config["mock_xcom"]
        use_ephemeral_airflow_db = context.op_config["use_ephemeral_airflow_db"]
        context.log.info("Running Airflow task: {task_id}".format(task_id=task.task_id))

        if context.has_partition_key:
            # for airflow DAGs that have been turned into SDAs
            execution_date_str = context.pipeline_run.tags.get("dagster/partition")
            execution_date = dateutil.parser.parse(execution_date_str)
            # execution_date = execution_date.replace(tzinfo=pytz.timezone(dag.timezone.name))
        else:
            # for airflow DAGs that have not been turned into SDAs
            if AIRFLOW_EXECUTION_DATE_STR not in context.pipeline_run.tags:
                raise DagsterInvariantViolationError(
                    'Could not find "{AIRFLOW_EXECUTION_DATE_STR}" in tags "{tags}". Please '
                    'add "{AIRFLOW_EXECUTION_DATE_STR}" to job tags before executing'.format(
                        AIRFLOW_EXECUTION_DATE_STR=AIRFLOW_EXECUTION_DATE_STR,
                        tags=context.pipeline_run.tags,
                    )
                )
            execution_date_str = context.pipeline_run.tags.get(AIRFLOW_EXECUTION_DATE_STR)
            check.str_param(execution_date_str, "execution_date_str")
            try:
                execution_date = dateutil.parser.parse(execution_date_str)
            except ValueError:
                raise DagsterInvariantViolationError(
                    'Could not parse execution_date "{execution_date_str}". Please use datetime'
                    " format compatible with  dateutil.parser.parse.".format(
                        execution_date_str=execution_date_str,
                    )
                )
            except OverflowError:
                raise DagsterInvariantViolationError(
                    'Date "{execution_date_str}" exceeds the largest valid C integer on the system.'
                    .format(
                        execution_date_str=execution_date_str,
                    )
                )

        check.inst_param(execution_date, "execution_date", datetime.datetime)

        with _mock_xcom() if mock_xcom and not use_ephemeral_airflow_db else nullcontext():
            with replace_airflow_logger_handlers():
                if airflow_version >= "2.0.0":
                    if use_ephemeral_airflow_db:
                        dag = context.resources.airflow_db["dag"]
                        dagrun = context.resources.airflow_db["dagrun"]
                        ti = dagrun.get_task_instance(task_id=task.task_id)
                        ti.task = dag.get_task(task_id=task.task_id)
                        ti.run(ignore_ti_state=True)
                    else:
                        # the airflow db is not initialized so no dagrun or task instance exists
                        ti = TaskInstance(
                            task=task,
                            execution_date=execution_date,
                            run_id=f"dagster_airflow_run_{execution_date}",
                        )
                        ti_context = (
                            dagster_get_template_context(ti, task, execution_date)
                            if not use_airflow_template_context
                            else ti.get_template_context()
                        )
                        task.render_template_fields(ti_context)
                        task.execute(ti_context)
                else:
                    if use_ephemeral_airflow_db:
                        dag = context.resources.airflow_db["dag"]
                        dagrun = context.resources.airflow_db["dagrun"]
                        ti = dagrun.get_task_instance(task_id=task.task_id)
                        ti.task = dag.get_task(task_id=task.task_id)
                        ti.run(ignore_ti_state=True)
                    else:
                        ti = TaskInstance(task=task, execution_date=execution_date)
                        ti_context = (
                            dagster_get_template_context(ti, task, execution_date)
                            if not use_airflow_template_context
                            else ti.get_template_context()
                        )
                        task.render_template_fields(ti_context)
                        task.execute(ti_context)
                return None

    return _solid


def dagster_get_template_context(task_instance, task, execution_date):
    """
    Modified from /airflow/models/taskinstance.py to not reference Airflow DB.

    (1) Removes the following block, which queries DB, removes dagrun instances, recycles run_id
    if hasattr(task, 'dag'):
        if task.dag.params:
            params.update(task.dag.params)
        from airflow.models.dagrun import DagRun  # Avoid circular import

        dag_run = (
            session.query(DagRun)
            .filter_by(dag_id=task.dag.dag_id, execution_date=execution_date)
            .first()
        )
        run_id = dag_run.run_id if dag_run else None
        session.expunge_all()
        session.commit()
    (2) Removes returning 'conf': conf which passes along Airflow config
    (3) Removes 'var': {'value': VariableAccessor(), 'json': VariableJsonAccessor()}, which allows
        fetching Variable from Airflow DB
    """
    from airflow import macros

    tables = None
    if "tables" in task.params:
        tables = task.params["tables"]

    params = {}
    run_id = ""
    dag_run = None

    ds = execution_date.strftime("%Y-%m-%d")
    ts = execution_date.isoformat()
    yesterday_ds = (execution_date - datetime.timedelta(1)).strftime("%Y-%m-%d")
    tomorrow_ds = (execution_date + datetime.timedelta(1)).strftime("%Y-%m-%d")

    # For manually triggered dagruns that aren't run on a schedule, next/previous
    # schedule dates don't make sense, and should be set to execution date for
    # consistency with how execution_date is set for manually triggered tasks, i.e.
    # triggered_date == execution_date.
    if dag_run and dag_run.external_trigger:
        prev_execution_date = execution_date
        next_execution_date = execution_date
    else:
        prev_execution_date = task.dag.previous_schedule(execution_date)
        next_execution_date = task.dag.following_schedule(execution_date)

    next_ds = None
    next_ds_nodash = None
    if next_execution_date:
        next_ds = next_execution_date.strftime("%Y-%m-%d")
        next_ds_nodash = next_ds.replace("-", "")
        next_execution_date = pendulum.instance(next_execution_date)

    prev_ds = None
    prev_ds_nodash = None
    if prev_execution_date:
        prev_ds = prev_execution_date.strftime("%Y-%m-%d")
        prev_ds_nodash = prev_ds.replace("-", "")
        prev_execution_date = pendulum.instance(prev_execution_date)

    ds_nodash = ds.replace("-", "")
    ts_nodash = execution_date.strftime("%Y%m%dT%H%M%S")
    ts_nodash_with_tz = ts.replace("-", "").replace(":", "")
    yesterday_ds_nodash = yesterday_ds.replace("-", "")
    tomorrow_ds_nodash = tomorrow_ds.replace("-", "")

    ti_key_str = "{dag_id}__{task_id}__{ds_nodash}".format(
        dag_id=task.dag_id, task_id=task.task_id, ds_nodash=ds_nodash
    )

    if task.params:
        params.update(task.params)

    return {
        "dag": task.dag,
        "ds": ds,
        "next_ds": next_ds,
        "next_ds_nodash": next_ds_nodash,
        "prev_ds": prev_ds,
        "prev_ds_nodash": prev_ds_nodash,
        "ds_nodash": ds_nodash,
        "ts": ts,
        "ts_nodash": ts_nodash,
        "ts_nodash_with_tz": ts_nodash_with_tz,
        "yesterday_ds": yesterday_ds,
        "yesterday_ds_nodash": yesterday_ds_nodash,
        "tomorrow_ds": tomorrow_ds,
        "tomorrow_ds_nodash": tomorrow_ds_nodash,
        "END_DATE": ds,
        "end_date": ds,
        "dag_run": dag_run,
        "run_id": run_id,
        "execution_date": pendulum.instance(execution_date),
        "prev_execution_date": prev_execution_date,
        "prev_execution_date_success": lazy_object_proxy.Proxy(
            lambda: task_instance.previous_execution_date_success
        ),
        "prev_start_date_success": lazy_object_proxy.Proxy(
            lambda: task_instance.previous_start_date_success
        ),
        "next_execution_date": next_execution_date,
        "latest_date": ds,
        "macros": macros,
        "params": params,
        "tables": tables,
        "task": task,
        "task_instance": task_instance,
        "ti": task_instance,
        "task_instance_key_str": ti_key_str,
        "test_mode": task_instance.test_mode,
        "inlets": task.inlets,
        "outlets": task.outlets,
    }
