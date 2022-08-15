import datetime
import logging
import sys
from contextlib import contextmanager

import dateutil
import lazy_object_proxy
import pendulum
from airflow.models import TaskInstance
from airflow.models.baseoperator import BaseOperator
from airflow.models.dag import DAG
from airflow.models.dagbag import DagBag
from airflow.settings import LOG_FORMAT
from dagster_airflow.patch_airflow_example_dag import patch_airflow_example_dag

from dagster import (
    DagsterInvariantViolationError,
    DependencyDefinition,
    In,
    MultiDependencyDefinition,
    Nothing,
    Out,
)
from dagster import _check as check
from dagster import op, repository
from dagster._core.definitions.utils import VALID_NAME_REGEX, validate_tags
from dagster._core.instance import AIRFLOW_EXECUTION_DATE_STR, IS_AIRFLOW_INGEST_PIPELINE_STR
from dagster._legacy import PipelineDefinition, SolidDefinition


class DagsterAirflowError(Exception):
    pass


def contains_duplicate_task_names(dag_bag, refresh_from_airflow_db):
    check.inst_param(dag_bag, "dag_bag", DagBag)
    check.bool_param(refresh_from_airflow_db, "refresh_from_airflow_db")
    seen_task_names = set()

    # To enforce predictable iteration order
    sorted_dag_ids = sorted(dag_bag.dag_ids)
    for dag_id in sorted_dag_ids:
        dag = dag_bag.dags.get(dag_id) if not refresh_from_airflow_db else dag_bag.get_dag(dag_id)
        for task in dag.tasks:
            if task.task_id in seen_task_names:
                return True
            else:
                seen_task_names.add(task.task_id)
    return False


def make_dagster_repo_from_airflow_dag_bag(
    dag_bag,
    repo_name,
    refresh_from_airflow_db=False,
    use_airflow_template_context=False,
):
    """Construct a Dagster repository corresponding to Airflow DAGs in DagBag.

    Usage:
        Create `make_dagster_repo.py`:
            from dagster_airflow.dagster_pipeline_factory import make_dagster_repo_from_airflow_dag_bag
            from airflow_home import my_dag_bag

            def make_repo_from_dag_bag():
                return make_dagster_repo_from_airflow_dag_bag(my_dag_bag, 'my_repo_name')

        Use RepositoryDefinition as usual, for example:
            `dagit -f path/to/make_dagster_repo.py -n make_repo_from_dag_bag`

    Args:
        dag_path (str): Path to directory or file that contains Airflow Dags
        repo_name (str): Name for generated RepositoryDefinition
        refresh_from_airflow_db (bool): If True, will refresh DAG if expired via DagBag.get_dag(),
            which requires access to initialized Airflow DB. If False (recommended), gets dag from
            DagBag's dags dict without depending on Airflow DB. (default: False)
        use_airflow_template_context (bool): If True, will call get_template_context() on the
            Airflow TaskInstance model which requires and modifies the DagRun table.
            (default: False)

    Returns:
        RepositoryDefinition
    """
    check.inst_param(dag_bag, "dag_bag", DagBag)
    check.str_param(repo_name, "repo_name")
    check.bool_param(refresh_from_airflow_db, "refresh_from_airflow_db")
    check.bool_param(use_airflow_template_context, "use_airflow_template_context")

    use_unique_id = contains_duplicate_task_names(dag_bag, refresh_from_airflow_db)

    pipeline_defs = []
    count = 0
    # To enforce predictable iteration order
    sorted_dag_ids = sorted(dag_bag.dag_ids)
    for dag_id in sorted_dag_ids:
        # Only call Airflow DB via dag_bag.get_dag(dag_id) if refresh_from_airflow_db is True
        dag = dag_bag.dags.get(dag_id) if not refresh_from_airflow_db else dag_bag.get_dag(dag_id)
        if not use_unique_id:
            pipeline_defs.append(
                make_dagster_pipeline_from_airflow_dag(
                    dag=dag,
                    tags=None,
                    use_airflow_template_context=use_airflow_template_context,
                )
            )
        else:
            pipeline_defs.append(
                make_dagster_pipeline_from_airflow_dag(
                    dag=dag,
                    tags=None,
                    use_airflow_template_context=use_airflow_template_context,
                    unique_id=count,
                )
            )
            count += 1

    @repository(name=repo_name)
    def _repo():
        return pipeline_defs

    return _repo


def make_dagster_repo_from_airflow_example_dags(repo_name="airflow_example_dags_repo"):
    """Construct a Dagster repository for Airflow's example DAGs.

    Execution of the following Airflow example DAGs is not currently supported:
            'example_external_task_marker_child',
            'example_pig_operator',
            'example_skip_dag',
            'example_trigger_target_dag',
            'example_xcom',
            'test_utils',

    Usage:

        Create `make_dagster_repo.py`:
            from dagster_airflow.dagster_pipeline_factory import make_dagster_repo_from_airflow_example_dags

            def make_airflow_example_dags():
                return make_dagster_repo_from_airflow_example_dags()

        Use RepositoryDefinition as usual, for example:
            `dagit -f path/to/make_dagster_repo.py -n make_airflow_example_dags`

    Args:
        repo_name (str): Name for generated RepositoryDefinition

    Returns:
        RepositoryDefinition
    """
    dag_bag = DagBag(
        dag_folder="some/empty/folder/with/no/dags",  # prevent defaulting to settings.DAGS_FOLDER
        include_examples=True,
    )

    # There is a bug in Airflow v1.10.8, v1.10.9, v1.10.10 where the python_callable for task
    # 'search_catalog' is missing a required position argument '_'. It is currently fixed in master.
    # v1.10 stable: https://github.com/apache/airflow/blob/v1-10-stable/airflow/example_dags/example_complex.py#L133
    # master (05-05-2020): https://github.com/apache/airflow/blob/master/airflow/example_dags/example_complex.py#L136
    patch_airflow_example_dag(dag_bag)

    return make_dagster_repo_from_airflow_dag_bag(dag_bag, repo_name)


def make_dagster_repo_from_airflow_dags_path(
    dag_path,
    repo_name,
    safe_mode=True,
    store_serialized_dags=False,
    use_airflow_template_context=False,
):
    """Construct a Dagster repository corresponding to Airflow DAGs in dag_path.

    ``DagBag.get_dag()`` dependency requires Airflow DB to be initialized.

    Usage:
        Create ``make_dagster_repo.py``:

        .. code-block:: python

            from dagster_airflow.dagster_pipeline_factory import make_dagster_repo_from_airflow_dags_path

            def make_repo_from_dir():
                return make_dagster_repo_from_airflow_dags_path(
                    '/path/to/dags/', 'my_repo_name'
                )

        Use RepositoryDefinition as usual, for example:
        ``dagit -f path/to/make_dagster_repo.py -n make_repo_from_dir``

    Args:
        dag_path (str): Path to directory or file that contains Airflow Dags
        repo_name (str): Name for generated RepositoryDefinition
        include_examples (bool): True to include Airflow's example DAGs. (default: False)
        safe_mode (bool): True to use Airflow's default heuristic to find files that contain DAGs
            (ie find files that contain both b'DAG' and b'airflow') (default: True)
        store_serialized_dags (bool): True to read Airflow DAGS from Airflow DB. False to read DAGS
            from Python files. (default: False)
        use_airflow_template_context (bool): If True, will call get_template_context() on the
            Airflow TaskInstance model which requires and modifies the DagRun table.
            (default: False)

    Returns:
        RepositoryDefinition
    """
    check.str_param(dag_path, "dag_path")
    check.str_param(repo_name, "repo_name")
    check.bool_param(safe_mode, "safe_mode")
    check.bool_param(store_serialized_dags, "store_serialized_dags")
    check.bool_param(use_airflow_template_context, "use_airflow_template_context")

    try:
        dag_bag = DagBag(
            dag_folder=dag_path,
            include_examples=False,  # Exclude Airflow example dags
            safe_mode=safe_mode,
            store_serialized_dags=store_serialized_dags,
        )
    except Exception:
        raise DagsterAirflowError("Error initializing airflow.models.dagbag object with arguments")

    return make_dagster_repo_from_airflow_dag_bag(dag_bag, repo_name, use_airflow_template_context)


def make_dagster_pipeline_from_airflow_dag(
    dag, tags=None, use_airflow_template_context=False, unique_id=None
):
    """Construct a Dagster pipeline corresponding to a given Airflow DAG.

    Tasks in the resulting pipeline will execute the ``execute()`` method on the corresponding
    Airflow Operator. Dagster, any dependencies required by Airflow Operators, and the module
    containing your DAG definition must be available in the Python environment within which your
    Dagster solids execute.

    To set Airflow's ``execution_date`` for use with Airflow Operator's ``execute()`` methods,
    either:

    1. (Best for ad hoc runs) Run Pipeline with 'default' preset, which sets execution_date to the
        time (in UTC) of pipeline invocation:

        .. code-block:: python

            execute_pipeline(
                pipeline=make_dagster_pipeline_from_airflow_dag(dag=dag),
                preset='default')

    2. Add ``{'airflow_execution_date': utc_date_string}`` to the PipelineDefinition tags. This will
       override behavior from (1).

        .. code-block:: python

            execute_pipeline(
                make_dagster_pipeline_from_airflow_dag(
                    dag=dag,
                    tags={'airflow_execution_date': utc_execution_date_str}
                )
            )

    3. (Recommended) Add ``{'airflow_execution_date': utc_date_string}`` to the PipelineRun tags,
        such as in the Dagit UI. This will override behavior from (1) and (2)


    We apply normalized_name() to the dag id and task ids when generating pipeline name and solid
    names to ensure that names conform to Dagster's naming conventions.

    Args:
        dag (DAG): The Airflow DAG to compile into a Dagster pipeline
        tags (Dict[str, Field]): Pipeline tags. Optionally include
            `tags={'airflow_execution_date': utc_date_string}` to specify execution_date used within
            execution of Airflow Operators.
        use_airflow_template_context (bool): If True, will call get_template_context() on the
            Airflow TaskInstance model which requires and modifies the DagRun table.
            (default: False)
        unique_id (int): If not None, this id will be postpended to generated solid names. Used by
            framework authors to enforce unique solid names within a repo.

    Returns:
        pipeline_def (PipelineDefinition): The generated Dagster pipeline

    """
    check.inst_param(dag, "dag", DAG)
    tags = check.opt_dict_param(tags, "tags")
    check.bool_param(use_airflow_template_context, "use_airflow_template_context")
    unique_id = check.opt_int_param(unique_id, "unique_id")

    if IS_AIRFLOW_INGEST_PIPELINE_STR not in tags:
        tags[IS_AIRFLOW_INGEST_PIPELINE_STR] = "true"

    tags = validate_tags(tags)

    pipeline_dependencies, solid_defs = _get_pipeline_definition_args(
        dag, use_airflow_template_context, unique_id
    )
    pipeline_def = PipelineDefinition(
        name=normalized_name(dag.dag_id, None),
        solid_defs=solid_defs,
        dependencies=pipeline_dependencies,
        tags=tags,
    )
    return pipeline_def


# Airflow DAG ids and Task ids allow a larger valid character set (alphanumeric characters,
# dashes, dots and underscores) than Dagster's naming conventions (alphanumeric characters,
# underscores), so Dagster will strip invalid characters and replace with '_'
def normalized_name(name, unique_id):
    base_name = "airflow_" + "".join(c if VALID_NAME_REGEX.match(c) else "_" for c in name)
    if not unique_id:
        return base_name
    else:
        return base_name + "_" + str(unique_id)


def _get_pipeline_definition_args(dag, use_airflow_template_context, unique_id=None):
    check.inst_param(dag, "dag", DAG)
    check.bool_param(use_airflow_template_context, "use_airflow_template_context")
    unique_id = check.opt_int_param(unique_id, "unique_id")

    pipeline_dependencies = {}
    solid_defs = []
    seen_tasks = []

    # To enforce predictable iteration order
    dag_roots = sorted(dag.roots, key=lambda x: x.task_id)
    for task in dag_roots:
        _traverse_airflow_dag(
            task,
            seen_tasks,
            pipeline_dependencies,
            solid_defs,
            use_airflow_template_context,
            unique_id,
        )
    return (pipeline_dependencies, solid_defs)


def _traverse_airflow_dag(
    task,
    seen_tasks,
    pipeline_dependencies,
    solid_defs,
    use_airflow_template_context,
    unique_id,
):
    check.inst_param(task, "task", BaseOperator)
    check.list_param(seen_tasks, "seen_tasks", BaseOperator)
    check.list_param(solid_defs, "solid_defs", SolidDefinition)
    check.bool_param(use_airflow_template_context, "use_airflow_template_context")
    unique_id = check.opt_int_param(unique_id, "unique_id")

    seen_tasks.append(task)
    current_solid = make_dagster_solid_from_airflow_task(
        task, use_airflow_template_context, unique_id
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
                child_task,
                seen_tasks,
                pipeline_dependencies,
                solid_defs,
                use_airflow_template_context,
                unique_id,
            )


@contextmanager
def replace_airflow_logger_handlers():
    prev_airflow_handlers = logging.getLogger("airflow.task").handlers
    try:
        # Redirect airflow handlers to stdout / compute logs
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        root = logging.getLogger("airflow.task")
        root.handlers = [handler]
        yield
    finally:
        # Restore previous log handlers
        logging.getLogger("airflow.task").handlers = prev_airflow_handlers


# If unique_id is not None, this id will be postpended to generated solid names, generally used
# to enforce unique solid names within a repo.
def make_dagster_solid_from_airflow_task(task, use_airflow_template_context, unique_id=None):
    check.inst_param(task, "task", BaseOperator)
    check.bool_param(use_airflow_template_context, "use_airflow_template_context")
    unique_id = check.opt_int_param(unique_id, "unique_id")

    @op(
        name=normalized_name(task.task_id, unique_id),
        ins={"airflow_task_ready": In(Nothing)},
        out={"airflow_task_complete": Out(Nothing)},
    )
    def _solid(context):  # pylint: disable=unused-argument
        if AIRFLOW_EXECUTION_DATE_STR not in context.pipeline_run.tags:
            raise DagsterInvariantViolationError(
                'Could not find "{AIRFLOW_EXECUTION_DATE_STR}" in {target} tags "{tags}". Please '
                'add "{AIRFLOW_EXECUTION_DATE_STR}" to {target} tags before executing'.format(
                    target="job" if context.pipeline_def.is_graph_job_op_target else "pipeline",
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
                'Could not parse execution_date "{execution_date_str}". Please use datetime format '
                "compatible with  dateutil.parser.parse.".format(
                    execution_date_str=execution_date_str,
                )
            )
        except OverflowError:
            raise DagsterInvariantViolationError(
                'Date "{execution_date_str}" exceeds the largest valid C integer on the system.'.format(
                    execution_date_str=execution_date_str,
                )
            )

        check.inst_param(execution_date, "execution_date", datetime.datetime)

        with replace_airflow_logger_handlers():
            task_instance = TaskInstance(task=task, execution_date=execution_date)

            ti_context = (
                dagster_get_template_context(task_instance, task, execution_date)
                if not use_airflow_template_context
                else task_instance.get_template_context()
            )
            task.render_template_fields(ti_context)

            task.execute(ti_context)

            return None

    return _solid


def dagster_get_template_context(task_instance, task, execution_date):
    """
    Modified from /airflow/models/taskinstance.py to not reference Airflow DB
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
